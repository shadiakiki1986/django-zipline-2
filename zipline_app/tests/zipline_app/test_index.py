from django.test import TestCase
from django.urls import reverse

class IndexViewTests(TestCase):
  def test_get(self):
    url = reverse('zipline_app:index')
    response = self.client.get(url, follow=True)
    self.assertContains(response, "blotter")
