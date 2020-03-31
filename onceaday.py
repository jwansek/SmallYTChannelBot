import subreddit
from time import sleep

SECONDS_IN_DAY = 24 * 60 * 60

while True:
    sleep(60 * 60 * 13)
    subreddit.every_day()
    print("Called @ %s" % subreddit.get_time())
    sleep(60 * 60 * 11)
