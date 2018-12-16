import praw
import database

reddit = praw.Reddit(client_id = "PyyyRXa3veWsWA",
                    client_secret = "hAMbhuzdHIew5hmn1CFwWb5FurM",
                    user_agent = "SmallYTChannelBot",
                    username = "SmallYTChannelBot",
                    password = "6NEWGNPBjJjbOjk3lbtm")

subreddit = reddit.subreddit("SmallYTChannel")
db = database.Database()

comment_stream = subreddit.stream.comments(pause_after=-1)
submission_stream = subreddit.stream.submissions(pause_after=-1)
while True:
    for comment in comment_stream:
        if comment is None:
            break
        if not db.id_in_blacklist(comment.id):
            print("archived: ", comment.id)
            db.add_to_blacklist(comment.id)

    for submission in submission_stream:
        if submission is None:
            break
        if not db.id_in_blacklist(submission.id):
            print("archived: ", submission.id)
            db.add_to_blacklist(submission.id)
