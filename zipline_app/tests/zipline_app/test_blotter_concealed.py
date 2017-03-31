from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1, create_fill
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.zipline_app import ZlModel
from ...models.zipline_app.side import BUY, SELL
from .test_fill import create_fill_from_order
from ...utils import myTestLogin

class BlotterConcealedViewsTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    myTestLogin(self.client)

  def test_one_order(self):
    order = create_order(order_text="random order", days=-1,  asset=self.ass, order_side=BUY, amount_unsigned=10,   account=self.acc                          )
    f1 = create_fill_from_order(order=order, fill_text="test fill", fill_price=2)

    url = reverse('zipline_app:blotter-concealed')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "random order")
    self.assertNotContains(response, "test fill")

    self.assertContains(response, "Fill") # used to be "Filled by"

  def test_two_orders_different(self):
    o_l = create_order(order_text="buy order",  days=-1,  asset=self.ass, order_side=BUY,  amount_unsigned=10,   account=self.acc)
    o_s = create_order(order_text="sell order", days=-1,  asset=self.ass, order_side=SELL, amount_unsigned=20,   account=self.acc)
    f_l = create_fill_from_order(order=o_l, fill_text="test fill buy", fill_price=2)
    f_s = create_fill_from_order(order=o_s, fill_text="test fill sell", fill_price=2)

    url = reverse('zipline_app:blotter-concealed')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "buy order")
    self.assertContains(response, "sell order")
    self.assertNotContains(response, "test fill buy")
    self.assertNotContains(response, "test fill sell")

  def test_no_fill_create_button(self):
    url = reverse('zipline_app:blotter-concealed')
    response = self.client.get(url, follow=True)
    self.assertNotContains(response, 'data-target="#fills-new"')
