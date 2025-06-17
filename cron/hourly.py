import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))

from discord_webhook import DiscordWebhook
from operator import itemgetter
import subprocess
import subreddit
import database
import datetime

def dump():
    subprocess.run(["rm", "-fv", "/tmp/*.sql*"])
    proc1 = subprocess.Popen(
        [
            "mysqldump", subreddit.CONFIG["mysql"]["database"], 
            "--ignore-table", "SmallYTChannel.log", "--verbose", 
            "-u", subreddit.CONFIG["mysql"]["user"], 
            "-h", subreddit.CONFIG["mysql"]["host"], 
            "-p%s" % subreddit.CONFIG["mysql"]["passwd"]
        ],
        stdout = subprocess.PIPE
    )
    proc2 = subprocess.Popen("gzip > /tmp/sytc_nolog.sql.gz", shell = True, stdin = proc1.stdout, stdout = subprocess.PIPE)
    output = proc2.communicate()

def push(fp = "/tmp/sytc_nolog.sql.gz"):
    webhook = DiscordWebhook(
        url = subreddit.CONFIG["discord_webhook"],
        content = "Hourly /u/SmallYTChannelBot database dump from %s" % datetime.datetime.now().astimezone().isoformat()
    )

    with open(fp, "rb") as f:
        webhook.add_file(file = f.read(), filename = os.path.split(fp)[-1])

    response = webhook.execute()
    subreddit.display(str(response))

if __name__ == "__main__":
    dump()
    push()

