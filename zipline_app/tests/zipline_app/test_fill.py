from django.test import TestCase
from .test_zipline_app import create_fill, create_asset, a1
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.side import LONG

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

