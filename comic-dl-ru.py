#!/usr/bin/python3

'''
This is a work in progress.
Based on comic-dl by Xonshiz ( https://github.com/Xonshiz/comic-dl )
I needed a script to download comics from readcomicsonline.ru
and at the time of writing this that was not an option using comic-dl
Pretty simple script which allows user to download
either the entire series, and individual issue or the entire weekly release
'''


import bs4 as bs
import re
import os
import urllib
import os.path
import shutil
import sys
import requests
import time
import grp
import argparse

from pathlib import Path
from urllib.request import Request, urlopen
from pwd import getpwnam
from configparser import SafeConfigParser


# Set to location of the .ini configuration file
ConfigurationFile = 'config.ini'

parser = SafeConfigParser()
parser.read(ConfigurationFile)

download_directory = parser.get('settings', 'download_directory')


# This function establishes our command line switches
def get_args():
    parser = argparse.ArgumentParser(description='Comic File Web Scrapper')
    parser.add_argument('-s', '--series', type=str, required=False,
                        metavar='<url of the comics series>')
    parser.add_argument('-i', '--issue', type=str, required=False,
                        metavar='<url of the SINGLE comic issue>')

    parser.add_argument('-w', '--weekly', type=str, required=False,
                        metavar='<url of the Weekly section>')

    args = parser.parse_args()
    series = args.series
    issue = args.issue
    weekly = args.weekly

    if not series and not issue and not weekly:
        parser.error('Comic Ripper requires an arguement')

    if series and issue and weekly:
        parser.error('Only 1 option is allowed')

    return (series, issue, weekly)


