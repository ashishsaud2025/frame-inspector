"""Frame extraction and classification using FFprobe/FFmpeg."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class FrameExtractor:
    """Extract and classify video frames by type (I, P, B)."""

    VALID_TYPES = {"I", "P", "B"}

    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        self._validate_ffmpeg()

    def _validate_ffmpeg(self):
        """Check if FFmpeg and FFprobe are available."""
        for cmd in ["ffmpeg", "ffprobe"]:
            try:
                subprocess.run(
                    [cmd, "-version"],
                    capture_output=True,
                    check=True
                )
            except FileNotFoundError:
                raise RuntimeError(f"{cmd} not found. Install FFmpeg first.")

    def get_video_info(self) -> Dict:
        """Get video metadata using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(self.video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def get_video_metadata(self) -> Dict:
        """Return the primary video stream and container metadata."""
        info = self.get_video_info()
        stream = next(
            (item for item in info.get("streams", []) if item.get("codec_type") == "video"),
            {},
        )
        format_info = info.get("format", {})
        return {
            "filename": str(self.video_path),
            "format": format_info.get("format_name"),
            "duration": _to_float(format_info.get("duration")),
            "bitrate": _to_int(format_info.get("bit_rate")),
            "codec": stream.get("codec_name"),
            "codec_long_name": stream.get("codec_long_name"),
            "width": stream.get("width"),
            "height": stream.get("height"),
            "pixel_format": stream.get("pix_fmt"),
            "frame_rate": _frame_rate(stream.get("r_frame_rate")),
            "frame_count": _to_int(stream.get("nb_frames")),
        }

    def analyze_frames(self) -> Dict[str, List[Dict]]:
        """Analyze video and return frames grouped by type."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "frame=pict_type,pts_time,pts,frame_num",
            "-print_format", "json",
            str(self.video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        frames_by_type: Dict[str, List[Dict]] = {"I": [], "P": [], "B": []}
        for frame in data.get("frames", []):
            frame_type = frame.get("pict_type", "Unknown")
            if frame_type in self.VALID_TYPES:
                frames_by_type[frame_type].append({
                    "type": frame_type,
                    "pts_time": float(frame.get("pts_time", 0)),
                    "frame_num": int(frame.get("frame_num", 0))
                })
        return frames_by_type

    def get_frame_stats(self) -> Dict[str, int]:
        """Get count of frames by type."""
        frames = self.analyze_frames()
        return {ftype: len(flst) for ftype, flst in frames.items()}

    def extract_frames(
        self,
        output_dir: str,
        frame_types: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        every: int = 1,
        max_frames: Optional[int] = None,
    ) -> Dict[str, List[str]]:
        """Extract frames to output directory organized by type."""
        if frame_types is None:
            frame_types = list(self.VALID_TYPES)

        invalid = set(frame_types) - self.VALID_TYPES
        if invalid:
            raise ValueError(f"Invalid frame types: {invalid}")
        if every < 1:
            raise ValueError("every must be at least 1")
        if max_frames is not None and max_frames < 1:
            raise ValueError("max_frames must be at least 1")
        if start_time is not None and start_time < 0:
            raise ValueError("start_time cannot be negative")
        if end_time is not None and start_time is not None and end_time < start_time:
            raise ValueError("end_time must be greater than or equal to start_time")

        out_path = Path(output_dir)
        all_frames = self.analyze_frames()
        frames = self.filter_frames(all_frames, start_time, end_time, every, max_frames)
        selected_numbers = {
            frame["frame_num"]
            for frame_list in frames.values()
            for frame in frame_list
        }
        extracted: Dict[str, List[str]] = {ftype: [] for ftype in frame_types}

        with tempfile.TemporaryDirectory(prefix="frame-inspector-") as temp_dir:
            temp_pattern = str(Path(temp_dir) / "frame_%08d.png")
            self._extract_all_frames(temp_pattern)
            extracted_indexes = {ftype: 0 for ftype in frame_types}

            for index, frame in enumerate(self._ordered_frames(all_frames), start=1):
                if frame["frame_num"] not in selected_numbers:
                    continue
                frame_type = frame["type"]
                if frame_type not in extracted:
                    continue

                type_dir = out_path / f"{frame_type.lower()}_frames"
                type_dir.mkdir(parents=True, exist_ok=True)
                type_index = extracted_indexes[frame_type]
                output_file = type_dir / f"frame_{type_index:04d}.png"
                source_file = Path(temp_dir) / f"frame_{index:08d}.png"
                if not source_file.exists():
                    raise RuntimeError(f"FFmpeg did not create expected frame: {source_file}")
                shutil.move(str(source_file), str(output_file))
                extracted[frame_type].append(str(output_file))
                extracted_indexes[frame_type] += 1

        return extracted

    @staticmethod
    def filter_frames(
        frames: Dict[str, List[Dict]],
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        every: int = 1,
        max_frames: Optional[int] = None,
    ) -> Dict[str, List[Dict]]:
        """Filter classified frames by time, stride, and total count."""
        if every < 1:
            raise ValueError("every must be at least 1")
        if max_frames is not None and max_frames < 1:
            raise ValueError("max_frames must be at least 1")
        if start_time is not None and start_time < 0:
            raise ValueError("start_time cannot be negative")
        if end_time is not None and start_time is not None and end_time < start_time:
            raise ValueError("end_time must be greater than or equal to start_time")
        ordered = FrameExtractor._ordered_frames(frames)
        selected = [
            frame for frame in ordered
            if (start_time is None or frame["pts_time"] >= start_time)
            and (end_time is None or frame["pts_time"] <= end_time)
        ][::every]
        if max_frames is not None:
            selected = selected[:max_frames]
        result = {frame_type: [] for frame_type in frames}
        for frame in selected:
            result.setdefault(frame["type"], []).append(frame)
        return result

    @staticmethod
    def _ordered_frames(frames: Dict[str, List[Dict]]) -> List[Dict]:
        """Return classified frames in their original video order."""
        return sorted(
            (frame for frame_list in frames.values() for frame in frame_list),
            key=lambda frame: frame["frame_num"]
        )

    def _extract_all_frames(self, output_pattern: str):
        """Extract all video frames in one FFmpeg process."""
        cmd = [
            "ffmpeg",
            "-v", "quiet",
            "-i", str(self.video_path),
            "-map", "0:v:0",
            "-vsync", "0",
            "-y",
            output_pattern
        ]
        subprocess.run(cmd, check=True)


def _to_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _frame_rate(value):
    if not value or "/" not in value:
        return _to_float(value)
    numerator, denominator = value.split("/", 1)
    denominator_value = _to_float(denominator)
    return _to_float(numerator) / denominator_value if denominator_value else None
