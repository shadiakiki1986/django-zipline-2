from django.test import TestCase
from .test_zipline_app import create_account, create_fill, create_order, create_asset, a1
from django.urls import reverse
from ...utils import myTestLogin
from ...models.zipline_app.side import BUY

class AssetViewsTests(TestCase):
    def setUp(self):
      myTestLogin(self.client)

    def test_list(self):
        url = reverse('zipline_app:accounts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        url = reverse('zipline_app:accounts-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_ok(self):
        a1a = create_account("test acc")
        url = reverse('zipline_app:accounts-delete', args=(a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        a1a = create_account("test acc")
        url = reverse('zipline_app:accounts-update', args=(a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class AccountModelTests(TestCase):
  def test_delete_fail(self):
    acc1 = create_account("test acc")
    a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    o1 = create_order(order_text="test?",days=-1, asset=a1a, order_side=BUY, amount_unsigned=10, account=acc1)

    with self.assertRaises(ValueError):
      acc1.delete()
