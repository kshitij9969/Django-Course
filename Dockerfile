# Setup the base image
FROM python:3.7-alpine
MAINTAINER Kshitij Singh

# Setup environment variable
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# Switch working directory
RUN mkdir /app
WORKDIR /app
COPY ./app /app

# Create another user to run application(for security purposes)
RUN adduser -D user
USER user

