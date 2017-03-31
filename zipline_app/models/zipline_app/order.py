from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse

from .asset import Asset
from .account import Account
from .zlmodel import ZlModel
from .side import BUY, FILL_SIDE_CHOICES, validate_nonzero, MARKET, ORDER_TYPE_CHOICES, PositiveFloatFieldModel, ORDER_STATUS_CHOICES, OPEN, CANCELLED, ORDER_VALIDITY_CHOICES, GTC

from numpy import average
from django.core.validators import MaxValueValidator, MinValueValidator
from ...utils import now_minute, chopSeconds
from django.contrib.auth.models import User

# Create your models here.

class AbstractOrder(models.Model):
    order_text = models.CharField(max_length=200, blank=True)
    pub_date = models.DateTimeField('date published',default=now_minute)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    order_qty_unsigned = models.PositiveIntegerField(
      default=0,
      validators=[MaxValueValidator(1000000), validate_nonzero],
      verbose_name="Qty"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    order_side = models.CharField(
      max_length=1,
      choices=FILL_SIDE_CHOICES,
      default=BUY,
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
      default=None,
      validators=[MaxValueValidator(1000000), MinValueValidator(0), validate_nonzero],
      null=True,
      blank=True
    )
    order_status = models.CharField(
      max_length=1,
      choices=ORDER_STATUS_CHOICES,
      default=OPEN,
      verbose_name="Status"
    )
    order_validity = models.CharField(
      max_length=1,
      choices=ORDER_VALIDITY_CHOICES,
      default=GTC,
      verbose_name="Validity"
    )
    validity_date = models.DateTimeField(
      default=None,
      null=True,
      blank=True
    )

    def diff(self, other):
      if other is None:
        return []
      messages = []
      attrs = ['order_text', 'pub_date', 'asset', 'order_qty_unsigned', 'account', 'order_side', 'order_type', 'limit_price', 'order_status', 'order_validity', 'validity_date']
      for attr in attrs:
        if getattr(self, attr) != getattr(other, attr):
          messages.append(
            "Changed %s from '%s' to '%s'" %
            (
              attr,
              getattr(other, attr),
              getattr(self, attr)
            )
          )
      return messages

    class Meta:
      abstract=True


class Order(AbstractOrder):
    def order_qty_signed(self):
      return self.order_qty_unsigned * (+1 if self.order_side==BUY else -1)

    def __str__(self):
        return "%s, %s, %s (%s, %s)" % (self.asset.asset_symbol, self.order_side, self.order_qty_unsigned, self.account.account_symbol, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def filled(self):
      if self.dedicated_fill() is not None:
        return self.dedicated_fill().fill_qty_signed()

      if self.id in ZlModel.zl_closed_keyed:
        return self.order_qty_signed()
      if self.id in ZlModel.zl_open_keyed:
        return ZlModel.zl_open_keyed[self.id].filled

      # get from the fills function
      # This works for cancelled orders with partial fills
      # and for orders that are completely unfilled
      sub = [txn["amount"] for txn in self.fills()]
      return sum(sub)

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

    def append_history(self):
      history = OrderHistory.objects.filter(order=self)
      previous = None
      if history.count()>0:
        previous = history.latest('id')
        diff = self.diff(previous)
        if len(diff)==0:
          return

      OrderHistory.objects.create(
        order=self,
        previous = previous,
        order_text = self.order_text,
        pub_date = self.pub_date,
        asset = self.asset,
        order_qty_unsigned = self.order_qty_unsigned,
        account = self.account,
        order_side = self.order_side,
        user = self.user,
        order_type = self.order_type,
        limit_price = self.limit_price,
        order_status = self.order_status,
        order_validity = self.order_validity,
        validity_date = self.validity_date
      )

    # excluding the first entry with previous=None since this is available regardless of edits made
    def history(self):
      return self.orderhistory_set.exclude(previous=None).order_by('-ed_date')

    def cancel(self):
      self.order_status = CANCELLED
      self.save()

#####################
# Model History in Django
# http://stackoverflow.com/a/14282776/4126114
class OrderHistory(AbstractOrder):
  order = models.ForeignKey(Order)
  previous = models.ForeignKey('self', null=True)
  ed_date = models.DateTimeField('date edited',default=timezone.now)

  def __str__(self):
    return ', '.join(self.diffPrevious())

  def diffPrevious(self):
    return self.diff(self.previous)
