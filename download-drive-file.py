#!/usr/bin/python3

'''
Download a file from Google Drive.
Either pass the URL as an argument or it will be requested by the script.
'''

# - Connect to file's Google page.
# - Get token.
# - Use [resumable?] download function to get entire file.

# Ref: https://github.com/nsadawi/Download-Large-File-From-Google-Drive-Using-Python
# Ref: https://stackoverflow.com/a/39225039
import re
import requests
import sys

from bs4 import BeautifulSoup
from pathlib import Path

def download_file_from_google_drive(id, dest_dir):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': id}, stream=True)
    if response.status_code != 200:
        print(f"Error: Server code {response.status_code}. Invalid Drive file ID?")
        exit(1)

    # Get file_name whether the response is a page or the content itself.
    file_name = None
    file_name_pat = '^.*\..{3}$'
    if response.headers['Content-Type'][:9] == 'text/html':
        # Web page: Filter out file_name from page.
        soup = BeautifulSoup(response.content, 'html.parser')
        all_links = soup.find_all('a')
        for item in all_links:
            # Find file name from link list.
            match = re.match(file_name_pat, str(item.contents[0]))
            if match:
                file_name = match.group()

        # Get updated response using session token.
        token = get_confirm_token(response)
        if token:
            params = {'id': id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)
    else:
        # Direct content: Get file_name from header.
        file_name_pat = '^.*filename="(.*\..{3})";.*$'
        # response.headers['Content-Disposition']:
        # 'attachment;filename="2019 Marti Christmas card.png";filename*=UTF-8\'\'2019%20Marti%20Christmas%20card.png'
        match = re.match(file_name_pat, response.headers['Content-Disposition'])
        if match:
            file_name = match.group(1)

    # Use file_name to define destination location.
    destination = dest_dir / 'drive_file'
    if file_name:
        destination = dest_dir / file_name
    else:
        print("Couldn't determine file name. Using 'drive_file' instead.")

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    print(f"Downloading file to \"{destination}\"")
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


try:
    infile = sys.argv[1]
except IndexError:
    try:
        infile = input("Drive file link or fileID: ")
    except KeyboardInterrupt:
        print()
        exit()

file_id = infile
if infile[:4] == 'http':
    # URL given. Need to grab the fileID from it.
    #https://drive.google.com/file/d/1kWHGGnvCCl7ISGD3F_70KNk8E5nNWHew/view?usp=sharing
    file_id = infile.split('/')[5]

dest_dir = Path.home()
download_file_from_google_drive(file_id, dest_dir)
