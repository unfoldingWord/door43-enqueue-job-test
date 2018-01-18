import flask
import redis
import rq

app = flask.Flask(__name__)

@app.route('/', methods=['GET','POST'])
def receiver():
    if flask.request.method == 'POST':
        payload = flask.request.get_json()
        q = rq.Queue(connection=StrictRedis(host='redis'))
        q.enqueue('webhook.job', payload)
        return 'Got it!'
    else:
        return 'This is a webhook receiver only.'

if __name__ == '__main__':
    app.run()
