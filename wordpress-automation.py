import requests
import json
from pathlib import Path
import re
import datetime
import random
import unidecode

requests.packages.urllib3.disable_warnings()

# Load urls
try:
    with open('immo_urls.json', 'r') as file:
        urls = json.load(file)
        URL_POST = urls.get("URL_POST")
        URL_BIEN = urls.get("URL_BIEN")
        URL_EDIT = urls.get("URL_EDIT")
except FileNotFoundError:
    print("immo_urls.json not found. Exitting.")
    exit(-1)

def get_goods(url_to_req, response_prefetched=None, cookies=None, headers=None):
    # Get page response if needed
    if response_prefetched is None and cookies is not None and headers is not None:
        response = requests.get(url_to_req, cookies=cookies, headers=headers).text
    elif response_prefetched is not None:
        response = response_prefetched
    else:
        print("Badly called get_goods(). Check it out.")
        exit(-1)

    # Get titles, URls and dates of goods
    regex_titles = re.compile(
        "(?<=<div class=\"post_title\">)[^<]*"
    )
    goods_titles = [x.group() for x in re.finditer(regex_titles, response)]

    regex_urls = re.compile(
        "(?<=<div class=\"post_name\">)[^<]*"
    )
    goods_urls = [x.group() for x in re.finditer(regex_urls, response)]
    
    
    regex_admin_urls = re.compile(
            f"(?<=<strong><a class=\"row-title\" href=\"){URL_POST}([^\ ]*)"
        )
    goods_admin_urls = [x.group() for x in re.finditer(regex_admin_urls, response)]
    goods_admin_urls = [u[:-1] for u in goods_admin_urls]

    regex_dates = re.compile(
        "(?<=\"Heure de publication\").*(?=td)"
    )
    regex_dates_filter = re.compile(
        "[0-9]{2}/[0-9]{2}/[0-9]{4}"
    )
    goods_dates = [x.group() for x in re.finditer(regex_dates, response)]
    goods_dates = ",".join(goods_dates)
    goods_dates_filtered = [x.group() for x in re.finditer(regex_dates_filter, goods_dates)]
    goods_dates_filtered = [datetime.datetime(int(d[-4:]), int(d[-7:-5]), int(d[-10:-8])) for d in goods_dates_filtered]

    regex_status = re.compile(
        "(?<=<td class='status column-status' data-colname=\"Statut\">).*?(?=</td>)"
    )
    statuses = [x.group() for x in re.finditer(regex_status, response)]
    statuses = ",".join(statuses)
    regex_status_filtered = re.compile(
        "(?<=\">)[^<]*"
    )
    statuses_filtered = [x.group() for x in re.finditer(regex_status_filtered, statuses)]

    assert(len(goods_urls) == len(goods_admin_urls) == len(goods_dates_filtered) == len(goods_titles) == len(statuses_filtered))

    for i in range(len(goods_titles)):
        goods_titles[i] += f" {statuses_filtered[i]}"

    # Return list of goods dicts
    goods_list = []
    for t, u, ua, d in zip(goods_titles, goods_urls, goods_admin_urls, goods_dates_filtered):
        goods_list.append(dict(title=t, url=f"{URL_BIEN}/{u}/", admin_url=ua, date=d))

    return goods_list

def select_goods(goods, amount=7, last_used=True, newer_than=None, max_months=None, exclude_urls=False):
    candidates = []
    goods_c = goods.copy()
    amount = min(amount, len(goods)) # We can't grab more items than what we have in total ...

    # URls in excluded_urls are removed from candidates no matter what
    if exclude_urls:
        with open("./goods/excluded_urls.log") as file:
            excluded_urls = [line.rstrip() for line in file]
            goods_c = [g for g in goods_c if g["url"] not in excluded_urls]

    # If we use last_used : No matter what, the goods that we never uploaded will be candidates
    if last_used:
        with open("./last_date.log") as file:
            read = [line.rstrip() for line in file][0]
            read = read.split(",")
            last_date = datetime.datetime(int(read[0]), int(read[1]), int(read[2]))
        candidates.append([g for g in goods_c if g["date"] > last_date])
        goods_c = [g for g in goods_c if g["date"] <= last_date]

    # If we use max_months, the goods older than a date will NOT be candidates no matter what
    if max_months is not None:
        now = datetime.datetime.now()
        goods_c = [g for g in goods_c if now.month - g["date"].month + 12*(now.year - g["date"].year) <= max_months]

    # If we use newer_than, the goods more recent than a date will be candidates no matter what
    if newer_than is not None:
        candidates.append([g for g in goods_c if g["date"] > newer_than])
        goods_c = [g for g in goods_c if g["date"] <= newer_than]

    # Complete
    if len(candidates) > amount:
        for i in range(len(candidates) - amount):
            candidates.pop(random.randrange(len(candidates)))
    elif len(candidates) < amount:
        i = amount - len(candidates)
        while i > 0:
            if(len(goods_c) > 0) :
                idx = random.randrange(len(goods_c))
                candidates.append(goods_c[idx])
                goods_c.pop(idx)
                i -= 1
            else:
                idx = random.randrange(len(goods))
                curr_url = goods[idx]["url"]
                cand_urls = [g["url"] for g in candidates]
                if curr_url not in cand_urls:
                    candidates.append(goods[idx])
                    i -= 1
                else:
                    goods[idx].pop()

    sanity_check(candidates)
    assert(len(candidates) == amount)
    return candidates

