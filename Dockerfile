FROM ubuntu:22.04
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y python3-pip  build-essential libjpeg-dev zlib1g-dev
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["subreddit.py"]
