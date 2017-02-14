import datetime

from django.utils import timezone
from django.test import TestCase

from .models import Order, ZlModel, Asset, Fill
from .matcher import reduce_concatenate
from django.urls import reverse

a1 = {
  "exchange":'exchange name',
  "symbol":'A1',
  "name":'A1 name',
}
a2 = {
  "exchange":'exchange name',
  "symbol":'A2',
  "name":'A2 name',
}

def create_asset(symbol, exchange, name):
    return Asset.objects.create(
      asset_exchange=exchange,
      asset_symbol=symbol,
      asset_name=name
    )

def create_order(order_text, days, asset, amount):
    """
    Creates a order with the given `order_text` and published the
    given number of `days` offset to now (negative for orders published
    in the past, positive for orders that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Order.objects.create(order_text=order_text, pub_date=time, asset=asset, amount=amount)

def create_fill(fill_text, days, asset, fill_qty, fill_price):
    time = timezone.now() + datetime.timedelta(days=days)
    return Fill.objects.create(fill_text=fill_text, pub_date=time, asset=asset, fill_qty=fill_qty, fill_price=fill_price)

class OrderMethodTests(TestCase):

    def test_was_published_recently_with_future_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is in the future.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        future_order = create_order(order_text="test?",days=30, asset=asset, amount=10)
        self.assertIs(future_order.was_published_recently(), False)

    def test_was_published_recently_with_old_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is older than 1 day.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        old_order = create_order(order_text="test?",days=-30, asset=asset, amount=10)
        self.assertIs(old_order.was_published_recently(), False)

    def test_was_published_recently_with_recent_order(self):
        """
        was_published_recently() should return True for orders whose
        pub_date is within the last day.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        recent_order = create_order(order_text="test?",days=-0.5, asset=asset, amount=10)
        self.assertIs(recent_order.was_published_recently(), True)

    def test_avg_price(self):
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        o = create_order(order_text="test?",days=-0.5, asset=asset, amount=10)
        ZlModel.zl_closed_keyed={o.id: {}}
        ZlModel.zl_txns=[
          {"order_id":o.id, "price":1, "amount":1},
          {"order_id":o.id, "price":1, "amount":1}
        ]
        self.assertEqual(o.avgPrice(), 1)

    def test_asset_to_dict(self):
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        o = create_order(order_text="test?",days=-0.5, asset=asset, amount=10)
        self.assertEqual(o.asset.to_dict(), a1)

class ZlModelMethodTests(TestCase):
    def setUp(self):
      ZlModel.clear()

    def test_update_no_orders_no_fills(self):
        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_some_orders_no_fills(self):
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        o = create_order(order_text="test?",days=-0.5, asset=asset, amount=10)
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
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        o = create_order(order_text="test?",days=-0.5, asset=asset, amount=10)
        self.assertEqual(len(ZlModel.orders.items()), 1)
        o.delete()
        self.assertEqual(len(ZlModel.orders.items()), 0)

    def test_update_some_orders_some_fills(self):
        a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        a2a = create_asset(a2["symbol"],a2["exchange"],a2["name"])
        o1 = create_order(order_text="test?",days=-0.5, asset=a1a, amount=10)
        o2 = create_order(order_text="test?",days=-0.5, asset=a2a, amount=10)
        f1 = create_fill(fill_text="test?",days=-0.5, asset=a1a, fill_qty=2, fill_price=2)
        f2 = create_fill(fill_text="test?",days=-0.5, asset=a2a, fill_qty=2, fill_price=2)

        self.assertEqual(len(ZlModel.zl_open), 2)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_fills_then_orders(self):
        a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        a2a = create_asset(a2["symbol"],a2["exchange"],a2["name"])
        f1 = create_fill(fill_text="test?",days=-0.5, asset=a1a, fill_qty=20, fill_price=2)
        f2 = create_fill(fill_text="test?",days=-0.5, asset=a2a, fill_qty=20, fill_price=2)
        o1 = create_order(order_text="test?",days=-0.5, asset=a1a, amount=10)
        o2 = create_order(order_text="test?",days=-0.5, asset=a2a, amount=10)

        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 2)

