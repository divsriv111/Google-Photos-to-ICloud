#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import argparse
import logging
import datetime
import shutil
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# For image handling (if needed for non-conversion operations)
try:
    from PIL import Image, ImageOps
except ImportError:
    print("Error: Pillow is not installed. Please run 'pip install Pillow' and try again.")
    sys.exit(1)

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --------------------------
# Supported File Extensions
# --------------------------
# Files that are acceptable either for copy or conversion.
SUPPORTED_MEDIA_EXTENSIONS = {'.jpg', '.jpeg',
                              '.png', '.mp4', '.mov', '.heic', '.avi', '.gif'}

# --------------------------
# Conversion Functions
# --------------------------


def convert_heic_to_jpg(heic_file: Path, jpg_file: Path) -> bool:
    """
    Converts a HEIC file to a JPEG using ImageMagick.
    The '-auto-orient' flag ensures the resulting JPEG is rotated properly.
    """
    # Check if file exists before attempting conversion
    if not heic_file.exists():
        logger.error(f"HEIC file not found: {heic_file.resolve()}")
        return False

    # Check if ImageMagick is installed
    if shutil.which("magick") is None:
        logger.error(
            "ImageMagick ('magick' command) not found in PATH. Please install ImageMagick and add it to your PATH.")
        return False

    logger.info(f"Converting HEIC: {heic_file} -> {jpg_file}")
    try:
        subprocess.run(
            ["magick", "convert", str(heic_file.resolve()),
             "-auto-orient", str(jpg_file.resolve())],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"HEIC conversion failed for {heic_file}: {e}")
        logger.error(f"Command output: {e.stdout}\nError: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error converting {heic_file}: {str(e)}")
        return False


def convert_video_to_mp4(mov_file: Path, mp4_file: Path) -> bool:
    """
    Converts a .mov file to .mp4 using ffmpeg.
    This version disables hardware acceleration, ignores unknown streams, disables data streams,
    and forces the pixel format to yuv420p to work around issues with extra metadata.
    """
    if shutil.which("ffmpeg") is None:
        logger.error(
            "ffmpeg not found in PATH. Please install ffmpeg and add it to your PATH.")
        return False

    # Check if source file exists
    if not mov_file.exists():
        logger.error(f"Source video file not found: {mov_file.resolve()}")
        return False

    # Ensure output directory exists
    mp4_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting: {mov_file} -> {mp4_file}")
    try:
        # Capture stderr instead of discarding it
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-hwaccel", "none",
                "-ignore_unknown",
                "-i", str(mov_file),
                "-map", "0:v:0?",  # Make stream selection optional with ?
                "-map", "0:a:0?",  # Make stream selection optional with ?
                "-dn",                   # Disable data streams
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-vf", "format=yuv420p",
                "-c:a", "aac",
                "-strict", "experimental",
                str(mp4_file)
            ],
            check=False,  # Don't raise an exception so we can handle it
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            logger.error(
                f"FFMPEG error converting {mov_file}: {result.stderr}")
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to convert {mov_file} to MP4: {e}")
        return False

# --------------------------
# Metadata Functions
# --------------------------


