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
        frame_types: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Extract frames to output directory organized by type."""
        if frame_types is None:
            frame_types = list(self.VALID_TYPES)

        invalid = set(frame_types) - self.VALID_TYPES
        if invalid:
            raise ValueError(f"Invalid frame types: {invalid}")

        out_path = Path(output_dir)
        frames = self.analyze_frames()
        extracted: Dict[str, List[str]] = {ftype: [] for ftype in frame_types}

        with tempfile.TemporaryDirectory(prefix="frame-inspector-") as temp_dir:
            temp_pattern = str(Path(temp_dir) / "frame_%08d.png")
            self._extract_all_frames(temp_pattern)
            extracted_indexes = {ftype: 0 for ftype in frame_types}

            for index, frame in enumerate(self._ordered_frames(frames), start=1):
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
