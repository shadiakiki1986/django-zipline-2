from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.zipline_app import ZlModel
from ...models.zipline_app.side import BUY, SELL
from ...utils import myTestLogin

class BlotterSideBySideViewsTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    myTestLogin(self.client)

  def test_one_order(self):
    order = create_order(order_text="random order",days=-1, asset=self.ass, order_side=BUY, order_qty_unsigned=10, account=self.acc)
    url = reverse('zipline_app:blotter-sideBySide')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "random order")

  def test_two_orders(self):
    o_l = create_order(order_text="buy order", days=-1, asset=self.ass, order_side=BUY,  order_qty_unsigned=10, account=self.acc)
    o_s = create_order(order_text="sell order",days=-1, asset=self.ass, order_side=SELL, order_qty_unsigned=10, account=self.acc)

    url = reverse('zipline_app:blotter-sideBySide')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "buy order")
    self.assertContains(response, "sell order")
