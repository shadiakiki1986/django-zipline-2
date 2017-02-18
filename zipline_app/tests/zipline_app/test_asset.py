from django.test import TestCase
from .test_zipline_app import create_asset, a1
from django.urls import reverse

class AssetViewsTests(TestCase):
    def test_list(self):
        url = reverse('zipline_app:assets-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        url = reverse('zipline_app:assets-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        url = reverse('zipline_app:assets-delete', args=(a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