def update_metadata_with_exiftool(target_file: Path, metadata: dict):
    """
    Uses ExifTool to update metadata in the target file based on JSON data.
    Expected fields include timestamps (from 'photoTakenTime' or 'creationTime'),
    GPS data, and an optional description.
    """
    exiftool_args = ["exiftool", "-overwrite_original"]

    # Timestamp update (if available)
    photo_timestamp = (metadata.get('photoTakenTime', {}).get('timestamp') or
                       metadata.get('creationTime', {}).get('timestamp'))
    if photo_timestamp:
        try:
            epoch_time = int(photo_timestamp)
            utc_time = datetime.datetime.utcfromtimestamp(epoch_time)
            date_str = utc_time.strftime("%Y:%m:%d %H:%M:%S")
            exiftool_args.extend([
                f"-DateTimeOriginal={date_str}",
                f"-CreateDate={date_str}",
                f"-ModifyDate={date_str}"
            ])
        except ValueError:
            logger.warning(
                f"Unable to parse timestamp {photo_timestamp} for {target_file}")

    # GPS Data update
    geo_data = metadata.get('geoData') or metadata.get('geoDataExif') or {}
    latitude = geo_data.get('latitude')
    longitude = geo_data.get('longitude')
    if latitude is not None and longitude is not None and (abs(latitude) > 0.00001 or abs(longitude) > 0.00001):
        exiftool_args.append(f"-GPSLatitude={latitude}")
        exiftool_args.append(f"-GPSLongitude={longitude}")
        exiftool_args.append(
            f"-GPSLatitudeRef={'N' if latitude >= 0 else 'S'}")
        exiftool_args.append(
            f"-GPSLongitudeRef={'E' if longitude >= 0 else 'W'}")

    # Optional description/caption
    description = metadata.get('description')
    if description:
        exiftool_args.append(f"-ImageDescription={description}")

    exiftool_args.append(str(target_file))
    logger.info(f"Updating metadata on: {target_file}")
    try:
        result = subprocess.run(exiftool_args, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(
                f"ExifTool error for {target_file}: {result.stderr.strip()}")
        else:
            logger.info(f"Metadata updated for {target_file}")
    except Exception as e:
        logger.error(f"Failed to run ExifTool for {target_file}: {e}")


def copy_metadata(src_file: Path, dst_file: Path) -> bool:
    """
    Copies metadata from src_file to dst_file using ExifTool.
    This is used when no JSON sidecar is available.
    """
    logger.info(f"Copying metadata from {src_file} to {dst_file}")
    try:
        subprocess.run([
            "exiftool",
            "-overwrite_original",
            "-TagsFromFile", str(src_file),
            "-All:All",
            str(dst_file)
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Metadata copy failed from {src_file} to {dst_file}: {e}")
        return False


def find_corresponding_json(media_file: Path) -> Path:
    """
    Looks for a JSON sidecar for the given media file.
    It checks for both 'File.ext.json' and 'File.json' patterns.
    """
    json_candidate1 = media_file.with_suffix(media_file.suffix + ".json")
    if json_candidate1.exists():
        return json_candidate1
    json_candidate2 = media_file.with_suffix(".json")
    if json_candidate2.exists():
        return json_candidate2
    return None

# --------------------------
# Processing Each File
# --------------------------


def process_file(file_path: Path, input_dir: Path, output_dir: Path) -> bool:
    """
    Processes a single media file:
      - Determines relative path to preserve folder structure.
      - Converts the file if needed (HEIC->JPG or MOV/AVI->MP4) or copies it as is.
      - Updates metadata using a JSON sidecar if available, otherwise copies metadata from the original if conversion was performed.
    Returns True if the file was processed successfully.
    """
    try:
        rel_path = file_path.relative_to(input_dir)
    except ValueError as e:
        logger.error(f"Error computing relative path for {file_path}: {e}")
        return False

    # Initialize output file path (will be adjusted if conversion is needed)
    output_file = output_dir / rel_path
    output_file.parent.mkdir(parents=True, exist_ok=True)

    ext = file_path.suffix.lower()
    conversion_performed = False

    # Determine if conversion is needed.
    if ext == ".heic":
        output_file = output_file.with_suffix(".jpg")
        if not convert_heic_to_jpg(file_path, output_file):
            return False
        conversion_performed = True
    elif ext in {".mov", ".avi"}:
        output_file = output_file.with_suffix(".mp4")
        if not convert_video_to_mp4(file_path, output_file):
            return False
        conversion_performed = True
    else:
        # No conversion needed: simply copy the file.
        try:
            shutil.copy2(file_path, output_file)
        except Exception as e:
            logger.error(f"Error copying {file_path} to {output_file}: {e}")
            return False

    # Check for a corresponding JSON sidecar.
    json_sidecar = find_corresponding_json(file_path)
    if json_sidecar and json_sidecar.exists():
        try:
            with open(json_sidecar, "r", encoding="utf-8") as jf:
                metadata = json.load(jf)
            # If the JSON sidecar is an array, use the first element.
            if isinstance(metadata, list) and metadata:
                metadata = metadata[0]
        except Exception as e:
            logger.warning(f"Could not parse JSON {json_sidecar}: {e}")
            metadata = {}
        update_metadata_with_exiftool(output_file, metadata)
    else:
        # No JSON sidecar: if conversion was performed, attempt to copy metadata from original.
        if conversion_performed:
            copy_metadata(file_path, output_file)
        else:
            logger.info(
                f"No JSON sidecar found for {file_path}. Preserving original metadata.")

    return True

# --------------------------
# Processing Directory with Multi-threading
# --------------------------


def process_directory(input_dir: Path, output_dir: Path):
    """
    Walks through input_dir recursively and processes each media file using a thread pool.
    A final report is printed at the end.
    """
    total_files = 0
    processed_files = 0
    failed_files = []
    extension_map = defaultdict(int)

    # Use a controlled number of worker threads (e.g., 4)
    max_workers = 4
    futures = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for root, dirs, files in os.walk(input_dir):
            for fname in files:
                file_path = Path(root) / fname
                if file_path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS:
                    total_files += 1
                    logger.info(f"Submitting file for processing: {file_path}")
                    future = executor.submit(
                        process_file, file_path, input_dir, output_dir)
                    futures[future] = file_path

        for future in as_completed(futures):
            file_path = futures[future]
            try:
                success = future.result()
                ext = file_path.suffix.lower()
                if success:
                    processed_files += 1
                    extension_map[ext] += 1
                else:
                    failed_files.append(str(file_path))
            except Exception as exc:
                logger.error(f"Error processing {file_path}: {exc}")
                failed_files.append(str(file_path))

    # Generate a final report.
    report_lines = [
        "=== FINAL REPORT ===",
        f"Input Directory : {input_dir.resolve()}",
        f"Output Directory: {output_dir.resolve()}",
        f"Total media files found : {total_files}",
        f"Successfully processed  : {processed_files}",
        f"Failed                  : {total_files - processed_files}",
        "",
        "File types processed:"
    ]
    for ext, count in sorted(extension_map.items()):
        report_lines.append(f"  {ext} : {count}")
    if failed_files:
        report_lines.append("\nFiles that failed to process:")
        for f in failed_files:
            report_lines.append(f"  {f}")
    else:
        report_lines.append("\nNo files failed.")
    report_text = "\n".join(report_lines)
    logger.info("\n" + report_text)

    # Optionally, write the report to a file in the output directory.
    try:
        report_path = output_dir / "report.txt"
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(report_text)
        logger.info(f"Report written to: {report_path.resolve()}")
    except Exception as e:
        logger.error(f"Failed to write report: {e}")

# --------------------------
# Main Entry Point
# --------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Recursively process an input folder to perform sequential operations: "
                    "convert unsupported media types (HEIC->JPG, MOV/AVI->MP4), update/copy metadata (using JSON sidecars when available), "
                    "and save the processed files preserving the original folder structure in an output folder."
    )
    parser.add_argument("input_folder", type=str,
                        help="Path to the input folder containing media files.")
    parser.add_argument("--output_folder", type=str, default="output",
                        help="Path to the output folder (default: ./output).")
    args = parser.parse_args()

    input_dir = Path(args.input_folder)
    output_dir = Path(args.output_folder)

    if not input_dir.is_dir():
        logger.error(f"Error: {input_dir} is not a valid directory.")
        sys.exit(1)

    process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()