class OrderViewTests(TestCase):

    def test_index_view_with_no_orders(self):
        """
        If no orders exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No orders are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_index_view_with_a_past_order(self):
        """
        Orders with a pub_date in the past should be displayed on the
        index page.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        create_order(order_text="Past order.", days=-30, asset=asset, amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, 10 (Past order.)>']
        )

    def test_index_view_with_a_future_order(self):
        """
        Orders with a pub_date in the future should not be displayed on
        the index page.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        create_order(order_text="Future order.", days=30, asset=asset, amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No orders are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_index_view_with_future_order_and_past_order(self):
        """
        Even if both past and future orders exist, only past orders
        should be displayed.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        create_order(order_text="Past order.", days=-30, asset=asset, amount=10)
        create_order(order_text="Future order.", days=30, asset=asset, amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, 10 (Past order.)>']
        )

    def test_index_view_with_two_past_orders(self):
        """
        The orders index page may display multiple orders.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        create_order(order_text="Past order 1.", days=-30, asset=asset, amount=10)
        create_order(order_text="Past order 2.", days=-5, asset=asset, amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, 10 (Past order 2.)>', '<Order: A1, 10 (Past order 1.)>']
        )

class OrderIndexDetailTests(TestCase):
    def test_detail_view_with_a_future_order(self):
        """
        The detail view of a order with a pub_date in the future should
        return a 404 not found.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        future_order = create_order(order_text='Future order.', days=5, asset=asset, amount=10)
        url = reverse('polls:detail', args=(future_order.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_order(self):
        """
        The detail view of a order with a pub_date in the past should
        display the order's text.
        """
        asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
        past_order = create_order(order_text='Past Order.', days=-5, asset=asset, amount=10)
        url = reverse('polls:detail', args=(past_order.id,))
        response = self.client.get(url)
        self.assertContains(response, past_order.order_text)

#####################################
import pandas as pd
from .matcher import factory as mmm_factory, Matcher as mmm_Matcher
from zipline.finance.execution import (
    MarketOrder,
)

class MatcherMethodTests(TestCase):

    def test_chopSeconds(self):
        sec_yes = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        sec_non = pd.Timestamp('2017-02-13 05:13', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5],
                "dt": [sec_yes]
            }).set_index("dt")
        }
        orders = {
          1: {
            1: {"dt": sec_yes},
          }
        }
        actual_fills, actual_orders = mmm_Matcher.chopSeconds(fills, orders)

        self.assertEqual(actual_fills[1].index, [sec_non])
        asList = reduce_concatenate([list(o.values()) for o in list(actual_orders.values())])
        self.assertEqual([x["dt"] for x in asList], [sec_non])

    def test_factory_some_orders_and_some_fills(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        # seconds in below timestamp will be rounded
        MID_DATE_4 = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5, 4.5, 4, 2.4],
                "volume": [10, 5, 7, 1],
                "dt": [MID_DATE_1,MID_DATE_2,MID_DATE_3,MID_DATE_4]
            }).set_index("dt"),
            2: pd.DataFrame({
                "close": [3.5],
                "volume": [1],
                "dt": [MID_DATE_4]
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          },
          2: {
            4: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1: a1, 2: a2}

        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(6,len(all_txns))
        self.assertEqual(2,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(1,len(open_orders[a1a]))

#        print("========================")
#        print("Remaining open")
#        #blotter.cancel(o3)
#        print("Open orders: %s" % (len(blotter.open_orders[a1])))
#        print("Open order status: %s" % ([[o.amount,o.filled,o.open] for o in blotter.open_orders[a1]]))
#
#        print("========================")
#        print("All closed orders:")
#        for cl in all_closed:
#          print(cl)
#
#        print("========================")
#        print("All transactions:")
#        for txn in [txn.to_dict() for txn in all_txns]:
#          print(txn)

    def test_factory_no_orders_and_no_fills(self):
        matcher = mmm_Matcher()
        fills = {}
        orders = {}
        assets = {}
        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_some_orders_and_no_fills(self):
        matcher = mmm_Matcher()

        fills={}

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(1,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(3,len(open_orders[a1a]))

    def test_factory_no_orders_and_some_fills(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5, 4.5, 4],
                "volume": [10, 5, 7],
                "dt": [MID_DATE_1,MID_DATE_2,MID_DATE_3]
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        orders = {
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_unsorted_input(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        # seconds in below timestamp will be rounded
        MID_DATE_4 = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5, 4.5, 4, 2.4],
                "volume": [10, 5, 7, 1],
                "dt": [MID_DATE_1,MID_DATE_2,MID_DATE_4,MID_DATE_3]
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(5,len(all_txns))
        self.assertEqual(1,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(1,len(open_orders[a1a]))

    def test_write_assets(self):
        matcher = mmm_Matcher()
        assets = {1:a1, 2:a2}
        matcher.write_assets(assets)
        # the below would fail if not found .. shouldnt fail in this case
        found = matcher.env.asset_finder.lookup_symbol(symbol=a1["symbol"], as_of_date=None)
        self.assertEqual(a1["symbol"],found.symbol)

        found = matcher.env.asset_finder.lookup_symbol(symbol=a2["symbol"], as_of_date=None)
        self.assertEqual(a2["symbol"],found.symbol)

    def test_factory_fills_before_orders(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [1, 2],
                "volume": [5, 5],
                "dt": [MID_DATE_1,MID_DATE_2]
            }).set_index("dt"),
        }

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 5, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(1,len(all_closed))
        self.assertEqual(1,len(all_txns))
        self.assertEqual(0,len(open_orders))

        txn = all_txns[0].to_dict()
        self.assertEqual(txn["price"], 2)

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(unused, {a1a:5})
