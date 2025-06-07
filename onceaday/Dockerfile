FROM smallytchannelbot
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y tzdata cron
COPY . /app
WORKDIR /app
COPY onceaday/crontab /etc/cron.d/oad-crontab
RUN chmod 0644 /etc/cron.d/oad-crontab && crontab /etc/cron.d/oad-crontab
RUN pip3 install -r onceaday/requirements.txt
ENTRYPOINT ["cron", "-f"]
