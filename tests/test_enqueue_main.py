from os import getenv
from unittest import TestCase
#from unittest.mock import Mock
import json

from flask import Flask, request
from redis import exceptions as redis_exceptions

from enqueue.enqueueMain import app, OUR_NAME, WEBHOOK_URL_SEGMENT, redis_hostname


app.config['TESTING'] = True
client = app.test_client()


class TestEnqueueMain(TestCase):

    # NOTE: the GET at '/' has been removed from enqueue
    #def test_index(self):
        #response = client.get('/')
        #self.assertEqual(response.status_code, 200)
        #self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        #expected = f'This {OUR_NAME} webhook service runs from http://localhost/{WEBHOOK_URL_SEGMENT}'
        #self.assertEqual(response.data, expected.encode())

    def test_invalid_url(self):
        response = client.get('/whatever/')
        self.assertEqual(response.status_code, 404)

    # This code was deleted from enqueue
    #def test_showDB_get(self):
        ## TODO: Can we run a local redis instance for these tests?
        #if redis_hostname == 'redis': # Using a (missing) local instance so won't work work
            #with self.assertRaises(redis_exceptions.ConnectionError):
                #response = client.get('/showDB/')
        #else: # non-local  instance of redis so it should all work and we should get a page back
            #response = client.get('/showDB/')
            #self.assertEqual(response.status_code, 200)
            #self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
            #self.assertGreater(response.headers['Content-Length'], 200 )

    def test_invalid_webhook_get(self):
        response = client.get('/'+WEBHOOK_URL_SEGMENT)
        self.assertEqual(response.status_code, 405)

    def test_webhook_with_empty_payload(self):
        response = client.post('/'+WEBHOOK_URL_SEGMENT)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = "Door43_webhook ignored invalid payload with {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}"
        self.assertEqual(response.data, expected.encode())

    def test_webhook_with_bad_headers(self):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload_json = {'something': 'anything',}
        response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = "Door43_webhook ignored invalid payload with {'error': 'This does not appear to be from DCS.'}"
        self.assertEqual(response.data, expected.encode())

    def test_webhook_with_bad_payload(self):
        headers = {'Content-type': 'application/json', 'X-Gogs-Event': 'push'}
        payload_json = {'something': 'anything',}
        response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = "Door43_webhook ignored invalid payload with {'error': 'No repo URL specified.'}"
        self.assertEqual(response.data, expected.encode())

    def test_webhook_with_minimal_json_payload(self):
        headers = {'Content-type': 'application/json', 'X-Gogs-Event': 'push'}
        payload_json = {
            'ref': 'refs/heads/master',
            'repository': {
                'html_url': 'https://git.door43.org/whatever',
                'default_branch': 'master',
                },
            }
        if redis_hostname == 'redis': # Using a (missing) local instance so won't all work
            with self.assertRaises(redis_exceptions.ConnectionError):
                response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
        else: # non-local  instance of redis so it should all work and we should get a page back
            response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
            self.assertTrue('queued valid job to' in response.data.decode())

    def test_webhook_with_typical_full_json_payload(self):
        headers = {'Content-type': 'application/json', 'X-Gogs-Event': 'push'}
        with open( 'tests/Resources/webhook_post.json', 'rt' ) as json_file:
            payload_json = json.load(json_file)
        if redis_hostname == 'redis': # Using a (missing) local instance so won't all work
            with self.assertRaises(redis_exceptions.ConnectionError):
                response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
        else: # non-local  instance of redis so it should all work and we should get a page back
            response = client.post('/'+WEBHOOK_URL_SEGMENT, data=json.dumps(payload_json), headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
            self.assertTrue('queued valid job to' in response.data.decode())
            # After job has run, should update https://dev.door43.org/u/tx-manager-test-data/en-obs-rc-0.2/93829a566c/

