# https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123
import pandas as pd
from app.polls.matcher import Matcher
from zipline.finance.execution import (
    MarketOrder,
)
#####################################
from testfixtures import TempDirectory

with TempDirectory() as tempdir:

  matcher = Matcher()
  a1=matcher.env.asset_finder.retrieve_asset(sid=1)
 
  # Use same sid as for assets above
  # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
  MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
  MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
  MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
  fills = {
      1: pd.DataFrame({
  	"close": [3.5, 4.5, 4],
  	"volume": [10, 5, 7],
  	"dt": [MID_DATE_1,MID_DATE_2,MID_DATE_3]
      }).set_index("dt")
  }
  print("data: %s" % (fills))

  all_minutes = matcher.fills2minutes(fills)
  equity_minute_reader = matcher.fills2reader(tempdir, all_minutes, fills)
 
  MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
  orders = [
    {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
    {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
    {"dt": MID_DATE_0, "sid": a1, "amount": 10, "style": MarketOrder()},
  ]

  blotter = matcher.orders2blotter(orders)
 
  bd = matcher.blotter2bardata(equity_minute_reader, blotter)
  all_closed, all_txns = matcher.match_orders_fills(blotter, bd, all_minutes, fills)

  print("========================")
  print("Remaining open")
  #blotter.cancel(o3)
  print("Open orders: %s" % (len(blotter.open_orders[a1])))
  print("Open order status: %s" % ([[o.amount,o.filled,o.open] for o in blotter.open_orders[a1]]))

  print("========================")
  print("All closed orders:")
  for cl in all_closed:
    print(cl)

  print("========================")
  print("All transactions:")
  for txn in [txn.to_dict() for txn in all_txns]:
    print(txn)
