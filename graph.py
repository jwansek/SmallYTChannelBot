from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt
import matplotlib
import datetime

def make_graph(data):
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