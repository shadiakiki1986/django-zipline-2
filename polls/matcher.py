import numpy
import pandas as pd

# initialize blotter
from zipline.finance.blotter import Blotter
#from zipline.finance.slippage import FixedSlippage
#slippage_func = FixedSlippage(spread=0.0)
from zipline.finance.slippage import VolumeShareSlippage

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
from pytz import timezone

from zipline.utils.memoize import lazyval
from pandas.tseries.offsets import CustomBusinessDay

import logging
logger = logging.getLogger(__name__)

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
        return timezone("UTC")

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
      index=[dt.floor('1Min') for dt in fills[sid].index]
      fills[sid].index = index
      fills[sid].sort_index(inplace=True)

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

    # append empty OHLC dataframes for sid's in orders but not (yet) in fills
    # dummy OHLC data with volume=0 so as not to affect orders
    empty = {"open":[0], "high":[0], "low":[0], "close":[0], "volume":[0], "dt":[minutes[0]]}
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
    blotter = Blotter(
      data_frequency=self.sim_params.data_frequency,
      asset_finder=self.env.asset_finder,
      slippage_func=slippage_func
    )
    return blotter

  def _orders2blotter(self, orders, blotter):
    #print("Place orders")
    for sid in orders:
      for oid, order in orders[sid].items():
        # skip orders in the future
        if order["dt"] > blotter.current_dt:
          #logger.debug("Order in future skipped: %s" % order)
          continue

        if oid in blotter.orders:
          #logger.debug("Order already included: %s" % order)
          continue

        #logger.debug("Order included: %s" % order)
        asset = self.env.asset_finder.retrieve_asset(sid=sid, default_none=True)

        blotter.order(
          sid=asset,
          amount=order["amount"],
          style=order["style"],
          order_id = oid
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

    bd = BarData(
      data_portal=dp,
      simulation_dt_func=lambda: blotter.current_dt,
      data_frequency=self.sim_params.data_frequency,
      trading_calendar=self.trading_calendar
    )

    return bd

  def match_orders_fills(self, blotter, bar_data, all_minutes, orders):
    all_closed = []
    all_txns = []
    for dt in all_minutes:
        #print("========================")
        dt = pd.Timestamp(dt, tz='utc')
        blotter.set_date(dt)
        self._orders2blotter(orders,blotter)
        #print("DQ1: %s" % (blotter.current_dt))
        #print("DQ6", blotter.open_orders)
        new_transactions, new_commissions, closed_orders = blotter.get_transactions(bar_data)

  #      print("Closed orders: %s" % (len(closed_orders)))
  #      for order in closed_orders:
  #        print("Closed orders: %s" % (order))
  #
  #      print("Transactions: %s" % (len(new_transactions)))
  #      for txn in new_transactions:
  #        print("Transactions: %s" % (txn.to_dict()))
  #
  #      print("Commissions: %s" % (len(new_commissions)))
  #      for txn in new_commissions:
  #        print("Commissions: %s" % (txn))

        blotter.prune_orders(closed_orders)
        #print("Open orders: %s" % (len(blotter.open_orders[a1])))
        #print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

        all_closed = numpy.concatenate((all_closed,closed_orders))
        all_txns = numpy.concatenate((all_txns, new_transactions))

    return all_closed, all_txns

  # check if any volume was not used for the orders yet
  def unused_fills(self,all_txns,fills):
    unused = {}
    for sid, fill in fills.items():
      sub = [x.amount for x in all_txns if x.sid.sid==sid]
      extra = fill.volume.sum() - sum(sub)
      if extra>0:
        asset = self.env.asset_finder.retrieve_asset(sid=sid)
        unused[asset]=extra
    return unused

from testfixtures import TempDirectory

def factory(matcher: Matcher, fills: dict, orders: dict, assets: dict):
  fills, orders = Matcher.chopSeconds(fills, orders)
  matcher.write_assets(assets)

  with TempDirectory() as tempdir:
    all_minutes = matcher.get_minutes(fills,orders)
    equity_minute_reader = matcher.fills2reader(tempdir, all_minutes, fills, orders)
    blotter = matcher.get_blotter()
    bd = matcher.blotter2bardata(equity_minute_reader, blotter)
    all_closed, all_txns = matcher.match_orders_fills(blotter, bd, all_minutes, orders)
    unused = matcher.unused_fills(all_txns,fills)

  return all_closed, all_txns, blotter.open_orders, unused, all_minutes
