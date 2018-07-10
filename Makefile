doc: clean_doc
	echo 'building docs...'
	cd docs && sphinx-apidoc --force -M -P -e -o source/ ../enqueue
	cd docs && make html

clean_doc:
	echo 'cleaning docs...'
	cd docs && rm -f source/enqueue
	cd docs && rm -f source/enqueue*.rst

dependencies:
	# It is recommended that a Python3 virtual environment be set-up before this point
	#  python3 -m venv venv
	#  source venv/bin/activate
	pip3 install --requirement enqueue/requirements.txt

# NOTE: The following optional environment variables can be set:
#	REDIS_URL (can be omitted for testing to use a local instance)
#	GRAPHITE_URL (defaults to localhost if missing)
#	QUEUE_PREFIX (set to dev- for testing)
#	FLASK_ENV (can be set to "development" for testing)
test:
	PYTHONPATH="enqueue/" python3 -m unittest discover -s tests/

run:
	# NOTE: For very preliminary testing only (unless REDIS_URL is already set-up)
	# This runs the enqueue process in Flask (for development/testing)
	#   and then connect at 127.0.0.1:5000/client/webhook
	# Needs a redis instance running
	# However, even without redis you can connect to http://127.0.0.1:5000/ and get the message there.
	QUEUE_PREFIX="dev-" python3 enqueue/enqueueMain.py

composeEnqueueRedis:
	# NOTE: For testing only
	# This runs the enqueue and redis processes via nginx/gunicorn
	#   and then connect at 127.0.0.1:8080/client/webhook
	#   and "rq worker --config settings_enqueue" can connect to redis at 127.0.0.1:6379
	docker-compose --file docker-compose-enqueue-redis.yaml build
	docker-compose --file docker-compose-enqueue-redis.yaml up

image:
	# Expects environment variable DOCKER_USERNAME to be set
	docker build --tag $(DOCKER_USERNAME)/door43_enqueuejob:latest enqueue

pushImage:
	# Expects environment variable DOCKER_USERNAME to be set
	# Expects to be already logged into Docker, e.g., docker login -u $(DOCKER_USERNAME)
	docker push $(DOCKER_USERNAME)/door43_enqueuejob:latest
