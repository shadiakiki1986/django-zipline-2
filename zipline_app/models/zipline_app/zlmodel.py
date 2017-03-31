from __future__ import unicode_literals
from ...utils import md5_wrap, chopSeconds
from zipline.finance.execution import (
    LimitOrder,
    MarketOrder,
#    StopLimitOrder,
#    StopOrder,
)
from django.db import connection

# Django Logging
# https://docs.djangoproject.com/en/1.10/topics/logging/
import logging
logger = logging.getLogger('zipline_app.models') #__name__)

import json
from ...matcher import factory as mmm_factory, Matcher as mmm_Matcher, ORDER_VALIDITY
from functools import reduce

from numpy import concatenate
import pandas as pd
from .side import LIMIT, MARKET, OPEN, GTC, GTD, DAY
from django.core.cache import cache

# This is an adapter connecting the django model datastructures to the zipline datastructures
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
    all_minutes = []
    lock = False

    @staticmethod
    def clear():
      logger.debug("ZlModel: Clear")
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
      ZlModel.all_minutes=[]

    @staticmethod
    def add_asset(asset):
      logger.debug("adding asset %s" % asset)
      ZlModel.assets[asset.id]=asset.to_dict()

    # cannot use typehinting as
    # def add_fill(fill: Fill): ...
    # because then I would need to import .fill in this file
    # and fill.py already has an import.zlmodel
    # so this will become a cyclic dependency
    @staticmethod
    def add_fill(fill):
      if fill.dedicated_to_order is not None:
        logger.debug("Fill is dedicated. Not adding to zipline model (+ dropping its order that is already in zlmodel): %s",fill)
        order = fill.dedicated_to_order
        ZlModel.delete_order(fill.dedicated_to_order, True)

        # no need to trigger update here, since already triggered in signalsProcessor
        # ZlModel.update()
        return

      ZlModel.add_asset(fill.asset)

      logger.debug("Adding fill: %s" % fill)
      if fill.asset.id not in ZlModel.fills:
        ZlModel.fills[fill.asset.id]={}

      ZlModel.fills[fill.asset.id][fill.id]={
        "close": fill.fill_price,
        "volume": fill.fill_qty_signed(),
        "dt": pd.Timestamp(fill.pub_date,tz='utc')
      }

    @staticmethod
    def fills_as_dict_df():
      # Copy keys to a new dictionary (Python)
      # http://stackoverflow.com/a/7369284/4126114
      # http://www.tutorialspoint.com/python/dictionary_fromkeys.htm
      fills2=dict.fromkeys(ZlModel.fills.keys(), pd.DataFrame({}))

      for sid in ZlModel.fills:
        # sub loses the fill id because of values
        sub = ZlModel.fills[sid].values()
        fills2[sid] = fills2[sid].append(pd.DataFrame({
          "close" : [y["close"] for y in sub],
          "volume": [y["volume"] for y in sub],
          "dt"    : [y["dt"] for y in sub],
        })).set_index("dt")

      return fills2

    @staticmethod
    def validity_django2zipline(validity):
      if validity==GTC:
        return ORDER_VALIDITY.GTC
      if validity==GTD:
        return ORDER_VALIDITY.GTD
      if validity==DAY:
        return ORDER_VALIDITY.DAY
      raise ValueError("Invalid validity: %s"%validity)

    # note that this method also edits existing orders
    @staticmethod
    def add_order(order):
      if order.order_status != OPEN:
        logger.debug("Not adding non-open order %s" % order)
        # check if already added before and status changed
        ZlModel.delete_order(order, True)
        return

      ZlModel.add_asset(order.asset)

      logger.debug("Add order %s" % order)
      if order.asset.id not in ZlModel.orders:
        ZlModel.orders[order.asset.id]={}

      style = None
      if order.order_type == LIMIT:
        style = LimitOrder(order.limit_price)
      else:
        if order.order_type == MARKET:
          style = MarketOrder()
        else:
          raise ValueError('Unsupported order type: %s'%order.order_type)

      ZlModel.orders[order.asset.id][order.id] = {
        "dt": order.pub_date,
        "asset": order.asset.id,
        "amount": order.order_qty_signed(),
        "style": style,
        "validity": {
          "type": ZlModel.validity_django2zipline(order.order_validity),
          "date": order.validity_date
        }
      }

    @staticmethod
    def delete_asset(asset):
      c_ord = asset.id in ZlModel.orders and any(ZlModel.orders[asset.id])
      c_fil = asset.id in ZlModel.fills and any(ZlModel.fills[asset.id])
      if c_ord or c_fil:
        logger.debug("Will not delete asset (used in order/fill): %s"%asset)
        return
      logger.debug("Delete asset %s" % asset)
      ZlModel.assets.pop(asset.id, None)
      ZlModel.fills.pop(asset.id, None)
      ZlModel.orders.pop(asset.id, None)

    @staticmethod
    def delete_fill(fill):
      if fill.dedicated_to_order is not None:
        # re-add the order since it was dropped with this fill
        ZlModel.add_order(fill.dedicated_to_order)
        return

      logger.debug("Delete fill %s" % fill)
      # How to remove a key from a python dictionary
      # http://stackoverflow.com/questions/11277432/ddg#11277439
      ZlModel.fills[fill.asset.id].pop(fill.id, None)
      if not any(ZlModel.fills[fill.asset.id]):
        ZlModel.fills.pop(fill.asset.id, None)
        ZlModel.delete_asset(fill.asset)

    @staticmethod
    def delete_order(order, force:bool=False):
      if order.dedicated_fill() is not None and not force:
        return

      if order.asset.id in ZlModel.orders:
        logger.debug("Delete order %s" % order.id)
        ZlModel.orders[order.asset.id].pop(order.id, None)
        if not any(ZlModel.orders[order.asset.id]):
          ZlModel.orders.pop(order.asset.id, None)
          ZlModel.delete_asset(order.asset)

    @staticmethod
    def db_ready():
      tables = connection.introspection.table_names()
      isready = "zipline_app_fill" in tables
      if not isready:
        logger.debug("db tables not available .. skipping zlmodel init")
      return isready

    @staticmethod
    def init(fills, orders):
      if not ZlModel.db_ready():
        return

      logger.debug("Initializing. %s vs %s" % (fills, ZlModel.fills))
      for order in orders:
        ZlModel.add_order(order)
      # important to run add_fill after add_order for the dedicated fills
      for fill in fills:
        ZlModel.add_fill(fill)

    @staticmethod
    def calculate_md5():
      md5_orders = []
      for sid,o1 in ZlModel.orders.items():
        for oid,o2 in o1.items():
          # No need for "account" here
          # since orders for 2 different accounts will have 2 different IDs anyway.
          # Also, order_text is not passed to the engine anyway
          md5_orders.append(
            "%s, %s, %s, %s, %s" % (
              chopSeconds(o2["dt"]), # use second-less timestamp to avoid re-run engine due to cleaning
              sid,
              o2["amount"],
              o2["style"].__class__.__name__, # use class name to avoid memory address changing => rerun engine
              o2["validity"],
            )
          )

      md5_fills = []
      for sid, f1 in ZlModel.fills.items():
        for fill_id, fill in f1.items():
          md5_fills.append(
            "%s, %s, %s, %s" % (
              sid,
              fill["volume"],
              fill["close"],
              fill_id
            )
          )
          
      md5 = md5_wrap(json.dumps({
        "fills" : md5_fills,
        "orders": md5_orders,
        "assets": ZlModel.assets,
      }))
      return md5

    @staticmethod
    def update():
      if not ZlModel.db_ready():
        return
      if ZlModel.lock:
        logger.debug("ZlModel locked. Caching request to update")
        cache.set('zl_update', True, None)
        return

      md5 = ZlModel.calculate_md5()
      #print('md5 vs md5', md5, ZlModel.md5)
      if ZlModel.md5==md5:
        logger.debug("Model unchanged .. not rerunning engine: "+md5)
        return

      logger.debug("Run matching engine: "+md5)
      ZlModel.lock=True

      matcher = mmm_Matcher()

      all_closed, all_txns, open_orders, ZlModel.zl_unused, ZlModel.all_minutes = mmm_factory(
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

      # save md5 at the end to ensure re-run if error occured
      ZlModel.md5=md5
      ZlModel.lock=False
      logger.debug("end of run engine")
      reUpdate = cache.get('zl_update')
      if reUpdate is not None and reUpdate:
        logger.debug('there was a request to update in the mean time')
        cache.set('zl_update',False)
        ZlModel.update()
