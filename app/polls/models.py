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
from django.db import connection

# Django Logging
# https://docs.djangoproject.com/en/1.10/topics/logging/
import logging
logger = logging.getLogger(__name__)

# Create your models here.

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

class Asset(models.Model):
    asset_symbol = models.CharField(max_length=20)
    asset_exchange = models.CharField(max_length=200)
    asset_name = models.CharField(max_length=200)

    def __str__(self):
        return "%s, %s, %s" % (self.asset_symbol, self.asset_exchange, self.asset_name)

    def to_dict(self):
        return {
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

    def md5(self):
        string = "%s, %s, %s (%s)" % (self.pub_date, self.asset.asset_symbol, self.amount, self.order_text)
        return md5_wrap(string)

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

    def md5(self):
        string = "%s, %s, %s, %s (%s)" % (self.pub_date, self.asset.asset_symbol, self.fill_qty, self.fill_price, self.fill_text)
        return md5_wrap(string)

    def has_unused(self):
      return self.asset.id in ZlModel.zl_unused

class ZlModel:
    md5 = None
    zl_open       = []
    zl_closed     = []
    zl_txns       = []
    zl_open_keyed = {}
    zl_closed_keyed = {}
    fills={}
    orders={}
    assets={}
    zl_unused = {}

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
      ZlModel.assets={}
      ZlModel.zl_unused = {}

    @staticmethod
    def add_asset(asset: Asset):
      #print("adding asset",asset,asset.id)
      ZlModel.assets[asset.id]=asset.to_dict()

    @staticmethod
    def add_fill(fill: Fill):
      #print("Adding fill: %s" % fill)
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
      if order.asset.id not in ZlModel.orders:
        ZlModel.orders[order.asset.id]={}

      ZlModel.orders[order.asset.id][order.id] = {
        "dt": order.pub_date,
        "asset": order.asset.id,
        "amount": order.amount,
        "style": MarketOrder()
      }

    @staticmethod
    def delete_asset(asset: Asset):
      ZlModel.assets.pop(asset.id, None)

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
    def db_ready():
      tables = connection.introspection.table_names()
      isready = "polls_fill" in tables
      if not isready:
        logger.debug("db tables not available .. skipping zlmodel init")
      return isready

    @staticmethod
    def init():
      if not ZlModel.db_ready():
        return

      for fill in Fill.objects.all():
        ZlModel.add_fill(fill)
      for order in Order.objects.all():
        ZlModel.add_order(order)
      for asset in Asset.objects.all():
        ZlModel.add_asset(asset)

    @staticmethod
    def update():
      if not ZlModel.db_ready():
        return

      md5 = md5_wrap(json.dumps({
        "fills":[x.md5() for x in Fill.objects.all()],
        "orders":[x.md5() for x in Order.objects.all()],
        "assets":{x.id: x.to_dict() for x in Asset.objects.all()},
      }))

      if ZlModel.md5==md5:
        logger.debug("Model unchanged .. not rerunning engine: "+md5)
        return

      logger.debug("Run matching engine: "+md5)

      matcher = mmm_Matcher()

      all_closed, all_txns, open_orders, unused = mmm_factory(
        matcher,
        ZlModel.fills_as_dict_df(),
        ZlModel.orders,
        ZlModel.assets
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
      ZlModel.zl_unused = unused

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

  def update_if_mine(sender):
    condition = sender.__name__=="Fill" or sender.__name__=="Order" or sender.__name__=="Asset"
    if condition:
      ZlModel.update()

  def post_save(sender, instance, **kwargs):
    #logger.debug("Signal: %s, %s" % ("post_save", sender))
    if sender.__name__=="Fill": ZlModel.add_fill(instance)
    if sender.__name__=="Order": ZlModel.add_order(instance)
    if sender.__name__=="Asset": ZlModel.add_asset(instance)
    SignalProcessor.update_if_mine(sender)

  def post_delete(sender, instance, **kwargs):
    #print("Signal: %s, %s" % ("post_delete", sender))
    if sender.__name__=="Fill": ZlModel.delete_fill(instance)
    if sender.__name__=="Order": ZlModel.delete_order(instance)
    if sender.__name__=="Asset": ZlModel.delete_asset(instance)
    SignalProcessor.update_if_mine(sender)

  def connection_created(sender, **kwargs):
  #  print("Signal: %s, %s" % ("connection_created", sender))
    ZlModel.init()
    ZlModel.update()

senders=("polls.Order", "polls.Fill", "polls.Asset")
for sender in senders:
  #models.signals.post_init.connect(SignalProcessor.post_init, sender=sender)
  models.signals.post_save.connect(SignalProcessor.post_save, sender=sender)
  models.signals.post_delete.connect(SignalProcessor.post_delete, sender=sender)
connection_created.connect(SignalProcessor.connection_created)

