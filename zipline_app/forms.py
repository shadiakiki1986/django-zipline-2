from django.forms import ModelForm
from .models.zipline_app.order import Order
from .models.zipline_app.fill import Fill
from .models.zipline_app.asset import Asset
from .models.zipline_app.account import Account

class OrderForm(ModelForm):
  class Meta:
    model = Order
    fields = ['pub_date','asset','amount','account','order_text']

class FillForm(ModelForm):
  class Meta:
    model = Fill
    fields = ['pub_date','asset','fill_qty','fill_price','fill_text','tt_order_key']

class AssetForm(ModelForm):
  class Meta:
    model = Asset
    fields = ['asset_symbol','asset_exchange','asset_name']

class AccountForm(ModelForm):
  class Meta:
    model = Account
    fields = ['account_symbol']

