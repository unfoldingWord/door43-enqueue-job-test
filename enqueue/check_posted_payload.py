# This code adapted by RJH June 2018 from tx-manager/client_webhook/ClientWebhookHandler
#   Updated Sept 2018 to add callback check

GOGS_URL = 'https://git.door43.org'


def check_posted_payload(request, logger):
    """
    Accepts webhook notification from DCS.
        Parameter is a rq request object

    Returns a 2-tuple:
        True or False if payload checks out
        The payload that was checked or error dict
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        logger.error("Received request but no payload found")
        return False, {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}

    # Bail if this is not from DCS
    if 'X-Gogs-Event' not in request.headers:
        logger.error(f"No 'X-Gogs-Event' in {request.headers}")
        return False, {'error': 'This does not appear to be from DCS.'}

    # Bail if this is not a push event
    if not request.headers['X-Gogs-Event'] == 'push':
        logger.error(f"X-Gogs-Event {request.headers['X-Gogs-Event']!r} is not a push")
        return False, {'error': 'This does not appear to be a push.'}

    # Get the json payload and check it
    payload_json = request.get_json()

    # Give a brief but helpful info message for the logs
    try:
        repo_name = payload_json['repository']['full_name']
    except (KeyError, AttributeError):
        repo_name = None
    try:
        pusher_name = payload_json['pusher']['full_name']
    except (KeyError, AttributeError):
        pusher_name = None
    try:
        commit_message = payload_json['commits'][0]['message'].strip() # Seems to always end with a newline
    except (KeyError, AttributeError, TypeError, IndexError):
        commit_message = None
    if repo_name or pusher_name or commit_message: # Ignore it if they are all None
        logger.info(f"{pusher_name} pushed '{repo_name}' with \"{commit_message}\"")

    # Bail if the URL to the repo is invalid
    try:
        if not payload_json['repository']['html_url'].startswith(GOGS_URL):
            logger.error(f"The repo at {payload_json['repository']['html_url']!r} does not belong to {GOGS_URL!r}")
            return False, {'error': f'The repo does not belong to {GOGS_URL}.'}
    except KeyError:
        logger.error("No repo URL specified")
        return False, {'error': 'No repo URL specified.'}

    # Bail if the commit branch is not the default branch
    try:
        commit_branch = payload_json['ref'].split('/')[2]
    except (IndexError, AttributeError):
        logger.error(f"Could not determine commit branch from {payload_json['ref']}")
        return False, {'error': 'Could not determine commit branch.'}
    except KeyError:
        logger.error("No commit branch specified")
        return False, {'error': "No commit branch specified."}
    try:
        if commit_branch != payload_json['repository']['default_branch']:
            logger.error(f"Commit branch: {commit_branch!r} is not the default branch")
            return False, {'error': f"Commit branch: {commit_branch!r} is not the default branch."}
    except KeyError:
        logger.error("No default branch specified")
        return False, {'error': "No default branch specified."}

    # Bail if this is not an actual commit
    # NOTE: What are these notifications??? 'before' and 'after' have the same commit id
    try:
        if not payload_json['commits']:
            logger.error("No commits found")
            try:
                logger.info(f"BEFORE is {payload_json['before']}")
                logger.info(f"AFTER  is {payload_json['after']}")
            except KeyError:
                pass
            return False, {'error': "No commits found."}
    except KeyError:
        logger.error("No commits specified")
        return False, {'error': "No commits specified."}

    logger.debug("Door43 payload seems ok")
    return True, payload_json
# end of check_posted_payload



def check_posted_callback_payload(request, logger):
    """
    Accepts callback notification from TX.
        Parameter is a rq request object

    Returns a 2-tuple:
        True or False if payload checks out
        The payload that was checked or error dict
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        logger.error("Received request but no payload found")
        return False, {'error': 'No payload found. You must submit a POST request'}

    # TODO: What headers do we need to check ???
    ## Bail if this is not from tX
    #if 'X-Gogs-Event' not in request.headers:
        #logger.error(f"Cannot find 'X-Gogs-Event' in {request.headers}")
        #return False, {'error': 'This does not appear to be from tX.'}

    ## Bail if this is not a push event
    #if not request.headers['X-Gogs-Event'] == 'push':
        #logger.error(f"X-Gogs-Event is not a push in {request.headers}")
        #return False, {'error': 'This does not appear to be a push.'}

    # Get the json payload and check it
    payload_json = request.get_json()
    logger.debug(f"callback payload is {payload_json}")

    # TODO: What info do we need to check and to match to a job
    ## Bail if the URL to the repo is invalid
    #try:
        #if not payload_json['repository']['html_url'].startswith(GOGS_URL):
            #logger.error(f"The repo at {payload_json['repository']['html_url']!r} does not belong to {GOGS_URL!r}")
            #return False, {'error': f'The repo does not belong to {GOGS_URL}.'}
    #except KeyError:
        #logger.error("No repo URL specified")
        #return False, {'error': 'No repo URL specified.'}

    ## Bail if the commit branch is not the default branch
    #try:
        #commit_branch = payload_json['ref'].split('/')[2]
    #except (IndexError, AttributeError):
        #logger.error(f"Could not determine commit branch from {payload_json['ref']}")
        #return False, {'error': 'Could not determine commit branch.'}
    #except KeyError:
        #logger.error("No commit branch specified")
        #return False, {'error': 'No commit branch specified.'}
    #try:
        #if commit_branch != payload_json['repository']['default_branch']:
            #logger.error(f'Commit branch: {commit_branch} is not the default branch')
            #return False, {'error': f'Commit branch: {commit_branch} is not the default branch.'}
    #except KeyError:
        #logger.error("No default branch specified")
        #return False, {'error': 'No default branch specified.'}

    logger.debug("Door43 callback payload seems ok")
    return True, payload_json
# end of check_posted_callback_payload
