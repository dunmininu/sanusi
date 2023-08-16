FROM python:3.8.3

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN mkdir /app

WORKDIR /app


RUN apt-get update && \
    apt-get install -y default-mysql-client default-libmysqlclient-dev

RUN pip install --upgrade pip  
RUN pip install python-decouple

COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 4001

RUN chmod +x ./docker-entrypoint.sh
CMD ["./docker-entrypoint.sh"] 

