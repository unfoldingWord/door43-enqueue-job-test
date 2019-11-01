# This code adapted by RJH June 2018 from tx-manager/client_webhook/ClientWebhookHandler
#   Updated Sept 2018 to add callback check

GITEA_URL = 'https://git.door43.org'
UNWANTED_REPO_OWNER_USERNAMES = (  # code repos, not "content", so don't convert
                                'translationCoreApps',
                                'unfoldingWord-box3',
                                'unfoldingWord-dev',
                                )


def check_posted_payload(request, logger):
    """
    Accepts webhook notification from DCS.
        Parameter is a rq request object

    Returns a 2-tuple:
        True or False if payload checks out
        Either the payload that was checked (if returning True above),
            or the error dict (if returning False above)
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        logger.error("Received request but no payload found")
        return False, {'error': 'No payload found. You must submit a POST request via a DCS webhook notification.'}

    # Check for a test ping from Nagios
    if 'User-Agent' in request.headers and 'nagios-plugins' in request.headers['User-Agent'] \
    and 'X-Gogs-Event' in request.headers and request.headers['X-Gogs-Event'] == 'push':
        return False, {'error': "This appears to be a Nagios ping for service availability testing."}

    # Bail if this is not from DCS
    if 'X-Gitea-Event' not in request.headers:
        logger.error(f"No 'X-Gitea-Event' in {request.headers}")
        return False, {'error': 'This does not appear to be from DCS.'}
    event_type = request.headers['X-Gitea-Event']
    logger.info(f"Got a '{event_type}' event from DCS") # Shows in prodn logs

    # Get the json payload and check it
    payload_json = request.get_json()
    logger.debug(f"Webhook payload is {payload_json}") # Only shows in dev- logs
    # Typical keys are: secret, ref, before, after, compare_url,
    #                               commits, (head_commit), repository, pusher, sender
    # logger.debug("Webhook payload:")
    # for payload_key, payload_entry in payload_json.items():
    #     logger.debug(f"  {payload_key}: {payload_entry!r}")

    # Bail if this is not a push, release (tag), or delete (branch) event
    #   Others include 'create', 'issue_comment', 'issues', 'pull_request', 'fork'
    if event_type not in ('push', 'release', 'delete'):
        logger.error(f"X-Gitea-Event '{event_type}' is not a push, release (tag), or delete (branch)")
        logger.info(f"Ignoring '{event_type}' payload: {payload_json}") # Also shows in prodn logs
        return False, {'error': "This does not appear to be a push, release, or delete."}
    our_event_verb = {'push':'pushed', 'release':'released', 'delete':'deleted'}[event_type]

    # Give a brief but helpful info message for the logs
    try:
        repo_name = payload_json['repository']['full_name']
    except (KeyError, AttributeError):
        repo_name = None
    try:
        pusher_username = payload_json['pusher']['username']
    except (KeyError, AttributeError):
        pusher_username = None
    try:
        sender_username = payload_json['sender']['username']
    except (KeyError, AttributeError):
        sender_username = None

    # Don't process known code repos (cf. content)
    try:
        repo_owner_username = payload_json['repository']['owner']['username']
    except (KeyError, AttributeError):
        repo_owner_username = None
    for unwanted_repo_username in UNWANTED_REPO_OWNER_USERNAMES:
        if unwanted_repo_username == repo_owner_username:
            logger.info(f"Ignoring black-listed \"non-content\" '{unwanted_repo_username}' repo: {repo_name}") # Shows in prodn logs
            return False, {'error': 'This appears to be a "non-content" (program code?) repo.'}

    commit_messages = []
    try:
        # Assemble a string of commit messages
        for commit_dict in payload_json['commits']:
            this_commit_message = commit_dict['message'].strip() # Seems to always end with a newline
            commit_messages.append(f'"{this_commit_message}"')
        commit_message = ', '.join(commit_messages)
    except (KeyError, AttributeError, TypeError, IndexError):
        commit_message = None

    try:
        extra_info = f" with ({len(commit_messages)}) {commit_message}" if event_type=='push' \
                    else f" with '{payload_json['release']['name']}'"
    except (KeyError, AttributeError):
        extra_info = ""
    if pusher_username:
        logger.info(f"'{pusher_username}' {our_event_verb} '{repo_name}'{extra_info}")
    elif sender_username:
        logger.info(f"'{sender_username}' {our_event_verb} '{repo_name}'{extra_info}")
    elif repo_name:
        logger.info(f"UNKNOWN {our_event_verb} '{repo_name}'{extra_info}")
    else: # they were all None
        logger.info(f"No pusher/sender/repo name in payload: {payload_json}")


    # Bail if the URL to the repo is invalid
    try:
        if not payload_json['repository']['html_url'].startswith(GITEA_URL):
            logger.error(f"The repo at '{payload_json['repository']['html_url']}' does not belong to '{GITEA_URL}'")
            return False, {'error': f'The repo does not belong to {GITEA_URL}.'}
    except KeyError:
        logger.error("No repo URL specified")
        return False, {'error': 'No repo URL specified.'}


    if event_type == 'push':
        # # Bail if the commit branch is not the default branch
        # try:
        #     commit_branch = payload_json['ref'].split('/')[2]
        # except (IndexError, AttributeError):
        #     logger.error(f"Could not determine commit branch from '{payload_json['ref']}'")
        #     return False, {'error': 'Could not determine commit branch.'}
        # except KeyError:
        #     logger.error("No commit branch specified")
        #     return False, {'error': "No commit branch specified."}
        # try:
        #     default_branch = payload_json['repository']['default_branch']
        #     if commit_branch != default_branch:
        #         err_msg = f"Commit branch: '{commit_branch}' is not the default branch ({default_branch})"
        #         # Suppress this particular case
        #         if commit_branch=='TESTING' and not repo_name and not pusher_username:
        #             return False, {'error': "This appears to be a ping for testing."}
        #         else:
        #             logger.error(err_msg)
        #             return False, {'error': f"{err_msg}."}
        # except KeyError:
        #     logger.error("No default branch specified")
        #     return False, {'error': "No default branch specified."}

        # Bail if this is not an actual commit
        # NOTE: What are these notifications??? 'before' and 'after' have the same commit id
        #   Even test/fake deliveries usually have a commit specified (even if after==before)
        try:
            if not payload_json['commits']:
                logger.error("No commits found")
                try: # Just display BEFORE & AFTER for interest if they exist
                    logger.debug(f"BEFORE is {payload_json['before']}")
                    logger.debug(f"AFTER  is {payload_json['after']}")
                except KeyError:
                    pass
                return False, {'error': "No commits found."}
        except KeyError:
            logger.error("No commits specified")
            return False, {'error': "No commits specified."}


    # Add the event to the payload to be passed on
    payload_json['DCS_event'] = event_type

    logger.debug("Door43 payload seems ok")
    return True, payload_json
# end of check_posted_payload



def check_posted_callback_payload(request, logger):
    """
    Accepts callback notification from tX-Job-Handler.
        Parameter is a rq request object

    Returns a 2-tuple:
        True or False if payload checks out
        Either the payload that was checked (if returning True above),
            or the error dict (if returning False above)
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        logger.error("Received request but no payload found")
        return False, {'error': 'No payload found. You must submit a POST request.'}

    # Get the json payload and check it
    callback_payload_json = request.get_json()
    logger.debug(f"Callback payload is {callback_payload_json}")

    if 'job_id' not in callback_payload_json or not callback_payload_json['job_id']:
        logger.error("No callback job_id specified")
        return False, {'error': "No callback job_id specified."}

    # Display some helpful info in the logs
    if 'status' in callback_payload_json and 'identifier' in callback_payload_json and callback_payload_json['identifier']:
        logger.info(f"Received '{callback_payload_json['status']}' callback for {callback_payload_json['identifier']}")
    if 'linter_warnings' in callback_payload_json and 'linter_success' in callback_payload_json:
        logger.info(f"linter_success={callback_payload_json['linter_success']} with {len(callback_payload_json['linter_warnings'])} warnings")
    if 'success' in callback_payload_json and 'converter_warnings' in callback_payload_json and 'converter_errors' in callback_payload_json:
        logger.info(f"success={callback_payload_json['success']} with {len(callback_payload_json['converter_errors'])} converter errors and {len(callback_payload_json['converter_warnings'])} warnings")

    logger.debug("Door43 callback payload seems ok")
    return True, callback_payload_json
# end of check_posted_callback_payload
