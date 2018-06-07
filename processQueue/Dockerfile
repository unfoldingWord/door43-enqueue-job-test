FROM python:alpine
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
EXPOSE 6379
CMD ["sh","startWorker.sh"]
