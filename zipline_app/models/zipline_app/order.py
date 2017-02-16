from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from .asset import Asset
from .account import Account
from .zlmodel import ZlModel
from .fill import Fill

from numpy import average

# Create your models here.

class Order(models.Model):
    order_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published',default=timezone.now)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    amount = models.IntegerField(default=0)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # static variable

    def __str__(self):
        return "%s, %s (%s, %s)" % (self.asset.asset_symbol, self.amount, self.account.account_symbol, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def filled(self):
      if self.id in ZlModel.zl_closed_keyed:
        return self.amount
      if self.id in ZlModel.zl_open_keyed:
        return ZlModel.zl_open_keyed[self.id].filled
      return 0

    def fills(self):
      return [txn for txn in ZlModel.zl_txns if txn["order_id"]==self.id]

    def avgPrice(self):
      if self.filled()==0:
        return float('nan')

      sub = self.fills()
      avg = average(a=[txn["price"] for txn in sub], weights=[txn["amount"] for txn in sub])
      return avg

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

