import os
import bs4
import tqdm
import requests

request_headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

def get_character_urls(page_no: int=1):
    char_urls = []
    url = f"https://www.anime-planet.com/characters/all?page={page_no}"
    response = requests.get(url.strip(), headers=request_headers)
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    char_anchor_tags = soup.find_all("a", class_="name")
    for tag in char_anchor_tags:
        char_urls.append(f"https://www.anime-planet.com{tag.attrs['href']}")

    return char_urls

# clear file on first run.
open("all_char_urls.txt", "w")
pbar = tqdm.tqdm(range(15327), desc="collected 0 characters")
char_count = 0
for i in pbar:
    f = open("all_char_urls.txt", "a")
    char_urls = get_character_urls(page_no=i+1)
    char_count += len(char_urls)
    for char_url in char_urls:
        f.write(char_url+"\n")
    f.close()
    pbar.set_description(f"collected {char_count} characters")
    print()
