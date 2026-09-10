# Architecture Overview

## System Components

```mermaid
graph TB
    subgraph "Frame Inspector"
        CLI[CLI Interface]
        EXT[Frame Extractor]
        REP[Frame Reports]
        VIS[Visualization Utils]
    end
    
    subgraph "External Tools"
        FFPROBE[FFprobe]
        FFMPEG[FFmpeg]
        OPENCV[OpenCV]
    end
    
    subgraph "User"
        USER[User]
    end
    
    USER -->|commands| CLI
    CLI -->|analyze, extract| EXT
    CLI -->|analyze| REP
    CLI -->|visualize, browse, grid| VIS
    CLI -->|info| EXT
    
    EXT -->|frame metadata| FFPROBE
    EXT -->|stream metadata| FFPROBE
    EXT -->|single-pass extraction| FFMPEG
    REP -->|JSON and CSV reports| USER
    VIS -->|display| OPENCV
    VIS -->|save images| OPENCV
```

## Data Flow - Frame Analysis

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant EXT as Extractor
    participant FP as FFprobe
    
    U->>CLI: analyze video.mp4 --report report.json
    CLI->>EXT: analyze_frames()
    EXT->>FP: ffprobe -show_entries frame=pict_type,pts_time,frame_num
    FP-->>EXT: JSON with frame types
    EXT-->>CLI: Frames grouped by I, P, and B type
    CLI-->>U: Display statistics
    CLI-->>U: Optionally write JSON or CSV report
```

## Data Flow - Frame Extraction

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant EXT as Extractor
    participant FF as FFmpeg
    
    U->>CLI: extract video.mp4 -o output --start 10 --every 2
    CLI->>EXT: analyze_frames()
    EXT->>FP: ffprobe frame metadata
    FP-->>EXT: Ordered I, P, and B frames
    CLI->>EXT: extract_frames(output, filters)
    EXT->>FF: Decode all frames in one pass
    FF-->>EXT: Temporary sequential PNG files
    EXT-->>CLI: Files organized into type folders
    CLI-->>U: Show extraction summary
```

## Data Flow - Video Metadata

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant EXT as Extractor
    participant FP as FFprobe

    U->>CLI: info video.mp4
    CLI->>EXT: get_video_metadata()
    EXT->>FP: ffprobe format and stream metadata
    FP-->>EXT: Codec, resolution, duration, and bitrate
    EXT-->>CLI: Normalized metadata
    CLI-->>U: Display metadata
```

## Component Diagram

```mermaid
classDiagram
    class FrameExtractor {
        +video_path: Path
        +get_video_info() Dict
        +get_video_metadata() Dict
        +analyze_frames() Dict
        +filter_frames(frames, start, end, every, max) Dict
        +extract_frames(output_dir, types, start, end, every, max) Dict
        -_validate_ffmpeg()
        -_extract_all_frames(pattern)
    }

    class Reports {
        +build_report(video, frames) Dict
        +write_report(path, report)
    }
    
    class CLI {
        +cmd_analyze(args)
        +cmd_extract(args)
        +cmd_visualize(args)
        +cmd_browse(args)
        +cmd_info(args)
        +cmd_grid(args)
        +main()
        -print_stats(stats, total)
    }
    
    class Utils {
        +load_frame(path) ndarray
        +create_frame_grid(paths, size) ndarray
        +create_comparison_grid(frames) ndarray
        +browse_frames(frames)
        +display_frame(frame)
        +display_grid(grid)
        +save_grid(grid, path)
    }
    
    CLI --> FrameExtractor
    CLI --> Reports
    CLI --> Utils
    FrameExtractor --> FFprobe
    FrameExtractor --> FFmpeg
    Utils --> OpenCV
```

## Output Structure

```
output/
├── i_frames/
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── p_frames/
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
└── b_frames/
    ├── frame_0000.png
    ├── frame_0001.png
    └── ...
```

## Frame Type Characteristics

| Type | Description | Size | Dependencies |
|------|-------------|------|--------------|
| I-Frame | Complete image, keyframe | Largest | None |
| P-Frame | Predicted from past | Medium | Previous I/P |
| B-Frame | Bidirectional prediction | Smallest | Past and future |
