FROM ubuntu:18.04

RUN apt-get update -y && apt-get install -y python3-pip python3-dev git gcc dos2unix g++

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

# Make `boot.sh` Linux-friendly and executable
RUN dos2unix app/boot.sh && apt-get --purge remove -y dos2unix
RUN chmod +x app/boot.sh

# Container listens on this port during runtime
EXPOSE 5000

# Upon starting the container, create the DB, initialize, and run our app
CMD ["./app/boot.sh"]
