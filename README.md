# comic-dl-ru
readcomicsonline.ru comic file downloader

This is a work in progress.

Based on comic-dl by Xonshiz ( https://github.com/Xonshiz/comic-dl )
I needed a script to download comics from readcomicsonline.ru and at the time of writing this that was not an option using comic-dl
Pretty simple script which allows user to download either the entire series, and individual issue or the entire weekly release

# Usage

comic-dl-ru.py <-i | --issue | -s | --series | -w | --weekly> <cooresponding url>
  
  examples
  
    comic-dl-ru.py -i https://readcomicsonline.ru/comic/journey-to-star-wars-the-rise-of-skywalker-allegiance-2019/4
  
        -- the above will download the single issue #4 of Star Wars The Rise Of Skywalker Allegiance
  
  
    comic-dl-ru.py -s https://readcomicsonline.ru/comic/journey-to-star-wars-the-rise-of-skywalker-allegiance-2019
  
        -- would download all available issues of Star Wars The Rise Of Skywalker Allegiance
  
  
    comic-dl-ru.py -w https://readcomicsonline.ru/news/weekly-comic-upload-oct-23rd-2019
  
        -- would download every comic available on October 23rd 2019
  
  
  Right now this ONLY work with https://readcomicsonline.ru and was meant to be an extra tool to use with https://github.com/Xonshiz/comic-dl
 
- Individual files are downloaded to the folder set in the config.ini file.
- Full series are also stored in the downloaded folder but are stored in cooresponding subfolders.  ie. A subfolder Batman would contain the individual issues.


I have only tested this using python 3 and ubuntu server.
