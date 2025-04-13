import os
import shutil
import argparse


def build_filename_set(folder):
    """
    Recursively builds a set of file names (with extensions) present in the given folder.
    """
    filenames = set()
    for dirpath, _, files in os.walk(folder):
        for f in files:
            filenames.add(f)
    return filenames


def compare_and_copy(folder1, folder2, output_folder):
    """
    Recursively scans folder1. For each file, if the filename (name and extension) is not found
    anywhere in folder2, copy the file to output_folder preserving metadata and directory structure.
    """
    # Build a set of file names from folder2
    folder2_filenames = build_filename_set(folder2)

    # Ensure output_folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Walk folder1 and check if each file's name is in folder2_filenames
    for dirpath, _, files in os.walk(folder1):
        for f in files:
            if f not in folder2_filenames:
                src_path = os.path.join(dirpath, f)
                # Preserve the relative path from folder1
                rel_path = os.path.relpath(src_path, folder1)
                dest_path = os.path.join(output_folder, rel_path)
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                # shutil.copy2(src_path, dest_path)  # copy2 preserves metadata
                print(f"Copied: {src_path} -> {dest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare two folders by file name and extension only, and copy missing files from folder1 to output_folder."
    )
    parser.add_argument("folder1", help="Path to the first folder (source)")
    parser.add_argument(
        "folder2", help="Path to the second folder (comparison target)")
    parser.add_argument(
        "output_folder", help="Path to the output folder where missing files will be copied")
    args = parser.parse_args()

    compare_and_copy(args.folder1, args.folder2, args.output_folder)
