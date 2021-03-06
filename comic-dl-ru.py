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
ConfigurationFile = '/root/test/config.ini'

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

    parser.add_argument('-l', '--latest', type=str, required=False,
                        metavar='<url of Main page>')
                        
    parser.add_argument('-r', '--rng', type=str, required=False,
                        metavar='Issue range <1-10> <url of Main page>')

    args = parser.parse_args()
    series = args.series
    issue = args.issue
    weekly = args.weekly
    latest = args.latest
    rng = args.rng

    if not series and not issue and not weekly and not latest:
        parser.error('Comic Ripper requires an arguement')

    if series and issue and weekly and latest:
        parser.error('Only 1 option is allowed')

    if rng and not series:
        parser.error('Range option requires series arguement')
    
    if rng and weekly and issue:
        parser.error('Range option only works with the series switch')
        
    return (series, issue, weekly, latest, rng)


# Purely for looks, this function displays a file download status
def download_file(url, file_name):
    start = time.clock()
    with open(file_name, "wb") as f:
        print("\nDownloading " + file_name, flush=True)
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'},
                                stream=True)
        total_length = int(response.headers.get('content-length'))

        if total_length:
            print(total_length / 1024, "Kb", flush=True)

        try:
            print(response.headers["date"], flush=True)
        except KeyError:
            print('No Header : Date', flush=True)

        if total_length is None:
            print(response.content, flush=True)
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

        print("\n")


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
    stripped = re.search(r'^\s+(.+?) Chapter.+?(\d+)',
                                clean_sub_title, re.IGNORECASE)

    cst = stripped.group(1)
    issue_number = stripped.group(2)

    if (int(issue_number) < 10):
        issue_number = '0' + issue_number

    if 'Annual' in clean_sub_title:
        formatted = cst + ' Annual' + ' #' + issue_number
    else:
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
            print("Downloading : " + sub_title, flush=True)

            create_zip(path, sub_comic, sub_title)

            os.chdir(path)

            if not os.path.exists(sub_title + '.zip'):
                print('Now Creating Comic Book Archive ....',
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
    print('File Creation Complete!\n\n', flush=True)


# function for single issue download
def download_single(issue, download_directory, full_issue, zip_dir):
    issue_request = get_url(issue)
    create_file_path(full_issue)
    imgs = issue_request.find_all("img", {"class": "img-responsive"})

    os.chdir(download_directory)
    print("------------------------------------------------------------", flush=True)
    print("\nDownloading --- | " + full_issue + " | ---\n", flush=True)
    print("------------------------------------------------------------", flush=True)

    for i in imgs:
        try:
            dl = i['data-src']

            if dl is not None:
                file_name = dl.rsplit('/', 1)[-1]
                file_name = file_name.strip()

                if not os.path.exists(file_name):
                    download_file(dl.strip(), file_name)
                    test_size = file_size(file_name)

                if int(test_size < 300000):
                    os.remove(file_name)
        except Exception:
            continue

    if not os.path.exists(full_issue + '.zip'):
        os.chdir(zip_dir)
        print('Now Creating Comic Book Archive ....', flush=True)
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
    print('File Creation Complete!\n\n', flush=True)


'''
Cleans the downloaded issue filename and preps it to be tagged.
I use commictagger by davide-romanini
( https://github.com/comictagger/comictagger )
'''


def process_issue(issue):
    cleaned_title, comic_name = clean_title(issue)
    striped = cleaned_title.strip()
    striped = re.sub(r'-|:', r'', striped).rstrip()

    issue_num = re.search(r"^(.+) Chapter (\d+).+$", striped)

    try:
        issue_name = issue_num.group(1)
    except Exception:
        issue_name = ''

    try:
        issue_number = issue_num.group(2)
    except Exception:
        issue_number = ''

    full_issue = (issue_name + ' #' + issue_number)

    check_file = full_issue + ".cbz"

    if check_if_exists(check_file) is True:
        print("Exists : " + full_issue, flush=True)
        return

    path = create_file_path(full_issue)
    download_single(issue, path, full_issue, download_directory)


def grab_latest_issue(latest):
    main_comic = get_url(latest)

    for sub_div in main_comic.find_all('i'):
        value = sub_div.attrs.get('class')[1]
        if value == 'fa-bars':
            next_tag = sub_div.findAllNext("a", href=True)
            for individual_issue in next_tag:
                match = re.match(".+\/\d+$", individual_issue.get('href'))
                if match:
                    process_issue(individual_issue.get('href'))


# process the entire series
def process_series(series):
    cleaned_title, comic_name = clean_title(series)
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


def check_if_exists(file):
    comics = os.listdir(download_directory)

    if file in comics:
        return True
    else:
        return False


url = get_args()
series, issue, weekly, latest, rng = get_args()

if series and not rng:
    process_series(series)

if issue:
    process_issue(issue)

if weekly:
    weekly_download(weekly)

if latest:
    grab_latest_issue(latest)

if rng:
    issue_range = rng.split('-')
    start = int(issue_range[0])
    stop = int(issue_range[1]) + 1
    series_range = range(start, stop)
    for dl_range in series_range:
        full_url = series + '/' + str(dl_range)
        process_issue(full_url)
