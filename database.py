import pymysql
import sqlite3
import subprocess
import subreddit
import time
import datetime
import logging
import re

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
        """Function for converting data from an SQLite3 database to
        MySQL. Will only be called once ever probably. First the data is
        converted using migrate() global function.

        Args:
            sqlitefile (str): Path to the SQLite3 file
        """
        conn = sqlite3.connect(sqlitefile)
        cur = conn.cursor()
        cur.execute("SELECT * FROM blacklist;")
        blacklist = [i[1] for i in cur.fetchall()]
        cur.close()
        conn.close()
        print("Got blacklist ids...")

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
            print("Finished altering tables...")

            #still cant get executemany to work :/
            # cursor.executemany("INSERT INTO blacklist (prawID) VALUES (%s);", (blacklist, ))
            for prawID in blacklist:
                cursor.execute("INSERT INTO blacklist (prawID) VALUES (%s);", (prawID, ))
            print("Finised adding blacklist ids...")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS log (
                log_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                pid INT UNSIGNED NULL,
                datetime_ DATETIME NOT NULL,
                category VARCHAR(10) NOT NULL DEFAULT 'INFO',
                data_ VARCHAR(500) NOT NULL,
                reddit_id VARCHAR(120) NULL
            );""")
            print("Added logging table...")

            with open("actions.log", "r") as f:
                for line in f:
                    self.append_log(line, commit = False)
            print("Done.")

        self.__connection.commit()

    def append_log(self, line, permalink = None, commit = True):
        """Function for adding a log file line to the database. Switched to
        use the database for logging at the same time as switched to MySQL.

        Args:
            line (str): a line of a log
            permalink (str, optional): a url about which the log line converns. Defaults to None.
            commit (bool, optional): autocommit. Defaults to True.
        """        
        def get_date(stri):
            # strip microseconds
            stri = stri.split(",")[0]
            try:
                return datetime.datetime.strptime(stri, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.datetime.strptime(stri, "%b %d %Y %H:%M:%S")

        addFlag = False    
        s = line.split("\t")
        if len(s) == 3:
            pid = int(s[0])
            date = get_date(s[1][1:-1])
            misc = s[2].rstrip()
            addFlag = True
 
        elif len(s) == 1:
            s = s[0].rstrip()
            result = re.search("\[(.*)\]", s)
            if result is not None:
                pid = None
                date = get_date(result.group(1))
                misc = s.replace("[%s]" % result.group(1), "")
                addFlag = True

        if addFlag:
            if re.search(r"{ERROR", misc) is not None:
                category = "ERROR"
            else:
                category = "INFO"

            with self.__connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO log (pid, datetime_, category, data_, reddit_id) VALUES (
                    %s, %s, %s, %s, %s
                );""", (pid, date, category, misc, permalink))

            if commit:
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
        "-h", subreddit.CONFIG["mysql"]["host"],
        "-d", subreddit.CONFIG["mysql"]["database"],
        "-u", subreddit.CONFIG["mysql"]["user"], 
        "-p", subreddit.CONFIG["mysql"]["passwd"]
    ])
    print("Converted table...")

    with Database() as db:
        db.migrate(sqlitefile)

if __name__ == "__main__":
    migrate("SmallYTChannelDatabase.db")
    # with Database() as db:
    #     #db.give_lambda("floofleberries", "https://www.reddit.com/r/SmallYTChannel/comments/ho5b5p/new_video_advice_would_help_but_even_just_a_watch/")
    #     print(db.id_in_blacklist("hyy6v0"))


