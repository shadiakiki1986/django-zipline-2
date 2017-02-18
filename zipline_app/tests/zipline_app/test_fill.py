from django.test import TestCase
from .test_zipline_app import create_fill, create_asset, a1
from django.urls import reverse

class FillViewsTests(TestCase):
    def test_list(self):
        url = reverse('zipline_app:fills-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        url = reverse('zipline_app:fills-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        f1 = create_fill(fill_text="test?",days=-30, asset=a1a, fill_qty=20, fill_price=2)
        url = reverse('zipline_app:fills-delete', args=(a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
