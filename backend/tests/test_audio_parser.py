import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))

from workers.parsers.audio_parser import AudioParser


def segment(speaker: int, text: str, start: int, end: int):
    return SimpleNamespace(speaker=speaker, text=text, start=start, end=end)


class AudioParserMergeTests(unittest.TestCase):
    def test_merges_nearby_chinese_segments_from_same_speaker(self):
        parser = AudioParser()

        blocks = parser._build_blocks([
            segment(0, "我们现在开始。", 0, 900),
            segment(0, "接下来讲第一个问题。", 1100, 2600),
        ])

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].content, "我们现在开始。接下来讲第一个问题。")
        self.assertEqual(blocks[0].extra["time_start"], 0)
        self.assertEqual(blocks[0].extra["time_end"], 2600)
        self.assertEqual(blocks[0].extra["source_segment_count"], 2)

    def test_keeps_different_speakers_separate(self):
        parser = AudioParser()

        blocks = parser._build_blocks([
            segment(0, "这个问题我先说一下。", 0, 900),
            segment(1, "我补充一个细节。", 1000, 1800),
        ])

        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].content, "这个问题我先说一下。")
        self.assertEqual(blocks[1].content, "我补充一个细节。")

    def test_text_units_handle_chinese_and_english_differently(self):
        parser = AudioParser()

        self.assertEqual(parser._text_units("中文测试"), 4)
        self.assertEqual(parser._text_units("hello world"), 4)
        self.assertLess(parser._text_units("internationalization"), len("internationalization"))


if __name__ == "__main__":
    unittest.main()
