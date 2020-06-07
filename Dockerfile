# Setup the base image
FROM python:3.7-alpine
MAINTAINER Kshitij Singh

# Setup environment variable
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
     gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev

RUN pip install -r ./requirements.txt
RUN apk del .tmp-build-deps

# Switch working directory
RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Add a directory for storing images
# media - uploaded by the user
# static - static files like JS, CSS
# which won't change(typically) during
# application execution
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

# Create another user to run application(for security purposes)
RUN adduser -D user
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web
USER user

