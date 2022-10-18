# Picture-Thread-Crawler
A simple Python program that scrapes all images posted in a thread on [Bahamut](https://forum.gamer.com.tw/).

## Known Issue(s)
Due to my laziness, some file paths filenames are hardcoded so that it would not work properly in other environments.

## Environment

This project mainly uses the following packages:
| Package | Version |
|---|---|
| python | 3.10.4 |
| requests | 2.28.1 |
| lxml | 4.9.1 |
| bs4 | 4.11.1 |

Detailed packages and versions can be found in [environment.yml](environment.yml). To create an identical virtual environment in Anaconda, use the command `conda env create -f environment.yml`.