# Purely for looks, this function displays a file download status
def download_file(url, file_name):
    start = time.clock()
    with open(file_name, "wb") as f:
        print("\nDownloading " + file_name, flush=True)
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'},
                                stream=True)
        total_length = int(response.headers.get('content-length'))

        try:
            print(response.headers["content-type"], flush=True)
        except KeyError:
            print('No Header : Content Type', flush=True)

        if total_length:
            print(total_length / 1024, "Kb", flush=True)

        try:
            print(response.headers["date"], flush=True)
        except KeyError:
            print('No Header : Date', flush=True)

        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s] %s bps" %
                                 ('=' * done, ' ' *
                                  (50-done), dl//(time.clock() - start)))
                sys.stdout.flush()


def file_size(fname):
    statinfo = os.stat(fname)
    return statinfo.st_size


# Returns a beautiful soup object
def get_url(url):
    opener = urllib.request.build_opener()
    urllib.request.install_opener(opener)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    response = urlopen(req)
    soup = bs.BeautifulSoup(response, 'lxml')
    return(soup)


# Cleans up the title of the file pulled from the title heading
def fix_title(content):
    sub_title = content.title.string
    clean_sub_title = re.sub(r'-|:', r'', sub_title).rstrip()
    clean_sub_title = re.search(r'^\s+(.+?) Chapter (\d+)',
                                clean_sub_title, re.IGNORECASE)
    cst = clean_sub_title.group(1)
    issue_number = clean_sub_title.group(2)

    if (int(issue_number) < 10):
        issue_number = '0' + issue_number

    formatted = cst + ' #' + issue_number
    return(formatted)


# Further cleans the title
def clean_title(url):
    main_comic = get_url(url)
    title = main_comic.title.string
    clean_title = re.sub(r"^(.+?) \(.+$", r"\1", title).rstrip()
    clean_title = re.sub(r'-|:', r'', clean_title).rstrip()

    return (clean_title, main_comic)


# Creates the folder in which the individual files will be stored
def create_file_path(clean_title):
    path = download_directory + clean_title
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


'''
Creates the zip archive.
This also will rename the archive to the comic book file format cbz
'''


def create_zip(path, sub_comic, sub_title):
    if not os.path.exists(sub_title + '.zip'):
        for sub in sub_comic.find_all('div'):
            for sub_b in sub.find_all('img'):
                img = sub_b.get('data-src')

                if img is not None:
                    file_name = img.rsplit('/', 1)[-1]
                    file_name = file_name.strip()

                    if not os.path.exists(file_name):
                        download_file(img.strip(), file_name)
                        test_size = file_size(file_name)

                        if int(test_size < 300000):
                            os.remove(file_name)

    return


# function for downloading the entire series
def download_entire_series(main_comic, path):
    for issue in main_comic.find_all('h5'):
        for issue_link in issue.find_all('a'):
            sub_url = issue_link.get('href')
            sub_comic = get_url(sub_url)
            sub_title = fix_title(sub_comic)
            full_path = path + '/' + sub_title
            Path(full_path).mkdir(parents=True, exist_ok=True)
            os.chdir(path + '/' + sub_title)
            print("\nDownloading : " + sub_title, flush=True)

            create_zip(path, sub_comic, sub_title)

            os.chdir(path)

            if not os.path.exists(sub_title + '.zip'):
                print('\nNow Creating Comic Book Archive ....\n',
                      flush=True)
                shutil.make_archive(sub_title, 'zip', full_path)
                shutil.rmtree(sub_title)
                os.rename(sub_title + '.zip', sub_title + '.cbz')
                os.chmod(sub_title + '.cbz', 0o777)
                uid = getpwnam('nobody')[2]
                gid = grp.getgrnam('nogroup')[2]
                os.chown(sub_title + '.cbz', uid, gid)

    os.chmod(path, 0o777)
    uid = getpwnam('nobody')[2]
    gid = grp.getgrnam('nogroup')[2]
    os.chown(path, uid, gid)
    print('\nFile Creation Complete!\n', flush=True)


# function for single issue download
def download_single(issue, download_directory, full_issue, zip_dir):
    issue_request = get_url(issue)
    create_file_path
    imgs = issue_request.find_all("img", {"class": "img-responsive"})

    os.chdir(download_directory)

    for i in imgs:
        try:
            dl = i['data-src']
            print(download_directory)

            if dl is not None:
                file_name = dl.rsplit('/', 1)[-1]
                file_name = file_name.strip()
                print("\nDownloading : " + file_name, flush=True)

                if not os.path.exists(file_name):
                    download_file(dl.strip(), file_name)
                    test_size = file_size(file_name)

                if int(test_size < 300000):
                    os.remove(file_name)
        except Exception:
            continue

    if not os.path.exists(full_issue + '.zip'):
        os.chdir(zip_dir)
        print('\nNow Creating Comic Book Archive ....\n', flush=True)
        shutil.make_archive(full_issue, 'zip', download_directory)
        shutil.rmtree(full_issue)
        os.rename(full_issue + '.zip', full_issue + '.cbz')
        os.chmod(full_issue + '.cbz', 0o777)
        uid = getpwnam('nobody')[2]
        gid = grp.getgrnam('nogroup')[2]
        os.chown(full_issue + '.cbz', uid, gid)

    os.chmod(full_issue + '.cbz', 0o777)
    uid = getpwnam('nobody')[2]
    gid = grp.getgrnam('nogroup')[2]
    os.chown(full_issue + '.cbz', uid, gid)
    print('\nFile Creation Complete!\n', flush=True)


'''
Cleans the downloaded issue filename and preps it to be tagged.
I use commictagger by davide-romanini
( https://github.com/comictagger/comictagger )
'''


def process_issue(issue):
    cleaned_title, comic_name = clean_title(issue)
    striped = cleaned_title.strip()
    striped = re.sub(r'-|:', r'', striped).rstrip()
    issue_num = re.search(r"^(.+?) \((\d+).+Chapter (\d+).+$", striped)
    full_issue = (issue_num.group(1) + " (" +
                  issue_num.group(2) + ") #" + issue_num.group(3))
    path = create_file_path(full_issue)
    download_single(issue, path, full_issue, download_directory)


# process the entire series
def process_series(series):
    cleaned_title, comic_name = clean_title(series)
    print(cleaned_title)
    path = create_file_path(cleaned_title)
    download_entire_series(comic_name, path)


# weekly download function
def weekly_download(weekly):
    '''
    I create a list to store found links so
    that I can later check them to prevent duplicate downloads
    '''

    list = []
    soup = get_url(weekly)
    images = soup.find_all("div", {"class": "row"})

    for image_link in images:
        download_image = image_link.find_all("ul")
        for list in download_image:
            href = list.find_all('a')
            for item in href:
                full_url = item['href']
                verify_url = full_url.rsplit('/', 1)[-1]
                if str.isdigit(verify_url):
                    if full_url not in list:
                        process_issue(full_url)
                        list.append(full_url)


url = get_args()
series, issue, weekly = get_args()

if series:
    process_series(series)

if issue:
    process_issue(issue)

if weekly:
    weekly_download(weekly)
