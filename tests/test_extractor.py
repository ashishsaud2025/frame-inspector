import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from frame_inspector import cli
from frame_inspector.extractor import FrameExtractor
from frame_inspector.reports import build_report, write_report


class FrameExtractorTests(unittest.TestCase):
    def test_filter_frames(self):
        frames = {
            "I": [{"type": "I", "frame_num": 1, "pts_time": 0.0}],
            "P": [
                {"type": "P", "frame_num": 2, "pts_time": 0.04},
                {"type": "P", "frame_num": 3, "pts_time": 0.08},
                {"type": "P", "frame_num": 4, "pts_time": 0.12},
            ],
            "B": [],
        }
        filtered = FrameExtractor.filter_frames(frames, start_time=0.04, every=2)

        self.assertEqual([frame["frame_num"] for frame in filtered["P"]], [2, 4])

    def test_filter_frames_rejects_invalid_range(self):
        with self.assertRaises(ValueError):
            FrameExtractor.filter_frames({}, start_time=2, end_time=1)

    def test_analyze_frames_groups_supported_types(self):
        probe_output = json.dumps({
            "frames": [
                {"pict_type": "I", "pts_time": "0", "frame_num": "1"},
                {"pict_type": "B", "pts_time": "0.04", "frame_num": "2"},
                {"pict_type": "P", "pts_time": "0.08", "frame_num": "3"},
                {"pict_type": "S", "pts_time": "0.12", "frame_num": "4"},
            ]
        })
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
            with patch("frame_inspector.extractor.subprocess.run") as run:
                run.side_effect = [None, None, type("Result", (), {"stdout": probe_output})()]
                frames = FrameExtractor(video.name).analyze_frames()

        self.assertEqual([frame["type"] for frame in frames["I"]], ["I"])
        self.assertEqual([frame["type"] for frame in frames["B"]], ["B"])
        self.assertEqual([frame["type"] for frame in frames["P"]], ["P"])

    def test_extract_frames_uses_one_ffmpeg_process(self):
        frames = {
            "I": [{"type": "I", "frame_num": 1, "pts_time": 0.0}],
            "P": [{"type": "P", "frame_num": 2, "pts_time": 0.04}],
            "B": [],
        }
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video, tempfile.TemporaryDirectory() as output:
            with patch.object(FrameExtractor, "_validate_ffmpeg"), patch.object(
                FrameExtractor, "analyze_frames", return_value=frames
            ), patch.object(FrameExtractor, "_extract_all_frames") as extract_all:
                def create_images(pattern):
                    pattern_path = Path(pattern)
                    pattern_path.parent.joinpath("frame_00000001.png").touch()
                    pattern_path.parent.joinpath("frame_00000002.png").touch()

                extract_all.side_effect = create_images
                result = FrameExtractor(video.name).extract_frames(output)

        self.assertEqual(len(result["I"]), 1)
        self.assertEqual(len(result["P"]), 1)
        extract_all.assert_called_once()

    def test_video_metadata_normalizes_stream_values(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
            with patch.object(FrameExtractor, "_validate_ffmpeg"), patch.object(
                FrameExtractor,
                "get_video_info",
                return_value={
                    "format": {
                        "format_name": "mov,mp4",
                        "duration": "2.5",
                        "bit_rate": "1000",
                    },
                    "streams": [{
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                        "r_frame_rate": "30/1",
                    }],
                },
            ):
                metadata = FrameExtractor(video.name).get_video_metadata()

        self.assertEqual(metadata["codec"], "h264")
        self.assertEqual(metadata["frame_rate"], 30.0)
        self.assertEqual(metadata["duration"], 2.5)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.frames = {
            "I": [{"type": "I", "frame_num": 1, "pts_time": 0.0}],
            "P": [{"type": "P", "frame_num": 2, "pts_time": 0.04}],
            "B": [],
        }

    def test_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            write_report(str(path), build_report("video.mp4", self.frames))
            report = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(report["total_frames"], 2)
        self.assertEqual(report["stats"]["I"], 1)

    def test_csv_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.csv"
            write_report(str(path), build_report("video.mp4", self.frames))
            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(lines[0], "frame_num,type,pts_time")
        self.assertEqual(len(lines), 3)

    def test_cli_accepts_report_option(self):
        frames = self.frames
        extractor = type(
            "Extractor",
            (),
            {"__init__": lambda self, video: None,
             "analyze_frames": lambda self: frames},
        )
        with patch.object(cli, "FrameExtractor", extractor), patch.object(
            cli, "write_report"
        ) as write_report, patch("sys.argv", ["cli", "analyze", "video.mp4", "--report", "report.json"]):
            cli.main()

        write_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
