import praw
import database
import login
import ytapi

reddit = login.REDDIT

subreddit = reddit.subreddit("SmallYTChannel")

tail = "\n\n\n ^/u/SmallYTChannelBot ^*made* ^*by* ^/u/jwnskanzkwk. ^*PM* ^*for* ^*bug* ^*reports.* ^*For* ^*more* ^*information,* ^*read* ^*the* ^[FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)"

submission_stream = subreddit.stream.submissions(pause_after=-1)
while True:

    for submission in submission_stream:
        if submission is not None:

            text = "Thank you for submitting..."
            ytid = ytapi.get_videoId_from_url(submission.url)
            if "/" not in ytid:
                ytdata = ytapi.get_video_data(ytid)

                print(ytdata["length"], submission.url)
