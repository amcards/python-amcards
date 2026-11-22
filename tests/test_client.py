import copy
import unittest
from unittest.mock import Mock, patch

import requests

from amcards import AMcardsClient
from amcards.exceptions import AMcardsException, AuthenticationError, OAuthTokenRefreshError


ADDRESS = {
    'first_name': 'Test',
    'last_name': 'Customer',
    'address_line_1': '1 Example Street',
    'city': 'Example',
    'state': 'CA',
    'postal_code': '90001',
    'country': 'US',
}


def response(payload, status=200):
    return Mock(ok=status < 400, status_code=status, json=lambda: payload, text='test response')


class ClientTimeoutTests(unittest.TestCase):
    def test_all_operations_inherit_and_override_timeouts_without_retrying(self):
        operations = {
            'user': {},
            'credit_transactions': {},
            'credit_transaction_count': {},
            'templates': {},
            'template': {'id': 1},
            'quicksends': {},
            'quicksend': {'id': 1},
            'campaigns': {},
            'campaign': {'id': 1},
            'cards': {},
            'card': {'id': 1},
            'card_count': {},
            'mailing': {'id': 1},
            'contacts': {},
            'contact': {'id': 1},
            'create_contact': ADDRESS,
            'delete_contact': {'id': 1},
            'send_card_cost': {'template_id': 1, 'shipping_address': ADDRESS},
            'send_card': {'template_id': 1, 'shipping_address': ADDRESS, 'initiator': 'test'},
            'send_campaign_cost': {'campaign_id': 1, 'shipping_address': ADDRESS},
            'send_campaign': {'campaign_id': 1, 'shipping_address': ADDRESS, 'initiator': 'test'},
            'send_campaign_multi': {'campaign_id': 1, 'contacts': [ADDRESS], 'initiator': 'test'},
            'send_cards': {'template_id': 1, 'shipping_addresses': [ADDRESS], 'initiator': 'test'},
        }
        for name, arguments in operations.items():
            for default, override in ((None, None), ((3, 6), None), ((3, 6), 9), (5, (1, 2))):
                with self.subTest(operation=name, default=default, override=override):
                    client = AMcardsClient('test-token', timeout=default)
                    with patch('amcards.amcards.requests.request', side_effect=requests.ReadTimeout) as request:
                        with self.assertRaises(requests.ReadTimeout):
                            getattr(client, name)(**copy.deepcopy(arguments), timeout=override)
                    request.assert_called_once()
                    self.assertEqual(request.call_args.kwargs['timeout'], default if override is None else override)
                    self.assertEqual(request.call_args.kwargs['headers'], {'Authorization': 'Bearer test-token'})

    def test_override_does_not_change_default_or_query_parameters(self):
        client = AMcardsClient('test-token', timeout=(3, 6))
        filters = {'third_party_contact_id': 'customer', 'order_by': ['-send_date', '-id']}
        with patch('amcards.amcards.requests.request', return_value=response({'objects': [], 'meta': {'next': None}})) as request:
            self.assertEqual(client.cards(1, 5, filters, timeout=2), [])
            self.assertEqual(request.call_args.kwargs['params'], {'limit': 1, 'offset': 5, **filters})
            self.assertEqual(request.call_args.kwargs['timeout'], 2)
            client.cards()
            self.assertEqual(request.call_args.kwargs['timeout'], (3, 6))
        self.assertNotIn('timeout', filters)

    def test_oauth_refresh_uses_effective_timeout_and_new_token(self):
        for override in (None, (1, 2)):
            with self.subTest(override=override):
                callback = Mock()
                config = {'refresh_token': 'old-refresh', 'expiration': 0, 'client_id': 'test-id', 'client_secret': 'test-secret'}
                client = AMcardsClient('old-token', config, callback, timeout=(3, 6))
                responses = [
                    response({'access_token': 'new-token', 'refresh_token': 'new-refresh', 'expires_in': 60}),
                    response({'objects': [], 'meta': {'next': None}}),
                ]
                with patch('amcards.amcards.requests.request', side_effect=responses) as request, patch('amcards.amcards.helpers.current_timestamp', return_value=1000):
                    client.cards(timeout=override)
                refresh, api = request.call_args_list
                expected = override or (3, 6)
                self.assertEqual(refresh.args[0], 'POST')
                self.assertTrue(refresh.args[1].endswith('/oauth2/token/'))
                self.assertNotIn('headers', refresh.kwargs)
                self.assertEqual(refresh.kwargs['timeout'], expected)
                self.assertEqual(api.kwargs['timeout'], expected)
                self.assertEqual(api.kwargs['headers'], {'Authorization': 'Bearer new-token'})
                callback.assert_called_once_with(access_token='new-token', refresh_token='new-refresh', expiration=61000)

    def test_failed_or_timed_out_refresh_does_not_make_api_call(self):
        for failure in (response({}, 400), requests.ConnectTimeout()):
            with self.subTest(failure=type(failure).__name__):
                client = AMcardsClient('old-token', {'refresh_token': 'test', 'expiration': 0, 'client_id': 'test', 'client_secret': 'test'}, timeout=3)
                with patch('amcards.amcards.requests.request', side_effect=[failure]) as request:
                    with self.assertRaises((OAuthTokenRefreshError, requests.ConnectTimeout)):
                        client.cards()
                request.assert_called_once()

    def test_default_without_timeout_remains_compatible(self):
        with patch('amcards.amcards.requests.request', return_value=response({'meta': {'total_count': 5}})) as request:
            self.assertEqual(AMcardsClient('test-token', None, None).card_count(), 5)
        self.assertIsNone(request.call_args.kwargs['timeout'])

    def test_contact_creation_override_covers_user_lookup_and_write(self):
        client = AMcardsClient('test-token', timeout=30)
        with patch('amcards.amcards.requests.request', side_effect=[response({'objects': [{}]}), requests.ReadTimeout()]) as request:
            with patch('amcards.models.User._from_json', return_value=Mock(id=123)):
                with self.assertRaises(requests.ReadTimeout):
                    client.create_contact(**ADDRESS, timeout=(2, 4))
        lookup, create = request.call_args_list
        self.assertEqual(lookup.args[0], 'GET')
        self.assertEqual(create.args[0], 'POST')
        self.assertEqual(lookup.kwargs['timeout'], (2, 4))
        self.assertEqual(create.kwargs['timeout'], (2, 4))
        self.assertEqual(create.kwargs['json']['first_name'], 'Test')

    def test_sdk_errors_remain_sdk_errors(self):
        for status, expected in ((401, AuthenticationError), (503, AMcardsException)):
            with self.subTest(status=status):
                with patch('amcards.amcards.requests.request', return_value=response({}, status)):
                    with self.assertRaises(expected):
                        AMcardsClient('test').cards()


if __name__ == '__main__':
    unittest.main()
