from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.zipline_app import ZlModel

class IndexViewsTests(TestCase):
  def test_one_order(self):
    ZlModel.clear()

    acc = create_account("test acc")
    ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    order = create_order(order_text="random order",days=-1, asset=ass, order_side=Fill.LONG, amount_unsigned=10, account=acc)

    url = reverse('zipline_app:index')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "random order")
