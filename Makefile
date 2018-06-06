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

# NOTE: The following environment variables are expected to be set:
#	REDIS_URL (can be omitted for testing to use a local instance)
#	DEBUG_MODE (can be set to any non-blank string to run in debug mode for testing)

test:
	PYTHONPATH="enqueue/" python -m unittest discover -s tests/

run:
	# This runs the enqueue process in Flask (for development/testing)
	#   and then connect at 127.0.0.1:5000/client/webhook/
	python enqueue/enqueueMain.py

compose:
	# This runs the enqueue and redis processes via nginx/gunicorn
	#   and then connect at 127.0.0.1:8080/client/webhook/
	docker-compose up
