# Frame Inspector

A command-line tool for extracting and classifying video frames by type (I, P, B).

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed and available in PATH

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd frame-inspector

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Analyze Video

Display frame type statistics for a video:

```bash
python -m frame_inspector.cli analyze video.mp4

# Save frame metadata as JSON
python -m frame_inspector.cli analyze video.mp4 --report report.json

# Save frame metadata as CSV
python -m frame_inspector.cli analyze video.mp4 --report report.csv
```

### Extract Frames

Extract frames into separate folders by type:

```bash
# Extract all frame types
python -m frame_inspector.cli extract video.mp4 -o output_dir

# Extract only I-frames
python -m frame_inspector.cli extract video.mp4 -o output_dir -t I

# Extract a time range, every second frame, with a limit
python -m frame_inspector.cli extract video.mp4 -o output_dir \
  --start 10 --end 20 --every 2 --max-frames 100
```

### Visualize Frame Types

Show a comparison grid of different frame types:

```bash
# Display grid in window
python -m frame_inspector.cli visualize video.mp4

# Save grid to file
python -m frame_inspector.cli visualize video.mp4 -s comparison.png

# Include only selected frames in the comparison
python -m frame_inspector.cli visualize video.mp4 --start 10 --every 10
```

### Browse Frames

Open an interactive OpenCV frame browser. Use `n` or the right arrow for the
next frame, `p` or the left arrow for the previous frame, and `q` or `Esc` to quit:

```bash
python -m frame_inspector.cli browse video.mp4
```

### Video Metadata

Display codec, resolution, frame rate, duration, bitrate, and pixel format:

```bash
python -m frame_inspector.cli info video.mp4
python -m frame_inspector.cli info video.mp4 --json
```

### Create Frame Grid

Generate a grid from extracted frames:

```bash
python -m frame_inspector.cli grid output_dir/i_frames -s grid.png
```

## Frame Types

- **I-Frames (Intra)**: Complete images, no dependencies on other frames
- **P-Frames (Predicted)**: Reference previous frames for compression
- **B-Frames (Bidirectional)**: Reference both past and future frames

**Note on extracted file sizes**: In the video stream, P and B frames are much smaller than I-frames because they store only differences from reference frames. When extracted as standalone images, each frame is reconstructed as a full image, so all frame types appear similar in size.

Frame extraction uses one FFmpeg pass to decode the video. The resulting images are then organized into type-specific folders using the frame metadata from FFprobe.

Reports contain frame counts and per-frame timestamps. JSON reports include the video path, summary statistics, and frame records. CSV reports contain one row per frame.

The `--start` and `--end` options filter by timestamp in seconds. `--every`
keeps every Nth selected frame, and `--max-frames` limits the final selection.

## Project Structure

```
frame-inspector/
├── frame_inspector/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── extractor.py    # Frame extraction logic
│   ├── reports.py      # JSON and CSV report writers
│   └── utils.py        # Visualization utilities
├── tests/
│   └── test_extractor.py
├── requirements.txt
├── README.md
└── architecture.md
```

## License

MIT License
