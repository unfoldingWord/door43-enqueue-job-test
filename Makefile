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
	pip3 install --upgrade pip
	pip3 install --requirement enqueue/requirements.txt

# NOTE: The following optional environment variables can be set:
#	REDIS_HOSTNAME (can be omitted for testing if a local instance is running; port 6379 is assumed always)
#	GRAPHITE_HOSTNAME (defaults to localhost if missing)
#	QUEUE_PREFIX (set it to dev- for testing)
#	FLASK_ENV (can be set to "development" for testing)
test:
	PYTHONPATH="enqueue/" python3 -m unittest discover -s tests/

runFlask:
	# NOTE: For very preliminary testing only (unless REDIS_HOSTNAME is already set-up)
	# This runs the enqueue process in Flask (for development/testing)
	#   and then connect at 127.0.0.1:5000/
	# Needs a redis instance running
	# Usually won't get far because there is often no redis instance running
	QUEUE_PREFIX="dev-" FLASK_ENV="development" python3 enqueue/enqueueMain.py

composeEnqueueRedis:
	# NOTE: For testing only (using the 'dev-' prefix)
	# This runs the enqueue and redis processes via nginx/gunicorn
	#   and then connect at 127.0.0.1:8080/
	#   and "rq worker --config settings_enqueue" can connect to redis at 127.0.0.1:6379
	docker-compose --file docker-compose-enqueue-redis.yaml build
	docker-compose --file docker-compose-enqueue-redis.yaml up

imageDev:
	# NOTE: This build sets the prefix to 'dev-' and sets debug mode
	docker build --file enqueue/Dockerfile-developBranch --tag unfoldingword/door43_enqueue_job:develop enqueue

imageMaster:
	docker build --file enqueue/Dockerfile-masterBranch --tag unfoldingword/door43_enqueue_job:master enqueue

pushDevImage:
	# Expects to be already logged into Docker, i.e., docker login -u $(DOCKER_USERNAME)
	docker push unfoldingword/door43_enqueue_job:develop

pushMasterImage:
	# Expects to be already logged into Docker, i.e., docker login -u $(DOCKER_USERNAME)
	docker push unfoldingword/door43_enqueue_job:master

# NOTE: To test the container use:
# 	docker run --env QUEUE_PREFIX="dev-" --env FLASK_ENV="development" --env REDIS_HOSTNAME=<redis_hostname> --net="host" --name door43_enqueue_job --rm door43_enqueue_job


# NOTE: To run the container in production use with the desired values:
# 	docker run --env GRAPHITE_HOSTNAME=<graphite_hostname> --env REDIS_HOSTNAME=<redis_hostname> --net="host" --name door43_enqueue_job --rm door43_enqueue_job
