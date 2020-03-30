# /u/SmallYTChannelBot Source Code

The source code for /u/SmallYTChannelBot. Currently refactoring is in progress.

# TODOs

- [x] Automatically flair when [] is in submission title (done with AutoModerator)

- [ ] Implement `!recheck` command to recheck already removed submissions

- [ ] Ignore bot commands when they're formatted as code (` ` or indentation)

- [ ] Write a bot for the discord

- [ ] Implement a stream for edited comments

- [x] Removed giving lambda in free posts

- [x] Removed lambda for giving lambda

- [x] Switched to using a JSON file for configuration, included template

- [x] Refactored main code

- [x] Changed license from MIT to GPLv3

- [ ] Update flair when using the !takelambda command

- [x] Reimplented the `!takelambda` command

- [ ] Change `!takelambda` to `!refundlambda` when negative

# About the database's structure

`users` is where usernames and the scores are kept. `lambdas` is for every
time a lambda is given. Is linked to `users`. `stats` keeps unique users (just
the amount of users in `users`), the total lambda in circulation (everyone's
lambda scores summed), and the times help given, which is just the sum of every
unique entry in `lambdas`. `blacklist` is the reddit id of every comment / 
submission the bot has dealt with. If running on a new system you'll need to
update this. You can do this using archive_posts.py
