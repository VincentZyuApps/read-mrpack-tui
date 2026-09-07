#!/usr/bin/env python3
"""Interactive reader for Modrinth .mrpack archives."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, Input, Static, TabbedContent, TabPane, Tree

from . import __version__
from .i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, Translator, load_translator
from .tree_search import TextSearchCache, TreeSearchResult, search_tree


def human_size(size: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def environment(entry: dict[str, Any], side: str) -> str:
    """Return the stable Modrinth environment value for one side."""
    return entry.get("env", {}).get(side, "required")


def side_group(entry: dict[str, Any]) -> str:
    """Return a stable group identifier, independent from the display language."""
    client = environment(entry, "client") != "unsupported"
    server = environment(entry, "server") != "unsupported"
    if client and server:
        return "both"
    if client:
        return "client_only"
    if server:
        return "server_only"
    return "unsupported"


class PackReadError(ValueError):
    def __init__(self, key: str, **values: object) -> None:
        super().__init__(key)
        self.key = key
        self.values = values


class SearchTree(Tree[None]):
    """A Tree whose navigation keys cycle through active search matches."""

    BINDINGS = [
        Binding("up,w", "previous_search_match", show=False),
        Binding("down,s", "next_search_match", show=False),
    ]

    def action_previous_search_match(self) -> None:
        self.app._move_tree_match(-1)  # type: ignore[attr-defined]

    def action_next_search_match(self) -> None:
        self.app._move_tree_match(1)  # type: ignore[attr-defined]


@dataclass(slots=True)
class PackData:
    path: Path
    index: dict[str, Any]
    archive_entries: list[zipfile.ZipInfo]
    text_search_cache: TextSearchCache | None = None

    @property
    def files(self) -> list[dict[str, Any]]:
        return self.index.get("files", [])

    @property
    def groups(self) -> Counter[str]:
        return Counter(side_group(entry) for entry in self.files)

    @property
    def archive_roots(self) -> Counter[str]:
        return Counter(info.filename.split("/", 1)[0] for info in self.archive_entries if info.filename)


def read_pack(value: str) -> PackData:
    path = Path(value).expanduser()
    if not path.is_file():
        raise PackReadError("errors.file_not_found", path=path)
    if path.suffix.casefold() != ".mrpack":
        raise PackReadError("errors.not_mrpack")

    try:
        with zipfile.ZipFile(path) as archive:
            try:
                raw_index = archive.read("modrinth.index.json")
            except KeyError as error:
                raise PackReadError("errors.missing_index") from error
            try:
                index = json.loads(raw_index.decode("utf-8-sig"))
            except json.JSONDecodeError as error:
                raise PackReadError("errors.invalid_json") from error
            entries = archive.infolist()
    except PackReadError:
        raise
    except zipfile.BadZipFile as error:
        raise PackReadError("errors.invalid_archive") from error
    except OSError as error:
        raise PackReadError("errors.read_failed", detail=str(error)) from error
    return PackData(path.resolve(), index, entries)


class MrpackApp(App[None]):
    """Textual UI for browsing the contents of a Modrinth pack."""

    CSS = """
    Screen { background: #101912; color: #e0eee4; }
    Header { background: #123d27; color: #f4fff7; }
    #path_bar { height: auto; padding: 1 2; background: #15271c; }
    #pack_path { width: 1fr; margin-right: 1; }
    #app_version { width: auto; min-width: 8; padding: 1 0 1 1; color: #84dca2; text-style: bold; }
    #status { height: 1; padding: 0 2; color: #afc8b7; background: #15271c; }
    #status.error { color: #ffb4a9; }
    TabbedContent { height: 1fr; margin: 1 2; }
    TabPane { padding: 1 0; }
    #summary { height: auto; padding: 1 2; margin-bottom: 1; background: #15271c; border: round #356345; }
    #dependencies, #files, #archive, #file_tree { height: 1fr; border: round #356345; }
    #file_tree { height: 1fr; padding: 1; }
    #filter_bar, #tree_filter_bar { height: auto; margin-bottom: 1; }
    #file_filter, #tree_filter { width: 1fr; }
    #previous_tree_match, #next_tree_match { width: 5; min-width: 5; }
    #tree_search_status { width: auto; color: #84dca2; padding: 1 0 0 1; }
    .section_title { padding: 0 1; color: #1bd96a; text-style: bold; }
    Button { background: #1b3424; color: #dff7e6; border: tall #356345; }
    Button:hover { background: #244b31; border: tall #1bd96a; }
    Button.-primary { background: #1bd96a; color: #062611; text-style: bold; border: tall #55e38b; }
    Button.-primary:hover { background: #55e38b; color: #062611; }
    Input { border: tall #356345; }
    Input:focus { border: tall #1bd96a; }
    ContentTab.-active { color: #1bd96a; text-style: bold; }
    Tabs { color: #1bd96a; }
    DataTable > .datatable--cursor { background: #1f4c30; color: #f4fff7; }
    """

    def __init__(self, translator: Translator, initial_path: str | None = None) -> None:
        super().__init__()
        self.translator = translator
        self.initial_path = initial_path or ""
        self.pack: PackData | None = None
        self._tree_search_timer: Any | None = None
        self._tree_match_nodes: list[Any] = []
        self._tree_match_index = 0
        self.title = self.ui("app.title")
        self.sub_title = self.ui("app.subtitle")
        self.BINDINGS = [
            Binding("ctrl+l", "load_pack", self.ui("actions.load_shortcut"), show=True),
            Binding("ctrl+f", "focus_filter", self.ui("actions.filter_shortcut"), show=True),
            Binding("ctrl+r", "reload_pack", self.ui("actions.reload_shortcut"), show=True),
            Binding("q", "quit", self.ui("actions.quit_shortcut"), show=True),
        ]

    def t(self, key: str, **values: object) -> str:
        return self.translator.t(key, **values)

    def ui(self, key: str, **values: object) -> str:
        return self.translator.ui(key, **values)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="path_bar"):
            yield Input(self.initial_path, placeholder=self.ui("input.pack_path"), id="pack_path")
            yield Button(self.ui("actions.load"), id="load", variant="primary")
            yield Static(f"v{__version__}", id="app_version")
        yield Static(self.ui("status.initial"), id="status")
        with TabbedContent(initial="overview"):
            with TabPane(self.ui("tabs.overview"), id="overview"):
                yield Static(self.ui("summary.no_pack"), id="summary")
                yield Static(self.ui("sections.dependencies"), classes="section_title")
                yield DataTable(id="dependencies", cursor_type="row", zebra_stripes=True)
            with TabPane(self.ui("tabs.indexed_files"), id="indexed_files"):
                with Horizontal(id="filter_bar"):
                    yield Input(placeholder=self.ui("input.file_filter"), id="file_filter")
                    yield Button(self.ui("actions.clear"), id="clear_filter")
                yield DataTable(id="files", cursor_type="row", zebra_stripes=True)
            with TabPane(self.ui("tabs.archive"), id="archive_tab"):
                yield DataTable(id="archive", cursor_type="row", zebra_stripes=True)
            with TabPane(self.ui("tabs.file_tree"), id="file_tree_tab"):
                with Horizontal(id="tree_filter_bar"):
                    yield Input(placeholder=self.ui("input.tree_filter"), id="tree_filter")
                    yield Button(self.ui("actions.clear"), id="clear_tree_filter")
                    yield Button("↑", id="previous_tree_match", tooltip=self.ui("actions.previous_match"), disabled=True)
                    yield Button("↓", id="next_tree_match", tooltip=self.ui("actions.next_match"), disabled=True)
                    yield Static("", id="tree_search_status")
                yield SearchTree(self.ui("tree.root"), id="file_tree")
        yield Footer()

    def on_mount(self) -> None:
        self._setup_tables()
        if self.initial_path:
            self.load_path(self.initial_path)

    def _setup_tables(self) -> None:
        self.query_one("#dependencies", DataTable).add_columns(self.ui("columns.dependency"), self.ui("columns.version"))
        self.query_one("#files", DataTable).add_columns(
            self.ui("columns.path"), self.ui("columns.side"), self.ui("columns.client"),
            self.ui("columns.server"), self.ui("columns.hash"), self.ui("columns.download"),
        )
        self.query_one("#archive", DataTable).add_columns(
            self.ui("columns.archive_root"), self.ui("columns.entries"), self.ui("columns.uncompressed_size")
        )

    def action_load_pack(self) -> None:
        self.load_path(self.query_one("#pack_path", Input).value)

    def action_reload_pack(self) -> None:
        if self.pack:
            self.load_path(str(self.pack.path))

    def action_focus_filter(self) -> None:
        self.query_one("#file_filter", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load":
            self.action_load_pack()
        elif event.button.id == "clear_filter":
            self.query_one("#file_filter", Input).value = ""
        elif event.button.id == "clear_tree_filter":
            self.query_one("#tree_filter", Input).value = ""
        elif event.button.id == "previous_tree_match":
            self._move_tree_match(-1)
        elif event.button.id == "next_tree_match":
            self._move_tree_match(1)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "pack_path":
            self.load_path(event.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "file_filter":
            self.populate_files(event.value)
        elif event.input.id == "tree_filter":
            if self._tree_search_timer:
                self._tree_search_timer.stop()
            self._tree_search_timer = self.set_timer(
                0.35, lambda value=event.value: self.search_file_tree(value)
            )

    @work(thread=True, exclusive=True)
    def load_path(self, value: str) -> None:
        path = value.strip()
        if not path:
            self.call_from_thread(self.set_status, self.ui("status.empty_path"), True)
            return
        try:
            pack = read_pack(path)
        except PackReadError as error:
            self.call_from_thread(self.set_status, self.ui(error.key, **error.values), True)
            return
        self.call_from_thread(self.show_pack, pack)

    def show_pack(self, pack: PackData) -> None:
        self.pack = pack
        self.query_one("#pack_path", Input).value = str(pack.path)
        self.set_status(self.ui("status.loaded", name=pack.path.name, files=len(pack.files), entries=len(pack.archive_entries)))
        self.populate_overview()
        self.populate_files(self.query_one("#file_filter", Input).value)
        self.populate_archive()
        self.query_one("#tree_filter", Input).value = ""
        self.query_one("#tree_search_status", Static).update("")
        self.populate_file_tree()

    def set_status(self, message: str, error: bool = False) -> None:
        status = self.query_one("#status", Static)
        status.update(message)
        status.set_class(error, "error")

    def display_group(self, group: str) -> str:
        return self.ui(f"group.{group}")

    def display_environment(self, value: str) -> str:
        return self.ui(f"environment.{value}")

    def populate_overview(self) -> None:
        if not self.pack:
            return
        groups = self.pack.groups
        self.query_one("#summary", Static).update(
            "\n".join((
                f"[bold #1bd96a]{self.ui('summary.title', name=self.pack.path.name)}[/]",
                self.ui("summary.metadata", format_version=self.pack.index.get("formatVersion", "?"), game=self.pack.index.get("game", "?"), archive_size=human_size(self.pack.path.stat().st_size)),
                self.ui("summary.files", total=len(self.pack.files), both=groups["both"], client_only=groups["client_only"], server_only=groups["server_only"]),
            ))
        )
        table = self.query_one("#dependencies", DataTable)
        table.clear()
        for name, version in sorted(self.pack.index.get("dependencies", {}).items()):
            table.add_row(name, str(version))

    def populate_files(self, filter_value: str = "") -> None:
        table = self.query_one("#files", DataTable)
        table.clear()
        if not self.pack:
            return
        needle = filter_value.casefold().strip()
        for entry in self.pack.files:
            client, server, group = environment(entry, "client"), environment(entry, "server"), side_group(entry)
            download = entry.get("downloads", [""])[0]
            searchable = " ".join((entry.get("path", ""), group, client, server, self.display_group(group), self.display_environment(client), self.display_environment(server), download)).casefold()
            if not needle or needle in searchable:
                table.add_row(entry.get("path", ""), self.display_group(group), self.display_environment(client), self.display_environment(server), entry.get("hashes", {}).get("sha512", "")[:16], download)

    def populate_archive(self) -> None:
        if not self.pack:
            return
        table = self.query_one("#archive", DataTable)
        table.clear()
        sizes: Counter[str] = Counter()
        for info in self.pack.archive_entries:
            sizes[info.filename.split("/", 1)[0]] += info.file_size
        for root, count in self.pack.archive_roots.most_common():
            table.add_row(root or self.ui("archive.root"), str(count), human_size(sizes[root]))

    @work(thread=True, group="tree-search", exclusive=True)
    def search_file_tree(self, value: str) -> None:
        pack = self.pack
        if not pack:
            return
        result, cache = search_tree(pack.path, pack.archive_entries, value, pack.text_search_cache)
        pack.text_search_cache = cache
        self.call_from_thread(self.show_tree_search, pack, result)

    def show_tree_search(self, pack: PackData, result: TreeSearchResult) -> None:
        if self.pack is not pack:
            return
        status = self.query_one("#tree_search_status", Static)
        if not result.query:
            status.update("")
        elif result.limited:
            status.update(self.ui("tree.search_limited", count=len(result.matches)))
        else:
            status.update(self.ui("tree.search_matches", count=len(result.matches)))
        self.populate_file_tree(result)

    def populate_file_tree(self, result: TreeSearchResult | None = None) -> None:
        """Populate a compact, lazily expanded view of every ZIP archive path."""
        tree = self.query_one("#file_tree", Tree)
        tree.clear()
        tree.root.set_label(self.ui("tree.root"))
        tree.root.expand()
        self._tree_match_nodes = []
        self._tree_match_index = 0
        self._set_tree_match_buttons(False)
        if not self.pack:
            return

        nodes: dict[tuple[str, ...], Any] = {(): tree.root}
        paths = sorted({info.filename.rstrip("/") for info in self.pack.archive_entries if info.filename.rstrip("/")})
        folder_keys = {
            parts[:index]
            for path in paths
            for parts in [tuple(part for part in path.split("/") if part)]
            for index in range(1, len(parts))
        }
        folder_keys.update(
            tuple(part for part in info.filename.rstrip("/").split("/") if part)
            for info in self.pack.archive_entries
            if info.is_dir() and info.filename.rstrip("/")
        )
        match_sources = {match.path: match.sources for match in result.matches} if result else {}
        visible_paths = result.visible_paths if result else None
        for path in paths:
            parts = tuple(part for part in path.split("/") if part)
            for index, part in enumerate(parts):
                key = parts[: index + 1]
                if visible_paths is not None and key not in visible_paths:
                    continue
                if key in nodes:
                    continue
                parent = nodes[key[:-1]]
                is_folder = key in folder_keys
                marker = "🔎 " if key in match_sources else ""
                nodes[key] = parent.add(
                    f"{'📁' if is_folder else '📄'} {marker}{part}", allow_expand=is_folder
                )

        if result and result.query and not result.matches:
            tree.root.add(self.ui("tree.no_matches"))
            return
        if not result or not result.matches:
            return

        self._tree_match_nodes = [nodes[match.path] for match in result.matches if match.path in nodes]
        if not self._tree_match_nodes:
            return
        self._set_tree_match_buttons(True)
        first_path = result.matches[0].path
        for index in range(1, len(first_path) + 1):
            path_key = first_path[:index]
            node = nodes.get(path_key)
            if node and path_key in folder_keys:
                node.expand()
        # TreeNode line numbers are assigned during the next screen refresh.
        self.call_after_refresh(self._focus_tree_match)

    def _focus_tree_match(self) -> None:
        if not self._tree_match_nodes:
            return
        tree = self.query_one("#file_tree", Tree)
        node = self._tree_match_nodes[self._tree_match_index]
        tree.move_cursor(node, animate=False)
        tree.scroll_to_node(node, animate=False)
        tree.focus()

    def _move_tree_match(self, offset: int) -> None:
        if not self._tree_match_nodes:
            return
        self._tree_match_index = (self._tree_match_index + offset) % len(self._tree_match_nodes)
        self._focus_tree_match()

    def _set_tree_match_buttons(self, enabled: bool) -> None:
        self.query_one("#previous_tree_match", Button).disabled = not enabled
        self.query_one("#next_tree_match", Button).disabled = not enabled

def parse_arguments(argv: list[str]) -> tuple[argparse.Namespace, Translator]:
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument("--lang", default=DEFAULT_LOCALE)
    bootstrap_args, _ = bootstrap.parse_known_args(argv)
    requested_locale = str(bootstrap_args.lang).casefold()
    translator = load_translator(requested_locale if requested_locale in SUPPORTED_LOCALES else DEFAULT_LOCALE)
    parser = argparse.ArgumentParser(description=translator.t("cli.description"))
    parser.add_argument("pack", nargs="?", help=translator.t("cli.pack_help"))
    parser.add_argument("--lang", default=DEFAULT_LOCALE, choices=SUPPORTED_LOCALES, type=str.casefold, help=translator.t("cli.language_help"))
    args = parser.parse_args(argv)
    return args, load_translator(args.lang)


def run() -> None:
    args, translator = parse_arguments(sys.argv[1:])
    MrpackApp(translator, args.pack).run()


if __name__ == "__main__":
    run()
