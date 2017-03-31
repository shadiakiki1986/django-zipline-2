from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1, create_fill
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.zipline_app import ZlModel
from ...models.zipline_app.side import BUY, SELL
from .test_fill import create_fill_from_order
from io import BytesIO
import pandas as pd
from ...utils import myTestLogin

class BlotterEngineViewsTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    myTestLogin(self.client)

  def test_get(self):
    o1 = create_order(order_text="random order 1", days=-1,  asset=self.ass, order_side=BUY, order_qty_unsigned=10,   account=self.acc)
    o2 = create_order(order_text="random order 2", days=-2,  asset=self.ass, order_side=BUY, order_qty_unsigned=20,   account=self.acc)
    o3 = create_order(order_text="random order 3", days=-3,  asset=self.ass, order_side=BUY, order_qty_unsigned=30,   account=self.acc)
    f3 = create_fill_from_order(order=o3, fill_price=3, fill_text="fill 3")

    url = reverse('zipline_app:blotter-engine')
    response = self.client.get(url, follow=True)

    self.assertContains(response, "random order 1")
    self.assertNotContains(response, "random order 3")
