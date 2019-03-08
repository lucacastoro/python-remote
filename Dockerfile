FROM python:3

RUN apt update -qq && apt install -y openssh-server
RUN adduser --disabled-password --quiet test
COPY ssh-key.pub /home/test/.ssh/authorized_keys
RUN chown test:test /home/test/.ssh/authorized_keys
RUN chmod 755 /home/test/.ssh
RUN chmod 640 /home/test/.ssh/authorized_keys
RUN mkdir /run/sshd
ENTRYPOINT ["/usr/sbin/sshd", "-D", "-e"]
