FROM python:3

RUN apt update -qq && apt install -y vim ssh
RUN adduser --disabled-password test
COPY docker-entry.sh /root/docker-entry.sh
RUN echo test > /etc/hostname
ENTRYPOINT ["/bin/bash", "/root/docker-entry.sh"]
