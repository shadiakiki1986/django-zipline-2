from django.test import TestCase
from .test_zipline_app import create_fill, create_asset, a1, create_order, create_account, a2
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.side import LONG, SHORT
from ...models.zipline_app.zipline_app import ZlModel
from django.core.exceptions import ValidationError

def create_fill_from_order(order, fill_text, fill_price, tt_order_key=""):
    return Fill.objects.create(
      fill_text=fill_text,
      pub_date=order.pub_date,
      asset=order.asset,
      fill_side=order.order_side,
      fill_qty_unsigned=order.amount_unsigned,
      fill_price=fill_price,
      tt_order_key=tt_order_key,
      dedicated_to_order=order
    )

class FillModelTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])

  def test_clean_invalid_dedicated_order_qty(self):
    order = create_order(order_text="random order", days=-1,  asset=self.a1a, order_side=LONG, amount_unsigned=10,   account=self.acc                          )
    with self.assertRaises(ValidationError):
      f1 = create_fill(    fill_text="test fill",     days=-1, asset=self.a1a, fill_side=LONG,  fill_qty_unsigned=20, fill_price=2,     dedicated_to_order=order)

  def test_clean_invalid_dedicated_order_side(self):
    order = create_order(order_text="random order", days=-1,  asset=self.a1a, order_side=LONG, amount_unsigned=10,   account=self.acc                          )
    with self.assertRaises(ValidationError):
      f1 = create_fill(    fill_text="test fill",     days=-1, asset=self.a1a, fill_side=SHORT,  fill_qty_unsigned=10, fill_price=2,     dedicated_to_order=order)

  def test_clean_invalid_dedicated_order_asset(self):
    order = create_order(order_text="random order", days=-1,  asset=self.a1a, order_side=LONG, amount_unsigned=10,   account=self.acc                          )
    a2a = create_asset(a2["symbol"],a2["exchange"],a2["name"])
    with self.assertRaises(ValidationError):
      f1 = create_fill(    fill_text="test fill",     days=-1, asset=a2a, fill_side=LONG,  fill_qty_unsigned=10, fill_price=2,     dedicated_to_order=order)

  def test_clean_invalid_dedicated_order_pub_date(self):
    order = create_order(order_text="random order", days=-1,  asset=self.a1a, order_side=LONG, amount_unsigned=10,   account=self.acc                          )
    with self.assertRaises(ValidationError):
      f1 = create_fill(    fill_text="test fill",     days=-30, asset=self.a1a, fill_side=LONG,  fill_qty_unsigned=10, fill_price=2,     dedicated_to_order=order)

  def test_clean_valid_dedicated_order(self):
    order = create_order(order_text="random order", days=-1,  asset=self.a1a, order_side=LONG, amount_unsigned=10,   account=self.acc                          )
    f1 = create_fill_from_order( order=order, fill_text="test fill", fill_price=22, tt_order_key="test key")

  # two opposite fills  within the same minute with the same quantities
  # cause an error: ZeroDivisionError: Weights sum to zero, can't be normalized
  # zipline_app/matcher.py", line 146, in <lambda>
  # grouped_close = grouped.apply(lambda g: numpy.average(g['close'],weights=g['volume']))
  def test_two_opposite_fills_same_minute(self):
    qty = 10
    o_l = create_order(order_text="long order",  days=-1,  asset=self.a1a, order_side=LONG,  amount_unsigned=qty,   account=self.acc)
    o_s = create_order(order_text="short order", days=-1,  asset=self.a1a, order_side=SHORT, amount_unsigned=qty,   account=self.acc)
    f_l = create_fill_from_order(order=o_l, fill_text="test fill long", fill_price=2)
    f_s = create_fill_from_order(order=o_s, fill_text="test fill short", fill_price=2)

class FillViewsTests(TestCase):
    def setUp(self):
        self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])

    def test_list(self):
        url = reverse('zipline_app:fills-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        url = reverse('zipline_app:fills-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        url = reverse('zipline_app:fills-delete', args=(f1.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_quantity_large_does_not_trigger_error_integer_too_large(self):
        time = '2015-01-01 00:00:00' #timezone.now() + datetime.timedelta(days=-0.5)
        url = reverse('zipline_app:fills-new')
        largeqty=100000000000000000000000000000
        response = self.client.post(url, {'pub_date':time, 'asset':self.a1a.id, 'fill_side': LONG, 'fill_qty_unsigned':largeqty, 'fill_price':1})
        self.assertContains(response,"Ensure this value is less than or equal to")
        response = self.client.post(url, {'pub_date':time, 'asset':self.a1a.id, 'fill_side': LONG, 'fill_qty_unsigned':1, 'fill_price':largeqty})
        self.assertContains(response,"Ensure this value is less than or equal to")

    def test_update_get(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        url = reverse('zipline_app:fills-update', args=(f1.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_post_wo_tt_order_key(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_side=LONG, fill_qty_unsigned=20, fill_price=2)
        url = reverse('zipline_app:fills-update', args=(f1.id,))
        f2={'pub_date':f1.pub_date, 'asset':f1.asset, 'fill_side': f1.fill_side, 'fill_qty_unsigned':4444, 'fill_price':f1.fill_price}
        response = self.client.post(url,f2)
        self.assertContains(response,"4444")

    def test_update_post_wi_tt_order_key(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_side=LONG, fill_qty_unsigned=20, fill_price=2, tt_order_key='bla key')
        url = reverse('zipline_app:fills-update', args=(f1.id,))
        f1={'pub_date':f1.pub_date, 'asset':f1.asset, 'fill_side': f1.fill_side, 'fill_qty_unsigned':f1.fill_qty_unsigned, 'fill_price':f1.fill_price, 'tt_order_key':'foo key'}
        response = self.client.post(url,f1)
        self.assertContains(response,"foo key")

    def test_new_fill_zero_qty(self):
        url = reverse('zipline_app:fills-new')
        time = '2015-01-01 06:00:00'
        f1={'pub_date':time, 'asset':self.a1a.id, 'fill_side': LONG, 'fill_qty_unsigned':0, 'fill_price':1}
        response = self.client.post(url,f1)
        self.assertContains(response,"Quantity 0 is not allowed")

    def test_new_fill_negative_price(self):
        url = reverse('zipline_app:fills-new')
        time = '2015-01-01 06:00:00'
        f1={'pub_date':time, 'asset':self.a1a.id, 'fill_side': LONG, 'fill_qty_unsigned':1, 'fill_price':-1}
        response = self.client.post(url,f1)
        self.assertContains(response,"Enter a positive number.")

    def test_new_fill_dedicated_to_order(self):
        acc = create_account("test acc")
        o1 = create_order(order_text="test", days=-10, asset=self.a1a, order_side=LONG, amount_unsigned=10, account=acc)
        o1.clean()
        o1.save()

        url = reverse('zipline_app:fills-new')
        f1={
          'pub_date':o1.pub_date.replace(hour=o1.pub_date.hour+2).strftime('%Y-%m-%d %H:%M'),
          'asset':o1.asset.id,
          'fill_side': o1.order_side,
          'fill_qty_unsigned':o1.amount_unsigned,
          'fill_price':1,
          'dedicated_to_order':o1.id
        }
        response = self.client.post(url,f1,follow=True)

        expected = reverse('zipline_app:orders-detail', args=(o1.id,))
        self.assertNotContains(response, "has-error")
        self.assertContains(response, expected)
