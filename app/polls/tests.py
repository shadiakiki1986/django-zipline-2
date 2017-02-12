import datetime

from django.utils import timezone
from django.test import TestCase

from .models import Order
from django.urls import reverse

def create_order(order_text, days):
    """
    Creates a order with the given `order_text` and published the
    given number of `days` offset to now (negative for orders published
    in the past, positive for orders that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Order.objects.create(order_text=order_text, pub_date=time)


class OrderMethodTests(TestCase):

    def test_was_published_recently_with_future_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is in the future.
        """
        future_order = create_order(order_text="test?",days=30)
        self.assertIs(future_order.was_published_recently(), False)

    def test_was_published_recently_with_old_order(self):
        """
        was_published_recently() should return False for orders whose
        pub_date is older than 1 day.
        """
        old_order = create_order(order_text="test?",days=-30)
        self.assertIs(old_order.was_published_recently(), False)

    def test_was_published_recently_with_recent_order(self):
        """
        was_published_recently() should return True for orders whose
        pub_date is within the last day.
        """
        recent_order = create_order(order_text="test?",days=-0.5)
        self.assertIs(recent_order.was_published_recently(), True)

class OrderViewTests(TestCase):

    def test_index_view_with_no_orders(self):
        """
        If no orders exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_index_view_with_a_past_order(self):
        """
        Orders with a pub_date in the past should be displayed on the
        index page.
        """
        create_order(order_text="Past order.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: Past order.>']
        )

    def test_index_view_with_a_future_order(self):
        """
        Orders with a pub_date in the future should not be displayed on
        the index page.
        """
        create_order(order_text="Future order.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_order_list'], [])

    def test_index_view_with_future_order_and_past_order(self):
        """
        Even if both past and future orders exist, only past orders
        should be displayed.
        """
        create_order(order_text="Past order.", days=-30)
        create_order(order_text="Future order.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: Past order.>']
        )

    def test_index_view_with_two_past_orders(self):
        """
        The orders index page may display multiple orders.
        """
        create_order(order_text="Past order 1.", days=-30)
        create_order(order_text="Past order 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_order_list'],
            ['<Order: Past order 2.>', '<Order: Past order 1.>']
        )

class OrderIndexDetailTests(TestCase):
    def test_detail_view_with_a_future_order(self):
        """
        The detail view of a order with a pub_date in the future should
        return a 404 not found.
        """
        future_order = create_order(order_text='Future order.', days=5)
        url = reverse('polls:detail', args=(future_order.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_order(self):
        """
        The detail view of a order with a pub_date in the past should
        display the order's text.
        """
        past_order = create_order(order_text='Past Order.', days=-5)
        url = reverse('polls:detail', args=(past_order.id,))
        response = self.client.get(url)
        self.assertContains(response, past_order.order_text)
