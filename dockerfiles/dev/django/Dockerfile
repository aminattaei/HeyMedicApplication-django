FROM python:3.12-slim

LABEL maintainer="aminattaei2000@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt


COPY ./core .