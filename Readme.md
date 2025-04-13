Description:
Python scripts that can iterate over the images and convert them in the format which icloud will understand, preserving the image/video metadata (like date, time, location etc). There could be number of reasons why we completely want to move to Icloud photso from google photos. There are not much of tools avail

Concept:
Google photos stores the images/videos in their compact form to save space, and the corresponding metadata of the media is stored in a saperate .json files. In software design pattern this is known as sidecar pattern.

What to expect?
WHen you will download photos dump from google photos and extract it, you will se different media files along with json files (both media and json having same name but different file formats).
Success rate of this tool is 98%, meaning after running this tool over 100 images you can expect the 98 images to be successfully converted along with metadata conserved. For remaining images, the reason could be simply because the corresponding metadata json is not present.
You can either delete or adjust those media's metadata using iphone's photos app (click on edit icon and scoll below you will see the option to adjust date time and location).

Instructions:
Download Google photos:

1. download your google photos dump from here: https://takeout.google.com/. Unselect everything and only select google photos.
2. Once the dumps are downloaded from the available download link, extract them all in current folder.

Install required softwares:

1. Install Python 3.
2. download required softwares from this link: https://drive.google.com/drive/folders/1RSdjvVQtnOu0dU-wjnE3DcOsKkKnjc_e?usp=sharing. Install the exe files and extract the zip folders.
3. Update the enviornment paths to point to bin folders of these softwares.

Install python dependency:

1. Clone/download this repo.
2. Open cmd/powershell/terminal in this folder and type below command:
   pip install -r requirements.txt

Preparation:

1. Once the step 1 is completed, COPY the Photos folder inside this cloned/downloaded folder. Do not cut and paste as we want to keep the original set of photos safe and clean and in case anything goes wrong we can re-paste these photos back in the folder.
2. Now run below commands in in terminal or command prompt while being in the folder:

Command: python count_extensions.py <directory_path>
Example: python count_extensions.py Original_Photos
Use: Shows the initial numbers for different types of file present in the original photos folder. You can take screenshot or copy it somewhere for future reference after run.

Command: python 2.delete_redundant_mp4.py <directory_path>
Example: python 2.delete_redundant_mp4.py Original_Photos
Use:

Command:
Example:
Use:
