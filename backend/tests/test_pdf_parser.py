import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))

from workers.parsers.pdf_parser import PDFParser


class PDFParserMinerUImageTypeTests(unittest.TestCase):
    def test_chart_items_with_image_paths_become_image_blocks(self):
        parser = PDFParser()

        blocks, images = parser._parse_content_list_to_blocks(
            [
                {
                    "type": "chart",
                    "img_path": "images/chart-a.jpg",
                    "content": "",
                    "chart_caption": ["Figure 1: Results."],
                    "bbox": [100, 200, 300, 400],
                    "page_idx": 2,
                }
            ],
            {"images/chart-a.jpg": "/tmp/chart-a.jpg"},
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(images), 1)
        self.assertEqual(blocks[0].content, "[Image]")
        self.assertEqual(blocks[0].page, 3)
        self.assertEqual(blocks[0].extra["bbox"], [100, 200, 300, 400])
        self.assertTrue(blocks[0].extra["is_image"])
        self.assertEqual(blocks[0].extra["image_index"], 0)
        self.assertEqual(blocks[0].extra["image_name"], "chart-a.jpg")
        self.assertEqual(blocks[0].extra["image_source_type"], "chart")
        self.assertEqual(blocks[0].extra["image_caption"], "Figure 1: Results.")
        self.assertEqual(images[0]["file_path"], "/tmp/chart-a.jpg")
        self.assertEqual(images[0]["page"], 3)
        self.assertEqual(images[0]["img_name"], "chart-a.jpg")

    def test_tables_with_image_paths_stay_table_blocks(self):
        parser = PDFParser()

        blocks, images = parser._parse_content_list_to_blocks(
            [
                {
                    "type": "table",
                    "img_path": "images/table-a.jpg",
                    "table_body": "<table><tr><td>A</td></tr></table>",
                    "table_caption": ["Table 1"],
                    "bbox": [10, 20, 30, 40],
                    "page_idx": 0,
                }
            ],
            {"images/table-a.jpg": "/tmp/table-a.jpg"},
        )

        self.assertEqual(len(blocks), 1)
        self.assertEqual(images, [])
        self.assertTrue(blocks[0].extra["is_table"])
        self.assertNotIn("is_image", blocks[0].extra)


if __name__ == "__main__":
    unittest.main()
