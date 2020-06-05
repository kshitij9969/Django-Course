# Setup the base image
FROM python:3.7-alpine
MAINTAINER Kshitij Singh

# Setup environment variable
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
     gcc libc-dev linux-headers postgresql-dev

RUN pip install -r ./requirements.txt
RUN apk del .tmp-build-deps

# Switch working directory
RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Create another user to run application(for security purposes)
RUN adduser -D user
USER user

