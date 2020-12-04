FROM python:latest

ADD . /app
WORKDIR /app

RUN pip install flask
RUN pip install flask_mysqldb
RUN pip install python-dotenv
RUN pip install flask_cors

