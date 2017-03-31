import numpy
import pandas as pd

# initialize blotter
from zipline.finance.blotter import Blotter
#from zipline.finance.slippage import FixedSlippage
#slippage_func = FixedSlippage(spread=0.0)
from zipline.finance.slippage import VolumeShareSlippage
from zipline.finance.asset_restrictions import NoRestrictions
from zipline.finance.cancel_policy import NeverCancel
from zipline.gens.sim_engine import SESSION_END
from zipline.finance.order import ORDER_STATUS

# try to use a data portal
from zipline.data.data_portal import DataPortal
from zipline._protocol import BarData

# fills2reader
from datetime import datetime, timedelta
from six import iteritems
import os
#from zipline.data.us_equity_pricing import BcolzDailyBarReader, BcolzDailyBarWriter
from zipline.data.minute_bars import BcolzMinuteBarReader, BcolzMinuteBarWriter
from functools import reduce

# constructor
from zipline.utils.calendars import (
  get_calendar,
  register_calendar
)
from zipline.finance.trading import TradingEnvironment
import zipline.utils.factory as zl_factory

from zipline.utils.calendars import TradingCalendar
from datetime import time
from pytz import timezone as timezone_pytz
from django.utils import timezone as timezone_django

from zipline.utils.memoize import lazyval
from pandas.tseries.offsets import CustomBusinessDay

import logging
logger = logging.getLogger("zipline_app") # __name__)

from .signals import order_cancelled

def reduce_concatenate(list_of_lists):
  return reduce(
    lambda a, b: numpy.concatenate((a,b)),
    list_of_lists,
    []
  )

class AlwaysOpenExchange(TradingCalendar):
    """
    Exchange calendar for AlwaysOpenExchange
    """
    @property
    def name(self):
        return "AlwaysOpen"

    @property
    def tz(self):
        return timezone_pytz("UTC")

    @property
    def open_time(self):
        return time(0, 1)

    @property
    def close_time(self):
        return time(23, 59)

    @lazyval
    def day(self):
        # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#custom-business-days-experimental
        return CustomBusinessDay(
            holidays=[],
            calendar=None,
            weekmask='Sun Mon Tue Wed Thu Fri Sat'
        )

#aoe =AlwaysOpenExchange()
#print('is open',aoe.is_open_on_minute(pd.Timestamp('2013-01-07 15:03:00+0000', tz='UTC')))
register_calendar("AlwaysOpen",AlwaysOpenExchange())

# order validity enum
# similar to ORDER_STATUS: https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/order.py#L24
from zipline.utils.enum import enum
ORDER_VALIDITY = enum(
  'GTC',
  'GTD',
  'DAY'
)

# my own blotter/order class to allow for order validity
from zipline.finance.order import Order
class MyOrder(Order):
  def __init__(self, validity, *args, **kwargs):
    super(MyOrder,self).__init__(*args, **kwargs)
    self.validity = validity

class MyBlotter(Blotter):
  # Copied from original, with the difference of MyOrder instead of Order
  # https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L77
  def order(self, sid, amount, style, order_id=None, validity=None):
    if amount == 0:
        # Don't bother placing orders for 0 shares.
        return None
    elif amount > self.max_shares:
        # Arbitrary limit of 100 billion (US) shares will never be
        # exceeded except by a buggy algorithm.
        raise OverflowError("Can't order more than %d shares" %
                            self.max_shares)

    is_buy = (amount > 0)
    order = MyOrder(
        dt=self.current_dt,
        sid=sid,
        amount=amount,
        stop=style.get_stop_price(is_buy),
        limit=style.get_limit_price(is_buy),
        id=order_id,
        validity=validity
    )

    self.open_orders[order.sid].append(order)
    self.orders[order.id] = order
    self.new_orders.append(order)

    return order.id

