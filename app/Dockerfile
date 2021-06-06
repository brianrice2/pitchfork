FROM ubuntu:latest

RUN apt-get update -y && apt-get install -y python3-pip python3-dev git gcc dos2unix g++

COPY . /app
WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN dos2unix run_app.sh && apt-get --purge remove -y dos2unix
RUN chmod +x run_app.sh

EXPOSE 5000

ENTRYPOINT ["make", "app"]
