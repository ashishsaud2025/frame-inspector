# Architecture Overview

## System Components

```mermaid
graph TB
    subgraph "Frame Inspector"
        CLI[CLI Interface]
        EXT[Frame Extractor]
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
    CLI -->|analyze| EXT
    CLI -->|extract| EXT
    CLI -->|visualize| VIS
    CLI -->|grid| VIS
    
    EXT -->|metadata| FFPROBE
    EXT -->|frame extraction| FFMPEG
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
    
    U->>CLI: analyze video.mp4
    CLI->>EXT: get_frame_stats()
    EXT->>FP: ffprobe -show_entries frame=pict_type
    FP-->>EXT: JSON with frame types
    EXT-->>CLI: {I: 120, P: 340, B: 540}
    CLI-->>U: Display statistics
```

## Data Flow - Frame Extraction

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant EXT as Extractor
    participant FF as FFmpeg
    
    U->>CLI: extract video.mp4 -o output
    CLI->>EXT: extract_frames(output_dir)
    EXT->>FF: Extract I-frames
    FF-->>EXT: PNG files
    EXT->>FF: Extract P-frames
    FF-->>EXT: PNG files
    EXT->>FF: Extract B-frames
    FF-->>EXT: PNG files
    EXT-->>CLI: List of extracted files
    CLI-->>U: Show extraction summary
```

## Component Diagram

```mermaid
classDiagram
    class FrameExtractor {
        +video_path: Path
        +get_video_info() Dict
        +analyze_frames() Dict
        +get_frame_stats() Dict
        +extract_frames(output_dir, types) Dict
        -_validate_ffmpeg()
        -_extract_single_frame(timestamp, path)
    }
    
    class CLI {
        +cmd_analyze(args)
        +cmd_extract(args)
        +cmd_visualize(args)
        +cmd_grid(args)
        +main()
        -print_stats(stats, total)
    }
    
    class Utils {
        +load_frame(path) ndarray
        +create_frame_grid(paths, size) ndarray
        +create_comparison_grid(frames) ndarray
        +display_frame(frame)
        +display_grid(grid)
        +save_grid(grid, path)
    }
    
    CLI --> FrameExtractor
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
