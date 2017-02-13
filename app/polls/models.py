from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime

from zipline.finance.execution import (
    LimitOrder,
    MarketOrder,
    StopLimitOrder,
    StopOrder,
)

from .matcher import factory as mmm_factory, Matcher as mmm_Matcher
import pandas as pd
from six import iteritems
from functools import reduce

import json
import hashlib
from numpy import average, concatenate

# Create your models here.

class Asset(models.Model):
    asset_symbol = models.CharField(max_length=20)
    asset_exchange = models.CharField(max_length=200)
    asset_name = models.CharField(max_length=200)

    def __str__(self):
        return "%s, %s, %s" % (self.asset_symbol, self.asset_exchange, self.asset_name)

    def to_dict(self):
        return {
          "sid": self.id,
          "symbol": self.asset_symbol,
          "exchange": self.asset_exchange,
          "name": self.asset_name
        }

class Order(models.Model):
    order_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    amount = models.IntegerField(default=0)

    # static variable

    def __str__(self):
        return "%s, %s (%s)" % (self.asset.asset_symbol, self.amount, self.order_text)

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

class ZlModel:
    md5 = None
    zl_open       = []
    zl_closed     = []
    zl_txns       = []
    zl_open_keyed = {}
    zl_closed_keyed = {}

    @staticmethod
    def update(sender, **kwargs):
      md5 = hashlib.md5(json.dumps({
        "fills":[x.__str__() for x in Fill.objects.all()],
        "orders":[x.__str__() for x in Order.objects.all()]
      }).encode('utf-8')).hexdigest()

      if ZlModel.md5==md5:
        print("Model unchanged .. not rerunning engine: "+md5)
        return

      print("Run matching engine: "+md5)

      matcher = mmm_Matcher()

      fills = {
          x.asset.id: pd.DataFrame({})
          for x in Fill.objects.all()
      }
      #print("sid, fills", sid, fills)
      for sid in fills:
        sub = [z for z in Fill.objects.all() if z.asset.id==sid]
        fills[sid]["close"] = [y.fill_price for y in sub]
        fills[sid]["volume"] = [y.fill_qty for y in sub]
        fills[sid]["dt"] = [pd.Timestamp(y.pub_date,tz='utc') for y in sub]
        fills[sid] = fills[sid].set_index("dt")

      #print("data: %s" % (fills))

      orders = [
        {
          "dt": x.pub_date,
          "asset": x.asset.to_dict(),
          "amount": x.amount,
          "style": MarketOrder(),
          "id": x.id
        }
        for x in Order.objects.all()
      ]

      all_closed, all_txns, open_orders = mmm_factory(matcher,fills,orders)

      ZlModel.zl_open = reduce(
        lambda a, b: concatenate((a,b)),
        [v for k,v in open_orders.items()],
        list()
      )
      ZlModel.zl_closed = all_closed
      ZlModel.zl_txns = [txn.to_dict() for txn in all_txns]
      ZlModel.zl_open_keyed = {v.id: v for v in ZlModel.zl_open}
      ZlModel.zl_closed_keyed = {v.id: v for v in ZlModel.zl_closed}

      # save md5 at the end to ensure re-run if error occured
      ZlModel.md5=md5

class Fill(models.Model):
    # 2017-01-12: unlink orders from fills and use zipline engine to perform matching
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fill_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    fill_qty = models.IntegerField(default=0)
    fill_price = models.FloatField(default=0)
    pub_date = models.DateTimeField('date published',default=timezone.now)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "%s, %s, %s (%s)" % (self.asset.asset_symbol, self.fill_qty, self.fill_price, self.fill_text)

# https://docs.djangoproject.com/en/1.11/topics/signals/#connecting-receiver-functions
#from django.db.models.signals import post_save
from django.core.signals import request_started
request_started.connect(ZlModel.update)
