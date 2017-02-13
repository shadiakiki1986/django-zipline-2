import datetime

from django.utils import timezone
from django.test import TestCase

from .models import Order, ZlModel
from django.urls import reverse

def create_order(order_text, days, order_sid, amount):
    """
    Creates a order with the given `order_text` and published the
    given number of `days` offset to now (negative for orders published
    in the past, positive for orders that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Order.objects.create(order_text=order_text, pub_date=time, order_sid=order_sid, amount=amount)


class OrderMethodTests(TestCase):

    def test_was_published_recently_with_future_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is in the future.
        """
        future_order = create_order(order_text="test?",days=30, order_sid="A1", amount=10)
        self.assertIs(future_order.was_published_recently(), False)

    def test_was_published_recently_with_old_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is older than 1 day.
        """
        old_order = create_order(order_text="test?",days=-30, order_sid="A1", amount=10)
        self.assertIs(old_order.was_published_recently(), False)

    def test_was_published_recently_with_recent_order(self):
        """
        was_published_recently() should return True for orders whose
        pub_date is within the last day.
        """
        recent_order = create_order(order_text="test?",days=-0.5, order_sid="A1", amount=10)
        self.assertIs(recent_order.was_published_recently(), True)

    def test_avg_price(self):
        o = create_order(order_text="test?",days=-0.5, order_sid="A1", amount=10)
        ZlModel.zl_closed_keyed={o.id: {}}
        ZlModel.zl_txns=[
          {"order_id":o.id, "price":1, "amount":1},
          {"order_id":o.id, "price":1, "amount":1}
        ]
        self.assertEqual(o.avgPrice(), 1)

class ZlModelMethodTests(TestCase):
    def test_update_no_orders_no_fills(self):
        ZlModel.update("test")
        self.assertEqual(len(ZlModel.zl_open), 0)
        self.assertEqual(len(ZlModel.zl_closed), 0)

    def test_update_no_orders_no_fills(self):
        o = create_order(order_text="test?",days=-0.5, order_sid="A1", amount=10)
        ZlModel.update("test")
        self.assertEqual(len(ZlModel.zl_open), 1)
        self.assertEqual(len(ZlModel.zl_closed), 0)

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
        create_order(order_text="Past order.", days=-30, order_sid="A1", amount=10)
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
        create_order(order_text="Future order.", days=30, order_sid="A1", amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No orders are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_index_view_with_future_order_and_past_order(self):
        """
        Even if both past and future orders exist, only past orders
        should be displayed.
        """
        create_order(order_text="Past order.", days=-30, order_sid="A1", amount=10)
        create_order(order_text="Future order.", days=30, order_sid="A1", amount=10)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, 10 (Past order.)>']
        )

    def test_index_view_with_two_past_orders(self):
        """
        The orders index page may display multiple orders.
        """
        create_order(order_text="Past order 1.", days=-30, order_sid="A1", amount=10)
        create_order(order_text="Past order 2.", days=-5, order_sid="A1", amount=10)
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
        future_order = create_order(order_text='Future order.', days=5, order_sid="A1", amount=10)
        url = reverse('polls:detail', args=(future_order.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_order(self):
        """
        The detail view of a order with a pub_date in the past should
        display the order's text.
        """
        past_order = create_order(order_text='Past Order.', days=-5, order_sid="A1", amount=10)
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
        orders = [
          {"dt": sec_yes, "sid": "bla"},
        ]
        actual_fills, actual_orders = mmm_Matcher.chopSeconds(fills, orders)

        self.assertEqual(actual_fills[1].index, [sec_non])
        self.assertEqual([x["dt"] for x in actual_orders], [sec_non])

    def test_factory_some_orders_and_some_fills(self):
        matcher = mmm_Matcher()
        a1=matcher.env.asset_finder.retrieve_asset(sid=1)

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
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = [
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
        ]

        all_closed, all_txns, open_orders = mmm_factory(matcher, fills, orders)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(5,len(all_txns))
        self.assertEqual(1,len(open_orders))
        self.assertEqual(1,len(open_orders[a1]))

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
        orders = []
        all_closed, all_txns, open_orders = mmm_factory(matcher, fills, orders)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_some_orders_and_no_fills(self):
        matcher = mmm_Matcher()
        a1=matcher.env.asset_finder.retrieve_asset(sid=1)

        fills={}

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = [
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
        ]

        all_closed, all_txns, open_orders = mmm_factory(matcher, fills, orders)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(1,len(open_orders))
        self.assertEqual(3,len(open_orders[a1]))

    def test_factory_no_orders_and_some_fills(self):
        matcher = mmm_Matcher()
        a1=matcher.env.asset_finder.retrieve_asset(sid=1)

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

        orders = [
        ]

        all_closed, all_txns, open_orders = mmm_factory(matcher, fills, orders)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_unsorted_input(self):
        matcher = mmm_Matcher()
        a1=matcher.env.asset_finder.retrieve_asset(sid=1)

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
        orders = [
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
        ]

        all_closed, all_txns, open_orders = mmm_factory(matcher, fills, orders)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(5,len(all_txns))
        self.assertEqual(1,len(open_orders))
        self.assertEqual(1,len(open_orders[a1]))

