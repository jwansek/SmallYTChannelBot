FROM reg.reaweb.uk/smallytchannelbot
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install -y tzdata cron mariadb-client
COPY . /app
WORKDIR /app
RUN pip3 install -r cron/requirements.txt

RUN echo "@daily root python3 /app/cron/daily.py > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/crontab
RUN echo "@hourly root python3 /app/cron/hourly.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab
ENTRYPOINT ["bash"]
CMD ["/app/cron/entrypoint.sh"]
