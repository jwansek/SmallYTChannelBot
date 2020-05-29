import sqlite3

class Database:
    def __init__(self):   
        self.connection = sqlite3.connect("SmallYTChannelDatabase.db")
        self.cursor = self.connection.cursor()

    def change_lambda(self, user, changeby):
        #this will make it go negative. You must check this operation is allowed.
        self.cursor.execute("UPDATE users SET lambda = ((SELECT lambda FROM users WHERE user_name = ?) + ?) WHERE user_name = ?;", (user, changeby, user))
        self.connection.commit()

    def give_lambda(self, user, link, timestamp = None, op = None):
        def give(user, link = None):
            #check if the user has an entry in the database
            self.cursor.execute("SELECT userID FROM users WHERE user_name = ?;", (user, ))
            try:
                id_ = self.cursor.fetchone()[0]
            except TypeError:
                #the user isn't in the database
                self.cursor.execute("INSERT INTO users (user_name, lambda) VALUES (?, 1);", (user, ))
                self.connection.commit()
                if link is not None:
                    self.cursor.execute("INSERT INTO lambdas (userID, permalink, created) VALUES ((SELECT userID FROM users WHERE user_name = ?), ?, ?);", (user, link, timestamp))
            else:
                #update their lambda and add to lambdas
                self.change_lambda(user, 1)
                if link is not None:
                    self.cursor.execute("INSERT INTO lambdas (userID, permalink, created) VALUES (?, ?, ?);", (id_, link, timestamp))
        
            self.connection.commit()

        #give one lambda to both the user and the OP
        give(user, link)
        if op is not None:
            give(op)

    def get_lambda(self, user):
        self.cursor.execute("SELECT lambda FROM users WHERE user_name = ?", (user, ))
        try:
            lambda_ = self.cursor.fetchone()[0]
        except TypeError:
            #the user isn't in the database, and therefore has no lambda 
            return 0, []
        else:
            self.cursor.execute("SELECT permalink FROM lambdas WHERE userID = (SELECT userID FROM users WHERE user_name = ?);", (user, ))
            links = [i[0] for i in self.cursor.fetchall()]

            return lambda_, links

    def link_in_db(self, link):
        self.cursor.execute("SELECT permalink FROM lambdas;")
        try:
            links = [i[0] for i in self.cursor.fetchall()]
        except TypeError:
            links = []

        return link in links

    def add_to_blacklist(self, id):
        self.cursor.execute("INSERT INTO blacklist (prawID) VALUES (?);", (id, ))
        self.connection.commit()

    def id_in_blacklist(self, id):
        self.cursor.execute("SELECT prawID FROM blacklist;")
        try:
            ids = [i[0] for i in self.cursor.fetchall()]
        except TypeError:
            ids = []

        return id in ids

    def get_scores(self):
        self.cursor.execute("SELECT users.user_name, users.lambda, COUNT(users.user_name) FROM lambdas INNER JOIN users ON users.userID = lambdas.userID GROUP BY users.user_name;")
        return self.cursor.fetchall()

    def update_stats(self):
        query = """INSERT INTO stats (lambdaCount, helpGiven, uniqueUsers, date) VALUES (
        (SELECT SUM(lambda) FROM users),
        (SELECT COUNT(lambdaID) FROM lambdas),
        (SELECT COUNT(user_name) FROM users),
        (SELECT strftime('%Y-%m-%d')));"""

        self.cursor.execute(query)
        self.connection.commit()

    def get_stats(self):
        self.cursor.execute("SELECT * FROM stats;")
        return self.cursor.fetchall()

    def user_given_lambda(self, user, permalink):
        links = self.get_lambda(user)[1]
        return permalink in links or permalink.replace("https://www.reddit.com", "") in links

    def get_all_lambdas(self):
        self.cursor.execute("SELECT lambdas.lambdaID, lambdas.permalink, users.user_name, lambdas.created FROM lambdas INNER JOIN users ON lambdas.userID = users.userID;")
        return self.cursor.fetchall()

    def add_date_to_permalink(self, permalink, date):
        self.cursor.execute("UPDATE lambdas SET created = ? WHERE permalink = ?;", (date, permalink))
        self.connection.commit()

    def get_lambda_leaderboard(self):
        self.cursor.execute("""
        SELECT users.user_name, COUNT(lambdas.userID) AS times_helped, users.lambda 
        FROM lambdas INNER JOIN users ON users.userID = lambdas.userID 
        WHERE created > (strftime('%s','now') - (60 * 60 * 24 * 30)) 
        GROUP BY lambdas.userID ORDER BY times_helped DESC LIMIT 10;
        """)
        return self.cursor.fetchall()

if __name__ == "__main__":
    import subreddit
    print(subreddit.every_day())