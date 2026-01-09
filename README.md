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
-C, --compress          Enable video compression (default: disabled)
--codec                 Video codec: libx264 or libx265 (default: libx264)
--crf                   CRF quality level, lower is better (default: 30)
```

## Examples

### Basic Usage (No Compression)

Split videos into 15-minute segments without compression (fast, lossless):

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

#### Light Compression (H.264, Default Quality)

Use H.264 codec with CRF 30 (moderate compression, good quality):

```bash
./segment_videos.py -C
```

#### High Quality Compression (H.264)

Use H.264 with CRF 18 (minimal compression, near-lossless quality):

```bash
./segment_videos.py -C --crf 18
```

#### Moderate Compression (H.264)

Use H.264 with CRF 23 (balanced compression and quality):

```bash
./segment_videos.py -C --crf 23
```

#### Heavy Compression (H.264)

Use H.264 with CRF 35 (high compression, lower quality):

```bash
./segment_videos.py -C --crf 35
```

#### H.265 Compression (Better Efficiency)

Use H.265 codec with default CRF 30 (better compression than H.264 at same quality):

```bash
./segment_videos.py -C --codec libx265
```

#### H.265 High Quality

Use H.265 with CRF 20 (excellent quality, smaller than H.264):

```bash
./segment_videos.py -C --codec libx265 --crf 20
```

#### H.265 Maximum Compression

Use H.265 with CRF 35 (maximum compression, acceptable quality):

```bash
./segment_videos.py -C --codec libx265 --crf 35
```

### Complete Examples

Split videos into 30-minute segments with H.264 compression, organized in folders:

```bash
./segment_videos.py -i ~/videos -l 30 -f -C --crf 23
```

Process videos from custom directory with H.265 compression, high quality:

```bash
./segment_videos.py -i /path/to/videos -s /path/to/output -C --codec libx265 --crf 20
```

Split into 10-minute segments with heavy H.264 compression to save space:

```bash
./segment_videos.py -l 10 -C --crf 32
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

**Note:** H.265 provides better compression than H.264 at the same CRF value, but encoding is slower.

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

## Notes

- Output files are always in MP4 format regardless of input format
- The script creates a `.bak` backup of the JSON file before processing
- Completed entries are removed from the JSON file after successful processing
- Videos are moved to the completed directory after splitting
- If a split fails, the entry remains in the JSON for retry
- The `skip` field uses `-ss` before `-i` in ffmpeg for fast input seeking (skips without decoding the entire beginning)
