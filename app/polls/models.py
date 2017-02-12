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
    sid = models.CharField(max_length=20, default='-')
    amount = models.IntegerField(default=0)

    def __str__(self):
        return "%s, %s (%s)" % (self.sid, self.amount, self.order_text)

    def was_published_recently(self):
        now = timezone.now()
        return now >= self.pub_date >= now - datetime.timedelta(days=1)

    def _asZiplineOrder(self):
      return zlOrder(self.pub_date, self.sid, self.amount, MarketOrder())

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

class Fill(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fill_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.fill_text
