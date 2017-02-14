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


class ZlModel:
    md5 = None
    zl_open       = []
    zl_closed     = []
    zl_txns       = []
    zl_open_keyed = {}
    zl_closed_keyed = {}
    fills={}
    orders={}

    @staticmethod
    def clear():
      ZlModel.md5 = None
      ZlModel.zl_open       = []
      ZlModel.zl_closed     = []
      ZlModel.zl_txns       = []
      ZlModel.zl_open_keyed = {}
      ZlModel.zl_closed_keyed = {}
      ZlModel.fills={}
      ZlModel.orders={}

    @staticmethod
    def add_fill(fill: Fill):
      print("Adding fill: %s" % fill)
      if fill.asset.id not in ZlModel.fills:
        ZlModel.fills[fill.asset.id]={}

      ZlModel.fills[fill.asset.id][fill.id]={
        "close": fill.fill_price,
        "volume": fill.fill_qty,
        "dt": pd.Timestamp(fill.pub_date,tz='utc')
      }

    @staticmethod
    def fills_as_dict_df():
      # Copy keys to a new dictionary (Python)
      # http://stackoverflow.com/a/7369284/4126114
      fills2=dict.fromkeys(ZlModel.fills.keys(),{})

      for sid in ZlModel.fills:
        fills2[sid] = pd.DataFrame({})
        sub = ZlModel.fills[sid].values()
        fills2[sid]["close"]=[y["close"] for y in sub]
        fills2[sid]["volume"]=[y["volume"] for y in sub]
        fills2[sid]["dt"]=[y["dt"] for y in sub]
        fills2[sid]=fills2[sid].set_index("dt")
      return fills2

    @staticmethod
    def add_order(order: Order):
      ZlModel.orders[order.id] = {
        "dt": order.pub_date,
        "asset": order.asset.to_dict(),
        "amount": order.amount,
        "style": MarketOrder(),
        "id": order.id
      }

    @staticmethod
    def orders_as_list():
      return ZlModel.orders.values()

    @staticmethod
    def delete_fill(fill: Fill):
      # How to remove a key from a python dictionary
      # http://stackoverflow.com/questions/11277432/ddg#11277439
      ZlModel.fills[fill.asset.id].pop(fill.id, None)
      if not any(ZlModel.fills[fill.asset.id]):
        ZlModel.fills.pop(fill.asset.id, None)

    @staticmethod
    def delete_order(order: Order):
      # How to remove a key from a python dictionary
      # http://stackoverflow.com/questions/11277432/ddg#11277439
      ZlModel.orders.pop(order.id, None)

    @staticmethod
    def update():
      md5 = hashlib.md5(json.dumps({
        "fills":[x.__str__() for x in Fill.objects.all()],
        "orders":[x.__str__() for x in Order.objects.all()]
      }).encode('utf-8')).hexdigest()

      if ZlModel.md5==md5:
        print("Model unchanged .. not rerunning engine: "+md5)
        return

      print("Run matching engine: "+md5)

      matcher = mmm_Matcher()

# Commenting out since added function `add_{fill,order}` and calling it from signals at bottom of this file
#      fills = {
#          x.asset.id: pd.DataFrame({})
#          for x in Fill.objects.all()
#      }
#      #print("sid, fills", sid, fills)
#      for sid in fills:
#        sub = [z for z in Fill.objects.all() if z.asset.id==sid]
#        fills[sid]["close"] = [y.fill_price for y in sub]
#        fills[sid]["volume"] = [y.fill_qty for y in sub]
#        fills[sid]["dt"] = [pd.Timestamp(y.pub_date,tz='utc') for y in sub]
#        fills[sid] = fills[sid].set_index("dt")
#      #print("data: %s" % (fills))
#      orders = [
#        {
#          "dt": x.pub_date,
#          "asset": x.asset.to_dict(),
#          "amount": x.amount,
#          "style": MarketOrder(),
#          "id": x.id
#        }
#        for x in Order.objects.all()
#      ]

      all_closed, all_txns, open_orders = mmm_factory(
        matcher,
        ZlModel.fills_as_dict_df(),
        ZlModel.orders_as_list()
      )

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


# https://docs.djangoproject.com/en/1.11/topics/signals/#connecting-receiver-functions
#from django.core.signals import request_started
#request_started.connect(ZlModel.update)

# connecting signals
from django.db.backends.signals import connection_created
class SignalProcessor:
  #def post_init(sender, **kwargs):
  #  print("Signal: %s, %s" % ("post_init", sender.__name__))

  def post_save(sender, **kwargs):
    #print("Signal: %s, %s" % ("post_save", sender))
    if sender.__name__=="Fill": ZlModel.add_fill(kwargs["instance"])
    if sender.__name__=="Order": ZlModel.add_order(kwargs["instance"])
    ZlModel.update()

  def post_delete(sender, **kwargs):
    #print("Signal: %s, %s" % ("post_delete", sender))
    if sender.__name__=="Fill": ZlModel.delete_fill(kwargs["instance"])
    if sender.__name__=="Order": ZlModel.delete_order(kwargs["instance"])
    ZlModel.update()

  #def connection_created(sender, **kwargs):
  #  print("Signal: %s, %s" % ("connection_created", sender))

senders=("polls.Order", "polls.Fill", "polls.Asset")
for sender in senders:
  #models.signals.post_init.connect(SignalProcessor.post_init, sender=sender)
  models.signals.post_save.connect(SignalProcessor.post_save, sender=sender)
  models.signals.post_delete.connect(SignalProcessor.post_delete, sender=sender)
#connection_created.connect(SignalProcessor.connection_created)

