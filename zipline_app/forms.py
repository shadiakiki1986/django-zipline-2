from .models.zipline_app.fill import Fill
from .models.zipline_app.order import Order
from .widgets import AssetModelSelect2Widget, AccountModelSelect2Widget
from django import forms

# override widget in createview
# http://stackoverflow.com/a/21407374/4126114
# Override a Django generic class-based view widget
# http://stackoverflow.com/a/27322032/4126114
class FillForm(forms.ModelForm):
  class Meta:
    model=Fill
    fields = [
      'pub_date', 'asset', 'fill_side', 'fill_qty_unsigned', 'fill_price', 'fill_text', 'tt_order_key',
      'dedicated_to_order'
    ]
    widgets = {
      'asset': AssetModelSelect2Widget()
    }

class OrderForm(forms.ModelForm):
  class Meta:
    model=Order
    fields = [
      'pub_date', 'asset', 'order_side', 'amount_unsigned', 'account', 'order_text',
      'order_type', 'limit_price',
    ]
    widgets = {
      'asset': AssetModelSelect2Widget(),
      'account': AccountModelSelect2Widget(),
    }
