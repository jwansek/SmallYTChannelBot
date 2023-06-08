import matplotlib.pyplot as plt
import datetime
import math
import os
import re

def round_to_min(dt: datetime.datetime):
    return datetime.datetime(
        year = dt.year,
        month = dt.month,
        day = dt.day,
        hour = dt.hour,
        minute = math.floor(dt.minute)
    )

with open(os.path.join("logs", "api.log"), "r") as f:
    s = f.read().split("\n")

timestamps = set()

for l in s:
    x = re.search(r"^.*\tResponse: 200", l)
    if x is not None:
        timestamps.add(datetime.datetime.strptime(x.group()[1:24], "%Y-%m-%d %H:%M:%S,%f"))

d = {}
for timestamp in timestamps:
    nearest = round_to_min(timestamp)

    try:
        d[nearest] += 1
    except KeyError:
        d[nearest] = 1

d_sorted = {k: v for k, v in sorted(d.items(), key=lambda x: x[0])}

fig, ax = plt.subplots()
ax.plot(list(d_sorted.keys()), list(d_sorted.values()))

plt.show()