from django.test import TestCase
from .test_zipline_app import create_fill, create_asset, a1
from django.urls import reverse

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
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_qty=20, fill_price=2)
        url = reverse('zipline_app:fills-delete', args=(self.a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_quantity_large_does_not_trigger_error_integer_too_large(self):
        time = '2015-01-01 00:00:00' #timezone.now() + datetime.timedelta(days=-0.5)
        url = reverse('zipline_app:fills-new')
        largeqty=100000000000000000000000000000
        response = self.client.post(url,{'pub_date':time,'asset':self.a1a.id,'fill_qty':largeqty,'fill_price':1})
        self.assertContains(response,"Ensure this value is less than or equal to")
        response = self.client.post(url,{'pub_date':time,'asset':self.a1a.id,'fill_qty':1,'fill_price':largeqty})
        self.assertContains(response,"Ensure this value is less than or equal to")

    def test_update(self):
        f1 = create_fill(fill_text="test?",days=-30, asset=self.a1a, fill_qty=20, fill_price=2)
        url = reverse('zipline_app:fills-update', args=(self.a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_fill_zero_qty(self):
        url = reverse('zipline_app:fills-new')
        time = '2015-01-01 06:00:00'
        f1={'pub_date':time,'asset':self.a1a.id,'fill_qty':0,'fill_price':1}
        response = self.client.post(url,f1)
        self.assertContains(response,"Quantity 0 is not allowed")

    def test_new_fill_negative_price(self):
        url = reverse('zipline_app:fills-new')
        time = '2015-01-01 06:00:00'
        f1={'pub_date':time,'asset':self.a1a.id,'fill_qty':1,'fill_price':-1}
        response = self.client.post(url,f1)
        self.assertContains(response,"Enter a positive number.")

