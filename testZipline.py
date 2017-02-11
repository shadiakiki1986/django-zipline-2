# https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123
import pandas as pd
from zipline.finance.order import Order
from zipline.finance.execution import (
    LimitOrder,
    MarketOrder,
    StopLimitOrder,
    StopOrder,
)
from zipline.assets import Asset

#  start_date=pd.Timestamp('2013-12-08 9:31AM', tz='UTC'),
START_DATE = pd.Timestamp('2006-01-05', tz='utc')

# https://github.com/quantopian/zipline/blob/cbe66903a93accf462a10d6704caa9b16058e77d/tests/test_assets.py#L105
a1=Asset(
  sid=1,
  exchange='bla',
  symbol='bla',
  asset_name='bla',
)
#amount=1
#is_buy=True
#order_id=1
#style=MarketOrder()
#o1 = Order(
#    dt=START_DATE,
#    sid=a1,
#    amount=amount,
#    stop=style.get_stop_price(is_buy),
#    limit=style.get_limit_price(is_buy),
#    id=order_id
#)
#print(o1)

#####################################
from zipline.finance.trading import TradingEnvironment
env = TradingEnvironment()

# save an asset
df = pd.DataFrame(
    {  
      "sid":1,
      "exchange":'bla',
      "symbol":'bla',
      "asset_name":'bla',
    },
    index=[1],
)
env.write_data(equities=df)

# initialize blotter
from zipline.finance.blotter import Blotter
from zipline.finance.slippage import FixedSlippage
blotter = Blotter(data_frequency='daily',asset_finder=env.asset_finder, slippage_func=FixedSlippage())

print("Start")
blotter.set_date(pd.Timestamp('2006-01-05', tz='utc'))
print(blotter.current_dt)

print("Order a1 +10")
o1=blotter.order(a1,10,MarketOrder())
print("Open orders: %s" % (len(blotter.open_orders[a1])))

print("Order a1 +10 and +10")
o2=blotter.order(a1,10,MarketOrder())
o3=blotter.order(a1,10,MarketOrder())
print("Open orders: %s" % (len(blotter.open_orders[a1])))

print("Cancel o2")
blotter.cancel(o2)
print("Open orders: %s" % (len(blotter.open_orders[a1])))
print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

print("Fill 5")
blotter.open_orders[a1][0].filled+=5
print("Open orders: %s" % (len(blotter.open_orders[a1])))
print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

print("Fill 5")
blotter.open_orders[a1][0].filled+=5
print("Open orders: %s" % (len(blotter.open_orders[a1])))
print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

print("Fill 5 extra")
blotter.open_orders[a1][0].filled+=5
print("Open orders: %s" % (len(blotter.open_orders[a1])))
print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

# try to use a data portal
from zipline.data.data_portal import DataPortal
from zipline.utils.calendars import get_calendar
dp = DataPortal(asset_finder=env.asset_finder, trading_calendar=get_calendar("NYSE"), first_trading_day=None)
from zipline._protocol import BarData
def simulation_dt_func():
  return START_DATE

bd = BarData(data_portal=dp,simulation_dt_func=simulation_dt_func,data_frequency='daily',trading_calendar=get_calendar("NYSE"))
blotter.get_transactions(bd)
print("Open orders: %s" % (len(blotter.open_orders[a1])))
print("Open order status: %s" % ([o.open for o in blotter.open_orders[a1]]))

print("Prune")
blotter.prune_orders([blotter.open_orders[a1][0]])
print("Open orders: %s" % (len(blotter.open_orders[a1])))

