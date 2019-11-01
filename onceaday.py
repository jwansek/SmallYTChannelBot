import SmallYTChannelBotSubmissions
from time import sleep

SECONDS_IN_DAY = 24 * 60 * 60

while True:
    sleep(60 * 60 * 24)
    SmallYTChannelBotSubmissions.every_day()
    print("Called @ %s" % SmallYTChannelBotSubmissions.get_time())
    #sleep(60 * 60 * 24)
