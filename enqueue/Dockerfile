FROM python:alpine

ADD . /code

WORKDIR /code

RUN pip install -r requirements.txt

# Make http port available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV QUEUE_PREFIX dev-
ENV DEBUG_MODE True

# NOTE: The following environment variables can be set:
#	QUEUE_PREFIX dev- (optional -- defaults to empty string)
#	DEBUG_MODE True (optional -- defaults to False)
#   REDIS_URL (optional -- defaults to 'redis')

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "enqueueMain:app"]
