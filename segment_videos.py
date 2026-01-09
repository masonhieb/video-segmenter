#!/usr/bin/env python3
"""
Interactive video segmentation script using ffmpeg.
Generates a titles file for video metadata and splits videos into segments.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


# Common video file extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'],
                      capture_output=True,
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def find_video_files(input_dir: Path) -> List[Path]:
    """Find all video files in the input directory."""
    video_files = []
    for file in input_dir.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(file)
    return sorted(video_files)


def generate_titles_file(input_dir: Path, output_file: str = "video_titles.json") -> None:
    """Generate a JSON file with video metadata."""
    video_files = find_video_files(input_dir)

    if not video_files:
        print(f"No video files found in {input_dir}")
        return

    video_data = []
    for video in video_files:
        video_data.append({
            "filename": video.name,
            "base_name": "",
            "directory_name": ""
        })

    output_path = Path.cwd() / output_file
    with open(output_path, 'w') as f:
        json.dump(video_data, f, indent=2)

    print(f"\n✓ Generated titles file: {output_path}")
    print(f"  Found {len(video_files)} video file(s)")
    print(f"\nPlease edit {output_file} to fill in 'base_name' and 'directory_name' fields.")


class VideoTitles:
    """Manages the video titles JSON file with automatic backup and save."""

    def __init__(self, titles_path: Path):
        """Initialize and load the titles file, creating a backup."""
        self.titles_path = titles_path
        self.video_data = []

        if not self.titles_path.exists():
            raise FileNotFoundError(f"Titles file not found: {self.titles_path}")

        # Load the JSON file
        with open(self.titles_path, 'r') as f:
            self.video_data = json.load(f)

        # Create backup file
        backup_path = self.titles_path.with_suffix('.json.bak')
        shutil.copy2(self.titles_path, backup_path)
        print(f"Created backup: {backup_path}")

    def get_videos(self) -> List[dict]:
        """Get the list of video entries."""
        return self.video_data

    def delete_entry(self, filename: str) -> bool:
        """Delete an entry by filename and auto-save the file."""
        original_length = len(self.video_data)
        self.video_data = [v for v in self.video_data if v.get('filename') != filename]

        if len(self.video_data) < original_length:
            self._save()
            return True
        return False

    def _save(self) -> None:
        """Save the current video data to the JSON file."""
        with open(self.titles_path, 'w') as f:
            json.dump(self.video_data, f, indent=2)


def format_time(minutes: int) -> str:
    """Convert minutes to HH:MM:SS format."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}:00"


