"""Bounded archive-tree search helpers shared by the Textual UI."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

MAX_TEXT_FILE_BYTES = 2 * 1024 * 1024
MAX_TEXT_TOTAL_BYTES = 32 * 1024 * 1024

PathKey = tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TreeMatch:
    """One matching file or directory path and its match sources."""

    path: PathKey
    sources: frozenset[str]


@dataclass(slots=True)
class TextSearchCache:
    """Lazily decoded UTF-8 file contents for one bounded archive scan."""

    contents: dict[PathKey, str] = field(default_factory=dict)
    scanned_bytes: int = 0
    skipped_nontext: int = 0
    skipped_large: int = 0
    limited: bool = False


@dataclass(frozen=True, slots=True)
class TreeSearchResult:
    """Filtered tree data without exposing matched text content."""

    query: str
    matches: tuple[TreeMatch, ...]
    visible_paths: frozenset[PathKey]
    limited: bool


def _key(filename: str) -> PathKey:
    return tuple(part for part in filename.rstrip("/").split("/") if part)


def _archive_paths(entries: list[zipfile.ZipInfo]) -> tuple[set[PathKey], set[PathKey], dict[PathKey, zipfile.ZipInfo]]:
    all_paths: set[PathKey] = set()
    directories: set[PathKey] = set()
    files: dict[PathKey, zipfile.ZipInfo] = {}
    for info in entries:
        path = _key(info.filename)
        if not path:
            continue
        all_paths.add(path)
        for index in range(1, len(path)):
            directories.add(path[:index])
            all_paths.add(path[:index])
        if info.is_dir():
            directories.add(path)
        else:
            files[path] = info
    return all_paths, directories, files


def scan_text_contents(path: Path, entries: list[zipfile.ZipInfo]) -> TextSearchCache:
    """Read only bounded, UTF-8 text entries and skip binary or oversized data."""

    _, _, files = _archive_paths(entries)
    cache = TextSearchCache()
    try:
        with zipfile.ZipFile(path) as archive:
            for key, info in sorted(files.items()):
                if info.file_size > MAX_TEXT_FILE_BYTES:
                    cache.skipped_large += 1
                    continue
                if cache.scanned_bytes + info.file_size > MAX_TEXT_TOTAL_BYTES:
                    cache.limited = True
                    continue
                try:
                    payload = archive.read(info)
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    cache.skipped_nontext += 1
                    continue
                cache.scanned_bytes += len(payload)
                if len(payload) > MAX_TEXT_FILE_BYTES:
                    cache.skipped_large += 1
                    continue
                if b"\x00" in payload:
                    cache.skipped_nontext += 1
                    continue
                try:
                    cache.contents[key] = payload.decode("utf-8-sig").casefold()
                except UnicodeDecodeError:
                    cache.skipped_nontext += 1
    except (OSError, zipfile.BadZipFile):
        return cache
    return cache


def search_tree(
    path: Path,
    entries: list[zipfile.ZipInfo],
    query: str,
    cache: TextSearchCache | None = None,
) -> tuple[TreeSearchResult, TextSearchCache | None]:
    """Find matching tree nodes by component name or bounded text content."""

    needle = query.casefold().strip()
    all_paths, directories, _ = _archive_paths(entries)
    if not needle:
        return TreeSearchResult("", (), frozenset(all_paths), False), cache

    if cache is None:
        cache = scan_text_contents(path, entries)

    sources: dict[PathKey, set[str]] = {}
    for path_key in all_paths:
        for index, component in enumerate(path_key):
            if needle in component.casefold():
                sources.setdefault(path_key[: index + 1], set()).add("path")
    for path_key, content in cache.contents.items():
        if needle in content:
            sources.setdefault(path_key, set()).add("content")

    visible: set[PathKey] = set()
    for path_key in sources:
        for index in range(1, len(path_key) + 1):
            visible.add(path_key[:index])
        if path_key in directories:
            visible.update(candidate for candidate in all_paths if candidate[: len(path_key)] == path_key)

    matches = tuple(
        TreeMatch(path_key, frozenset(match_sources))
        for path_key, match_sources in sorted(sources.items())
    )
    return TreeSearchResult(needle, matches, frozenset(visible), cache.limited), cache
