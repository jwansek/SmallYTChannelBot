from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from imgurpython import ImgurClient
import matplotlib.pyplot as plt
from operator import itemgetter
from database import Database
import matplotlib
import datetime
import login
import time
import praw
import re

reddit = login.REDDIT

subreddit = reddit.subreddit("SmallYTChannel")
#subreddit = reddit.subreddit("jwnskanzkwktest")
db = Database()

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
    ax1.plot(date, lambdaCount, label = "Total λ given", color = "r")
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

    content += "\n\n##Statistics from %s:\n\n![](%%%%wikigraph%%%%)\n\nTotal λ given|Useful advice given|Unique users\n:--|:--|:--\n%i|%i|%i" % (date, data[-1][1], data[-1][2], data[-1][3])
    
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

                    if "!mylambda" in comment.body and str(comment.author) != "SmallYTChannelBot":
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


                    if "!givelambda" in comment.body and str(comment.author) != "SmallYTChannelBot":
                        submission = comment.submission
                        parentauthour = str(comment.parent().author)
                        op = str(comment.author)
                        if op == parentauthour:
                            text = "You cannot give yourself λ."
                        elif op == "SmallYTChannelBot":
                            text = "Please only give lambda to humans."
                        elif op != str(submission.author):
                            text = "Only the OP can give λ."
                        elif comment.is_root:
                            text = "You can only give λ to top-level comments."
                        else:
                            print("'/u/%s' has given '/u/%s' lambda!" % (op, parentauthour))
                            text = "You have given /u/%s 1λ. /u/%s now has %iλ" % (parentauthour, parentauthour, db.get_lambda(parentauthour)[0] + 1)
                            
                            if not db.link_in_db(submission.permalink) or not db.link_in_db(submission.permalink.replace("https://www.reddit.com", "")):
                                db.give_lambda(parentauthour, submission.permalink, op)
                                print("The OP has received lambda too!")
                            else:
                                db.give_lambda(parentauthour, submission.permalink)
                        
                        update_users_flair(comment)
                        update_users_flair(comment.parent())
                        reply = comment.reply(text + tail)
                        reply.mod.distinguish()
      
            for submission in submission_stream:
                if submission is None:
                    break
                if not db.id_in_blacklist(submission.id):
                    db.add_to_blacklist(submission.id)                         
                    print("There has been a new submission: '%s', with flair '%s'" % (submission.title, submission.link_flair_text))

                    if str(submission.author) not in get_mods():
                        score = db.get_lambda(str(submission.author))[0]
                        if submission.link_flair_text in ["Discussion", "Meta", "Collab"]:
                            text = "Your post is a discussion, meta or collab post so it costs 0λ."
                        else:
                            if score < 3:
                                text = """Thank you for submitting to /r/SmallYTChannel. Please be aware that soon you will need to have at least 3λ to submit here.
                                You currently have %iλ. /u/%s, please comment `!givelambda` to the most helpful advice you are given. You will be rewarded 1λ if you
                                do so. For more information, read the [FAQ](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % (score, str(submission.author))
                                #submission.mod.remove()
                            else:
                                #db.change_lambda(str(submission.author), -3)
                                text = """Thank you for submitting to /r/SmallYTChannel. You have spent 3λ to submit here, making your current balance %iλ. Soon
                                you will have to spend your λ to post here.  /u/%s, please comment `!givelambda` to the most helpful advice you are given. You
                                will be rewarded 1λ if you do so.  For more information, read the [FAQ](https://www.reddit.com/user/SmallYTChannelBot/comments/a4u7qj/smallytchannelbot_faq/)""" % (score, str(submission.author))

                        update_users_flair(submission)
                        reply = submission.reply(text + tail)
                        reply.mod.distinguish(sticky = True)

        except Exception as e:
            print("[ERROR]\t%s" % e)
            continue

if __name__ == "__main__":
    main()

