# Adapted by RJH June 2018 from fork of https://github.com/lscsoft/webhook-queue (Public Domain / unlicense.org)
#   The main change was to add some vetting of the json payload before allowing the job to be queued.

# TODO: Needs to be tested with the actual AWS redis instance
# TODO: Still haven't figured out how to view stats

# Python imports
from os import getenv

# Library (PyPi) imports
from flask import Flask, request
from redis import StrictRedis
from rq import Queue
from datetime import datetime
from statsd import StatsClient # Graphite front-end

# Local imports
from check_posted_payload import check_posted_payload

OUR_NAME = 'Door43_webhook' # Becomes the (perhaps prefixed) queue name (and graphite name) -- MUST match setup.py in door43-job-handler
WEBHOOK_URL_SEGMENT = 'client/webhook/' # Note that there is compulsory trailing slash


# Look at relevant environment variables
prefix = getenv('QUEUE_PREFIX', '') # Gets (optional) QUEUE_PREFIX environment variable -- set to 'dev-' for development
queue_name = prefix + OUR_NAME

# Get the redis URL from the environment, otherwise use a local test instance
redis_url = getenv('REDIS_URL', 'redis')

# Get the Graphite URL from the environment, otherwise use a local test instance
graphite_url = getenv('GRAPHITE_URL','localhost')
stats_client = StatsClient(host=graphite_url, port=8125, prefix=OUR_NAME)



app = Flask(__name__)


# This code should never be executed in the real world and presumably can be removed
@app.route('/', methods=['GET'])
def index():
    """
    Display a helpful message to a user connecting to our root URL.
    """
    return f'This {OUR_NAME} webhook service runs from {request.url}{WEBHOOK_URL_SEGMENT}'
# end of index()


# This code is for debugging only and can be removed
@app.route('/showDB/', methods=['GET'])
def showDB():
    """
    Display a helpful status list to a user connecting to our debug URL.
    """
    r = StrictRedis(host=redis_url)
    result_string = f'This {OUR_NAME} webhook enqueuing service has:'

    # Look at environment variables
    result_string += '<h1>Environment Variables</h1>'
    result_string += f"<p>QUEUE_PREFIX={getenv('QUEUE_PREFIX', '(not set)=>(no prefix)')}</p>"
    result_string += f"<p>FLASK_ENV={getenv('FLASK_ENV', '(not set)=>(normal/production)')}</p>"
    result_string += f"<p>REDIS_URL={getenv('REDIS_URL', '(not set)=>redis')}</p>"
    result_string += f"<p>GRAPHITE_URL={getenv('GRAPHITE_URL', '(not set)=>localhost')}</p>"

    # Look at all the potential queues
    for this_queue_name in (OUR_NAME, 'dev-'+OUR_NAME, 'failed'):
        q = Queue(this_queue_name, connection=r)
        queue_output_string = ''
        #queue_output_string += '<p>Job IDs ({0}): {1}</p>'.format(len(q.job_ids), q.job_ids)
        queue_output_string += f'<p>Jobs ({len(q.jobs)}): {q.jobs}</p>'
        result_string += f'<h1>{this_queue_name} queue:</h1>{queue_output_string}'

    # Look at the raw keys
    keys_output_string = ''
    for key in r.scan_iter():
       keys_output_string += '<p>' + key.decode() + '</p>\n'
    result_string += f'<h1>All keys ({len(r.keys())}):</h1>{keys_output_string}'

    return result_string
# end of showDB()


@app.route('/'+WEBHOOK_URL_SEGMENT, methods=['POST'])
def job_receiver():
    """
    Accepts POST requests and checks the (json) payload

    Queues approved jobs at redis instance at global redis_url.
    Queue name is queue_name.
    """
    if request.method == 'POST':
        stats_client.incr('TotalPostsReceived')
        response_ok, data_dict = check_posted_payload(request) # data_dict is json payload if successful, else error info
        if response_ok:
            stats_client.incr('GoodPostsReceived')
            r = StrictRedis(host=redis_url)
            q = Queue(queue_name, connection=r)
            len_q = len(q)
            stats_client.gauge(prefix+'QueueLength', len_q)
            failed_q = Queue('failed', connection=r)
            len_failed_q = len(failed_q)
            stats_client.gauge('FailedQueueLength', len_failed_q)
            # NOTE: No ttl specified on the next line -- this seems to cause unrun jobs to be just silently dropped
            #       The timeout value determines the max run time of the worker once the job is accessed
            q.enqueue('webhook.job', data_dict, timeout='120s') # A function named webhook.job will be called by the worker
            # NOTE: The above line can return a result from the webhook.job function
            #   By default, the result remains available for 500s
            if prefix:
                other_queue_name = OUR_NAME if prefix else 'dev-'+OUR_NAME
                other_q = Queue(other_queue_name, connection=StrictRedis(host=redis_url))
                return f'{OUR_NAME} queued valid job to {queue_name} ({len(q)} jobs now, {len(other_q)} jobs in {other_queue_name} queue, {len_failed_q} failed jobs) at {datetime.utcnow()}'
            else: #production mode
                return f'{OUR_NAME} queued valid job to {queue_name} ({len(q)} jobs now, {len_failed_q} failed jobs) at {datetime.utcnow()}'
        else:
            stats_client.incr('InvalidPostsReceived')
            # TODO: Check if we also need to log these errors (in data_dict) somewhere?
            #           -- they could signal either a caller fault or an attack
            return f'{OUR_NAME} ignored invalid payload with {data_dict}', 400
    else: # should never happen
        return f'This is a {OUR_NAME} webhook receiver only.'
# end of job_receiver()


if __name__ == '__main__':
    app.run()
