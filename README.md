# video-segmenter

Simple tool for splitting groups of large video files into smaller segments using ffmpeg.


## Requirements

- Python 3.6+
- ffmpeg (must be installed and in PATH)

## Usage

### Basic Workflow

1. **Generate titles file**: Scan directory and create JSON metadata
2. **Edit JSON file**: Fill in `base_name` and optionally `directory_name` for each video
3. **Split videos**: Process videos according to the metadata file

### Command-Line Arguments

```
-i, --input-dir         Input directory containing video files (default: .)
-s, --split-dir         Output directory for split videos (default: ./split)
-c, --completed-dir     Directory to move completed videos (default: ./completed)
-f, --folder-per-split  Create a separate folder for each split video
-l, --segment-length    Segment length in minutes (default: 15)
-t, --titles-file       Name of the titles JSON file (default: video_titles.json)
--no-compress           Disable compression and use stream copy instead (faster but may be incompatible)
--codec                 Video codec: libx264 or libx265 (default: libx264)
--crf                   CRF quality level, lower is better (default: 30)
```

## Examples

### Basic Usage (Default Compression)

Split videos into 15-minute segments with H.264 re-encoding (default CRF 28):

```bash
./segment_videos.py
```

### Custom Segment Length

Split videos into 20-minute segments:

```bash
./segment_videos.py -l 20
```

### With Folder Organization

Create a separate folder for each video's segments:

```bash
./segment_videos.py -f
```

### Compression Examples

#### High Quality (H.264)

Use H.264 with CRF 18 (minimal compression, near-lossless quality):

```bash
./segment_videos.py --crf 18
```

#### Balanced Quality (H.264)

Use H.264 with CRF 23 (balanced compression and quality):

```bash
./segment_videos.py --crf 23
```

#### Heavy Compression (H.264)

Use H.264 with CRF 35 (high compression, lower quality):

```bash
./segment_videos.py --crf 35
```

#### H.265 Compression (Better Efficiency)

Use H.265 codec with default CRF 28. Note: H.265 may not be compatible with all players.

```bash
./segment_videos.py --codec libx265
```

### Stream Copy (No Re-encoding)

Skip re-encoding for speed. Only use this if the source is already in a compatible format:

```bash
./segment_videos.py --no-compress
```

### Complete Examples

Split videos into 30-minute segments, organized in folders:

```bash
./segment_videos.py -i ~/videos -l 30 -f --crf 23
```

Process videos from a custom directory with high quality:

```bash
./segment_videos.py -i /path/to/videos -s /path/to/output --crf 20
```

Split into 10-minute segments with heavy compression to save space:

```bash
./segment_videos.py -l 10 --crf 32
```

### Skipping Video Start

The `skip` field in the JSON metadata allows you to skip the beginning of a video before splitting. This is useful for removing intros, logos, or unwanted footage.

Example JSON with skip:

```json
[
  {
    "filename": "lecture.mp4",
    "base_name": "lecture_main",
    "directory_name": "",
    "skip": "00:05:30"
  }
]
```

This will skip the first 5 minutes and 30 seconds of the video before splitting. The skip value can be:
- Time format: `HH:MM:SS` (e.g., "00:05:30" for 5 minutes 30 seconds)
- Seconds: `150` (equivalent to 2 minutes 30 seconds)

**Note:** The script uses `-ss` *before* `-i` in ffmpeg, which enables **fast input seeking**. This means ffmpeg skips to the position before decoding, making it much faster than output seeking. The trade-off is slightly less accuracy (may not be frame-perfect), but for splitting large videos, the speed improvement is significant.

## CRF Values Guide

CRF (Constant Rate Factor) controls video quality and file size. Lower values = better quality, larger files.

**Recommended CRF ranges:**

### H.264 (libx264)
- **18-20**: Near-lossless quality, large files
- **21-23**: High quality, recommended for most use cases
- **24-28**: Good quality, balanced file size
- **29-32**: Acceptable quality, smaller files
- **33+**: Lower quality, maximum compression

### H.265 (libx265)
- **20-22**: Near-lossless quality, large files
- **23-26**: High quality, recommended for most use cases
- **27-30**: Good quality, balanced file size
- **31-34**: Acceptable quality, smaller files
- **35+**: Lower quality, maximum compression

**Note:** H.265 provides better compression than H.264 at the same CRF value, but encoding is slower and may not be compatible with all players.

## JSON Metadata Format

The titles file contains metadata for each video:

```json
[
  {
    "filename": "original_video.mp4",
    "base_name": "vacation_2024",
    "directory_name": "family_vacation",
    "skip": "00:02:30"
  }
]
```

- **filename**: Original video filename (auto-filled)
- **base_name**: Base name for output segments (required, e.g., "vacation_2024_001.mp4")
- **directory_name**: Directory name when using `--folder-per-split` (optional, falls back to base_name)
- **skip**: Time to skip from the start of the video in HH:MM:SS or seconds format (optional, e.g., "00:02:30" or "150")