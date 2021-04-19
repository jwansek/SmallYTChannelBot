from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import js2py
import os

if os.path.split(os.getcwd())[-1] == "onceaday":
    configpath = "../config.json"
else:
    configpath = "config.json"

with open(configpath, "r") as f:
    CONFIG = json.load(f)

ERROR_DICT =  {
        "title": "ERROR Video deleted?",
        "description": "ERROR Video deleted?",
        "channel": "ERROR Video deleted?",
        "subscribers": "ERROR Video deleted?",
        "videos": "ERROR Video deleted?",
        "channelViews": "ERROR Video deleted?",
        "channelThumb": "ERROR Video deleted?",
        "thumbnail": "ERROR Video deleted?",
        "length": "ERROR Video deleted?",
        "views": "ERROR Video deleted?",
        "likes": "ERROR Video deleted?",
        "dislikes": "ERROR Video deleted?",
        "comments": "ERROR Video deleted?"
    }

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = CONFIG["youtubeapi"]["developer_key"]
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

#run JavaScript because I don't understand regular expressions so we can copy this bad boy from Stack Overflow
get_videoId_from_url = js2py.eval_js(r"""function $(url){
                            var re = /https?:\/\/(?:[0-9A-Z-]+\.)?(?:youtu\.be\/|youtube(?:-nocookie)?\.com\S*?[^\w\s-])([\w-]{11})(?=[^\w-]|$)(?![?=&+%\w.-]*(?:['"][^<>]*>|<\/a>))[?=&+%\w.-]*/ig;
                            return url.replace(re, '$1');
                        }""")

def _yt_time_to_norm(time):
    origtime = time
    if time == "ERROR Video deleted?":
        return time

    time = time[2:].replace("H", ":").replace("M", ":").replace("S", "")

    out = ""
    for i in time.split(":"):
        if len(i) == 1:
            out += "0" + i + ":"
        elif len(i) == 0:
            out += "00:"
        else:
            out += i + ":"

    return out[:-1]



#this would be better as a class but I can't be bothered so dictionary it is
def get_video_data(videoId):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)


    #youTubeData = youtube.videos().list(part = "snippet", id = videoId).execute()["items"][0]["snippet"]

    #return {"title": youTubeData["title"], "description": youTubeData["description"], "tags": youTubeData["tags"]}

    try:
        youTubeData = youtube.videos().list(part = "snippet,contentDetails,statistics", id = videoId).execute()["items"][0]
    except IndexError:
        return ERROR_DICT

    snippet = youTubeData["snippet"]
    length = youTubeData["contentDetails"]["duration"]
    stats = youTubeData["statistics"]
    channelId = snippet["channelId"]

    channelData = youtube.channels().list(part = 'snippet,statistics', id = channelId).execute()["items"][0]

    return {
        "title": snippet["title"],
        "description": snippet["description"].replace("\n", "⤶"),
        "channel": channelData["snippet"]["title"],
        "subscribers": channelData["statistics"]["subscriberCount"],
        "videos": channelData["statistics"]["videoCount"],
        "channelViews": channelData["statistics"]["viewCount"],
        "channelThumb": channelData["snippet"]["thumbnails"]["high"]["url"],
        "thumbnail": snippet["thumbnails"]["high"]["url"],
        "length": _yt_time_to_norm(length),
        "views": stats["viewCount"],
        "likes": stats["likeCount"],
        "dislikes": stats["dislikeCount"],
        "comments": stats["commentCount"]
    }


if __name__ == '__main__':
    try:
        print(get_video_data(get_videoId_from_url("https://www.youtube.com/watch?v=ZYqG31V4qtA")))
    except HttpError as e:
        print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))