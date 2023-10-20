import requests
import json
from pathlib import Path
import re
import datetime
import random
import unidecode
import argparse

requests.packages.urllib3.disable_warnings()

def cook_request():
    pass

def post_request():
    pass

def display_request():
    pass

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--post', type=bool, help='Only post if true')
    args = parser.parse_args()

    req = cook_request()

    if args.post:
        post_request()
    else:
        display_request()

## TODO cronjob to load batch every week and script to download the batch and check if everything is ok
# the poster will remove one folder everytime
# sanity check on the batch and mail if something is wrong, create a flag to stop doing anything