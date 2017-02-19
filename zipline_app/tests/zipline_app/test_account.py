from django.test import TestCase
from .test_zipline_app import create_account
from django.urls import reverse

class AssetViewsTests(TestCase):
    def test_list(self):
        url = reverse('zipline_app:accounts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        url = reverse('zipline_app:accounts-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        a1a = create_account("test acc")
        url = reverse('zipline_app:accounts-delete', args=(a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
