import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from ...models.zipline_app.zipline_app import ZlModel
from .test_zipline_app import create_asset, create_order, create_account, a1

class OrderGeneralViewsTests(TestCase):
    def setUp(self):
      ZlModel.clear()
      self.acc1 = create_account(symbol="TEST01")
      self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])
 
    def test_list(self):
        url = reverse('zipline_app:orders-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_get(self):
        url = reverse('zipline_app:orders-new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        o1 = create_order(order_text="test?",days=-1, asset=self.a1a, amount=10, account=self.acc1)

        url = reverse('zipline_app:orders-delete', args=(self.a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        # http://stackoverflow.com/questions/40005411/django-django-test-client-post-request
        time = '2015-01-01 00:00:00' #timezone.now() + datetime.timedelta(days=-0.5)
        url = reverse('zipline_app:orders-new')
        response = self.client.post(url,{'pub_date':time,'asset':self.a1a.id,'amount':10,'account':self.acc1.id})
        self.assertEqual(response.status_code, 302)
#        print(response.context)
#        self.assertFormError(response, 'form', 'pub_date', 'Enter a valid date/time.')
        #self.assertFormError(response, 'form', 'asset', 'Enter a valid date/time.')
        #self.assertFormError(response, 'form', 'amount', 'Enter a valid date/time.')
        #self.assertFormError(response, 'form', 'account', 'Select a valid choice. That choice is not one of the available choices.')

    def test_quantity_large_does_not_trigger_error_integer_too_large(self):
        time = '2015-01-01 00:00:00' #timezone.now() + datetime.timedelta(days=-0.5)
        url = reverse('zipline_app:orders-new')
        largeqty=100000000000000000000000000000
        response = self.client.post(url,{'pub_date':time,'asset':self.a1a.id,'amount':largeqty,'account':self.acc1.id})
        self.assertContains(response,"Ensure this value is less than or equal to")

    def test_new_order_timezone(self):
        url = reverse('zipline_app:orders-new')
        time = '2015-01-01 06:00:00'
        o1={'pub_date':time,'asset':self.a1a.id,'amount':1,'account':self.acc1.id}
        response = self.client.post(url,o1,follow=True)
        self.assertContains(response,"06:00")

    def test_new_order_zeroqty(self):
        url = reverse('zipline_app:orders-new')
        time = '2015-01-01 06:00:00'
        o1={'pub_date':time,'asset':self.a1a.id,'amount':0,'account':self.acc1.id}
        response = self.client.post(url,o1)
        self.assertContains(response,"Quantity 0 is not allowed")

class OrderDetailViewTests(TestCase):
    def setUp(self):
      self.acc1 = create_account(symbol="TEST01")
      self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])

    def test_detail_view_with_a_future_order(self):
        """
        The detail view of a order with a pub_date in the future should
        return a 404 not found.
        """
        future_order = create_order(order_text='Future order.', days=5, asset=self.a1a, amount=10, account=self.acc1)
        url = reverse('zipline_app:orders-detail', args=(future_order.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_order(self):
        """
        The detail view of a order with a pub_date in the past should
        display the order's text.
        """
        past_order = create_order(order_text='Past Order.', days=-5, asset=self.a1a, amount=10, account=self.acc1)
        url = reverse('zipline_app:orders-detail', args=(past_order.id,))
        response = self.client.get(url)
        self.assertContains(response, past_order.order_text)

    def test_update(self):
        o1 = create_order(order_text="test?",days=-1, asset=self.a1a, amount=10, account=self.acc1)

        url = reverse('zipline_app:orders-update', args=(self.a1a.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
