from django.test import TestCase
from .other import create_asset, create_account, create_order, a1, a2, create_fill
from ...models.zipline_app.zipline_app import ZlModel
import pandas as pd

class ZlModelMethodTests(TestCase):
    def setUp(self):
      ZlModel.clear()
      self.acc1 = create_account(symbol="TEST01")
      self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
      self.a2a = create_asset(a2["symbol"],a2["exchange"],a2["name"])

    def test_update_no_orders_no_fills(self):
        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_some_orders_no_fills(self):
        o = create_order(order_text="test?",days=-0.5, asset=self.a1a, amount=10, account=self.acc1)
        self.assertEqual(len(ZlModel.zl_open), 1)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_no_orders_no_fills_again(self):
        """
        To make sure that eventhough ZlModel has static methods/fields,
        it gets reset automatically for each test,
        especially after the create_order above
        """
        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_fills_as_dict_df(self):
        ZlModel.fills={
          1: {
            1: { "dt": "2015-01-01", "close": 1, "volume": 1 },
            2: { "dt": "2015-01-01", "close": 2, "volume": 2 }
          },
          2: {}
        }
        expected = {
          1: pd.DataFrame({
            "dt": ["2015-01-01","2015-01-01"],
            "close": [1, 2],
            "volume": [1, 2]
          }).set_index("dt"),
          2: pd.DataFrame({
            "dt": [],
            "close": [],
            "volume": []
          }).set_index("dt")
        }
        actual = ZlModel.fills_as_dict_df()
        pd.util.testing.assert_frame_equal(actual[1], expected[1])
        pd.util.testing.assert_frame_equal(actual[2], expected[2])

    def test_create_delete(self):
        """
        Test that creating an order sends the signal and adds the order in the static variable
        """
        o = create_order(order_text="test?",days=-0.5, asset=self.a1a, amount=10, account=self.acc1)
        self.assertEqual(len(ZlModel.orders.items()), 1)
        o.delete()
        self.assertEqual(len(ZlModel.orders.items()), 0)

    def test_update_some_orders_some_fills(self):
        o1 = create_order(order_text="test?",days=-0.5, asset=self.a1a, amount=10, account=self.acc1)
        o2 = create_order(order_text="test?",days=-0.5, asset=self.a2a, amount=10, account=self.acc1)
        f1 = create_fill(fill_text="test?",days=-0.5, asset=self.a1a, fill_qty=2, fill_price=2)
        f2 = create_fill(fill_text="test?",days=-0.5, asset=self.a2a, fill_qty=2, fill_price=2)

        self.assertEqual(len(ZlModel.zl_open), 2)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_fills_then_orders(self):
        f1 = create_fill(fill_text="test?",days=-0.5, asset=self.a1a, fill_qty=20, fill_price=2)
        f2 = create_fill(fill_text="test?",days=-0.5, asset=self.a2a, fill_qty=20, fill_price=2)
        o1 = create_order(order_text="test?",days=-0.5, asset=self.a1a, amount=10, account=self.acc1)
        o2 = create_order(order_text="test?",days=-0.5, asset=self.a2a, amount=10, account=self.acc1)

        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 2)
