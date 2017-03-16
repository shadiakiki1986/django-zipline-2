from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse

from .asset import Asset
from .account import Account
from .zlmodel import ZlModel
from .fill import Fill, validate_nonzero

from numpy import average
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

class Order(models.Model):
    order_text = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date published',default=timezone.now)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    amount_unsigned = models.PositiveIntegerField(
      default=0,
      validators=[MaxValueValidator(1000000), validate_nonzero],
      verbose_name="Qty"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    order_side = models.CharField(
      max_length=1,
      choices=Fill.FILL_SIDE_CHOICES,
      default=Fill.LONG,
      verbose_name="Side"
    )

    def amount_signed(self):
      return self.amount_unsigned * (+1 if self.order_side==Fill.LONG else -1)

    def __str__(self):
        return "%s, %s, %s (%s, %s)" % (self.asset.asset_symbol, self.order_side, self.amount_unsigned, self.account.account_symbol, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def filled(self):
      if self.id in ZlModel.zl_closed_keyed:
        return self.amount_signed()
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

# using get_success_url in OrderCreate instead of this
#
#    def get_absolute_url(self):
#      return reverse('zipline_app:orders-list') # TODO rename to orders
#      return reverse('zipline_app:orders-list', kwargs={'pk': self.pk})
