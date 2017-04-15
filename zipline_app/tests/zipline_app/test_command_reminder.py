from django.test import TestCase

# Testing management commands
# https://docs.djangoproject.com/en/1.10/topics/testing/tools/#management-commands
from django.core.management import call_command
from django.utils.six import StringIO

from ...models.zipline_app.side import BUY
from .test_zipline_app import create_asset, create_order, create_account, a1
from django.core import mail
from ...utils import myTestLogin

class ReminderCommandTests(TestCase):
  def setUp(self):
    self.acc1 = create_account(symbol="TEST01")
    self.a1a = create_asset(a1["symbol"],a1["exchange"],a1["name"])

  def testMain(self):
    with StringIO() as out, StringIO() as err:
      user = myTestLogin(self.client)
      o1 = create_order(order_text="test?",days=-1, asset=self.a1a, order_side=BUY, order_qty_unsigned=10, account=self.acc1)
      call_command('reminder', stderr=err, stdout=out, debug=True)
      self.assertEqual(len(mail.outbox), 2) # 1 email for creating the order, and another for the reminder

  def testNoRecipients(self):
    with StringIO() as out, StringIO() as err:
      o1 = create_order(order_text="test?",days=-1, asset=self.a1a, order_side=BUY, order_qty_unsigned=10, account=self.acc1)
      call_command('reminder', stderr=err, stdout=out, debug=True)
      self.assertEqual(len(mail.outbox), 0)
      self.assertNotIn("Failed", err.getvalue())
      self.assertIn("No users", err.getvalue())
      self.assertEquals(out.getvalue(), "")

  def testNoOrders(self):
    with StringIO() as out, StringIO() as err:
      call_command('reminder', stderr=err, stdout=out, debug=True)
      self.assertEqual(len(mail.outbox), 0)
      self.assertNotIn("Failed", err.getvalue())
      self.assertIn("No pending", err.getvalue())
      self.assertEquals(out.getvalue(), "")
