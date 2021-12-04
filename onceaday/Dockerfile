FROM debian:latest
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
RUN apt-get update -y
RUN apt-get install -y tzdata python3-pip python-dev build-essential pkg-config cron libjpeg-dev zlib1g-dev
COPY . /app
WORKDIR /app
COPY onceaday/crontab /etc/cron.d/oad-crontab
RUN chmod 0644 /etc/cron.d/oad-crontab && crontab /etc/cron.d/oad-crontab
RUN pip3 install -r onceaday/requirements.txt
ENTRYPOINT ["cron", "-f"]
