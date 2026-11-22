import unittest
from unittest.mock import Mock, patch

from amcards import AMcardsClient
from amcards.exceptions import AMcardsException


def response(payload, status=200):
    return Mock(ok=status < 400, status_code=status, json=lambda: payload, text='test response')


class CardTests(unittest.TestCase):
    def test_malformed_card_list_is_not_an_empty_result(self):
        for payload in ({}, [], {'objects': []}, {'objects': None, 'meta': {'next': None}}, {'objects': [], 'meta': {}}):
            with self.subTest(payload=payload):
                with patch('amcards.amcards.requests.request', return_value=response(payload)):
                    with self.assertRaises(AMcardsException):
                        AMcardsClient('test').cards()


if __name__ == '__main__':
    unittest.main()
