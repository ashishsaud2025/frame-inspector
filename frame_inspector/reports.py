"""Report writers for frame analysis results."""

import csv
import json
from pathlib import Path
from typing import Dict, List


def build_report(video: str, frames: Dict[str, List[Dict]]) -> Dict:
    """Build a serializable report containing frame metadata and counts."""
    stats = {frame_type: len(frame_list) for frame_type, frame_list in frames.items()}
    ordered_frames = sorted(
        (frame for frame_list in frames.values() for frame in frame_list),
        key=lambda frame: frame["frame_num"]
    )
    return {
        "video": video,
        "total_frames": sum(stats.values()),
        "stats": stats,
        "frames": ordered_frames,
    }


def write_report(path: str, report: Dict):
    """Write a JSON or CSV report based on the output extension."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return
    if output_path.suffix.lower() == ".csv":
        with output_path.open("w", newline="", encoding="utf-8") as report_file:
            writer = csv.DictWriter(
                report_file,
                fieldnames=["frame_num", "type", "pts_time"],
            )
            writer.writeheader()
            writer.writerows(report["frames"])
        return
    raise ValueError("Report path must end with .json or .csv")
