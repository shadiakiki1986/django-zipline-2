from django.test import TestCase
from ...utils import chopSeconds, now_minute
from django.utils import timezone

class UtilsTests(TestCase):
  def test_chopSeconds(self):
    ts1 = timezone.now()
    ts2 = chopSeconds(ts1)
    self.assertEqual(ts2.second,0)
    self.assertEqual(ts2.microsecond,0)

  def test_now_minute(self):
    ts1 = timezone.now()
    ts2=now_minute()
    self.assertEqual(ts2.second,0)
    self.assertEqual(ts2.microsecond,0)
    self.assertEqual(ts2.minute,ts1.minute)
    self.assertEqual(ts2.hour,ts1.hour)
