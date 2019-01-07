import SmallYTChannelBotSubmissions
from time import sleep

SECONDS_IN_DAY = 25 * 60 * 60

while True:
    SmallYTChannelBotSubmissions.every_day()
    print("Called @ %s" % SmallYTChannelBotSubmissions.get_time)
    sleep(SECONDS_IN_DAY)
