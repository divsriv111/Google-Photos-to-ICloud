#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path


def convert_heic_to_jpg(heic_file: Path, jpg_file: Path) -> bool:
    """
    Converts a .heic file to .jpg using `heif-convert` (from libheif).
    Returns True if the command succeeds, otherwise False.

    If you have ImageMagick installed, comment out the `heif-convert`
    line and uncomment the `magick convert` line below.
    """
    print(f"[CONVERT] {heic_file.name} -> {jpg_file.name}")
    try:
        # --- Using libheif ---
        # subprocess.run(
        #     ["heif-convert", str(heic_file), str(jpg_file)],
        #     check=True
        # )

        # --- Or, if you prefer ImageMagick, use this instead: ---
        subprocess.run(
            ["magick", "convert", str(heic_file), str(jpg_file)],
            check=True
        )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Conversion failed on {heic_file} -> {e}")
        return False


def copy_metadata_from_heic_to_jpg(heic_file: Path, jpg_file: Path) -> bool:
    """
    Copies metadata from the original .heic to the .jpg using ExifTool.
    Returns True if successful, otherwise False.
    """
    print(f"[METADATA] Copying from {heic_file.name} to {jpg_file.name}")
    try:
        subprocess.run([
            "exiftool",
            "-overwrite_original",
            "-TagsFromFile", str(heic_file),
            "-All:All",
            str(jpg_file)
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: ExifTool failed to copy metadata -> {e}")
        return False


def process_heic_in_place(root_dir: Path):
    """
    Recursively searches for .heic files in `root_dir`, converts them to .jpg,
    copies metadata, and removes the original .heic.
    """
    if not root_dir.is_dir():
        print(f"Error: '{root_dir}' is not a directory.")
        sys.exit(1)

    print(
        f"\nStarting in-place HEIC -> JPG conversion in: {root_dir.resolve()}")

    total_heic = 0
    converted = 0
    failures = []

    for path, dirs, files in os.walk(root_dir):
        for fname in files:
            file_path = Path(path) / fname
            if file_path.suffix.lower() == ".heic":
                total_heic += 1

                # Construct the .jpg file path in the same directory
                jpg_file = file_path.with_suffix(".jpg")

                # 1) Convert the .heic to .jpg
                if not convert_heic_to_jpg(file_path, jpg_file):
                    failures.append(str(file_path))
                    continue  # Skip metadata copy if conversion failed

                # 2) Copy metadata from the original HEIC to the new JPG
                if not copy_metadata_from_heic_to_jpg(file_path, jpg_file):
                    failures.append(str(file_path))
                    # Optionally, remove the .jpg if metadata copy fails
                    continue

                # 3) Remove the original .heic if everything succeeded
                try:
                    file_path.unlink()
                    converted += 1
                except Exception as e:
                    print(f"Warning: Could not remove {file_path} -> {e}")
                    failures.append(str(file_path))

    # Print summary
    print("\n=== Conversion Summary ===")
    print(f"  Total .heic files found : {total_heic}")
    print(f"  Successfully converted  : {converted}")
    print(f"  Failed                 : {len(failures)}")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  {f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python heic_inplace_convert.py <folder>")
        sys.exit(1)

    root_dir = Path(sys.argv[1])
    process_heic_in_place(root_dir)


if __name__ == "__main__":
    main()
