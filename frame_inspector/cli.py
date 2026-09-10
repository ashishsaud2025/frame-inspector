"""Command-line interface for Frame Inspector."""

import argparse
import sys
from pathlib import Path

from .extractor import FrameExtractor
from .reports import build_report, write_report
from .utils import (
    create_frame_grid,
    create_comparison_grid,
    display_grid,
    save_grid
)


def print_stats(stats: dict, total: int):
    """Print frame statistics."""
    print("\nFrame Statistics:")
    print("-" * 40)
    for ftype, count in stats.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {ftype}-Frames: {count:6d} ({pct:5.1f}%)")
    print("-" * 40)
    print(f"  {'Total':6s}: {total:6d}")


def cmd_analyze(args):
    """Analyze video and show frame statistics."""
    extractor = FrameExtractor(args.video)
    frames = extractor.analyze_frames()
    stats = {ftype: len(frame_list) for ftype, frame_list in frames.items()}
    total = sum(stats.values())
    print_stats(stats, total)
    if args.report:
        write_report(args.report, build_report(args.video, frames))
        print(f"Report saved to {args.report}")


def cmd_extract(args):
    """Extract frames to output directory."""
    extractor = FrameExtractor(args.video)
    types = args.types.split(",") if args.types else None
    extracted = extractor.extract_frames(args.output, types)

    for ftype, files in extracted.items():
        print(f"{ftype}-Frames: {len(files)} extracted to {args.output}/{ftype}_frames/")


def cmd_visualize(args):
    """Show frame comparison grid."""
    extractor = FrameExtractor(args.video)
    frames = extractor.analyze_frames()

    frame_paths = {}
    for ftype, frame_list in frames.items():
        frame_paths[ftype] = []
        for frame in frame_list[:args.max_per_type]:
            output_dir = Path(args.output) / f"{ftype}_frames"
            output_file = output_dir / f"frame_{frame['frame_num']:04d}.png"
            if output_file.exists():
                frame_paths[ftype].append(str(output_file))

    if not any(frame_paths.values()):
        print("Extracting frames first...")
        extracted = extractor.extract_frames(args.output)
        for ftype, file_list in extracted.items():
            frame_paths[ftype] = file_list[:args.max_per_type]

    if not any(frame_paths.values()):
        print("No frames could be extracted.")
        sys.exit(1)

    grid = create_comparison_grid(frame_paths, args.max_per_type)
    if args.save:
        save_grid(grid, args.save)
        print(f"Grid saved to {args.save}")
    else:
        display_grid(grid)


def cmd_grid(args):
    """Create grid from extracted frames."""
    frame_paths = []
    input_path = Path(args.input)

    if input_path.is_dir():
        for ext in ["*.png", "*.jpg", "*.jpeg"]:
            frame_paths.extend(str(p) for p in input_path.glob(ext))
    else:
        frame_paths.append(str(input_path))

    if not frame_paths:
        print("No frames found.")
        sys.exit(1)

    grid = create_frame_grid(frame_paths, (args.rows, args.cols))
    if args.save:
        save_grid(grid, args.save)
        print(f"Grid saved to {args.save}")
    else:
        display_grid(grid)


def main():
    parser = argparse.ArgumentParser(
        description="Frame Inspector - Extract and classify video frames"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # analyze command
    analyze = subparsers.add_parser("analyze", help="Analyze video frame types")
    analyze.add_argument("video", help="Path to video file")
    analyze.add_argument("-r", "--report", default=None,
                         help="Write a .json or .csv frame report")
    analyze.set_defaults(func=cmd_analyze)

    # extract command
    extract = subparsers.add_parser("extract", help="Extract frames by type")
    extract.add_argument("video", help="Path to video file")
    extract.add_argument("-o", "--output", default="output",
                         help="Output directory (default: output)")
    extract.add_argument("-t", "--types", default=None,
                         help="Frame types to extract (e.g., I,P,B)")
    extract.set_defaults(func=cmd_extract)

    # visualize command
    visualize = subparsers.add_parser("visualize",
                                       help="Show frame type comparison")
    visualize.add_argument("video", help="Path to video file")
    visualize.add_argument("-o", "--output", default="output",
                           help="Directory with extracted frames")
    visualize.add_argument("-m", "--max-per-type", type=int, default=3,
                           help="Max frames per type to show")
    visualize.add_argument("-s", "--save", default=None,
                           help="Save grid to file instead of displaying")
    visualize.set_defaults(func=cmd_visualize)

    # grid command
    grid = subparsers.add_parser("grid", help="Create frame grid")
    grid.add_argument("input", help="Directory or file with frames")
    grid.add_argument("-r", "--rows", type=int, default=3,
                      help="Grid rows (default: 3)")
    grid.add_argument("-c", "--cols", type=int, default=3,
                      help="Grid columns (default: 3)")
    grid.add_argument("-s", "--save", default=None,
                      help="Save grid to file instead of displaying")
    grid.set_defaults(func=cmd_grid)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
