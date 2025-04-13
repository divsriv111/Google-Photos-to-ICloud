
from pathlib import Path
import shutil
import logging
import argparse
import subprocess
import sys

#!/usr/bin/env python3

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def convert_mov_to_mp4(mov_file: Path, mp4_file: Path) -> bool:
    """
    Converts a .mov file to .mp4 using ffmpeg.
    This version disables hardware acceleration, ignores unknown streams, disables data streams,
    and forces the pixel format to yuv420p to work around issues with extra metadata.
    """
    if shutil.which("ffmpeg") is None:
        logger.error(
            "ffmpeg not found in PATH. Please install ffmpeg and add it to your PATH.")
        return False

    logger.info(f"Converting: {mov_file} -> {mp4_file}")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-hwaccel", "none",
                "-ignore_unknown",
                "-i", str(mov_file),
                "-map", "0:v:0",
                "-map", "0:a:0",
                "-dn",                   # Disable data streams
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                # Explicit filter chain (redundant with -pix_fmt but sometimes helps)
                "-vf", "format=yuv420p",
                "-c:a", "aac",
                "-strict", "experimental",
                str(mp4_file)
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert {mov_file} to MP4: {e}")
        return False


def copy_metadata(src_file: Path, dst_file: Path) -> bool:
    """
    Copies metadata from the source file to the destination file using ExifTool.
    """
    logger.info(f"Copying metadata from {src_file} to {dst_file}")
    try:
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                "-TagsFromFile", str(src_file),
                "-All:All",
                str(dst_file)
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Metadata copy failed for {src_file} -> {dst_file}: {e}")
        return False


def process_failed_list(failed_list_file: Path, base_dir: Path, output_dir: Path):
    """
    Reads a text file containing failed .mov file paths (one per line), computes the relative path
    (so that folder structure is maintained) and converts each .mov to .mp4, copying metadata afterwards.
    """
    if not failed_list_file.exists():
        logger.error(f"Failed list file {failed_list_file} does not exist.")
        sys.exit(1)

    with open(failed_list_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    success_count = 0

    for file_str in lines:
        mov_file = Path(file_str)
        if not mov_file.exists():
            logger.error(f"File does not exist: {mov_file}")
            continue

        try:
            rel_path = mov_file.relative_to(base_dir)
        except ValueError as e:
            logger.error(
                f"File {mov_file} is not under base directory {base_dir}: {e}")
            continue

        # Construct output file path with the same folder structure and .mp4 extension.
        output_file = output_dir / rel_path
        output_file = output_file.with_suffix(".mp4")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if convert_mov_to_mp4(mov_file, output_file):
            if copy_metadata(mov_file, output_file):
                logger.info(f"Successfully processed {mov_file}")
                success_count += 1
            else:
                logger.error(f"Metadata copy failed for {mov_file}")
        else:
            logger.error(f"Conversion failed for {mov_file}")

    logger.info(
        f"Processed {success_count} out of {total} files successfully.")


def main():
    # parser = argparse.ArgumentParser(
    #     description="Retry conversion of failed .mov files to MP4 while preserving the folder structure."
    # )
    # parser.add_argument(
    #     "failed_list",
    #     type=str,
    #     help="Path to the text file containing failed .mov file paths (one per line)."
    # )
    # parser.add_argument(
    #     "--base_dir",
    #     type=str,
    #     required=True,
    #     help="The base directory common to all failed files (used to preserve the folder structure)."
    # )
    # parser.add_argument(
    #     "--output_dir",
    #     type=str,
    #     default="output",
    #     help="Directory to store the converted MP4 files (default: output)."
    # )
    # args = parser.parse_args()

    failed_list_file = Path("report.txt")
    base_dir = Path("Photos")
    output_dir = Path("output")

    process_failed_list(failed_list_file, base_dir, output_dir)


if __name__ == "__main__":
    main()
