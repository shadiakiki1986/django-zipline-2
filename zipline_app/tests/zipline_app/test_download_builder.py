from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1, create_fill
from ...models.zipline_app.zipline_app import ZlModel
from ...models.zipline_app.side import BUY
from ...views.zipline_app._download_builder import DownloadBuilder
from pandas import DataFrame
import tempfile
from os.path import exists
from django.http import FileResponse

class DownloadBuilderTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    self.builder = DownloadBuilder()

  def test_orders2df(self):
    o1 = create_order(order_text="random order 1", days=-1,  asset=self.ass, order_side=BUY, amount_unsigned=10,   account=self.acc)
    o2 = create_order(order_text="random order 2", days=-2,  asset=self.ass, order_side=BUY, amount_unsigned=20,   account=self.acc)
    o3 = create_order(order_text="random order 3", days=-3,  asset=self.ass, order_side=BUY, amount_unsigned=30,   account=self.acc)

    orders = [o1, o2, o3]
    df = self.builder.orders2df(orders)
    self.assertTrue(isinstance(df, DataFrame))

  def test_df2xlsx(self):
    df = self.builder.empty_df()
    full_name = self.builder.df2xlsx(df)
    self.assertNotEqual(full_name, None)
    self.assertEqual(exists(full_name),1)

  def test_fn2response(self):
    with tempfile.NamedTemporaryFile() as fn:
      response = self.builder.fn2response(fn.name)
      self.assertTrue(isinstance(response, FileResponse))

