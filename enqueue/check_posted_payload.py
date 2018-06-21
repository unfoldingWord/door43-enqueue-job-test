# This code adapted by RJH June 2018 from tx-manager/client_webhook/ClientWebhookHandler

GOGS_URL = 'https://git.door43.org'


def check_posted_payload(request):
    """
    Returns True or False
    """

    """
    Accepts webhook notification from DCS.

    :param dict commit_data:
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        return False, {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}

    # Bail if this is not from DCS
    if 'X-Gogs-Event' not in request.headers:
        return False, {'error': 'This does not appear to be from DCS.'}

    # Bail if this is not a push event
    if not request.headers['X-Gogs-Event'] == 'push':
        return False, {'error': 'This does not appear to be a push.'}

    # Get the json payload and check that
    payload_json = request.get_json()
    #print( repr(payload_json))

    # Bail if the URL to the repo is invalid
    if not payload_json['repository']['html_url'].startswith(GOGS_URL):
        return False, {'error': f'The repo does not belong to {GOGS_URL}.'}

    # Bail if the commit branch is not the default branch
    try:
        commit_branch = payload_json['ref'].split('/')[2]
    except IndexError:
        return False, {'error': 'Could not determine commit branch, exiting.'}
    except KeyError:
        return False, {'error': 'This does not appear to be a push, exiting.'}
    if commit_branch != payload_json['repository']['default_branch']:
        return False, {'error': f'Commit branch: {commit_branch} is not the default branch.'}

    # TODO: Check why this code was commented out in tx-manager -- if it's not necessary let's delete it
    # Check that the user token is valid
    #if not App.gogs_user_token:
        #raise Exception('DCS user token not given in Payload.')
    #user = App.gogs_handler().get_user(App.gogs_user_token)
    #if not user:
        #raise Exception('Invalid DCS user token given in Payload')

    return True, payload_json
