from mpl_toolkits.axes_grid1 import host_subplot
from misc_classes import SimpleLogger
import mpl_toolkits.axisartist as AA
from imgurpython import ImgurClient
import matplotlib.pyplot as plt
from operator import itemgetter
from database import Database
import matplotlib
import ytapi
import datetime
import logging
import ytapi
import login
import time
import praw
import re
import os

reddit = login.REDDIT

subreddit = reddit.subreddit("SmallYTChannel")
#subreddit = reddit.subreddit("jwnskanzkwktest")

db = Database()
simplelogger = SimpleLogger()

def get_time():
    #this is not the correct way to do this but I don't care
    return str(datetime.datetime.now())[:-7]

def display(message):
    message = "%d\t[%s]\t%s" % (os.getpid(), get_time(), message)
    print(message)
    simplelogger.log(message)

def get_lambda_from_flair(s):
    result = re.search("\[(.*)\]", s)
    if result is not None and "λ" in result.group(1):
        return result.group(1)
    else:
        return ""

def update_users_flair(comment):
    username = str(comment.author)
    flairscore = get_lambda_from_flair(str(comment.author_flair_text))
    flairtext = comment.author_flair_text
    if flairtext is None:
        flairtext = ""
    else:
        flairtext = str(flairtext.replace("[%s] " % flairscore, ""))
    if username in [str(i) for i in subreddit.moderator()] + ["AutoModerator"]:
        newflair = "[∞λ] %s" % (flairtext)
    else:
        actualscore = db.get_lambda(username)[0]
        newflair = "[%iλ] %s" % (actualscore, flairtext)
    subreddit.flair.set(redditor = username, text = newflair)

def get_mods():
    return [str(i) for i in subreddit.moderator()] + ["AutoModerator"]

def _make_graph(data):
    fig = plt.figure()
    
    lambdaCount = [i[1] for i in data]
    helpGiven = [i[2] for i in data]
    uniqueUsers = [i[3] for i in data]
    date = [datetime.datetime.strptime(i[4], "%Y-%m-%d") for i in data]

    fig, ax1 = plt.subplots()
    ax1.plot(date, lambdaCount, label = "Total λ in circulation", color = "r")
    ax1.set_ylabel("Total λ / help given")

    ax1.plot(date, helpGiven, label = "Times help given", color = "g")
    
    ax2 = ax1.twinx()
    ax2.plot(date, uniqueUsers, label = "Unique users")
    ax2.set_ylabel("No. Unique Users")

    ax1.legend()
    ax2.legend(loc = 4)
    fig.autofmt_xdate()

    filepath = "graph.png"
    fig.savefig(filepath)
    return filepath

def _update_tables(scores, data):
    content = ""
    date = str(datetime.date.today())
    mods = get_mods()
    imagepath = _make_graph(data)
    imageurl = _upload_image(imagepath, date)
    bylambda = [i for i in sorted(scores, key = itemgetter(1), reverse = True) if i[0] not in mods][:10]
    byhelps = sorted(scores, key = itemgetter(2), reverse = True)[:10]

    subreddit.stylesheet.upload("wikigraph", imagepath)

    content += "\n\n##/r/SmallYTChannel lambda tables: %s" % date

    content += "\n\n###By lambda:"
    content += "\n\nUsername|Lambda|Help given\n:--|:--|:--"
    for line in bylambda:
        content += "\n/u/%s|%i|%i" % (line[0], line[1], line[2])

    content += "\n\n###By Help given:"
    content += "\n\nUsername|Lambda|Help given\n:--|:--|:--"
    for line in byhelps:
        λ = str(line[1])
        if line[0] in mods:
            λ = "∞"
        content += "\n/u/%s|%s|%i" % (line[0], λ, line[2])

    content += "\n\n##Statistics from %s:\n\n![](%%%%wikigraph%%%%)\n\nTotal λ in circulation|Useful advice given|Unique users\n:--|:--|:--\n%i|%i|%i" % (date, data[-1][1], data[-1][2], data[-1][3])
    
    reddit.subreddit("u_SmallYTChannelBot").submit("/r/SmallYTChannel Statistics: %s" % date, url = imageurl).reply(content).mod.distinguish(sticky = True)

    subreddit.wiki["lambdatables"].edit(content, reason = "Update: %s" % date)
    subreddit.wiki[date].edit(content, reason = "Update: %s" % date)

    currentdata = subreddit.wiki["index"].content_md
    currentdata += "\n\n* [%s](/r/SmallYTChannel/wiki/%s)" % (date, date)

    subreddit.wiki["index"].edit(currentdata, reason = "Update: %s" % date)

