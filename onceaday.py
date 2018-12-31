import SmallYTChannelBotSubmissions
from time import sleep

SECONDS_IN_DAY = 25 * 60 * 60

while True:
    SmallYTChannelBotSubmissions.every_day()
    sleep(SECONDS_IN_DAY)