def split_video(video_path: Path,
                output_dir: Path,
                base_name: str,
                segment_length: int) -> bool:
    """Split a video into segments using ffmpeg."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare output pattern (always output as .mp4)
    output_pattern = output_dir / f"{base_name}_%03d.mp4"

    segment_time = format_time(segment_length)

    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-c', 'copy',
        '-map', '0',
        '-segment_time', segment_time,
        '-f', 'segment',
        '-reset_timestamps', '1',
        str(output_pattern)
    ]

    print(f"\nSplitting: {video_path.name}")
    print(f"  Output: {output_dir}/")
    print(f"  Segment length: {segment_length} minutes")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Successfully split {video_path.name}")
            return True
        else:
            print(f"✗ Error splitting {video_path.name}")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception while splitting {video_path.name}: {e}")
        return False


def split_videos(input_dir: Path,
                split_dir: Path,
                completed_dir: Path,
                titles_file: str,
                folder_per_split: bool,
                segment_length: int) -> None:
    """Split videos based on titles file configuration."""
    titles_path = Path.cwd() / titles_file

    # Initialize the titles manager (will create backup and load JSON)
    try:
        titles_manager = VideoTitles(titles_path)
    except FileNotFoundError:
        print(f"Error: Titles file not found: {titles_path}")
        print("Please run option 1 first to generate the titles file.")
        return

    video_data = titles_manager.get_videos()

    if not video_data:
        print("No videos found in titles file.")
        return

    # Create directories
    split_dir.mkdir(parents=True, exist_ok=True)
    completed_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    failed = 0

    for video_info in video_data:
        filename = video_info['filename']
        base_name = video_info.get('base_name', '')
        directory_name = video_info.get('directory_name', '')

        video_path = input_dir / filename

        if not video_path.exists():
            print(f"\n✗ Video not found: {video_path}")
            failed += 1
            continue

        # Ensure base_name is provided
        if not base_name:
            print(f"\n✗ Error: 'base_name' is empty for {filename}")
            print(f"Please edit the titles file and fill in the 'base_name' field for all videos.")
            sys.exit(1)

        # Determine output directory
        if folder_per_split:
            if directory_name:
                output_dir = split_dir / directory_name
            else:
                output_dir = split_dir / base_name
        else:
            output_dir = split_dir

        # Split the video
        success = split_video(video_path, output_dir, base_name, segment_length)

        if success:
            # Move to completed directory
            dest_path = completed_dir / filename
            try:
                shutil.move(str(video_path), str(dest_path))
                print(f"  Moved to: {dest_path}")
                processed += 1

                # Delete entry from JSON file
                titles_manager.delete_entry(filename)
                print(f"  Removed from titles file")
            except Exception as e:
                print(f"  Warning: Could not move file to completed dir: {e}")
                processed += 1

                # Still delete from JSON even if move failed
                titles_manager.delete_entry(filename)
                print(f"  Removed from titles file")
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"  Successfully processed: {processed}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}")


def interactive_menu(args: argparse.Namespace) -> None:
    """Display interactive menu and handle user choice."""
    input_dir = Path(args.input_dir).resolve()
    split_dir = Path(args.split_dir).resolve()
    completed_dir = Path(args.completed_dir).resolve()

    while True:
        print("\n" + "="*60)
        print("Video Segmenter")
        print("="*60)
        print(f"Input directory: {input_dir}")
        print(f"Split directory: {split_dir}")
        print(f"Completed directory: {completed_dir}")
        print(f"Segment length: {args.segment_length} minutes")
        print(f"Folder per split: {args.folder_per_split}")
        print("="*60)
        print("\nOptions:")
        print("  1. Generate titles file")
        print("  2. Split videos into segments")
        print("  3. Exit")
        print()

        choice = input("Select an option (1-3): ").strip()

        if choice == '1':
            generate_titles_file(input_dir)
        elif choice == '2':
            split_videos(
                input_dir,
                split_dir,
                completed_dir,
                args.titles_file,
                args.folder_per_split,
                args.segment_length
            )
        elif choice == '3':
            print("\nExiting...")
            break
        else:
            print("\nInvalid option. Please select 1, 2, or 3.")


def main():
    """Main entry point."""
    # Check for ffmpeg first
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not found in PATH.")
        print("Please install ffmpeg before running this script.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Interactive video segmentation tool using ffmpeg"
    )
    parser.add_argument(
        '-i', '--input-dir',
        default='.',
        help='Input directory containing video files (default: current directory)'
    )
    parser.add_argument(
        '-s', '--split-dir',
        default='split',
        help='Output directory for split videos (default: ./split)'
    )
    parser.add_argument(
        '-c', '--completed-dir',
        default='completed',
        help='Directory to move completed videos (default: ./completed)'
    )
    parser.add_argument(
        '-f', '--folder-per-split',
        action='store_true',
        help='Create a separate folder for each split video'
    )
    parser.add_argument(
        '-l', '--segment-length',
        type=int,
        default=15,
        help='Segment length in minutes (default: 15)'
    )
    parser.add_argument(
        '-t', '--titles-file',
        default='video_titles.json',
        help='Name of the titles JSON file (default: video_titles.json)'
    )

    args = parser.parse_args()

    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory does not exist: {input_path}")
        sys.exit(1)

    interactive_menu(args)


if __name__ == '__main__':
    main()
