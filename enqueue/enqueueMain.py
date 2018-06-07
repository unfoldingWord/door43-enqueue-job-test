# Adapted by RJH June 2018 from fork of https://github.com/lscsoft/webhook-queue (Public Domain / unlicense.org)
#   The main change was to add some vetting of the json payload before deciding to queue the job.

# Python imports
from os import getenv

# Library (PyPi) imports
from flask import Flask, request
from redis import StrictRedis
from rq import Queue
from datetime import datetime

#Local imports
from check_posted_payload import check_posted_payload

OUR_NAME = 'Door43'
# TODO: Check whether the DCS webhook calls include the trailing slash or not
WEBHOOK_URL_SEGMENT = 'client/webhook/' # Note that Flask requires the trailing slash when connecting, but nginx/gunicorn redirects with 301


app = Flask(__name__)

# This code should never be executed in the real world and presumably can be removed
@app.route('/', methods=['GET'])
def index():
    """
    Display a helpful message to a user connecting to our root URL.
    """
    return 'This {0} webhook service runs from {1}{2}'.format(OUR_NAME, request.url, WEBHOOK_URL_SEGMENT)


# This code is for debugging only and can be removed
@app.route('/showDB/', methods=['GET'])
def show():
    """
    Display a helpful list to a user connecting to our debug URL.
    """
    redis_url = getenv('REDIS_URL','redis')
    r = StrictRedis(host=redis_url)
    # Look at the raw keys
    keys_output_string = ''
    for key in r.scan_iter():
       print(key)
       keys_output_string += '<p>' + key.decode() + '</p>\n'
    q = Queue(OUR_NAME, connection=StrictRedis(host=redis_url))
    queue_output_string = ''
    queue_output_string += '<p>Job IDs ({0}): {1}</p>'.format(len(q.job_ids), q.job_ids)
    queue_output_string += '<p>Jobs ({0}): {1}</p>'.format(len(q.jobs), q.jobs)
    return 'This {0} webhook service has <h1>Keys ({1}):</h1>{2} <h1>Queue:</h1>{3}'.format(OUR_NAME, len(r.keys()), keys_output_string, queue_output_string)


@app.route('/'+WEBHOOK_URL_SEGMENT, methods=['POST'])
def receiver():
    """
    Accepts POST requests and checks the (json) payload

    Queues approved jobs at redis instance at global redis_url.
    Queue name is OUR_NAME.
    """
    if request.method == 'POST':
        response_ok, data_dict = check_posted_payload(request) # data_dict is json payload if successful, else error info
        if response_ok:
            # Get the redis URL from the environment, otherwise use a test instance
            redis_url = getenv('REDIS_URL','redis')
            q = Queue(OUR_NAME, connection=StrictRedis(host=redis_url))
            q.enqueue('webhook.job', data_dict) # A function named webhook.job will be called by the worker
            return '{0} queued valid job at {1}'.format(OUR_NAME,datetime.utcnow())
        else:
            # TODO: Check if we also need to log these errors (in data_dict) somewhere?
            #           -- they could signal either a caller fault or an attack
            return '{0} ignored invalid payload with {1}'.format(OUR_NAME, data_dict)
    else: # should never happen
        return 'This is a {0} webhook receiver only.'.format(OUR_NAME)

if __name__ == '__main__':
    debug_flag = getenv('DEBUG_MODE',False)
    app.run(debug=debug_flag)
