import numpy
import pandas as pd

# initialize blotter
from zipline.finance.blotter import Blotter
#from zipline.finance.slippage import FixedSlippage
#slippage_func = FixedSlippage(spread=0.0)
from zipline.finance.slippage import VolumeShareSlippage

from zipline.finance.execution import (
    MarketOrder,
)

class Matcher:
  def orders2blotter(self, sim_params, env, orders):
    slippage_func = VolumeShareSlippage(
      volume_limit=1,
      price_impact=0
    )
    blotter = Blotter(
      data_frequency=sim_params.data_frequency,
      asset_finder=env.asset_finder,
      slippage_func=slippage_func
    )
    
    print("-----------------------")
    print("Place orders")
    a1=env.asset_finder.retrieve_asset(sid=1)
    MID_DATE_0 = pd.Timestamp('2013-01-07 15:00', tz='utc')
    blotter.set_date(MID_DATE_0)
    print(blotter.current_dt)
  
    print("Order a1 +10")
    o1=blotter.order(a1,10,MarketOrder())
    print("Open orders: %s" % (len(blotter.open_orders[a1])))
    
    print("Order a1 +10 and +10")
    o2=blotter.order(a1,10,MarketOrder())
    o3=blotter.order(a1,10,MarketOrder())
    return blotter
   
  def match_orders_fills(self,blotter,bar_data,fills):
    all_closed = []
    all_txns = []
    for _,sid in fills.items():
      for dt in sid.index.values:
        print("========================")
        dt = pd.Timestamp(dt, tz='utc')
        blotter.set_date(dt)
        print("use data portal to dequeue open orders: %s" % (blotter.current_dt))
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
