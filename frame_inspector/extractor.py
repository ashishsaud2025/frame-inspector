"""Frame extraction and classification using FFprobe/FFmpeg."""

import json
import subprocess
import os
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
        extracted: Dict[str, List[str]] = {}

        for ftype in frame_types:
            if not frames[ftype]:
                continue

            type_dir = out_path / f"{ftype.lower()}_frames"
            type_dir.mkdir(parents=True, exist_ok=True)
            extracted[ftype] = []

            for i, frame in enumerate(frames[ftype]):
                output_file = type_dir / f"frame_{i:04d}.png"
                self._extract_single_frame(frame["pts_time"], output_file)
                extracted[ftype].append(str(output_file))

        return extracted

    def _extract_single_frame(self, timestamp: float, output_path: Path):
        """Extract a single frame at given timestamp."""
        cmd = [
            "ffmpeg",
            "-v", "quiet",
            "-ss", str(timestamp),
            "-i", str(self.video_path),
            "-vframes", "1",
            "-y",
            str(output_path)
        ]
        subprocess.run(cmd, check=True)