def _upload_image(path, date):
    client = login.IMGUR

    config = {
		'album': None,
		'name':  'SmallYTChannelBot Statistics graph: %s' % date,
		'title': 'SmallYTChannelBot Statistics graph: %s' % date,
		'description': 'SmallYTChannelBot Statistics graph: %s' % date
    }

    image = client.upload_from_path(path, config = config)

    return "https://i.imgur.com/%s.png" % image["id"]

def every_day():
    display("Updated statistics")
    db.update_stats()
    _update_tables(db.get_scores(), db.get_stats())

def main():
    tail = "\n\n\n ^/u/SmallYTChannelBot ^*made* ^*by* ^/u/jwnskanzkwk. ^*PM* ^*for* ^*bug* ^*reports.* ^*For* ^*more* ^*information,* ^*read* ^*the* ^[FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)"

    comment_stream = subreddit.stream.comments(pause_after=-1)
    submission_stream = subreddit.stream.submissions(pause_after=-1)
    while True:
        try:
            for comment in comment_stream:
                if comment is None:
                    break
                if not db.id_in_blacklist(comment.id):
                    db.add_to_blacklist(comment.id)

                    if "!mylambda" in comment.body.lower() and str(comment.author) != "SmallYTChannelBot":
                        author = str(comment.author)
                        λ, links = db.get_lambda(author)
                        if author in get_mods():
                            text = "/u/%s is a moderator, and therefore has ∞λ." % author
                        else:
                            if λ == 0:
                                text = "/u/%s has 0λ." % author
                            else:
                                text = "/u/%s has %iλ, from helping the following posts:" % (author, λ)
                                count = 0
                                for link in links:
                                    if "www.reddit.com" not in link:
                                        link = "https://www.reddit.com" + link

                                    #set a max limit on the number of times this will iterate to stop it
                                    #breaking because of Reddit's character limit.
                                    count += 1
                                    text += "\n\n- [%s](%s)" % (reddit.submission(url = link).title, link)
                                    if count > 20:  #experminent with this number
                                        text += "\n\n[%i more...]" % len(links) - count
                                        break

                        reply = comment.reply(text + tail)
                        reply.mod.distinguish(sticky = False)
                        update_users_flair(comment)


                    if "!givelambda" in comment.body.lower() and str(comment.author) != "SmallYTChannelBot":
                        submission = comment.submission
                        parentauthour = str(comment.parent().author)
                        op = str(comment.author)
                        if op == parentauthour:
                            text = "You cannot give yourself λ."
                        elif parentauthour == "SmallYTChannelBot":
                            text = "Please only give lambda to humans."
                        elif str(comment.author) in get_mods():
                            text = "The moderator /u/%s has given /u/%s 1λ. /u/%s now has %iλ." % (str(comment.author), parentauthour, parentauthour, db.get_lambda(parentauthour)[0] + 1)
                            db.give_lambda(parentauthour, submission.permalink) 
                            display(text)
                        elif op != str(submission.author):
                            text = "Only the OP can give λ."
                        elif db.user_given_lambda(parentauthour, str(submission.permalink)):
                            text = "You have already given /u/%s λ for this submission. Why not give λ to another user instead?" % parentauthour
                        else:
                            display("'/u/%s' has given '/u/%s' lambda!" % (op, parentauthour))
                            text = "You have given /u/%s 1λ. /u/%s now has %iλ" % (parentauthour, parentauthour, db.get_lambda(parentauthour)[0] + 1)
                           
                            if not db.link_in_db(submission.permalink) or not db.link_in_db(submission.permalink.replace("https://www.reddit.com", "")):
                                db.give_lambda(parentauthour, submission.permalink, op)
                                display("The OP received lambda too!")
                            else:
                                db.give_lambda(parentauthour, submission.permalink)
                        
                        update_users_flair(comment)
                        update_users_flair(comment.parent())
                        reply = comment.reply(text + tail)
                        reply.mod.distinguish()

                    if comment.body[:11] == "!takelambda" and str(comment.author) in get_mods():
                        try:
                            splitted = comment.body.split()
                            user = splitted[1].replace("/u/", "")
                            toremove = int(splitted[2])
                            reason = " ".join(splitted[3:])
                        
                            text = "/u/%s has had %iλ taken away from them for the reason '%s'. /u/%s now has %iλ" % (user, toremove, reason, user, db.get_lambda(user)[0] - toremove)
                            db.change_lambda(user, -toremove)
                            dispay("A moderator removed %i lambda from /u/%s for the reason '%s'" % (toremove,  user, reason))
                        except Exception as e:
                            display("{ERROR while removing λ} %s" % e)
                            text = r"An error was encountered. Please use the syntax `!takelambda [user] [how much to remove {integer}] [reason]`"
                            reply = comment.reply(text + tail)
                            reply.mod.distinguish()
                            continue

                        update_users_flair(comment.parent())
                        reply = comment.reply(text + tail)
                        reply.mod.distinguish()

      
            for submission in submission_stream:
                if submission is None:
                    break
                if not db.id_in_blacklist(submission.id):
                    db.add_to_blacklist(submission.id)                         
                    display("There has been a new submission: '%s', with flair '%s'" % (submission.title, submission.link_flair_text))

                    if str(submission.author) not in get_mods():
                        score = db.get_lambda(str(submission.author))[0]
                        if submission.link_flair_text in ["Discussion", "Meta", "Collab"]:
                            if "youtube.com" in str(submission.url) or "youtu.be" in str(submission.url):
                                text = "Your post has been removed because it has the wrong flair. [Discussion], [Meta] and [Collab] flairs are only for text submissions."
                                submission.mod.remove()
                                display("/u/%s had their submission removed for using the wrong flair." % submission.author)
                            else:
                                text = "Your post is a discussion, meta or collab post so it costs 0λ."
                        else:
                            if score < 3:
                                text = """Thank you for submitting to /r/SmallYTChannel. Unfortunally, you submission has been removed since you do not have enough λ. You need
                                3λ to post. You currently have %iλ. For more information, read the [FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % score
                                submission.mod.remove()
                                display("/u/%s had their submission removed for insufficient lambda." % submission.author)
                            else:
                                text = """Thank you for submitting to /r/SmallYTChannel. You have spent 3λ to submit here, making your current balance %iλ.
                                /u/%s, please comment `!givelambda` to the most helpful advice you are given. You
                                will be rewarded 1λ if you do so.  For more information, read the [FAQ.](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % (score - 3, str(submission.author))
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
Likes/Dislikes|%s/%s
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
                                except:
                                    pass

                        update_users_flair(submission)
                        reply = submission.reply(text + tail)
                        reply.mod.distinguish(sticky = True)
                        reply.mod.approve()

        except Exception as e:
            display("{ERROR} %s" % e)
            continue

if __name__ == "__main__":
    file = open("pid.txt", "w")
    file.write(str(os.getpid()))
    file.close()

    logging.basicConfig(filename = "api.log", format = "[%(asctime)s] %(process)d\t%(message)s", level = logging.DEBUG)

    display("\n####################\n[%s] RESTARTED\n####################\n" % get_time())
    main()

