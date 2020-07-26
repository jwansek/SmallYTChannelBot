import pymysql
import sqlite3
import subprocess
import subreddit
import time

class Database:
    def __enter__(self):
        self.__connection = pymysql.connect(
            **subreddit.CONFIG["mysql"],
            charset = "utf8mb4",
            # cursorclass = pymysql.cursors.DictCursor
        )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def migrate(self, sqlitefile):
        conn = sqlite3.connect(sqlitefile)
        cur = conn.cursor()
        cur.execute("SELECT * FROM blacklist;")
        blacklist = [i[1] for i in cur.fetchall()]
        cur.close()
        conn.close()

        with self.__connection.cursor() as cursor:
            cursor.execute("DELETE FROM blacklist;")
            cursor.execute("""
            ALTER TABLE blacklist CHANGE blacklistID blacklistID int(11) AUTO_INCREMENT;
            """)
            cursor.execute("""
            ALTER TABLE lambdas CHANGE lambdaID lambdaID int(11) AUTO_INCREMENT;
            """)
            cursor.execute("""
            ALTER TABLE lambdas DROP FOREIGN KEY lambdas_FK_0_0;
            """)
            cursor.execute("""
            ALTER TABLE users CHANGE userID userID int(11) AUTO_INCREMENT;
            """)
            cursor.execute("""
            ALTER TABLE lambdas ADD FOREIGN KEY (userID) REFERENCES users(userID);
            """)
            cursor.execute("""
            ALTER TABLE stats CHANGE statID statID int(11) AUTO_INCREMENT;
            """)

            #still cant get executemany to work :/
            # cursor.executemany("INSERT INTO blacklist (prawID) VALUES (%s);", (blacklist, ))
            for prawID in blacklist:
                cursor.execute("INSERT INTO blacklist (prawID) VALUES (%s);", (prawID, ))
        
        self.__connection.commit()

    def change_lambda(self, user, changeby):
        with self.__connection.cursor() as cursor:
        #this will make it go negative. You must check this operation is allowed.
            cursor.execute("""
            UPDATE users SET lambda = (
                (SELECT lambda FROM users WHERE user_name = %s) + %s
            ) WHERE user_name = %s;
            """, (user, changeby, user))
        
        self.__connection.commit()

    def give_lambda(self, user, link, timestamp = int(time.time()), op = None):
        def give(user, link = None):
            with self.__connection.cursor() as cursor:
                #check if the user has an entry in the database
                cursor.execute("SELECT userID FROM users WHERE user_name = %s;", (user, ))
                try:
                    id_ = cursor.fetchone()[0]
                except TypeError:
                    #the user isn't in the database
                    cursor.execute("""
                    INSERT INTO users (user_name, lambda) VALUES (%s, 1);
                    """, (user, ))
                    if link is not None:
                        cursor.execute("""
                        INSERT INTO lambdas (userID, permalink, created) VALUES ((
                            SELECT userID FROM users WHERE user_name = %s
                        ), %s, %s);
                        """, (user, link, timestamp))
                else:
                    #update their lambda and add to lambdas
                    self.change_lambda(user, 1)
                    if link is not None:
                        cursor.execute("""
                        INSERT INTO lambdas (userID, permalink, created) VALUES (%s, %s, %s);
                        """, (id_, link, timestamp))
        
            self.__connection.commit()

        #give one lambda to both the user and the OP
        give(user, link)
        if op is not None:
            give(op)

    def get_lambda(self, user):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT lambda FROM users WHERE user_name = %s", (user, ))
            try:
                lambda_ = cursor.fetchone()[0]
            except TypeError:
                #the user isn't in the database, and therefore has no lambda 
                return 0, []
            else:
                cursor.execute("SELECT permalink FROM lambdas WHERE userID = (SELECT userID FROM users WHERE user_name = %s);", (user, ))
                links = [i[0] for i in cursor.fetchall()]

                return lambda_, links

    def link_in_db(self, link):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT permalink FROM lambdas WHERE permalink = %s;", (link, ))
            try:
                links = [i[0] for i in cursor.fetchall()]
            except TypeError:
                links = []

            return link in links

    def add_to_blacklist(self, id):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO blacklist (prawID) VALUES (%s);", (id, ))
        self.__connection.commit()

    def id_in_blacklist(self, id):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT prawID FROM blacklist WHERE prawID = %s;", (id, ))
            try:
                ids = [i[0] for i in cursor.fetchall()]
            except TypeError:
                ids = []

            return id in ids

    def get_scores(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT users.user_name, users.lambda, COUNT(users.user_name) 
            FROM lambdas INNER JOIN users ON users.userID = lambdas.userID 
            GROUP BY users.user_name;
            """)
            return cursor.fetchall()

    def update_stats(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO stats (lambdaCount, helpGiven, uniqueUsers, date) VALUES (
                (SELECT SUM(lambda) FROM users),
                (SELECT COUNT(lambdaID) FROM lambdas),
                (SELECT COUNT(user_name) FROM users),
            (SELECT DATE_FORMAT(NOW(), "%Y-%m-%d")));
            """)
            self.__connection.commit()

    def get_stats(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT * FROM stats;")
            return cursor.fetchall()

    def user_given_lambda(self, user, permalink):
        links = self.get_lambda(user)[1]
        return permalink in links or permalink.replace("https://www.reddit.com", "") in links

    def get_all_lambdas(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT lambdas.lambdaID, lambdas.permalink, users.user_name, lambdas.created 
            FROM lambdas INNER JOIN users ON lambdas.userID = users.userID;
            """)
            return cursor.fetchall()

    def add_date_to_permalink(self, permalink, date):
        with self.__connection.cursor() as cursor:
            cursor.execute("UPDATE lambdas SET created = %s WHERE permalink = %s;", (date, permalink))
        self.__connection.commit()

    def get_lambda_leaderboard(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT users.user_name, COUNT(lambdas.userID) AS times_helped, users.lambda 
            FROM lambdas INNER JOIN users ON users.userID = lambdas.userID 
            WHERE created > (UNIX_TIMESTAMP() - (60 * 60 * 24 * 30)) 
            GROUP BY lambdas.userID ORDER BY times_helped DESC LIMIT 10;
            """)
            return cursor.fetchall()
        

def migrate(sqlitefile):
    subprocess.run([
        "sqlite3mysql", 
        "-f", sqlitefile,
        "-d", "SmallYTChannel",
        "-u", subreddit.CONFIG["mysql"]["user"], 
        "-p", subreddit.CONFIG["mysql"]["passwd"]
    ])

    with Database() as db:
        db.migrate(sqlitefile)

if __name__ == "__main__":
    # migrate("SmallYTChannelDatabase.db")
    with Database() as db:
        #db.give_lambda("floofleberries", "https://www.reddit.com/r/SmallYTChannel/comments/ho5b5p/new_video_advice_would_help_but_even_just_a_watch/")
        print(db.get_lambda_leaderboard())


