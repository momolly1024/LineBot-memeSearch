from fastapi import FastAPI, Request, HTTPException

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, VideoSendMessage, ImageSendMessage
)
import json
import random
import requests
import os
from dotenv import load_dotenv
load_dotenv()

line_bot_api = LineBotApi(os.getenv("Channel_access_token"))
handler = WebhookHandler(os.getenv("Channel_secret"))
api_key = os.getenv("GiphyAPI_Key")

app = FastAPI()

MIN_FRAMES = 15


@app.post("/")
async def echoBot(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameters")
    return "OK"


@handler.add(MessageEvent, message=(TextMessage))
def handling_message(event):
    if isinstance(event.message, TextMessage):
        text = event.message.text
        want_video = 'gif' in text.lower()
        clean_text = text.lower().replace('gif', '').strip()

        if clean_text in ['隨機', 'random']:
            result = getRandom()
            if want_video:
                msg = VideoSendMessage(
                    original_content_url=result['mp4'],
                    preview_image_url=result['still']
                )
            else:
                msg = ImageSendMessage(
                    original_content_url=result['url'],
                    preview_image_url=result['url']
                )
            line_bot_api.reply_message(event.reply_token, msg)

        elif clean_text in ['熱門', 'popular']:
            results = getTrend()
            if want_video:
                data = [VideoSendMessage(original_content_url=r['mp4'], preview_image_url=r['still']) for r in results]
            else:
                data = [ImageSendMessage(original_content_url=r['url'], preview_image_url=r['url']) for r in results]
            line_bot_api.reply_message(event.reply_token, data)

        else:
            keyword = text.replace('gif', '').replace('GIF', '').strip()
            try:
                results = getSearch(keyword)
                if want_video:
                    data = [VideoSendMessage(original_content_url=r['mp4'], preview_image_url=r['still']) for r in results]
                else:
                    data = [ImageSendMessage(original_content_url=r['url'], preview_image_url=r['url']) for r in results]
                line_bot_api.reply_message(event.reply_token, data)
            except LineBotApiError:
                errorText = f"找不到與 {keyword} 有關的迷因圖片"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=errorText))


def _extract(gif):
    return {
        'url': gif["images"]["original"]["url"],
        'mp4': gif["images"]["original"]["mp4"],
        'still': gif["images"]["original_still"]["url"]
    }


def _long_enough(gif):
    return int(gif["images"]["original"].get("frames", 0)) >= MIN_FRAMES


def getSearch(keyWord):
    offset = random.randint(0, 25)
    response = requests.get(f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={keyWord}&limit=10&offset={offset}")
    if response.status_code == 200:
        gifs = response.json()["data"]
        results = [_extract(g) for g in gifs if _long_enough(g)]
        return results[:3]
    return []


def getTrend():
    offset = random.randint(0, 25)
    response = requests.get(f"https://api.giphy.com/v1/gifs/trending?api_key={api_key}&limit=10&offset={offset}")
    if response.status_code == 200:
        gifs = response.json()["data"]
        results = [_extract(g) for g in gifs if _long_enough(g)]
        return results[:3]
    return []


def getRandom():
    for _ in range(3):
        response = requests.get(f"https://api.giphy.com/v1/gifs/random?api_key={api_key}&tag=meme")
        if response.status_code == 200:
            gif = response.json()['data']
            if _long_enough(gif):
                return _extract(gif)
    return None
