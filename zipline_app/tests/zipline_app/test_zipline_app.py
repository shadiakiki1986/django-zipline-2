import datetime
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from time import sleep
import pandas as pd
from unittest import skip
from ...models.zipline_app.zipline_app import Order, ZlModel, Fill, Account, Asset
from ...models.zipline_app.side import LONG
from ...utils import myTestLogin, chopSeconds

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

def create_account(symbol):
    return Account.objects.create(
      account_symbol=symbol
    )

def create_asset(symbol, exchange, name):
    return Asset.objects.create(
      asset_exchange=exchange,
      asset_symbol=symbol,
      asset_name=name
    )

def create_order(order_text, days, asset, order_side, amount_unsigned, account, user=None):
    """
    Creates a order with the given `order_text` and published the
    given number of `days` offset to now (negative for orders published
    in the past, positive for orders that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    time = chopSeconds(time)
    order = Order.objects.create(
      order_text=order_text,
      pub_date=time,
      asset=asset,
      order_side=order_side,
      amount_unsigned=amount_unsigned,
      account=account,
      user=user
    )
    order.clean()
    order.save()
    return order

def create_fill(fill_text, days, asset, fill_side, fill_qty_unsigned, fill_price, tt_order_key="", dedicated_to_order=None, user=None):
    time = timezone.now() + datetime.timedelta(days=days)
    fill = Fill.objects.create(
      fill_text=fill_text, pub_date=time, asset=asset,
      fill_side=fill_side, fill_qty_unsigned=fill_qty_unsigned, fill_price=fill_price,
      tt_order_key=tt_order_key,
      dedicated_to_order=dedicated_to_order,
      user=user
    )
    fill.clean()
    fill.save()
    return fill

class OrderMethodTests(TestCase):
    def setUp(self):
      ZlModel.clear()
      self.acc1 = create_account(symbol="TEST01")
      self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
      self.a2a = create_asset(a2["symbol"],a2["exchange"],a2["name"])

    def test_was_published_recently_with_future_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is in the future.
        """
        future_order = create_order(order_text="test?",days=30, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=self.acc1)
        self.assertIs(future_order.was_published_recently(), False)

    def test_was_published_recently_with_old_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is older than 1 day.
        """
        old_order = create_order(order_text="test?",days=-30, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=self.acc1)
        self.assertIs(old_order.was_published_recently(), False)

    def test_was_published_recently_with_recent_order(self):
        """
        was_published_recently() should return True for orders whose
        pub_date is within the last day.
        """
        recent_order = create_order(order_text="test?",days=-0.5, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=self.acc1)
        self.assertIs(recent_order.was_published_recently(), True)

    def test_avg_price(self):
        o = create_order(order_text="test?",days=-0.5, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=self.acc1)
        ZlModel.zl_closed_keyed={o.id: {}}
        ZlModel.zl_txns=[
          {"order_id":o.id, "price":1, "amount":1},
          {"order_id":o.id, "price":1, "amount":1}
        ]
        self.assertEqual(o.avgPrice(), 1)

    def test_asset_to_dict(self):
        o = create_order(order_text="test?",days=-0.5, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=self.acc1)
        self.assertEqual(o.asset.to_dict(), a1)

class OrderViewTests(TestCase):

    def setUp(self):
      ZlModel.clear()
      self.acc1 = create_account(symbol="TEST01")
      self.asset = create_asset(a1["symbol"],a1["exchange"],a1["name"])
      myTestLogin(self.client)

    def test_blotter_engine_view_with_no_orders(self):
        """
        If no orders exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('zipline_app:blotter-engine'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No orders are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])
        self.assertContains(response, "New fill")

    def test_blotter_engine_view_with_a_past_order(self):
        """
        Orders with a pub_date in the past should be displayed on the
        blotter_engine page.
        """
        create_order(order_text="Past order.", days=-30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        response = self.client.get(reverse('zipline_app:blotter-engine'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, L, 10 (TEST01, Past order.)>']
        )

    def test_blotter_engine_view_with_a_future_order(self):
        """
        Orders with a pub_date in the future should not be displayed on
        the blotter_engine page.
        """
        create_order(order_text="Future order.", days=30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        response = self.client.get(reverse('zipline_app:blotter-engine'))
        self.assertContains(response, "No orders are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_blotter_engine_view_with_future_order_and_past_order(self):
        """
        Even if both past and future orders exist, only past orders
        should be displayed.
        """
        create_order(order_text="Past order.", days=-30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        create_order(order_text="Future order.", days=30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        response = self.client.get(reverse('zipline_app:blotter-engine'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, L, 10 (TEST01, Past order.)>']
        )

    def test_blotter_engine_view_with_two_past_orders(self):
        """
        The orders blotter_engine page may display multiple orders.
        """
        create_order(order_text="Past order 1.", days=-30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        create_order(order_text="Past order 2.", days=-5, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        response = self.client.get(reverse('zipline_app:blotter-engine'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: A1, L, 10 (TEST01, Past order 2.)>', '<Order: A1, L, 10 (TEST01, Past order 1.)>']
        )

    def test_index_view_combined_general(self):
        """
        This test sometimes fails and then passes when re-run
        .. not sure why yet
        .. seems to be solved by sleep 50 ms
        """
        o1 = create_order(order_text="Past order 1.", days=-30, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        o2 = create_order(order_text="Past order 2.", days=-5, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        f1 = create_fill(fill_text="test?",days=-30, asset=self.asset, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        f2 = create_fill(fill_text="test?",days=-0.5, asset=self.asset, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        sleep(0.05)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))

        pointer = response.context['combined'][2]
        self.assertEqual(
            pointer["minute"],
            pd.Timestamp(o1.pub_date,tz='utc').floor('1Min')
        )

        pointer = pointer["duos"][0]
        self.assertEqual(
          pointer["asset"],
          o1.asset
        )

        self.assertQuerysetEqual(
            pointer['orders'],
            [
              '<Order: A1, L, 10 (TEST01, Past order 1.)>',
            ]
        )
        self.assertQuerysetEqual(
            pointer['fills'],
            [
              '<Fill: A1, L 20, 2.0 (, test?)>',
            ]
        )

    def test_index_unused_fills(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.asset, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        sleep(0.05)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertEqual(len(ZlModel.zl_unused),1)
        self.assertContains(response, "Assets with extra fills")

    def test_index_view_deleted_order_implies_deleted_minute(self):
        # be careful that with days=0 this test will fail
        # but not because the minute is showing up
        # but because the default field for order pub_date is also timezone.now()
        o1a = create_order(order_text="test", days=-10, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        f1 = create_fill(fill_text="test?",days=-10, asset=self.asset, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        o1b = create_order(order_text="test", days=-9, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)

        time = o1b.pub_date
        sleep(0.05)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertContains(response, time.strftime("%Y-%m-%d"))

        o1b.delete()
        sleep(0.05)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertNotContains(response, time.strftime("%Y-%m-%d"))

    @skip("This test is not capturing the messages queue for some reason, and I couldnt get it to work")
    def test_index_view_create_delete_order_toggle_django_message(self):
        time = timezone.now()
        url = reverse('zipline_app:orders-new')
        o1 = {'pub_date':time, 'asset':self.asset.id, 'order_side': LONG, 'amount_unsigned':10, 'account':self.acc1.id}
        response = self.client.post(url,o1,follow=True)

        messages = list(response.context['messages'])
        self.assertContains(messages[0],"Successfully created order")
#        o1.delete()
#        get_assert_contains(self,"Successfully deleted order")
#
#        f1 = create_fill(fill_text="test?",days=-30, asset=self.asset, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
#        get_assert_contains(self,"Successfully created fill")
#        f1.delete()
#        get_assert_contains(self,"Successfully deleted fill")
#
#        as1=create_asset("test","test","test")
#        get_assert_contains(self,"Successfully created asset")
#
#        ac1=create_account("test")
#        get_assert_contains(self,"Successfully created account")

    def test_fills_required_per_asset(self):
        o1 = create_order(order_text="test", days=-10, asset=self.asset, order_side=LONG, amount_unsigned=10, account=self.acc1)
        sleep(0.05)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertEqual(response.context['fills_required_per_asset'], {self.asset:10})
        self.assertContains(response, "Assets with required fills")
        self.assertContains(response, self.asset.asset_symbol+": 10")

        f1 = create_fill(fill_text="test?",days=-10, asset=self.asset, fill_side=LONG, fill_qty_unsigned=5, fill_price=2)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertEqual(response.context['fills_required_per_asset'], {self.asset:5})

        f2 = create_fill(fill_text="test?",days=-10, asset=self.asset, fill_side=LONG, fill_qty_unsigned=5, fill_price=2)
        response = self.client.get(reverse('zipline_app:blotter-sideBySide'))
        self.assertEqual(response.context['fills_required_per_asset'], {})
        self.assertNotContains(response, "Assets with required fills")
