FROM python:3.7-slim

RUN apt update && apt -y install libpq-dev build-essential

RUN apt install nano

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -r requirements.txt --no-cache-dir

COPY ./ /app

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]