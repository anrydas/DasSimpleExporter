FROM python:3.13-alpine

MAINTAINER -=:dAs:=-

RUN apk add gcc python3-dev musl-dev linux-headers

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY metrics/*.py metrics/

EXPOSE 15200

CMD [ "python", "./main.py" ]
