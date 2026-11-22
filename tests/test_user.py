import unittest

from amcards.models import User


class UserTests(unittest.TestCase):
    def test_published_monthly_report_emails_are_preserved(self):
        payload = {
            'resource_uri': '/.api/v1/user/1/',
            'first_name': 'Test', 'last_name': 'User', 'credits': 0, 'email': 'test@example.com', 'phone': '',
            'date_joined': '2026-11-21T10:00:00', 'address_line_1': '', 'city': '', 'state': '', 'postal': '', 'country': 'US',
            'postage': {'domestic_cost': 0, 'international_cost': 0, 'domestic_countries': ['US']},
            'product_pricing_info': {'5x7greetingcard': 0},
        }
        for emails in (None, [], ['reports@example.com']):
            with self.subTest(emails=emails):
                self.assertEqual(User._from_json(payload | {'monthly_report_emails': emails}).monthly_report_emails, emails or [])


if __name__ == '__main__':
    unittest.main()
