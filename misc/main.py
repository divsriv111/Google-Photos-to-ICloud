#!/usr/bin/env python3

import os
import json
import subprocess
import sys
from pathlib import Path
import datetime
import shutil
from collections import defaultdict

# Extensions we want to process
SUPPORTED_MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.mp4', '.mov', '.heic', '.avi', '.gif'
}

# The output root directory where processed files (with updated metadata) will go
OUTPUT_DIRECTORY = Path("./output")  # <-- CHANGE if desired


def is_jpeg(file_path: Path) -> bool:
    """
    Quick signature check for JPEG files.
    JPEG files usually start with bytes 0xFF, 0xD8.
    """
    if not file_path.exists():
        return False
    try:
        with open(file_path, "rb") as f:
            start_bytes = f.read(2)
        return start_bytes == b'\xff\xd8'
    except:
        return False


def update_metadata_with_exiftool(media_file: Path, metadata: dict):
    """
    Calls ExifTool to write metadata into the media file.
    `metadata` is a dictionary containing relevant fields extracted from the JSON sidecar.
    """
    exiftool_args = ["exiftool", "-overwrite_original"]

    # 1. Extract a date/time from the JSON (often stored under 'photoTakenTime' or 'creationTime')
    photo_timestamp = metadata.get('photoTakenTime', {}).get('timestamp') \
        or metadata.get('creationTime', {}).get('timestamp')
    if photo_timestamp:
        try:
            epoch_time = int(photo_timestamp)
            utc_time = datetime.datetime.utcfromtimestamp(epoch_time)
            date_str = utc_time.strftime("%Y:%m:%d %H:%M:%S")

            exiftool_args.append(f"-DateTimeOriginal={date_str}")
            exiftool_args.append(f"-CreateDate={date_str}")
            exiftool_args.append(f"-ModifyDate={date_str}")
        except ValueError:
            print(
                f"Warning: Unable to parse timestamp {photo_timestamp} for {media_file}")

    # 2. GPS Data
    geo_data = metadata.get('geoData') or metadata.get('geoDataExif') or {}
    latitude = geo_data.get('latitude')
    longitude = geo_data.get('longitude')
    if latitude and longitude and (abs(latitude) > 0.00001 or abs(longitude) > 0.00001):
        exiftool_args.append(f"-GPSLatitude={latitude}")
        exiftool_args.append(f"-GPSLongitude={longitude}")
        # Determine N/S and E/W from sign
        exiftool_args.append(
            f"-GPSLatitudeRef={'N' if latitude >= 0 else 'S'}")
        exiftool_args.append(
            f"-GPSLongitudeRef={'E' if longitude >= 0 else 'W'}")

    # 3. Optional: Description/Caption
    description = metadata.get('description')
    if description:
        exiftool_args.append(f"-ImageDescription={description}")

    # Finally, specify the target file
    exiftool_args.append(str(media_file))

    print(f"Running ExifTool for: {media_file}")
    subprocess.run(exiftool_args)


def find_corresponding_json(media_file: Path):
    """
    Google Takeout can produce JSON sidecars with various naming patterns:
      - File.jpg and File.jpg.json
      - File.jpg and File.json
    This function attempts to find the JSON sidecar by checking typical patterns.
    """
    # e.g., "IMG_1234.JPG" => "IMG_1234.JPG.json"
    json_path_1 = media_file.with_suffix(media_file.suffix + ".json")
    if json_path_1.exists():
        return json_path_1

    # e.g., "IMG_1234.JPG" => "IMG_1234.json"
    json_path_2 = media_file.with_suffix(".json")
    if json_path_2.exists():
        return json_path_2

    return None


