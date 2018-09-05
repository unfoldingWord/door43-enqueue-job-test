# Adapted by RJH June 2018 from fork of https://github.com/lscsoft/webhook-queue (Public Domain / unlicense.org)
#   The main change was to add some vetting of the json payload before allowing the job to be queued.

# TODO: We don't currently have any way to clear the failed queue

# Python imports
from os import getenv
import sys
from datetime import datetime
import logging

# Library (PyPi) imports
from flask import Flask, request
# NOTE: We use StrictRedis() because we don't need the backwards compatibility of Redis()
from redis import StrictRedis
from rq import Queue
from statsd import StatsClient # Graphite front-end

# Local imports
from check_posted_payload import check_posted_payload


logging.basicConfig(level=logging.DEBUG)
logging.info(f"enqueueMain.py running on Python version {sys.version}")

OUR_NAME = 'Door43_webhook' # Becomes the (perhaps prefixed) queue name (and graphite name) -- MUST match setup.py in door43-job-handler

#WEBHOOK_URL_SEGMENT = 'client/webhook/' # Note that there is compulsory trailing slash
WEBHOOK_URL_SEGMENT = '' # Leaving this blank will cause the service to run at '/'

JOB_TIMEOUT = '200s' # Then a running job (taken out of the queue) will be considered to have failed
    # NOTE: This is only the time until webhook.py returns after submitting the jobs
    #           -- the actual conversion jobs might still be running.


# Look at relevant environment variables
prefix = getenv('QUEUE_PREFIX', '') # Gets (optional) QUEUE_PREFIX environment variable -- set to 'dev-' for development
if prefix not in ('', 'dev-'):
    logging.critical(f"Unexpected prefix: {prefix!r} -- expected '' or 'dev-'")
our_adjusted_name = prefix + OUR_NAME
# NOTE: The prefixed version must also listen at a different port (specified in gunicorn run command)

# Get the redis URL from the environment, otherwise use a local test instance
redis_hostname = getenv('REDIS_HOSTNAME', 'redis')
logging.info(f"redis_hostname is {redis_hostname!r}")

# Get the Graphite URL from the environment, otherwise use a local test instance
graphite_url = getenv('GRAPHITE_HOSTNAME', 'localhost')
logging.info(f"graphite_url is {graphite_url!r}")
stats_client = StatsClient(host=graphite_url, port=8125, prefix=our_adjusted_name)



app = Flask(__name__)


## This code is for debugging only and can be removed
#@app.route('/showDB/', methods=['GET'])
#def show_DB():
    #"""
    #Display a helpful status list to a user connecting to our debug URL.
    #"""
    #r = StrictRedis(host=redis_hostname)
    #result_string = f'This {OUR_NAME} enqueuing service has:'

    ## Look at environment variables
    #result_string += '<h1>Environment Variables</h1>'
    #result_string += f"<p>QUEUE_PREFIX={getenv('QUEUE_PREFIX', '(not set)=>(no prefix)')}</p>"
    #result_string += f"<p>FLASK_ENV={getenv('FLASK_ENV', '(not set)=>(normal/production)')}</p>"
    #result_string += f"<p>REDIS_HOSTNAME={getenv('REDIS_HOSTNAME', '(not set)=>redis')}</p>"
    #result_string += f"<p>GRAPHITE_HOSTNAME={getenv('GRAPHITE_HOSTNAME', '(not set)=>localhost')}</p>"

    ## Look at all the potential queues
    #for this_our_adjusted_name in (OUR_NAME, 'dev-'+OUR_NAME, 'failed'):
        #q = Queue(this_our_adjusted_name, connection=r)
        #queue_output_string = ''
        ##queue_output_string += '<p>Job IDs ({0}): {1}</p>'.format(len(q.job_ids), q.job_ids)
        #queue_output_string += f'<p>Jobs ({len(q.jobs)}): {q.jobs}</p>'
        #result_string += f'<h1>{this_our_adjusted_name} queue:</h1>{queue_output_string}'

    #if redis_hostname == 'redis': # Can't do this for production redis (too many keys!!!)
        ## Look at the raw keys
        #keys_output_string = ''
        #for key in r.scan_iter():
            #keys_output_string += '<p>' + key.decode() + '</p>\n'
        #result_string += f'<h1>All keys ({len(r.keys())}):</h1>{keys_output_string}'

    #return result_string
## end of show_DB()


# This is the main workhorse part of this code
@app.route('/'+WEBHOOK_URL_SEGMENT, methods=['POST'])
def job_receiver():
    """
    Accepts POST requests and checks the (json) payload

    Queues the approved jobs at redis instance at global redis_hostname:6379.
    Queue name is our_adjusted_name (may be prefixed).
    """
    if request.method == 'POST':
        stats_client.incr('TotalPostsReceived')
        response_ok, data_dict = check_posted_payload(request) # data_dict is json payload if successful, else error info
        if response_ok:
            stats_client.incr('GoodPostsReceived')
            r = StrictRedis(host=redis_hostname)
            q = Queue(our_adjusted_name, connection=r)
            len_q = len(q)
            stats_client.gauge(prefix+'QueueLength', len_q)
            failed_q = Queue('failed', connection=r)
            len_failed_q = len(failed_q)
            stats_client.gauge('FailedQueueLength', len_failed_q)
            # NOTE: No ttl specified on the next line -- this seems to cause unrun jobs to be just silently dropped
            #           (For now at least, we prefer them to just stay in the queue if they're not getting processed.)
            #       The timeout value determines the max run time of the worker once the job is accessed
            q.enqueue('webhook.job', data_dict, timeout=JOB_TIMEOUT) # A function named webhook.job will be called by the worker
            # NOTE: The above line can return a result from the webhook.job function. (By default, the result remains available for 500s.)

            other_our_adjusted_name = OUR_NAME if prefix else 'dev-'+OUR_NAME
            other_q = Queue(other_our_adjusted_name, connection=StrictRedis(host=redis_hostname))
            info_message = f'{OUR_NAME} queued valid job to {our_adjusted_name} ({len(q)} jobs now, ' \
                        f'{len(other_q)} jobs in {other_our_adjusted_name} queue, ' \
                        f'{len_failed_q} failed jobs) at {datetime.utcnow()}'
            logging.info(info_message)
            return f'{OUR_NAME} queued valid job to {our_adjusted_name} at {datetime.utcnow()}'
        else:
            stats_client.incr('InvalidPostsReceived')
            error_message = f'{OUR_NAME} ignored invalid payload with {data_dict}'
            logging.error(error_message)
            return error_message, 400
    # NOTE: Code below is not required because rq automatically returns a "Method Not Allowed" error for a GET, etc.
    #else: # should never happen
        #return f'This is a {OUR_NAME} webhook receiver only.'
# end of job_receiver()


if __name__ == '__main__':
    app.run()
