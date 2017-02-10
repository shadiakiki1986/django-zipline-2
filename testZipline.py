# https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123
from zipline.finance import Order
START_DATE = pd.Timestamp('2006-01-05', tz='utc')
sid=1
amount=1
is_buy=True
order_id=1
o1 = new Order(
    dt=START_DATE,
    sid=sid,
    amount=amount,
    stop=style.get_stop_price(is_buy),
    limit=style.get_limit_price(is_buy),
    id=order_id
)
