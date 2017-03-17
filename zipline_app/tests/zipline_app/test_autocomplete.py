from django.test import TestCase
from django.urls import reverse
from .test_zipline_app import create_asset, create_account

class AutoCompletAssetTests(TestCase):
  def test_get(self):
    asset1 = create_asset(symbol='asset1 symbol', exchange='asset1 exchange', name='asset1 name')
    asset2 = create_asset(symbol='asset2 symbol', exchange='asset2 exchange', name='asset2 name')

    url = reverse('zipline_app:autocomplete-asset')
    response = self.client.get(url, {'term':'asset1'}, follow=True)
    self.assertContains(response, "asset1 exchange")
    self.assertNotContains(response, "asset2 exchange")

    acc1 = create_account(symbol="TEST01")

class AutoCompletAccountTests(TestCase):
  def test_get(self):
    acc1 = create_account(symbol="ACC01")
    acc2 = create_account(symbol="ACC02")

    url = reverse('zipline_app:autocomplete-account')
    response = self.client.get(url, {'term':'ACC01'}, follow=True)
    self.assertContains(response, "ACC01")
    self.assertNotContains(response, "ACC02")
