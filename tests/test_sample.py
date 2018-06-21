from unittest import TestCase

class TestSample(TestCase):

    def test_success(self):
        input = 'name'
        output = sample_service(input)
        expected = {
            'hello': input
        }
        self.assertEqual(output, expected)

    def test_error(self):
        output = sample_service()
        expected = {
            'error': "what's your name?"
        }
        self.assertEqual(output, expected)
