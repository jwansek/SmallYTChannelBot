import praw
import database
import login
import ytapi

reddit = login.REDDIT

subreddit = reddit.subreddit("jwnskanzkwktest")

tail = "\n\n\n ^/u/SmallYTChannelBot ^*made* ^*by* ^/u/jwnskanzkwk. ^*PM* ^*for* ^*bug* ^*reports.* ^*For* ^*more* ^*information,* ^*read* ^*the* ^[FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)"

submission_stream = subreddit.stream.submissions(pause_after=-1)
while True:

    for submission in submission_stream:
        if submission is not None:

            text = "Thank you for submitting..."
            ytid = ytapi.get_videoId_from_url(submission.url)
            if "/" not in ytid:
                ytdata = ytapi.get_video_data(ytid)

                text += """
\n\n\n##Video data:

Field|Data
:-|:-
Title|%s
Thumbnail|[Link](%s)
Views|%s
Length|%s
Likes/Dislikes|%s/%s
Comments|%s
Description|%s

##Channel Data:

Field|Data
:-|:-
Name|%s
Thumbnail|[Link](%s)
Subscribers|%s
Videos|%s
Views|%s

                """ % (
                    ytdata["title"],
                    ytdata["thumbnail"],
                    ytdata["views"],
                    ytdata["length"],
                    ytdata["likes"],
                    ytdata["dislikes"],
                    ytdata["comments"],
                    ytdata["description"],
                    ytdata["channel"],
                    ytdata["channelThumb"],
                    ytdata["subscribers"],
                    ytdata["videos"],
                    ytdata["channelViews"]
                )

                curflair = submission.link_flair_text
                if str(curflair) != "None":
                    submission.mod.flair(" %s | %s | :youtube: %s" % (curflair, ytdata["length"], ytdata["channel"]))
                else:    
                    submission.mod.flair("%s | :youtube: %s" % (ytdata["length"], ytdata["channel"]))

                reply = submission.reply(text + tail)
                reply.mod.distinguish(sticky = True)
