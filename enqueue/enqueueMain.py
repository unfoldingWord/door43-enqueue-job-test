# Adapted by RJH June 2018 from fork of https://github.com/lscsoft/webhook-queue (Public Domain / unlicense.org)
#   The main change was to add some vetting of the json payload before allowing the job to be queued.

# Python imports
from os import getenv

# Library (PyPi) imports
from flask import Flask, request
from redis import StrictRedis
from rq import Queue
from datetime import datetime
from statsd import StatsClient # Graphite front-end

#Local imports
from check_posted_payload import check_posted_payload

OUR_NAME = 'DCS_webhook' # Becomes the (perhaps prefixed) queue name -- must match setup.py in door43-job-handler
WEBHOOK_URL_SEGMENT = 'client/webhook/' # Note that there is compulsory trailing slash

prefix = getenv('QUEUE_PREFIX','') # Gets (optional) QUEUE_PREFIX environment variable -- set to 'dev-' for development
queue_name = prefix + OUR_NAME

# Look at relevant environment variables
debug_flag = getenv('DEBUG_MODE',False) # Gets (optional) DEBUG_MODE environment variable
# Get the redis URL from the environment, otherwise use a test instance
redis_url = getenv('REDIS_URL','redis')



app = Flask(__name__)
stats = StatsClient('localhost', port=8125, prefix=OUR_NAME)


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
    r = StrictRedis(host=redis_url)
    result_string = 'This {0} webhook enqueuing service has:'.format(OUR_NAME)

    # Look at environment variables
    result_string += '<h1>Environment Variables</h1>'
    result_string += '<p>QUEUE_PREFIX={0}</p>'.format(getenv('QUEUE_PREFIX',''))
    result_string += '<p>DEBUG_MODE={0}</p>'.format(getenv('DEBUG_MODE',False))
    result_string += '<p>REDIS_URL={0}</p>'.format(getenv('REDIS_URL','redis'))

    # Look at the queues
    for this_queue_name in (OUR_NAME, 'dev-'+OUR_NAME, 'failed'):
        q = Queue(this_queue_name, connection=r)
        queue_output_string = ''
        #queue_output_string += '<p>Job IDs ({0}): {1}</p>'.format(len(q.job_ids), q.job_ids)
        queue_output_string += '<p>Jobs ({0}): {1}</p>'.format(len(q.jobs), q.jobs)
        result_string += '<h1>{0} queue:</h1>{1}'.format(this_queue_name, queue_output_string)

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
    Queue name is queue_name.
    """
    if request.method == 'POST':
        stats.incr('TotalPostsReceived')
        response_ok, data_dict = check_posted_payload(request) # data_dict is json payload if successful, else error info
        if response_ok:
            stats.incr('GoodPostsReceived')
            r = StrictRedis(host=redis_url)
            q = Queue(queue_name, connection=r)
            len_q = len(q)
            stats.gauge(prefix+'QueueLength', len_q)
            failed_q = Queue('failed', connection=r)
            len_failed_q = len(failed_q)
            stats.gauge('FailedQueueLength', len_failed_q)
            # NOTE: No ttl specified on the next line -- this seems to cause unrun jobs to be just silently dropped
            #       The timeout value determines the max run time of the worker once the job is accessed
            q.enqueue('webhook.job', data_dict, timeout='120s') # A function named webhook.job will be called by the worker
            # NOTE: The above line can return a result from the webhook.job function
            #   By default, the result remains available for 500s
            if prefix or debug_flag:
                other_queue_name = OUR_NAME if prefix else 'dev-'+OUR_NAME
                other_q = Queue(other_queue_name, connection=StrictRedis(host=redis_url))
                return '{0} queued valid job to {1} ({2} jobs now, {3} jobs in {4} queue, {5} failed jobs) at {6}' \
                    .format(OUR_NAME, queue_name, len(q), len(other_q), other_queue_name, len_failed_q, datetime.utcnow())
            else: #production mode
                return '{0} queued valid job to {1} ({2} jobs now, {3} failed jobs) at {4}' \
                    .format(OUR_NAME, queue_name, len(q), len_failed_q, datetime.utcnow())
        else:
            stats.incr('InvalidPostsReceived')
            # TODO: Check if we also need to log these errors (in data_dict) somewhere?
            #           -- they could signal either a caller fault or an attack
            return '{0} ignored invalid payload with {1}'.format(OUR_NAME, data_dict), 400
    else: # should never happen
        return 'This is a {0} webhook receiver only.'.format(OUR_NAME)
# end of job_receiver()


if __name__ == '__main__':
    if debug_flag: print("Flask will be operating in debug mode")
    app.run(debug=debug_flag)
