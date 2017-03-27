from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse

from .asset import Asset
from .account import Account
from .zlmodel import ZlModel
from .side import LONG, FILL_SIDE_CHOICES, validate_nonzero, MARKET, ORDER_TYPE_CHOICES, PositiveFloatFieldModel

from numpy import average
from django.core.validators import MaxValueValidator, MinValueValidator
from ...utils import now_minute, chopSeconds
from django.contrib.auth.models import User

# Create your models here.

class AbstractOrder(models.Model):
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
    user = models.ForeignKey(User, null=True, default=None)
    order_type = models.CharField(
      max_length=1,
      choices=ORDER_TYPE_CHOICES,
      default=MARKET,
      verbose_name="Type"
    )
    limit_price = PositiveFloatFieldModel(
      default=0,
      validators=[MaxValueValidator(1000000), MinValueValidator(0), validate_nonzero],
    )
    class Meta:
      abstract=True


class Order(AbstractOrder):
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

    def save(self):
      order = super(Order, self).save()
      latest_id = OrderHistory.objects.filter(order=order).latest('id')
      previous = OrderHistory.objects.get(latest_id)
      OrderHistory.objects.create(
        order=order,
        previous = previous,
        order_text = order.order_text,
        pub_date = order.pub_date,
        asset = order.asset,
        amount_unsigned = order.amount_unsigned,
        account = order.account,
        order_side = order.order_side,
        user = order.user,
        order_type = order.order_type,
        limit_price = order.limit_price,
      )

#####################
# Model History in Django
# http://stackoverflow.com/a/14282776/4126114
class OrderHistory(AbstractOrder):
  order = models.ForeignKey(Order)
  previous = models.ForeignKey(OrderHistory)
  def diff(self):
    messages = []
    attrs = ['order_text', 'pub_date', 'asset', 'amount_unsigned', 'account', 'order_side', 'order_type', 'limit_price']
    for attr in attrs:
      if getattr(self, attr) != getattr(self.previous, attr):
        messages.push("Changed %s from '%s' to '%s'" % (attr, getattr(self, attr), getattr(self.previous, attr)))
    return messages
