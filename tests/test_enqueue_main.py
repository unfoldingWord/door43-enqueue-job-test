from os import getenv
from unittest import TestCase
#from unittest.mock import Mock

from flask import Flask, request


from enqueue.enqueueMain import app, OUR_NAME, WEBHOOK_URL_SEGMENT, redis_url


app.config['TESTING'] = True
client = app.test_client()


class TestEnqueueMain(TestCase):


    def test_index(self):
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = f'This {OUR_NAME} webhook service runs from http://localhost/{WEBHOOK_URL_SEGMENT}'
        self.assertEqual(response.data, expected.encode())

    def test_invalid_url(self):
        response = client.get('/whatever/')
        self.assertEqual(response.status_code, 404)

    def test_showDB_get(self):
        # TODO: Can we run a local redis instance for these tests?
        if redis_url != 'redis': # Using a non-local instance so should work
            response = client.get('/showDB/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
            self.assertGreater(response.headers['Content-Length'], 200 )

    def test_invalid_webhook_get(self):
        response = client.get('/'+WEBHOOK_URL_SEGMENT)
        self.assertEqual(response.status_code, 405)

    def test_webhook_with_empty_payload(self):
        response = client.post('/'+WEBHOOK_URL_SEGMENT)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = "Door43_webhook ignored invalid payload with {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}"
        self.assertEqual(response.data, expected.encode())

    def test_webhook_with_good_payload(self):
        # TODO: Why does this fail? How should the json be presented?
        payload_json = {
            'ref':'refs/heads/master',
            'repository':{
                'html_url':'https://git.door43.org/whatever',
                'default_branch':'master',
                },
            }
        response = client.post('/'+WEBHOOK_URL_SEGMENT, data=payload_json)
        self.assertEqual(response.status_code, 200)
        print( response.data)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8' )
        expected = "Door43_webhook ignored invalid payload with {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}"
        self.assertEqual(response.data, expected.encode())