def add_to_excluded(selected):
    with open("./goods/excluded_urls.log", "a") as file:
        for s in selected:
            file.write(s["url"])
        # with open(f"./cre/{args.cookies}", "r") as file:
        #     _ = file.read() # empty file

def sanity_check(goods):
    urls = [g["url"] for g in goods]
    urls_uniq = set(urls)
    if (len(urls) != len(urls_uniq)):
        print("Error ! We've got duplicates in our selected goods. If this error repeats, just do a set() in the sanity check to filter.")
        print(urls)
        exit(-1)

def get_ext(url):
    ext = url[-3:]
    if "jpg" not in ext and "png" not in ext:
        print(f"Picture URL didn't have jpg or png? {url} - {ext}")
        exit(-1)
    return ext

def fetch_good(good, index, choice_mode="first", amount=4, cookies=None, headers=None):
    
    # Mkdir
    filepath = f"./goods/{index}"
    path = Path(filepath)
    path.mkdir(parents=True)
    
    # Write post.log
    with open(f"{filepath}/post.log", "w+") as file:
        file.write(f"{good['title']}\n\n{good['description']}")

    # Download pictures
    regex_images = re.compile(
        '(?<=href=").*?(?=" data-fancybox="gallery")'
    )
    r = requests.get(good["url"], cookies=cookies, headers=headers)
    url_pics = [x.group() for x in re.finditer(regex_images, r.text)]
    print(url_pics)
    amount = min(amount, len(url_pics))

    img = requests.get(url_pics[0], headers=headers)
    ext = get_ext(url_pics[0])
    with open(f"{filepath}/1.{ext}", "wb") as dest:
        dest.write(img.content)
        amount -= 1
    
    if choice_mode == "first":
        for i in range(1, amount + 1):
            img = requests.get(url_pics[i], headers=headers)
            ext = get_ext(url_pics[i])
            with open(f"{filepath}/{i+1}.{ext}", "wb") as dest:
                dest.write(img.content)
    else:
        i = 1
        url_pics[0].pop()
        while i < amount + 1:
            idx = random.randrange(0, len(url_pics))
            img = requests.get(url_pics[idx], headers=headers)
            with open(f"{filepath}/{i+1}.{ext}", "wb") as dest:
                dest.write(img.content)
            url_pics[idx].pop()
            i += 1
    



########### RUN ##########

# Set cookies
cooks = "./cre/cooks.txt"
cook_file = Path(f"{cooks}")
if cook_file.is_file():
    with open(f"{cooks}") as file:
        cookies = [json.loads(cookie) for cookie in file]
        cookies = cookies[0]
else:
    print(f"Cookies file {cooks} isn't a file")
    exit(-1)

# Set mandatory headers
headers = {
    "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1",
}

r = requests.get(URL_EDIT, cookies=cookies, headers=headers)

# Get page number
regex_page_number = re.compile(
    "(?<=<a class='last-page button' href=')[^<>]*"
)
page_num = [x.group() for x in re.finditer(regex_page_number, r.text)]
num_pages = int(page_num[0].split("paged=")[-1][:-1])
assert( num_pages == int(page_num[1].split("paged=")[-1][:-1]))

# Get URLs of pages
next_urls = []
for i in range(1, num_pages):
    page_url = f"{URL_EDIT}&paged={i+1}"
    next_urls.append(page_url)

# Get goods list
goods_list = get_goods(url_to_req=None, response_prefetched=r.text)
for u in next_urls:
    goods_list.extend(get_goods(url_to_req=u, cookies=cookies, headers=headers))

selected_goods = select_goods(goods_list, amount=2, last_used=False, max_months=2, exclude_urls=True)

for s in selected_goods:
    s["admin_url"] = s["admin_url"].replace("amp;", "")

regex_price = re.compile(
    '[\d]*(?=" type="text" id="REAL_HOMES_property_price")'
)
regex_desc = re.compile(
    '(?<=name="content" id="content">).*?(?=</textarea>)', re.DOTALL
)

# regex_desc = re.compile(
#     '(?<=<div class="rh_content">.*?(?=</div>)', re.DOTALL
# )

for s in selected_goods:
    r = requests.get(s["admin_url"], cookies=cookies, headers=headers)
    s["price"] = str(int([x.group() for x in re.finditer(regex_price, r.text)][0]))
    if s["title"].endswith("louer"):
        s["title"] += f" à {s['price']} DHS/mois"
    elif s["title"].endswith("vendre"):
        s["title"] += f" à {s['price']} DHS"
    else:
        print(f"Why don't we have louer/vendre at the end of status at this :\n{s['title']} ?\nExitting....")
        exit(-1)

    description = [x.group() for x in re.finditer(regex_desc, r.text)][0]
    s["description"] = unidecode.unidecode(description)

for s in selected_goods:
    print(s)

for i, g in enumerate(selected_goods):
    fetch_good(g, i + 1, cookies=cookies, headers=headers)

# testing purposes
if False:
    add_to_excluded(selected_goods)

# TODO : check how /r and /n work on FB or insta