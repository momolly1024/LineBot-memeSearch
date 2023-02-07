from fastapi import FastAPI, Request, HTTPException

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,VideoSendMessage,ImageSendMessage
)
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()

line_bot_api = LineBotApi(os.getenv("Channel_access_token"))
handler = WebhookHandler(os.getenv("Channel_secret"))
api_key = os.getenv("GiphyAPI_Key")

app = FastAPI()
 
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
        if event.message.text=='隨機' or event.message.text=='random':
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=getRandom(), preview_image_url=getRandom()))
        elif event.message.text=='熱門' or event.message.text=='popular':
            data = []
            for i in getTrend():
                data.append(ImageSendMessage(
                    original_content_url=i,
                    preview_image_url=i,
                ))
            line_bot_api.reply_message(event.reply_token, data)
        else:
            try:
                data = []
                for i in getSearch(event.message.text):
                    data.append(ImageSendMessage(
                    original_content_url=i,
                    preview_image_url=i,
                ))
                line_bot_api.reply_message(event.reply_token, data)            
            except LineBotApiError as e:
                errorText=f"找不到與 {event.message.text} 有關的迷因圖片"
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=errorText))

        
        
        
        
        
        
        
        
        
        
        
def getSearch(keyWord):
    
    response = requests.get(f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={keyWord}&limit=3")
    res=[]
    
    if response.status_code == 200:
        data = response.json()
        gifs = data["data"]
        for i, gif in enumerate(gifs):
            gif_url = gif["images"]["original"]["url"]
            res.append(gif_url)
        return res     
    else:
        print("Search request failed with status code ", response.status_code)



# 熱門前10張
def getTrend():
    url = f"https://api.giphy.com/v1/gifs/trending?api_key={api_key}&limit=3"
    response = requests.get(url)
    res=[]  
    if response.status_code == 200:
        data = json.loads(response.content.decode("utf-8"))
        gifs = data["data"]
        for i, gif in enumerate(gifs):
            gif_url = gif["images"]["original"]["url"]
            res.append(gif_url)
        return res  
    else:
        print("Something went wrong")


# 隨機一張
def getRandom():
    response = requests.get(f"http://api.giphy.com/v1/gifs/random?api_key={api_key}&tag=meme")
    if response.status_code == 200:
        gifs = response.json()['data']
        return gifs["images"]["original"]["url"]


