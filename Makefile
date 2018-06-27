doc: clean_doc
	echo 'building docs...'
	cd docs && sphinx-apidoc --force -M -P -e -o source/ ../enqueue
	cd docs && make html

clean_doc:
	echo 'cleaning docs...'
	cd docs && rm -f source/enqueue
	cd docs && rm -f source/enqueue*.rst

dependencies:
	pip install -r enqueue/requirements.txt

# NOTE: The following optional environment variables can be set:
#	REDIS_URL (can be omitted for testing to use a local instance)
#	GRAPHITE_URL (defaults to localhost if missing)
#	QUEUE_PREFIX (set to dev- for testing)
#	FLASK_ENV (can be set to development)
test:
	PYTHONPATH="enqueue/" python -m unittest discover -s tests/

run:
	# This runs the enqueue process in Flask (for development/testing)
	#   and then connect at 127.0.0.1:5000/client/webhook
	# Needs a redis instance running
	# However, even without redis you can connect to http://127.0.0.1:5000/ and get the message there.
	QUEUE_PREFIX="dev-" python enqueue/enqueueMain.py

composeEnqueue:
	# This runs the enqueue and redis processes via nginx/gunicorn
	#   and then connect at 127.0.0.1:8080/client/webhook
	#   and "rq worker --config settings_enqueue" can connect to redis at 127.0.0.1:6379
	docker-compose -f docker-compose-enqueue.yaml build
	docker-compose -f docker-compose-enqueue.yaml up
