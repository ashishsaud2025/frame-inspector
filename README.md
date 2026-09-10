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
```

### Visualize Frame Types

Show a comparison grid of different frame types:

```bash
# Display grid in window
python -m frame_inspector.cli visualize video.mp4

# Save grid to file
python -m frame_inspector.cli visualize video.mp4 -s comparison.png
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

## Project Structure

```
frame-inspector/
├── frame_inspector/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── extractor.py    # Frame extraction logic
│   └── utils.py        # Visualization utilities
├── requirements.txt
├── README.md
└── architecture.md
```

## License

MIT License
