import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))

from operator import itemgetter
import subreddit
import database
import datetime
import graph

def main():
    subreddit.display("Starting every day program...")
    subreddit.display("Updating database statistics...")
    with database.Database() as db:
        db.update_stats()
        subreddit.display("Posting and updating wiki...")
        # update_tables(db.get_scores(), db.get_stats())

    subreddit.display("Formatting leaderboard...")
    leaderboard = format_monthly_leaderboard()
    subreddit.display("Made the following leaderboard:\n======================\n%s\n======================\n" % leaderboard)
    subreddit.display("Updating sidebar...")
    #it'd be cool to find a way to access this directly without iteration
    for widget in subreddit.SUBREDDIT.widgets.sidebar:
        if widget.shortName == "Monthly Lambda Leaderboard":
            widget.mod.update(text = leaderboard)
            subreddit.display("Updated in new reddit...")
    
    sidebar = subreddit.SUBREDDIT.mod.settings()["description"]
    oldtable = sidebar.split("------")[-1]
    subreddit.SUBREDDIT.wiki['config/sidebar'].edit(content = sidebar.replace(oldtable, "\n\n## Monthly Lambda Leaderboard\n\n" + leaderboard))
    subreddit.display("Updated in old reddit...")
    subreddit.display("Completed.")

    subreddit.logging.info("Called OAD prog @ %s" % subreddit.get_time())

# def update_tables(scores, data):
#     # really ought to switch to jinja for this...
#     content = ""
#     date = str(datetime.date.today())
#     mods = get_mods()
#     # imagepath = graph.make_graph(data)
#     # imageurl = upload_image(imagepath, date)
#     bylambda = [i for i in sorted(scores, key = itemgetter(1), reverse = True) if i[0] not in mods][:10]
#     byhelps = sorted(scores, key = itemgetter(2), reverse = True)[:10]

#     content += "\n\n##/r/SmallYTChannel lambda tables: %s" % date

#     content += "\n\n###By lambda:"
#     content += "\n\nUsername|Lambda|Help given\n:--|:--|:--"
#     for line in bylambda:
#         content += "\n/u/%s|%i|%i" % (line[0], line[1], line[2])

#     content += "\n\n###By Help given:"
#     content += "\n\nUsername|Lambda|Help given\n:--|:--|:--"
#     for line in byhelps:
#         λ = str(line[1])
#         if line[0] in mods:
#             λ = "∞"
#         content += "\n/u/%s|%s|%i" % (line[0], λ, line[2])

#     # content += "\n\n##Statistics from %s:\n\nIf you're looking at this through the wiki, not through the bot's profile, then" % (date)
#     # content += "the most up-to-date graph will be shown below. To see the graph at this date, follow [this link.](%s)" % (imageurl)
#     content += "\n\n![](%%%%wikigraph%%%%)\n\nTotal λ in circulation|Useful advice given|Unique users\n:--|:--|:--\n%i|%i|%i" % (data[-1][1], data[-1][2], data[-1][3])
    
#     # subreddit.REDDIT.subreddit("u_SmallYTChannelBot").submit("/r/SmallYTChannel Statistics: %s" % date, url = imageurl).reply(content)


def get_mods():
    return [str(i) for i in subreddit.SUBREDDIT.moderator()] + ["AutoModerator"]

def format_monthly_leaderboard():
    with database.Database() as db:
        leaderboard = db.get_lambda_leaderboard()
        out = "**Username**|**Medal**|**Times Helped**|**Lambda**\n:-|:-|:-|:-\n"
        for username, times_helped, λ in leaderboard:
            out += "/u/%s|%1s|%s|%sλ\n" % (username, subreddit.get_medal(λ)[:-1], times_helped, λ)
        return out + "\nLast updated: %s" % subreddit.get_time()

# def upload_image(path, date):
#     config = {
# 		'album': None,
# 		'name':  'SmallYTChannelBot Statistics graph: %s' % date,
# 		'title': 'SmallYTChannelBot Statistics graph: %s' % date,
# 		'description': 'SmallYTChannelBot Statistics graph: %s' % date
#     }

#     image = subreddit.IMGUR.upload_from_path(path, config = config)

#     return "https://i.imgur.com/%s.png" % image["id"]

if __name__ == "__main__":
    main()
