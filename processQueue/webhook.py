print( "webhook.py got loaded")


def job(json_payload):
    # NOTE: The job is already removed from the queue at this point
    print("Got a job: {}".format(json_payload))
    print("  Have a big sleep.............zzzzzzzzzzzzzzzzzzzz")
    from time import sleep
    sleep(15) # seconds
    print("  Ok, awake again now!")
