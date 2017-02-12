from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime

from zipline.finance.order import Order as zlOrder
from zipline.finance.execution import (
    LimitOrder,
    MarketOrder,
    StopLimitOrder,
    StopOrder,
)

# Create your models here.

class Order(models.Model):
    order_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    order_sid = models.CharField(max_length=20, default='-')
    amount = models.IntegerField(default=0)

    def __str__(self):
        return "%s, %s (%s)" % (self.order_sid, self.amount, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def _asZiplineOrder(self):
      return zlOrder(dt=self.pub_date, order_sid=self.order_sid, amount=self.amount, style=MarketOrder())

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

class Fill(models.Model):
    # 2017-01-12: unlink orders from fills and use zipline engine to perform matching
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fill_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    fill_qty = models.IntegerField(default=0)
    fill_price = models.FloatField(default=0)
    pub_date = models.DateTimeField('date published',default=timezone.now)
    fill_sid = models.CharField(max_length=20, default='-')

    def __str__(self):
        return "%s, %s, %s (%s)" % (self.fill_sid, self.fill_qty, self.fill_price, self.fill_text)
