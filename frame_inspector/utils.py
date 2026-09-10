"""Utility functions for frame visualization and display."""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional


def load_frame(frame_path: str) -> Optional[np.ndarray]:
    """Load a frame image from path."""
    frame = cv2.imread(frame_path)
    return frame if frame is not None else None


def create_frame_grid(
    frame_paths: List[str],
    grid_size: tuple = (3, 3),
    cell_size: tuple = (320, 240)
) -> np.ndarray:
    """Create a grid visualization of multiple frames."""
    rows, cols = grid_size
    cell_w, cell_h = cell_size
    grid = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, path in enumerate(frame_paths[:rows * cols]):
        frame = load_frame(path)
        if frame is None:
            continue
        resized = cv2.resize(frame, (cell_w, cell_h))
        r, c = divmod(idx, cols)
        y1, y2 = r * cell_h, (r + 1) * cell_h
        x1, x2 = c * cell_w, (c + 1) * cell_w
        grid[y1:y2, x1:x2] = resized

    return grid


def create_comparison_grid(
    frames_by_type: Dict[str, List],
    max_per_type: int = 3,
    cell_size: tuple = (320, 240)
) -> np.ndarray:
    """Create a side-by-side comparison grid of frame types."""
    type_colors = {"I": (0, 255, 0), "P": (255, 0, 0), "B": (0, 0, 255)}
    cell_w, cell_h = cell_size

    all_frames = []
    labels = []
    for ftype in ["I", "P", "B"]:
        if ftype not in frames_by_type:
            continue
        for item in frames_by_type[ftype][:max_per_type]:
            if isinstance(item, dict):
                all_frames.append((item["path"], ftype, item))
            else:
                all_frames.append((item, ftype, {}))
            labels.append(ftype)

    if not all_frames:
        return np.zeros((cell_h, cell_w, 3), dtype=np.uint8)

    n = len(all_frames)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols

    grid_h = rows * cell_h + 40
    grid_w = cols * cell_w
    grid = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)

    for idx, (path, ftype, metadata) in enumerate(all_frames):
        frame = load_frame(path)
        if frame is None:
            continue
        resized = cv2.resize(frame, (cell_w, cell_h))
        color = type_colors.get(ftype, (255, 255, 255))
        label = f"{ftype}-Frame"
        if metadata:
            label += f"  #{metadata['frame_num']}  {metadata['pts_time']:.3f}s"
        cv2.putText(
            resized, label,
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
            1, color, 2
        )
        r, c = divmod(idx, cols)
        y1, y2 = r * cell_h, (r + 1) * cell_h
        x1, x2 = c * cell_w, (c + 1) * cell_w
        grid[y1:y2, x1:x2] = resized

    return grid


def display_frame(frame: np.ndarray, window_name: str = "Frame"):
    """Display a frame using OpenCV."""
    cv2.imshow(window_name, frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def display_grid(grid: np.ndarray, window_name: str = "Frame Grid"):
    """Display a frame grid."""
    cv2.imshow(window_name, grid)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def browse_frames(frames: List[Dict], window_name: str = "Frame Browser"):
    """Browse extracted frames with left/right keys and quit with q or Esc."""
    if not frames:
        return
    index = 0
    max_width, max_height = 1280, 720
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, max_width, max_height)
    while True:
        item = frames[index]
        frame = load_frame(item["path"])
        if frame is None:
            index = (index + 1) % len(frames)
            continue
        label = f"{item['type']}-Frame #{item['frame_num']}  {item['pts_time']:.3f}s"
        cv2.putText(frame, label, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 255), 2)
        height, width = frame.shape[:2]
        scale = min(max_width / width, max_height / height, 1.0)
        if scale < 1.0:
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord("n"), 83):
            index = (index + 1) % len(frames)
        elif key in (ord("p"), 81):
            index = (index - 1) % len(frames)
    cv2.destroyAllWindows()


def save_grid(grid: np.ndarray, output_path: str):
    """Save a grid image to file."""
    cv2.imwrite(output_path, grid)
