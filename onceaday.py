import os
os.chdir("/root/SmallYTChannelBotSubmissions")

import subreddit

subreddit.every_day()
subreddit.logging.info("Called OAD prog @ %s" % subreddit.get_time())
