from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from read_mrpack_tui import tree_search


class TreeSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "sample.mrpack"
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("modrinth.index.json", "{}")
            archive.writestr("overrides/config/lantern.txt", "A bright lantern lives here.")
            archive.writestr("overrides/config/other.txt", "Nothing to see.")
            archive.writestr("assets/icon.bin", b"\x00\x01binary")
            archive.writestr("large.txt", "needlecontent" * 8)
        with zipfile.ZipFile(self.path) as archive:
            self.entries = archive.infolist()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_folder_match_retains_descendants(self) -> None:
        result, _ = tree_search.search_tree(self.path, self.entries, "config")
        self.assertEqual(result.matches[0].path, ("overrides", "config"))
        self.assertIn(("overrides", "config", "lantern.txt"), result.visible_paths)
        self.assertIn(("overrides", "config", "other.txt"), result.visible_paths)

    def test_text_match_excludes_binary_entries(self) -> None:
        result, cache = tree_search.search_tree(self.path, self.entries, "bright lantern")
        self.assertEqual([match.path for match in result.matches], [("overrides", "config", "lantern.txt")])
        self.assertEqual(result.matches[0].sources, frozenset({"content"}))
        self.assertIsNotNone(cache)
        self.assertGreater(cache.skipped_nontext, 0)

    def test_empty_query_returns_full_tree_without_scanning_text(self) -> None:
        result, cache = tree_search.search_tree(self.path, self.entries, "")
        self.assertFalse(result.matches)
        self.assertIsNone(cache)
        self.assertIn(("assets", "icon.bin"), result.visible_paths)

    def test_text_scan_enforces_entry_limit(self) -> None:
        old_file_limit, old_total_limit = tree_search.MAX_TEXT_FILE_BYTES, tree_search.MAX_TEXT_TOTAL_BYTES
        tree_search.MAX_TEXT_FILE_BYTES = 32
        tree_search.MAX_TEXT_TOTAL_BYTES = 48
        try:
            result, cache = tree_search.search_tree(self.path, self.entries, "needlecontent")
        finally:
            tree_search.MAX_TEXT_FILE_BYTES = old_file_limit
            tree_search.MAX_TEXT_TOTAL_BYTES = old_total_limit
        self.assertFalse(result.matches)
        self.assertIsNotNone(cache)
        self.assertGreater(cache.skipped_large, 0)


if __name__ == "__main__":
    unittest.main()