########################
class Matcher:
  def __init__(self):
    self.env = TradingEnvironment()

    # prepare for data portal
    # from zipline/tests/test_finance.py#L238
    # Note that 2013-01-05 and 2013-01-06 were Sat/Sun
    # Also note that in UTC, NYSE starts trading at 14.30
    # TODO tailor for FFA Dubai
    #  start_date=pd.Timestamp('2013-12-08 9:31AM', tz='UTC'),
    START_DATE = pd.Timestamp('2013-01-01', tz='utc')
    END_DATE = pd.Timestamp(datetime.now(), tz='utc')
    self.sim_params = zl_factory.create_simulation_parameters(
        start = START_DATE,
        end = END_DATE,
        data_frequency="minute"
    )

    self.trading_calendar=get_calendar("AlwaysOpen")
  #  self.trading_calendar=get_calendar("NYSE")
   # self.trading_calendar=get_calendar("ICEUS")

  def get_minutes(self,fills,orders):
    if len(fills)==0 and len(orders)==0:
      return []

    # get fill minutes
    minutes_fills = [sid.index.values.tolist() for _, sid in fills.items()]
    minutes_fills = reduce_concatenate(minutes_fills)

    # get order minutes
    minutes_orders = [list(o.values()) for o in list(orders.values())]
    minutes_orders = [o["dt"] for o in reduce_concatenate(minutes_orders)]

    # concatenate
    #print("minutes",[type(x).__name__ for x in minutes])
    #print("minutes",minutes)
    minutes = numpy.concatenate((
      minutes_fills,
      minutes_orders
    ))

    minutes = [pd.Timestamp(x, tz='utc') for x in minutes]
    minutes = list(set(minutes))
    minutes.sort()
    #print("minutes",minutes)
    return minutes

  @staticmethod
  def chopSeconds(fills, orders):
    for sid in fills:
      # for fills, start by adding a floored-minute "index" column, and group by it
      # Combination of
      #    http://stackoverflow.com/a/34297689/4126114
      #    http://stackoverflow.com/a/29583335/4126114
      fills[sid] = fills[sid].reset_index()
      fills[sid]['dt_fl'] = [dt.floor('1Min') for dt in fills[sid]['dt']]
      del fills[sid]['dt']

      # group in preparation of aggregation
      # http://pandas.pydata.org/pandas-docs/stable/groupby.html#applying-different-functions-to-dataframe-columns
      grouped = fills[sid].groupby('dt_fl')

      # weighted-average of price
      # http://stackoverflow.com/a/35327787/4126114
      grouped_close = grouped.apply(lambda g: numpy.average(g['close'],weights=g['volume']))
      grouped_close = pd.DataFrame({'close':grouped_close})

      # add all volumes of fills at the same minute
      grouped_volume = grouped['volume'].aggregate('sum')
      grouped2 = pd.concat([grouped_close, grouped_volume], axis=1)

      # go back to original indexing
      # http://pandas.pydata.org/pandas-docs/stable/groupby.html#aggregation
      grouped2.reset_index().set_index('dt_fl')
      grouped2.sort_index(inplace=True)

      # replace original
      fills[sid] = grouped2

    # For orders, just floor the minute
    for sid in orders:
      for oid,order in orders[sid].items():
        order["dt"]=pd.Timestamp(order["dt"],tz="utc").floor('1Min')

    #print("chop seconds fills ", fills)
    #print("chop seconds orders", orders)
    return fills, orders

  def fills2reader(self, tempdir, minutes, fills, orders):
    if len(minutes)==0:
      return None

    for _,fill in fills.items():
      fill["open"] = fill["close"]
      fill["high"] = fill["close"]
      fill["low"]  = fill["close"]

      # since the below abs affects the original dataframe, storing the sign for later revert
      fill["is_neg"] = fill["volume"]<0

      # take absolute value, since negatives are split in the factory function to begin with
      # and zipline doesnt support negative OHLC volumes (which dont make sense anyway)
      fill["volume"] = abs(fill["volume"])

    # append empty OHLC dataframes for sid's in orders but not (yet) in fills
    # dummy OHLC data with volume=0 so as not to affect orders
    empty = {"open":[0], "high":[0], "low":[0], "close":[0], "volume":[0], "dt":[minutes[0]], "is_neg":[False]}
    for sid in orders:
      if sid not in fills:
        fills[sid]=pd.DataFrame(empty).set_index("dt")

    d1 = self.trading_calendar.minute_to_session_label(
      minutes[0]
    )
    d2=self.trading_calendar.minute_to_session_label(
      minutes[-1]
    )
    days = self.trading_calendar.sessions_in_range(d1, d2)
    #print("minutes",minutes)
    #print("days: %s, %s, %s" % (d1, d2, days))

    #path = os.path.join(tempdir.path, "testdata.bcolz")
    path = tempdir.path
    writer = BcolzMinuteBarWriter(
      rootdir=path,
      calendar=self.trading_calendar,
      start_session=days[0],
      end_session=days[-1],
      minutes_per_day=1440
    )
    #print("Writer session labels: %s" % (writer._session_labels))
    #print('last date for sid 1', writer.last_date_in_output_for_sid(1))
    #print('last date for sid 2', writer.last_date_in_output_for_sid(2))
    #for f in iteritems(fills): print("fill",f)
    writer.write(iteritems(fills))

    # now that the data is written, revert the volume sign and drop the extra columns
    for _,fill in fills.items():
      del fill["open"]
      del fill["high"]
      del fill["low"]
      if any(fill["is_neg"]):
        fill.loc[fill["is_neg"],"volume"] = -1 * fill["volume"]
      del fill["is_neg"]

    #print("temp path: %s" % (path))
    reader = BcolzMinuteBarReader(path)

    return reader

  # save an asset
  def write_assets(self, assets: dict):
    # unique assets by using sid
    # http://stackoverflow.com/a/11092590/4126114
    if not any(assets):
      #raise ValueError("Got empty orders!")
      return

    # make assets unique by "symbol" field also
    assets2 = { a["symbol"]: {"k":k,"a":a} for k,a in assets.items() }
    assets2  = {v["k"]: v["a"] for v in assets2.values() }

    # log dropped sid's
    dropped = [k for k in assets.keys() if k not in assets2.keys()]
    if len(dropped)>0: logger.error("Dropped asset ID with duplicated symbol: %s" % dropped)

    assets = assets2

    # check zipline/zipline/assets/asset_writer.py#write
    df = pd.DataFrame(
        {
          "sid"       : list(assets.keys()),
          "exchange"  : [asset["exchange"] for asset in list(assets.values())],
          "symbol"    : [asset["symbol"] for asset in list(assets.values())],
          "asset_name": [asset["name"] for asset in list(assets.values())],
        }
    ).set_index("sid")
    #print("write data",df)
    self.env.write_data(equities=df)

  def get_blotter(self):
    slippage_func = VolumeShareSlippage(
      volume_limit=1,
      price_impact=0
    )
    blotter = MyBlotter(
      data_frequency=self.sim_params.data_frequency,
      asset_finder=self.env.asset_finder,
      slippage_func=slippage_func,
      # https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/tests/test_blotter.py#L136
      cancel_policy=NeverCancel()
    )
    return blotter

  def _orders2blotter(self, orders, blotter):
    #print("Place orders")
    for sid in orders:

      # append 'id' in object, otherwise it will be lost after the sorting
      for oid,order in orders[sid].items():
        order["id"]=oid

      # sort by field
      # http://stackoverflow.com/questions/72899/ddg#73050
      orders2 = sorted(orders[sid].values(), key=lambda k: k['dt'])

      for order in orders2:
        # 2017-02-17: Actually it's a good idea to allo orders to match with earlier fill
        #             It allows to assign extra fills to an error account for example, or to another client
        #             Note that this is coupled with:
        #             - moving the _orders2blotter out of the for loop in match_orders_fills
        #             - adding the blotter.set_date below
        #             - sorting the orders by ascending time above
        # 2017-02-15: skip orders in the future
        #if order["dt"] > blotter.current_dt:
        #  #logger.debug("Order in future skipped: %s" % order)
        #  continue
        #if oid in blotter.orders:
        #  #logger.debug("Order already included: %s" % order)
        #  continue
        blotter.set_date(order["dt"])

        #logger.debug("Order included: %s" % order)
        asset = self.env.asset_finder.retrieve_asset(sid=sid, default_none=True)

        blotter.order(
          sid=asset,
          amount=order["amount"],
          style=order["style"],
          order_id = order["id"],
          validity = None if "validity" not in order else order["validity"]
        )

    #print("Open orders: %s" % ({k.symbol: len(v) for k,v in iteritems(blotter.open_orders)}))
    return blotter

  def blotter2bardata(self, equity_minute_reader, blotter):
    if equity_minute_reader is None:
      return None

    dp = DataPortal(
      asset_finder=self.env.asset_finder,
      trading_calendar=self.trading_calendar,
      first_trading_day=equity_minute_reader.first_trading_day,
      equity_minute_reader=equity_minute_reader
    )

    restrictions=NoRestrictions()

    bd = BarData(
      data_portal=dp,
      simulation_dt_func=lambda: blotter.current_dt,
      data_frequency=self.sim_params.data_frequency,
      trading_calendar=self.trading_calendar,
      restrictions=restrictions
    )

    return bd

  # Cannot use zipline cancellation policy based on order expiration type, expiration date, and current date because it will cancel all orders (and not filter based on type)
  # Will use cancel orders one-by-one instead, with the NeverCancel being the default
  #
  # Definition of cancellation policies
  # https://github.com/quantopian/zipline/blob/e1b27c45ae4b881e5416a5c50e8945232527ea59/zipline/finance/cancel_policy.py
  #
  # Execution of cancellation policy cancels all
  # https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L238
  def _cancel_expired(self, blotter):
    #print('*'*100)
    for asset, orders in iteritems(blotter.open_orders):
      order_ids = [order.id for order in orders]
      #print('order ids', order_ids)
      for order_id in order_ids:
        order = blotter.orders[order_id]
        # cancel past day orders .. necessary if the latest open order s in the past
        logger.debug('0. look to cancel order %s, now: %s, blotter: %s, order: %s'%(order.id, timezone_django.now().day, blotter.current_dt.day, order.dt.day))
        if timezone_django.now().day != blotter.current_dt.day:
          if order.validity is not None:
            if order.validity['type']==ORDER_VALIDITY.DAY:
              if order.dt.day != timezone_django.now().day:
                logger.debug('1. will cancel order %s %s %s'%(order.id, timezone_django.now().day, blotter.current_dt.day))
                blotter.cancel(order.id)
                continue

        # do not cancel orders not reached yet with the clock
        if order.dt > blotter.current_dt:
          continue

        # treat orders without a validity as GTC orders
        if order.validity is None:
          continue

        if order.validity['type']==ORDER_VALIDITY.GTC:
          continue
        if order.validity['type']==ORDER_VALIDITY.GTD:
          if order.validity['date'] < blotter.current_dt:
            logger.debug('2. will cancel order %s'%order.id)
            blotter.cancel(order.id)
          continue
        if order.validity['type']==ORDER_VALIDITY.DAY:
          if order.dt.day != blotter.current_dt.day:
            logger.debug('3. will cancel order %s'%order.id)
            blotter.cancel(order.id)
          continue
        raise ValueError("Invalid order validity type used: %s"%order.validity['type'])

  def match_orders_fills(self, blotter, bar_data, all_minutes, orders):
    all_closed = []
    all_txns = []
    self._orders2blotter(orders,blotter)
    #print('all mins', all_minutes)
    for dt in all_minutes:
        logger.debug("======================== %s"%dt)
        dt = pd.Timestamp(dt, tz='utc')
        blotter.set_date(dt)

        self._cancel_expired(blotter)

        #self._orders2blotter(orders,blotter)
        #logger.debug("DQ1: %s" % (blotter.current_dt))
        #logger.debug("DQ6: %s" % blotter.open_orders)
        new_transactions, new_commissions, closed_orders = blotter.get_transactions(bar_data)

        #logger.debug("Closed orders: %s" % (len(closed_orders)))
        #for order in closed_orders:
        #  logger.debug("Closed orders: %s" % (order))
  
        #logger.debug("Transactions: %s" % (len(new_transactions)))
        #for txn in new_transactions:
        #  logger.debug("Transactions: %s" % (txn.to_dict()))
  
        #logger.debug("Commissions: %s" % (len(new_commissions)))
        #for txn in new_commissions:
        #  logger.debug("Commissions: %s" % (txn))

        blotter.prune_orders(closed_orders)
        ##logger.debug("Open orders: %s" % (len(blotter.open_orders[a1])))
        ##logger.debug("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

        all_closed = numpy.concatenate((all_closed,closed_orders))
        all_txns = numpy.concatenate((all_txns, new_transactions))

    # https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/tests/test_blotter.py#L154
    for order in blotter.orders.values():
      if order.status==ORDER_STATUS.CANCELLED:
        order_cancelled.send(sender=None, id=order.id)

    return all_closed, all_txns

  # check if any volume was not used for the orders yet
  def unused_fills(self,all_txns,fills):
    unused = {}
    for sid, fill in fills.items():
      sub = [x.amount for x in all_txns if x.sid.sid==sid]
      extra = fill.volume.sum() - sum(sub)
      if extra!=0:
        asset = self.env.asset_finder.retrieve_asset(sid=sid,default_none=True)
        # if the asset was already dropped because it was a duplicate, ignore
        if asset is None:
          logger.warning("Ignoring asset "+str(sid)+" as it was not imported into ZlModel (possible duplicate symbol?)")
          continue
        unused[asset]=extra
    return unused

  @staticmethod
  def filterBySign(mySign, fills_all, orders_all):
    fills_sub ={}
    orders_sub={}

    for sid in fills_all:
      condition = fills_all[sid]['volume']*mySign > 0
      filtered = fills_all[sid][condition]
      if len(filtered)>0:
        # Need .copy
        # http://stackoverflow.com/a/32682095/4126114
        fills_sub[sid]=filtered.copy()

    for sid in orders_all:
      filtered = {}
      for oid, order in orders_all[sid].items():
        if order['amount']*mySign>0:
          filtered[oid]=order
      if len(filtered)>0:
        orders_sub[sid]=filtered

    return fills_sub, orders_sub


