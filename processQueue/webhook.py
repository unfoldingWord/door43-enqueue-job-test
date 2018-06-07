print( "webhook.py got loaded")


def job(json_payload):
    print("Got a job: {}".format(json_payload))
    print("  Have a big sleep.............zzzzzzzzzzzzzzzzzzzz")
    from time import sleep
    sleep(10) # seconds
    print("  Ok, awake again now!")
