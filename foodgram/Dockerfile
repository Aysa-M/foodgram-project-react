FROM python:3.7-slim
RUN apt update && apt -y install libpq-dev build-essential
ENTRYPOINT /bin/bash
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
COPY ./ /app