def process_directory(input_directory: Path):
    """
    Recursively iterates over input_directory, finds media files, and:
      1) Copies them to OUTPUT_DIRECTORY (replicating subfolder structure),
      2) Renames “fake HEIC” files to .jpg if detected,
      3) Reads the corresponding JSON sidecar (if any) and updates Exif metadata,
      4) Collects stats for a final report (written to OUTPUT_DIRECTORY/report.txt).
    """
    if not OUTPUT_DIRECTORY.exists():
        OUTPUT_DIRECTORY.mkdir(parents=True)

    # Tracking stats
    total_files = 0
    processed_files = 0
    failed_files = []  # List of file paths (or names) that failed
    # We'll track how many times we have (input_ext -> output_ext)
    extension_map = defaultdict(int)

    for root, dirs, files in os.walk(input_directory):
        for file_name in files:
            file_path = Path(root) / file_name
            input_ext = file_path.suffix.lower()

            # Check if this file has an extension we want to process
            if input_ext in SUPPORTED_MEDIA_EXTENSIONS:
                total_files += 1

                # Create a relative path to preserve the subdirectory structure
                rel_path = file_path.relative_to(input_directory)
                output_path = OUTPUT_DIRECTORY / rel_path

                # Ensure the subdirectory exists in the output
                output_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    # Copy the original file to output_path
                    shutil.copy2(file_path, output_path)

                    # Potential rename if .heic but actually JPEG
                    final_ext = output_path.suffix.lower()
                    if final_ext == ".heic" and is_jpeg(output_path):
                        new_output_path = output_path.with_suffix(".jpg")
                        output_path.rename(new_output_path)
                        output_path = new_output_path
                        final_ext = ".jpg"

                    # 2) Find JSON sidecar and parse metadata
                    json_sidecar = find_corresponding_json(file_path)
                    if json_sidecar and json_sidecar.exists():
                        try:
                            with open(json_sidecar, "r", encoding="utf-8") as jf:
                                metadata = json.load(jf)
                            # Some Google JSON sidecars are arrays
                            if isinstance(metadata, list) and len(metadata) > 0:
                                metadata = metadata[0]
                        except Exception as e:
                            print(
                                f"Warning: Could not parse JSON {json_sidecar}: {e}")
                            metadata = {}
                    else:
                        metadata = {}

                    # 3) Update Exif metadata on the (possibly renamed) output file
                    update_metadata_with_exiftool(output_path, metadata)
                    processed_files += 1

                    # Record the input -> output extension relationship
                    extension_map[(input_ext, final_ext)] += 1

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    failed_files.append(str(file_path))

    # ---------------------------
    # Generate the final report
    # ---------------------------
    report_lines = []
    report_lines.append("=== FINAL REPORT ===\n")
    report_lines.append(f"Input Directory : {input_directory.resolve()}")
    report_lines.append(f"Output Directory: {OUTPUT_DIRECTORY.resolve()}\n")

    report_lines.append(f"Total media files found : {total_files}")
    report_lines.append(f"Successfully processed  : {processed_files}")
    report_lines.append(
        f"Failed                : {total_files - processed_files}\n")

    # Summarize extension changes
    report_lines.append(
        "File type comparison (input_ext -> output_ext: count):")
    for (in_ext, out_ext), count in sorted(extension_map.items()):
        report_lines.append(f"  {in_ext} -> {out_ext} : {count}")
    report_lines.append("")

    # List failed files if any
    if failed_files:
        report_lines.append("Files that failed to process:")
        for f in failed_files:
            report_lines.append(f"  {f}")
    else:
        report_lines.append("No files failed.\n")

    report_text = "\n".join(report_lines)
    print("\n" + report_text)

    # Write the report to a text file in the output directory
    report_path = OUTPUT_DIRECTORY / "report.txt"
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(report_text)

    print(f"Report written to: {report_path.resolve()}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <input_directory>")
        sys.exit(1)

    input_directory = Path(sys.argv[1])
    if not input_directory.is_dir():
        print(f"Error: {input_directory} is not a valid directory.")
        sys.exit(1)

    process_directory(input_directory)


if __name__ == "__main__":
    main()
