from imgurpython import ImgurClient
from operator import itemgetter
import database
import datetime
import logging
import ytapi
# import graph
import time
import praw
import json
import re
import os

if os.path.split(os.getcwd())[-1] == "onceaday":
    configpath = "../config.json"
else:
    configpath = "config.json"

with open(configpath, "r") as f:
    CONFIG = json.load(f)

REDDIT = praw.Reddit(**CONFIG["redditapi"])
REDDIT.validate_on_submit = True
SUBREDDIT = REDDIT.subreddit(CONFIG["subreddit"])
COMMENT_TAIL = CONFIG["comment_tail"]
FREE_FLAIRS = CONFIG["free_flairs"]

IMGUR = ImgurClient(**CONFIG["imgurapi"])

# logging.basicConfig( 
#     format = "%(process)s\t[%(asctime)s]\t%(message)s", 
#     level = logging.INFO,
#     handlers=[
#         logging.FileHandler("actions.log"),
#         logging.StreamHandler()
#     ])

handler = logging.FileHandler("/logs/api.log")
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("[%(asctime)s]\t%(message)s"))
for logger_name in ("praw", "prawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

def get_time():
    return time.strftime("%b %d %Y %H:%M:%S", time.gmtime())

def display(message, concerning = None):
    # logging.info(message)
    print(message)

    #yes it'd be prettier to do this with a logging.Handler, but alas
    #due to `concerning` it'd be more complicated than doing it like this
    with database.Database() as db:
        db.append_log("%d\t[%s]\t%s" % (os.getpid(), get_time(), message), concerning)

def get_lambda_from_flair(s):
    result = re.search("\[(.*)\]", s)
    if result is not None and "λ" in result.group(1):
        return result.group(1)
    else:
        return ""

def update_users_flair_from_comment(comment, reddit):
    #implemented only for legacy
    update_users_flair(str(comment.author), reddit)

def get_medal(actualscore):
    if actualscore >= 10 and actualscore < 25:
        return "🥉 Bronze "
    elif actualscore >= 25 and actualscore < 50:
        return "🥈 Silver "
    elif actualscore >= 50 and actualscore < 100:
        return "🥇 Gold "
    elif actualscore > 100:
        return "🏆 Platinum "
    else:
        return ""

def update_users_flair(username, reddit):
    flairtext = next(reddit.subreddit(CONFIG["subreddit"]).flair(redditor=username))["flair_text"]
    if flairtext is None:
        flairtext = ""
    else:
        flairscore = get_lambda_from_flair(flairtext)
        flairtext = str(flairtext.replace("[%s] " % flairscore, ""))
    if username in get_mods(reddit):
        newflair = "[🏆 ∞λ] %s" % (flairtext)
    else:
        with database.Database() as db:
            actualscore = db.get_lambda(username)[0]
        newflair = "[%s%iλ] %s" % (get_medal(actualscore), actualscore, flairtext)

    logging.info("/u/%s had their flair updated" % username)
    reddit.subreddit(CONFIG["subreddit"]).flair.set(redditor = username, text = newflair)

def get_mods(reddit):
    return [str(i) for i in reddit.subreddit(CONFIG["subreddit"]).moderator()] + ["AutoModerator"]

def handle_mylambda(comment, reddit):
    author = str(comment.author)
    with database.Database() as db:
        λ, links = db.get_lambda(author)
    if author in get_mods(reddit):
        text = "/u/%s is a moderator, and therefore has ∞λ." % author
    else:
        text = "/u/%s currently has %iλ, and has helped helping the following posts:" % (author, λ)
        count = 0
        for link in links:
            if "www.reddit.com" not in link:
                link = "https://www.reddit.com" + link

            #set a max limit on the number of times this will iterate to stop it
            #breaking because of Reddit's character limit.
            count += 1
            text += "\n\n- [%s](%s)" % (REDDIT.submission(url = link).title, link)
            if count > 100:  #experminent with this number
                text += "\n\n[%i more...]" % len(links) - count
                break

    update_users_flair_from_comment(comment, reddit)
    return text

def handle_givelambda(comment, reddit):
    submission = comment.submission
    parentauthour = str(comment.parent().author)
    op = str(comment.author)
    with database.Database() as db:
        if op == parentauthour:
            text = "You cannot give yourself λ."
        elif parentauthour == "SmallYTChannelBot":
            text = "Please only give lambda to humans."
        elif str(comment.author) in get_mods(reddit):
            text = "The moderator /u/%s has given /u/%s 1λ. /u/%s now has %iλ." % (str(comment.author), parentauthour, parentauthour, db.get_lambda(parentauthour)[0] + 1)
            db.give_lambda(parentauthour, submission.permalink, timestamp = int(submission.created_utc)) 
            display(text, concerning=comment.permalink)
        elif submission.link_flair_text in FREE_FLAIRS:
            text = "You cannot give lambda in free posts anymore."
            display("Giving lambda was rejected due to being a free post", concerning=comment.permalink)
        elif op != str(submission.author):
            text = "Only the OP can give λ."
        elif db.user_given_lambda(parentauthour, str(submission.permalink)):
            text = "You have already given /u/%s λ for this submission. Why not give λ to another user instead?" % parentauthour
            display("Giving lambda was rejected for being the same user", concerning=comment.permalink)
        elif len(comment.parent().body) < CONFIG["min_comment_len"]:
            text = "You can no longer give λ to comments that are fewer than %i characters in length. This is to encourage specific, detailed feedback." % CONFIG["min_comment_len"]
            display("Giving lambda was rejected due to insufficient length", concerning=comment.permalink)
        else:
            display("'/u/%s' has given '/u/%s' lambda!" % (op, parentauthour), concerning=comment.permalink)
            text = "You have given /u/%s 1λ. /u/%s now has %iλ" % (parentauthour, parentauthour, db.get_lambda(parentauthour)[0] + 1)
        
            #bonus lambda giving was removed
            # if not db.link_in_db(submission.permalink) or not db.link_in_db(submission.permalink.replace("https://www.reddit.com", "")):
            #     db.give_lambda(parentauthour, submission.permalink, op)
            #     display("The OP received lambda too!")
            # else:
            db.give_lambda(parentauthour, submission.permalink, timestamp = int(submission.created_utc))
    
    # update_users_flair_from_comment(comment)
    update_users_flair_from_comment(comment.parent(), reddit)
    return text

def handle_setlambda(comment, reddit):
    try:
        splitted = comment.body.split()
        user = splitted[1].replace("/u/", "").replace("u/", "")
        toset = int(splitted[2].replace("\\", ""))
    
        with database.Database() as db:
            text = "/u/%s had their lambda set to %iλ by a moderator." % (user, toset)
            db.set_lambda(user, toset)
        display("A moderator set /u/%s λ to %d" % (user, toset), concerning=comment.permalink)
    except Exception as e:
        display("{ERROR while setting λ} %s" % e, concerning=comment.permalink)
        text = r"An error was encountered. Please use the syntax `!setlambda <user> <set to {integer}>`" + "\n\nThe error was:\n\n" + str(e)

    update_users_flair(user, reddit)
    return text

def handle_submission(submission, reddit):
    with database.Database() as db:
        score = db.get_lambda(str(submission.author))[0]
    if submission.link_flair_text in FREE_FLAIRS:
        if "youtube.com" in str(submission.url) or "youtu.be" in str(submission.url):
            text = "Your post has been removed because it has the wrong flair. [Discussion], [Meta] and [Collab] flairs are only for text submissions."
            submission.mod.remove()
            display("/u/%s had their submission removed for using the wrong flair." % submission.author, concerning=submission.permalink)
        else:
            text = "Your post is a discussion, meta or collab post so it costs 0λ."
    else:
        if score < 3:
            text = """Thank you for submitting to /r/SmallYTChannel. Unfortunally, you submission has been removed since you do not have enough λ. You need
            3λ to post. You currently have %iλ. For more information, read the [FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % score
            submission.mod.remove()
            display("/u/%s had their submission removed for insufficient lambda." % submission.author, concerning=submission.permalink)
        else:
            text = """Thank you for submitting to /r/SmallYTChannel. You have spent 3λ to submit here, making your current balance %iλ.
            /u/%s, please comment `!givelambda` to the most helpful advice you are given. 
            For more information, read the [FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % (score - 3, str(submission.author))
            with database.Database() as db:
                db.change_lambda(str(submission.author), -3)

            try:
                ytid = ytapi.get_videoId_from_url(submission.url)
                if "/" not in ytid:
                    ytdata = ytapi.get_video_data(ytid)

                    text += """
\n\n\n##Video data:

**Field**|**Data**
:-|:-
Title|%s
Thumbnail|[Link](%s)
Views|%s
Length|%s
Likes|%s
Comments|%s
Description|%s

##Channel Data:

**Field**|**Data**
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
            except:
                pass

    update_users_flair(str(submission.author), reddit)
    return text

def handle_comment(comment, reddit):
    response = None
    if "!mylambda" in comment.body.lower() and str(comment.author) != "SmallYTChannelBot":
        response = handle_mylambda(comment, reddit)

    if "!givelambda" in comment.body.lower() and str(comment.author) != "SmallYTChannelBot":
        response = handle_givelambda(comment, reddit)        

    if comment.body.startswith("!setlambda") and str(comment.author) in get_mods(reddit):
        response = handle_setlambda(comment, reddit)

    if response is not None:
        reply = comment.reply(response + COMMENT_TAIL)
        reply.mod.distinguish(sticky = False)

def stream(reddit):
    subreddit = reddit.subreddit(CONFIG["subreddit"])
    streams = [subreddit.stream.comments(pause_after=-1), subreddit.stream.submissions(pause_after=-1)]
    with database.Database() as db:
        while True:
            for stream in streams:
                for item in stream:
                    if item is None:
                        break

                    if db.id_in_blacklist(item.id):
                        continue

                    db.add_to_blacklist(item.id)
                    if str(type(item)) == "<class 'praw.models.reddit.comment.Comment'>":
                        handle_comment(item, reddit)

                    elif str(type(item)) == "<class 'praw.models.reddit.submission.Submission'>":
                        display("There has been a new submission: '%s', with flair '%s'" % (item.title, item.link_flair_text), concerning=item.permalink)

                        if str(item.author) not in get_mods(reddit):
                            reply = item.reply(handle_submission(item, reddit) + COMMENT_TAIL)
                            reply.mod.distinguish(sticky = True)
                            reply.mod.approve()

def main():
    reddit = praw.Reddit(**CONFIG["redditapi"])
    reddit.validate_on_submit = True
    try:
        stream(reddit)
    except Exception as e:
        display("{ERROR} %s" % str(e))
        time.sleep(60)
        main()


if __name__ == "__main__":
    main()

