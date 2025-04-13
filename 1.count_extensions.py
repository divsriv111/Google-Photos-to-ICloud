import os
import sys
from collections import defaultdict
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python count_extensions.py <directory_path>")
        sys.exit(1)

    directory_path = Path(sys.argv[1])
    if not directory_path.is_dir():
        print(f"Error: '{directory_path}' is not a valid directory.")
        sys.exit(1)

    # Dictionary (extension -> count)
    ext_counts = defaultdict(int)

    # Recursively walk through the directory
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Get the file extension using Path or os.path.splitext
            extension = Path(file).suffix.lower()

            # If there's no extension (e.g., "README" without ".md"), we can label it differently
            if extension == "":
                extension = "<no_extension>"

            ext_counts[extension] += 1

    # Print results
    print(f"\nFile extension counts for '{directory_path}':")
    for extension, count in ext_counts.items():
        print(f"{extension}: {count}")


if __name__ == "__main__":
    main()
