master:
[![Build Status](https://travis-ci.org/unfoldingWord-dev/door43-enqueue-job.svg?branch=master)](https://travis-ci.org/unfoldingWord-dev/door43-enqueue-job?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/unfoldingWord-dev/door43-enqueue-job/badge.svg?branch=master)](https://coveralls.io/github/unfoldingWord-dev/door43-enqueue-job?branch=master)

develop:
[![Build Status](https://travis-ci.org/unfoldingWord-dev/door43-enqueue-job.svg?branch=develop)](https://travis-ci.org/unfoldingWord-dev/door43-enqueue-job?branch=develop)
[![Coverage Status](https://coveralls.io/repos/github/unfoldingWord-dev/door43-enqueue-job/badge.svg?branch=develop)](https://coveralls.io/github/unfoldingWord-dev/door43-enqueue-job?branch=develop)

# Door43-Enqueue-Job

This is part of tX translationConverter platform initiated by a commit to the
DCS (Door43 Content Service) at door43.org.

See [here](https://forum.ccbt.bible/t/door43-org-tx-development-architecture/65)
for a diagram of the overall flow of the tx (translationConverter) platform.

That is more up-to-date than the write-up of the previous platform
[here](https://github.com/unfoldingWord-dev/door43.org/wiki/tX-Development-Architecture)
(which was too dependant on expensive AWS lambda functions).


## Door43 modifications

Modified June 2018 by RJH mainly to add vetting of the json payload from DCS
before the job is added to the redis queue.

Also added Graphite stats collection (using statsd package).

See the `Makefile` for a list of environment variables which are looked for.

Requires:
    python 3.6

To setup:
    python3 -m venv venv
    source venv/bin/activate
    make dependencies

To run:
    make composeEnqueue

Basically this small program collects the json payload from the DCS (Door43
Content Service) which connects to the .../client/webhook/ URL. (Notice the
trailing slash.)

This enqueue process checks for various fields for simple validation of the
payload, and then puts the job onto a (rq) queue (stored in redis) to be
processed.

The Python code is run in Flask, which is then served by Green Unicorn (gunicorn)
but with nginx facing the outside world.

The next part in the Door43 workflow can be found in the door43-job-handler
repo. The job handler contains `webhook.py` (see below) which is given jobs
that have been removed from the queue and then processes them -- adding them
back to a `failed` queue if they give an exception or time-out. Note that the
queue name here in `enqueueMain.py` must match the one in the job-handler `rq_settings.py`.


# The following is the initial (forked) README
# Webhook job queue
The webhook job queue is designed to receive notifications from services and
store the JSON as a dictionary in a `python-rq` redis queue. It is designed
to work with a [Webhook Relay](https://github.com/lscsoft/webhook-relay) that
validates and relays webhooks from known services such as DockerHub, Docker
registries, GitHub, and GitLab. However, this is not required and the receiver
may listen directly to these services.

A worker must be spawned separately to read from the queue and perform tasks in
response to the event. The worker must have a function named `webhook.job`.

## Running

The job queue requires [docker-compose](https://docs.docker.com/compose/install/)
and, in its simplest form, can be invoked with `docker-compose up`. By default,
it will bind to `localhost:8080` but allow clients from all IP addresses. This
may appear odd, but on MacOS and Windows, traffic to the containers will appear
as though it's coming from the gateway of the network created by
Docker's linux virtualization.

In a production environment without the networking restrictions imposed by
MacOS/Windows, you might elect to provide different defaults through the
the shell environment. _e.g._
```
ALLOWED_IPS=A.B.C.D LISTEN_IP=0.0.0.0 docker-compose up
```
where `A.B.C.D` is an IP address (or CIDR range) from which your webhooks will
be sent.

A [worker must be spawned](#example-worker) to perform tasks by removing the
notification data from the redis queue. The redis keystore is configured to
listen only to clients on the `localhost`.

## Example worker
To run jobs using the webhooks as input:

1. Create a file named `webhook.py`
2. Define a function within named `job` that takes a `dict` as its lone argument
3. Install `python-rq`
    * _e.g._ `pip install rq`
4. Run `rq worker` from within that directory

See the [CVMFS-to-Docker converter](https://github.com/lscsoft/cvmfs-docker-worker)
for a real world example.
