# Google Photos to iCloud Migration Tool

A collection of Python scripts to help you migrate your Google Photos library to iCloud while preserving metadata (dates, locations, descriptions).

## Overview

### What This Tool Does

This tool helps you convert Google Photos media files to formats compatible with iCloud Photos while preserving important metadata like:

- Original capture date/time
- GPS location data
- Photo descriptions

### Why Use This Tool?

Google Photos exports use a "sidecar" pattern with separate JSON files for metadata. This tool reads those JSON files and embeds the metadata directly into the media files so iCloud Photos can properly display and organize them.

### Expected Success Rate

- **~98% success rate** for media files with corresponding JSON metadata
- Failed conversions are usually due to missing JSON metadata files
- Manual metadata adjustment can be done through the iOS Photos app for any problematic files

## Installation

### Prerequisites

1. **Python 3** - [Download from python.org](https://www.python.org/downloads/)
2. **Required software tools**:
   - [Download here](https://drive.google.com/drive/folders/1RSdjvVQtnOu0dU-wjnE3DcOsKkKnjc_e?usp=sharing)
   - Install the .exe files and extract the .zip folders
   - Add the bin folders to your system PATH environment variable, for these softwares.

### Setup

1. Clone/download this repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage Instructions

### Step 1: Download Your Google Photos

1. Go to [Google Takeout](https://takeout.google.com/)
2. Deselect all services except Google Photos
3. Request the download and wait for Google to prepare your archive
4. Download and extract all archive files to a folder

### Step 2: Prepare Your Workspace

1. **Important**: Copy (don't move) your extracted Google Photos folder into this tool's directory
   - Keep your original Google Photos export safe as a backup

### Step 3: Process Your Photos

Run the following scripts in order:

#### 1. Count File Extensions

```
python 1.count_extensions.py <photos_folder>
```

Example:

```
python 1.count_extensions.py Photos
```

This shows what types of files are in your Google Photos export. Keep this information for reference.

#### 2. Remove Redundant Files

```
python 2.delete_redundant_mp4.py <photos_folder>
```

Example:

```
python 2.delete_redundant_mp4.py Photos
```

This removes duplicate MP4 files created by Google Photos' "live photo" feature.

#### 3. Convert and Process All Files

```
python 3.final_script.py <photos_folder> [output_folder]
```

Example:

```
python 3.final_script.py Photos Output
```

This is the main processing script that:

- Converts HEIC files to JPG
- Converts MOV/AVI files to MP4
- Embeds metadata from JSON files into the media files
- Preserves the original folder structure
- Generates a report of the processing results

**Note:** This process can take several hours depending on how many files you have.

#### 4. (Optional) Process Failed Conversions

```
python 4.failed_mpv_optional.py
```

Only run this if the main script reported failed conversions. By default, it processes files listed in `output/report.txt`.

## Uploading to iCloud

1. Install the iCloud for Windows app (from Microsoft Store or [Apple's website](https://support.apple.com/en-us/HT204283))
2. Sign in with your Apple ID
3. Open File Explorer and navigate to your iCloud Photos folder
4. Copy all subfolders and files from your output folder to the iCloud Photos folder
5. Allow sufficient time for the upload to complete (can take several days for large libraries)

## Cleaning Up Google Photos (Optional)

If you want to delete your Google Photos content after migration:

1. Go to the [Google Photos website](https://photos.google.com/)
2. Select the first photo on the page
3. Press **Page Down** several times to load more photos
4. Hold **Shift** and click the last photo on the page to select all photos between the first and last
5. Click the **Delete** icon
6. Repeat as needed (each batch can select ~2000 photos)

**Important:** Wait until your iCloud Photos library is fully uploaded and verified before deleting your Google Photos.

## Issues and Support

If you encounter any problems, please [open an issue](https://github.com/divsriv111/google-photos-to-icloud/issues) in this repository.
