from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse

from .asset import Asset
from .account import Account
from .zlmodel import ZlModel
from .side import LONG, FILL_SIDE_CHOICES, validate_nonzero

from numpy import average
from django.core.validators import MaxValueValidator, MinValueValidator
from ...utils import now_minute, chopSeconds

# Create your models here.

class Order(models.Model):
    order_text = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date published',default=now_minute)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    amount_unsigned = models.PositiveIntegerField(
      default=0,
      validators=[MaxValueValidator(1000000), validate_nonzero],
      verbose_name="Qty"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    order_side = models.CharField(
      max_length=1,
      choices=FILL_SIDE_CHOICES,
      default=LONG,
      verbose_name="Side"
    )

    def amount_signed(self):
      return self.amount_unsigned * (+1 if self.order_side==LONG else -1)

    def __str__(self):
        return "%s, %s, %s (%s, %s)" % (self.asset.asset_symbol, self.order_side, self.amount_unsigned, self.account.account_symbol, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def filled(self):
      if self.dedicated_fill() is not None:
        return self.dedicated_fill().fill_qty_signed()

      if self.id in ZlModel.zl_closed_keyed:
        return self.amount_signed()
      if self.id in ZlModel.zl_open_keyed:
        return ZlModel.zl_open_keyed[self.id].filled
      return 0

    def fills(self):
      if self.dedicated_fill() is not None:
        fill = self.dedicated_fill()
        txn = {
          'order_id':self.id,
          'price': fill.fill_price,
          'amount': fill.fill_qty_signed(),
          'dt': fill.pub_date,
          'sid': {
            'symbol': fill.asset.asset_symbol,
          },
        }
        return [txn]

      return [txn for txn in ZlModel.zl_txns if txn["order_id"]==self.id]

    def avgPrice(self):
      if self.filled()==0:
        return float('nan')

      sub = self.fills()
      avg = average(a=[txn["price"] for txn in sub], weights=[txn["amount"] for txn in sub])
      return avg

    def clean(self):
      # drop seconds from pub_date
      self.pub_date = chopSeconds(self.pub_date)

    # access one-to-one reverse field
    # https://docs.djangoproject.com/en/1.10/topics/db/examples/one_to_one/
    def dedicated_fill(self):
      if hasattr(self,'fill'):
        return self.fill
      return None

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

# using get_success_url in OrderCreate instead of this
#
#    def get_absolute_url(self):
#      return reverse('zipline_app:orders-list') # TODO rename to orders
#      return reverse('zipline_app:orders-list', kwargs={'pk': self.pk})
