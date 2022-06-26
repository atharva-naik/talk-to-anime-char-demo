import os
import bs4
import json
import jinja2
import uvicorn
import requests
from typing import *
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.templating import Jinja2Templates
# templates = Jinja2Templates(directory="static")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


CHAR_URLS_PATH = "all_char_urls.txt"
NGROK_URL = "https://9d64-49-32-136-100.in.ngrok.io/"

char_urls = []
with open(CHAR_URLS_PATH, "r") as f:
    for line in f:
        char_urls.append(line.strip())
char_json_db = {}
current_char_id = ""

def get_char_name_from_url(url):
    return " ".join(os.path.basename(url).split("-")).title()

bio_missing = len(char_urls)
for char_url in char_urls:
    name = get_char_name_from_url(char_url)
    char_json_db[name] = {
        "name": name,
        "bio": None,
        "url": char_url,
        "profile_pic_url": None,
    }

with open("char_json_db.json", "w") as f:
    json.dump(char_json_db, f, indent=4)
print(f"found {len(char_json_db)} characters in database.")
print(f"bio missing for {bio_missing} characters.")

def fetch_char_data_from_url(url):
    soup = bs4.BeautifulSoup(requests.get(url).text, features="html.parser")
    return {
        "bio": soup.find("div", itemprop="description").text,
        "profile_pic_url": soup.find("img", itemprop="image").attrs["src"],
    }

def fetch_char_bio_from_url(url):
    soup = bs4.BeautifulSoup(requests.get(url).text, features="html.parser")
    return soup.find("div", itemprop="description").text

def get_char_bio(key: str, db: dict):
    # add bio to db and return it if bio is missing
    bio = db[key]["bio"]
    # print(db[key])
    # print(db[key]["url"])
    if bio is None:
        print(f"missing bio for '{key}'. Will be downloaded now!")
        url = db[key]["url"]
        bio = fetch_char_bio_from_url(url)
        db[key]["bio"] = bio

    return bio, db

def get_char_data(key: str, db: dict):
    # add bio to db and return it if bio is missing
    bio = db[key]["bio"]
    profile_pic_url = db[key]["profile_pic_url"]
    if bio is None or profile_pic_url is None:
        print(f"missing bio/profile_pic for '{key}'. Will be downloaded now!")
        url = db[key]["url"]
        data = fetch_char_data_from_url(url)
        db[key].update(data)

    return db[key], db

class CharInfo(BaseModel):
    bio: str
    profile_pic_url: str

# print(len(char_json_db.keys()))
@app.get("/character")
def fetch_character(name: str):
    global char_json_db
    global current_char_id
    print(f"\x1b[34;1mcalled api for character: {name}\x1b[0m")
    data, char_json_db = get_char_data(key=name, db=char_json_db)
    # item = CharInfo(bio=bio, profile_pic_url="")
    item = {"bio": data["bio"], "profile_pic_url": data['profile_pic_url']}
    print(item)
    # init ModMax character:
    current_char_id = json.loads(
        requests.get(
            os.path.join(NGROK_URL, 
            f"init?desc={data['bio']}")
        ).text
    )
    print(f"set current_char_id to: {current_char_id}")

    return JSONResponse(content=item)

@app.get("/message")
def send_message_to_character(body: str):
    import urllib.parse
    global current_char_id
    print(f"\x1b[32;1msending message: {body} to {current_char_id}\x1b[0m")  
    json_response = json.loads(
        requests.get(
            os.path.join(NGROK_URL, 
            f"prompt?query='{urllib.parse.quote_plus(body)}'&char_id={current_char_id}")
        ).text
    )

    return JSONResponse({"text": json_response["text"]})

@app.get("/")
def home():
    global char_json_db
    first_item = list(char_json_db.keys())[0]
    first_item_data, char_json_db = get_char_data(first_item, char_json_db)
    fetch_character(name=first_item)
    html = jinja2.Template(r"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Talk to Anime Characters :)</title>
        <link rel="stylesheet" href="static/style.css" />
    </head>
    <body>
        <div style="text-align: center; margin-left: auto; margin-right: auto">
            <select id="char_dropdown" class="char-dropdown">
            {% for name, record in json_db.items() %}
                <option class="char-dropdown-option" value="{{ name }}">{{ name }}</option>
            {% endfor %}
            </select>
        </div>
        <br>
        <div style="text-align: center; margin-left: auto; margin-right: auto; width: 70%;">
            <p class="sub-heading"> Character Biography</p>
            <img class="profile-pic" id="profile_pic" height="200" src="{{ first_item_image }}"/> 
            <div class="bio" id="description">
                {{ first_item_bio }}
            </div>
        </div>
        <br>
        <div style="text-align: center; margin-left: auto; margin-right: auto; width: 70%;">
            <div id="chat_pod"></div>
        </div>
        <br>
        <div style="text-align: center; margin-left: auto; margin-right: auto;">
            <textarea id="chat_input" placeholder="Talk to {{ name }} using the power of GPT-3"></textarea>
            <br>
            <button type="button" onclick="sendMessageToModMax()" id="submit_btn" class="btn btn-primary">Send Message</button>
        </div> 
        <script>
            function addMyMessage(text) {
                var msg = document.createElement("div");
                msg.classList.add("container");
                msg.classList.add("darker");
                var img = document.createElement("img");
                img.src = "https://www.w3schools.com/w3images/avatar_g2.jpg"
                img.classList.add("right");

                msg.appendChild(img);
                var msgBody = document.createElement("p");
                msgBody.textContent = text;
                msg.appendChild(msgBody)
                chat_pod.appendChild(msg);
            }
            function addBotMessage(text) {
                var msg = document.createElement("div");
                msg.classList.add("container");
                var img = document.createElement("img");
                img.src = profile_pic.src;

                msg.appendChild(img);
                var msgBody = document.createElement("p");
                msgBody.textContent = text;
                msg.appendChild(msgBody)
                chat_pod.appendChild(msg);
            }
            function sendMessageToModMax() {
                console.log(chat_input.value);
                addMyMessage(chat_input.value)
                var url = `./message?body=${chat_input.value}`;
                fetch(url)
                .then((response) => response.json())
                .then((data) => {
                    console.log(data);
                    addBotMessage(data.text);
                })  
                chat_input.value = "";
            }
            char_dropdown.addEventListener('change', (event) => {
                console.log(event.target.value);
                var url = `./character?name=${event.target.value}`;
                fetch(url)
                .then((response) => response.json())
                .then((data) => {
                    console.log(data);
                    description.innerText = data.bio;
                    profile_pic.src = data.profile_pic_url;
                })
                chat_pod.innerHTML = "";                
            });
        </script>
    </body>
</html>""").render(
    name=first_item,
    first_item_image=first_item_data["profile_pic_url"],
    json_db=char_json_db, 
    first_item_bio=first_item_data["bio"]
)
    # print(html)
    return HTMLResponse(content=html, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, log_level="debug")


