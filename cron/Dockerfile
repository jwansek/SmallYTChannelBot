FROM reg.reaweb.uk/smallytchannelbot
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y tzdata cron mysql-client
COPY . /app
WORKDIR /app
RUN pip3 install -r cron/requirements.txt

RUN echo "@daily root python3 /app/cron/daily.py > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontab
RUN echo "@hourly root python3 /app/cron/hourly.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab
ENTRYPOINT ["bash"]
CMD ["entrypoint.sh"]
