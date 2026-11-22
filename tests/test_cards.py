import unittest
from unittest.mock import Mock, patch

from amcards import AMcardsClient
from amcards.exceptions import AMcardsException
from amcards.models import Card


CARD = {
    'id': 1,
    'amount_charged': 1.25,
    'status': 0,
    'initiator': 'test',
    'send_date': '2026-11-22',
    'created': '2026-11-21T10:00:00',
    'last_modified': None,
    'fulfilled': None,
    'is_international': False,
    'template_name': 'Example',
    'thumbnail': '',
    'campaign_pk': 1,
    'third_party_contact_id': 'customer',
    'gifts': [],
    'extra_data': "{'custom_field': 'value'}",
    'tracking_id': 'test-tracking',
}


def response(payload, status=200):
    return Mock(ok=status < 400, status_code=status, json=lambda: payload, text='test response')


class CardTests(unittest.TestCase):
    def test_list_and_detail_expose_tracking_and_custom_metadata(self):
        for method in ('cards', 'card'):
            with self.subTest(method=method):
                payload = {'objects': [CARD], 'meta': {'next': None}} if method == 'cards' else CARD
                with patch('amcards.amcards.requests.request', return_value=response(payload)):
                    result = getattr(AMcardsClient('test'), method)(1)
                card = result[0] if method == 'cards' else result
                self.assertEqual(card.tracking_id, 'test-tracking')
                self.assertEqual(card.extra_data, {'custom_field': 'value'})
                self.assertEqual(card.shipping_address['third_party_contact_id'], 'customer')

    def test_absent_null_and_empty_tracking_are_optional(self):
        without_tracking = {key: value for key, value in CARD.items() if key != 'tracking_id'}
        for payload in (without_tracking, CARD | {'tracking_id': None}, CARD | {'tracking_id': ''}):
            with self.subTest(payload=payload.get('tracking_id', 'absent')):
                self.assertIsNone(Card._from_json(payload).tracking_id)

    def test_old_card_constructor_remains_compatible(self):
        card = Card(1, 100, 100, 0, 'test', '2026-11-22', None, None, None, False, 'Example', '', None, {}, {}, [], {})
        self.assertIsNone(card.tracking_id)

    def test_malformed_card_list_is_not_an_empty_result(self):
        for payload in ({}, [], {'objects': []}, {'objects': None, 'meta': {'next': None}}, {'objects': [], 'meta': {}}):
            with self.subTest(payload=payload):
                with patch('amcards.amcards.requests.request', return_value=response(payload)):
                    with self.assertRaises(AMcardsException):
                        AMcardsClient('test').cards()


if __name__ == '__main__':
    unittest.main()