from testfixtures import TempDirectory

def factory(matcher: Matcher, fills_all: dict, orders_all: dict, assets: dict):
  matcher.write_assets(assets)

  all_closed=[]
  all_txns=[]
  all_open_orders={}
  all_minutes=[]
  all_unused={}

  for mySign in [-1,+1]:
    logger.debug('matcher factory for sign: %s'%mySign)
    fills_sub, orders_sub = Matcher.filterBySign(mySign, fills_all, orders_all)
    # eventhough the orders/fills models contain their own floored-minute value,
    # flooring here again as a safety measure
    fills_sub, orders_sub = Matcher.chopSeconds(fills_sub, orders_sub)

    with TempDirectory() as tempdir:
      sub_closed, sub_txns, open_orders_sub, sub_unused, sub_minutes = _factory_sub(matcher, fills_sub, orders_sub, assets)

      all_txns = numpy.concatenate((all_txns, sub_txns))
      all_closed = numpy.concatenate((all_closed, sub_closed))
      for sid, ordersList in open_orders_sub.items():
        if sid not in all_open_orders:
          all_open_orders[sid]=ordersList
          continue
        all_open_orders[sid] = numpy.concatenate((all_open_orders[sid],ordersList))
      for sid, nf in sub_unused.items():
        if sid not in all_unused:
          all_unused[sid]=[nf]
          continue
        all_unused[sid].append(nf)

      all_minutes = numpy.concatenate((all_minutes, sub_minutes))

  all_minutes = list(set(all_minutes)) # make unique list
  return all_closed, all_txns, all_open_orders, all_unused, all_minutes

def _factory_sub(matcher: Matcher, fills: dict, orders: dict, assets: dict):
  with TempDirectory() as tempdir:
    all_minutes = matcher.get_minutes(fills,orders)
    equity_minute_reader = matcher.fills2reader(tempdir, all_minutes, fills, orders)
    blotter = matcher.get_blotter()
    bd = matcher.blotter2bardata(equity_minute_reader, blotter)
    all_closed, all_txns = matcher.match_orders_fills(blotter, bd, all_minutes, orders)

  unused = matcher.unused_fills(all_txns, fills)
  return all_closed, all_txns, blotter.open_orders, unused, all_minutes
