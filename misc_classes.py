import os

class SimpleLogger:
    def __init__(self):
        if not os.path.exists("actions.log"):
            file = open("actions.log", "w")
            file.close()

    def log(self, message):
        file = open("actions.log", "a")
        file.write("%s\n" % message)
        file.close()