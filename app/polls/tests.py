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
from .matcher import Matcher
from zipline.finance.execution import (
    MarketOrder,
)
from testfixtures import TempDirectory

class MatcherMethodTests(TestCase):

    def test_runs(self):
      with TempDirectory() as tempdir:
        matcher = Matcher()
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

        all_minutes = matcher.fills2minutes(fills)
        equity_minute_reader = matcher.fills2reader(tempdir, all_minutes, fills)

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = [
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
          {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
        ]

        blotter = matcher.orders2blotter(orders)

        bd = matcher.blotter2bardata(equity_minute_reader, blotter)
        all_closed, all_txns = matcher.match_orders_fills(blotter, bd, all_minutes, fills)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(5,len(all_txns))
        self.assertEqual(1,len(blotter.open_orders))
        self.assertEqual(1,len(blotter.open_orders[a1]))

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
