from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from textual.widgets import Input, Tree

from read_mrpack_tui.app import MrpackApp, read_pack
from read_mrpack_tui.i18n import load_translator


class TreeUiTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_focuses_first_match_and_cycles_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.mrpack"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("modrinth.index.json", "{}")
                archive.writestr("config/lantern.txt", "bright lantern")
                archive.writestr("config/lantern-two.txt", "another lantern")

            app = MrpackApp(load_translator("en-us"))
            async with app.run_test() as pilot:
                app.show_pack(read_pack(str(path)))
                app.query_one("#tree_filter", Input).value = "lantern"
                await pilot.pause(0.8)
                tree = app.query_one("#file_tree", Tree)
                self.assertIs(app.focused, tree)
                self.assertEqual(len(app._tree_match_nodes), 2)
                first_index = app._tree_match_index
                await pilot.press("s")
                self.assertNotEqual(first_index, app._tree_match_index)
                await pilot.press("w")
                self.assertEqual(first_index, app._tree_match_index)


if __name__ == "__main__":
    unittest.main()
