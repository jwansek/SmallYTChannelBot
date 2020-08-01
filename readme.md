# /u/SmallYTChannelBot Source Code

The source code for /u/SmallYTChannelBot. This is a WIP branch that uses MySQL
instead of SQLite3 and is designed to work in a docker container.

# Docker

- Clone the repo

- Edit the configuration file and rename

- If applicable, download the newest SQLite3 database and run the migration script

- Build the image:

`sudo docker build -t smallytchannelbot:latest .`

- Start the container:

`sudo docker run --name smallytchannelbot --net=host -d smallytchannelbot`

# TODOs

- [ ] Implement `!recheck` command to recheck already removed submissions

- [ ] Ignore bot commands when they're formatted as code (` ` or indentation)

- [ ] Write a bot for the discord

- [ ] Implement a stream for edited comments

# About the database's structure

`users` is where usernames and the scores are kept. `lambdas` is for every
time a lambda is given. Is linked to `users`. `stats` keeps unique users (just
the amount of users in `users`), the total lambda in circulation (everyone's
lambda scores summed), and the times help given, which is just the sum of every
unique entry in `lambdas`. `blacklist` is the reddit id of every comment / 
submission the bot has dealt with. If running on a new system you'll need to
update this. You can do this using archive_posts.py
