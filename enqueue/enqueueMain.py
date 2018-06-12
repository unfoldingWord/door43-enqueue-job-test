# Adapted by RJH June 2018 from fork of https://github.com/lscsoft/webhook-queue (Public Domain / unlicense.org)
#   The main change was to add some vetting of the json payload before allowing the job to be queued.

# TODO: Add Graphite Gauge metrics for queued jobs -- see metrics repository for examples of use

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
WEBHOOK_URL_SEGMENT = 'client/webhook/' # Note that there is compulsory trailing slash


app = Flask(__name__)


# This code should never be executed in the real world and presumably can be removed
@app.route('/', methods=['GET'])
def index():
    """
    Display a helpful message to a user connecting to our root URL.
    """
    return 'This {0} webhook service runs from {1}{2}'.format(OUR_NAME, request.url, WEBHOOK_URL_SEGMENT)
# end of index()


# This code is for debugging only and can be removed
@app.route('/showDB/', methods=['GET'])
def show():
    """
    Display a helpful status list to a user connecting to our debug URL.
    """
    redis_url = getenv('REDIS_URL','redis')
    r = StrictRedis(host=redis_url)
    result_string = 'This webhook service has'

    # Look at the queues
    for queue_name in (OUR_NAME, 'failed'):
        q = Queue(queue_name, connection=StrictRedis(host=redis_url))
        queue_output_string = ''
        #queue_output_string += '<p>Job IDs ({0}): {1}</p>'.format(len(q.job_ids), q.job_ids)
        queue_output_string += '<p>Jobs ({0}): {1}</p>'.format(len(q.jobs), q.jobs)
        result_string += '<h1>{0} queue:</h1>{1}'.format(queue_name, queue_output_string)

    # Look at the raw keys
    keys_output_string = ''
    for key in r.scan_iter():
       keys_output_string += '<p>' + key.decode() + '</p>\n'
    result_string += '<h1>All keys ({0}):</h1>{1}'.format(len(r.keys()), keys_output_string )

    return result_string
# end of show()


@app.route('/'+WEBHOOK_URL_SEGMENT, methods=['POST'])
def job_receiver():
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
            failed_q = Queue('failed', connection=StrictRedis(host=redis_url))
            # NOTE: No ttl specified on the next line -- this seems to cause unrun jobs to be just silently dropped
            #       The timeout value determines the max run time of the worker once the job is accessed
            q.enqueue('webhook.job', data_dict, timeout='120s') # A function named webhook.job will be called by the worker
            # NOTE: The above line can return a result from the webhook.job function
            #   By default, the result remains available for 500s
            return '{0} queued valid job ({1} jobs now, {2} failed jobs) at {3}'.format(OUR_NAME, len(q), len(failed_q), datetime.utcnow())
        else:
            # TODO: Check if we also need to log these errors (in data_dict) somewhere?
            #           -- they could signal either a caller fault or an attack
            return '{0} ignored invalid payload with {1}'.format(OUR_NAME, data_dict), 400
    else: # should never happen
        return 'This is a {0} webhook receiver only.'.format(OUR_NAME)
# end of job_receiver()


if __name__ == '__main__':
    debug_flag = getenv('DEBUG_MODE',False) # Gets (optional) DEBUG_MODE environment variable
    app.run(debug=debug_flag)
