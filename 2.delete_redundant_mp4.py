#!/usr/bin/env python3
import argparse
from pathlib import Path


def delete_mp4_versions(root_dir: Path):
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a valid directory.")
        return

    total_checked = 0
    total_deleted = 0

    # Search recursively for image files with .heic or .jpg extensions.
    for image_file in root_dir.rglob("*"):
        if image_file.is_file() and image_file.suffix.lower() in {".heic", ".jpg"}:
            total_checked += 1
            # Construct a potential mp4 file name in the same directory with the same stem.
            mp4_candidate = image_file.with_suffix(".mp4")
            if mp4_candidate.exists() and mp4_candidate.is_file():
                try:
                    mp4_candidate.unlink()
                    print(f"Deleted: {mp4_candidate}")
                    total_deleted += 1
                except Exception as e:
                    print(f"Failed to delete {mp4_candidate}: {e}")

    print(
        f"\nSummary: Checked {total_checked} image files and deleted {total_deleted} corresponding .mp4 files.")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively delete .mp4 files that correspond to image files (.heic or .jpg) in the given folder."
    )
    parser.add_argument("directory", type=str, default="Photos",
                        help="Path to the folder to process")
    args = parser.parse_args()

    root_dir = Path(args.directory)
    delete_mp4_versions(root_dir)


if __name__ == "__main__":
    main()
