from django.test import TestCase
import pandas as pd
from ...matcher import factory as mmm_factory, Matcher as mmm_Matcher
from ...matcher import reduce_concatenate
from .other import a1,a2

from zipline.finance.execution import (
    MarketOrder,
)

class MatcherMethodTests(TestCase):

    def test_chopSeconds_dropsSeconds(self):
        sec_yes = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        sec_non = pd.Timestamp('2017-02-13 05:13', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5],
                "volume": [1],
                "dt": [sec_yes]
            }).set_index("dt")
        }
        orders = {
          1: {
            1: {"dt": sec_yes},
          }
        }
        actual_fills, actual_orders = mmm_Matcher.chopSeconds(fills, orders)

        self.assertEqual(actual_fills[1].index, [sec_non])
        asList = reduce_concatenate([list(o.values()) for o in list(actual_orders.values())])
        self.assertEqual([x["dt"] for x in asList], [sec_non])

    def test_chopSeconds_aggregatesFillsInSameMinute(self):
        sec1 = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        sec2 = pd.Timestamp('2017-02-13 05:13:24', tz='utc')
        sec_non = pd.Timestamp('2017-02-13 05:13', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [1,3],
                "volume": [1,3],
                "dt": [sec1,sec2]
            }).set_index("dt")
        }
        orders = {}
        actual_fills, actual_orders = mmm_Matcher.chopSeconds(fills, orders)

        self.assertEqual(actual_fills[1].index, [sec_non])
        self.assertEqual(actual_fills[1][sec_non]['close' ], 2.5)
        self.assertEqual(actual_fills[1][sec_non]['volume'], 4)

    def test_factory_some_orders_and_some_fills(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        # seconds in below timestamp will be floored
        MID_DATE_4 = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5, 4.5, 4, 2.4],
                "volume": [10, 5, 7, 1],
                "dt": [MID_DATE_1,MID_DATE_2,MID_DATE_3,MID_DATE_4]
            }).set_index("dt"),
            2: pd.DataFrame({
                "close": [3.5],
                "volume": [1],
                "dt": [MID_DATE_4]
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          },
          2: {
            4: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1: a1, 2: a2}

        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(6,len(all_txns))
        self.assertEqual(2,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(1,len(open_orders[a1a]))

#        print("========================")
#        print("Remaining open")
#        #blotter.cancel(o3)
#        print("Open orders: %s" % (len(blotter.open_orders[a1])))
#        print("Open order status: %s" % ([[o.amount,o.filled,o.open] for o in blotter.open_orders[a1]]))
#
#        print("========================")
#        print("All closed orders:")
#        for cl in all_closed:
#          print(cl)
#
#        print("========================")
#        print("All transactions:")
#        for txn in [txn.to_dict() for txn in all_txns]:
#          print(txn)

    def test_factory_no_orders_and_no_fills(self):
        matcher = mmm_Matcher()
        fills = {}
        orders = {}
        assets = {}
        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_some_orders_and_no_fills(self):
        matcher = mmm_Matcher()

        fills={}

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(1,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(3,len(open_orders[a1a]))

    def test_factory_no_orders_and_some_fills(self):
        matcher = mmm_Matcher()

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
        #print("data: %s" % (fills))

        orders = {
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(0,len(all_closed))
        self.assertEqual(0,len(all_txns))
        self.assertEqual(0,len(open_orders))

    def test_factory_unsorted_input(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        MID_DATE_3 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        # seconds in below timestamp will be floored
        MID_DATE_4 = pd.Timestamp('2017-02-13 05:13:23', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [3.5, 4.5, 4, 2.4],
                "volume": [10, 5, 7, 1],
                "dt": [MID_DATE_1,MID_DATE_2,MID_DATE_4,MID_DATE_3]
            }).set_index("dt")
        }
        #print("data: %s" % (fills))

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:00', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            2: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
            3: {"dt": MID_DATE_0, "amount": 10, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(2,len(all_closed))
        self.assertEqual(5,len(all_txns))
        self.assertEqual(1,len(open_orders))

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(1,len(open_orders[a1a]))

    def test_write_assets(self):
        matcher = mmm_Matcher()
        assets = {1:a1, 2:a2}
        matcher.write_assets(assets)
        # the below would fail if not found .. shouldnt fail in this case
        found = matcher.env.asset_finder.lookup_symbol(symbol=a1["symbol"], as_of_date=None)
        self.assertEqual(a1["symbol"],found.symbol)

        found = matcher.env.asset_finder.lookup_symbol(symbol=a2["symbol"], as_of_date=None)
        self.assertEqual(a2["symbol"],found.symbol)

    def test_factory_fills_before_orders(self):
        matcher = mmm_Matcher()

        # Use same sid as for assets above
        # NOT Multiplying by 1000 as documented in zipline/data/minute_bars.py#L419
        MID_DATE_1 = pd.Timestamp('2013-01-07 17:01', tz='utc')
        MID_DATE_2 = pd.Timestamp('2013-01-07 17:03', tz='utc')
        fills = {
            1: pd.DataFrame({
                "close": [1, 2],
                "volume": [5, 5],
                "dt": [MID_DATE_1,MID_DATE_2]
            }).set_index("dt"),
        }

        MID_DATE_0 = pd.Timestamp('2013-01-07 17:02', tz='utc')
        orders = {
          1: {
            1: {"dt": MID_DATE_0, "amount": 5, "style": MarketOrder()},
          }
        }

        assets = {1:a1}

        all_closed, all_txns, open_orders, unused, all_minutes = mmm_factory(matcher, fills, orders, assets)

        self.assertEqual(1,len(all_closed))
        self.assertEqual(1,len(all_txns))
        self.assertEqual(0,len(open_orders))

        txn = all_txns[0].to_dict()
        self.assertEqual(txn["price"], 2)

        a1a=matcher.env.asset_finder.retrieve_asset(sid=1)
        self.assertEqual(unused, {a1a:5})
