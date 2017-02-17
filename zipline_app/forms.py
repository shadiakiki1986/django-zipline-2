from django.forms import ModelForm
from .models.zipline_app.order import Order

class OrderForm(ModelForm):
  class Meta:
    model = Order
    fields = ['pub_date','asset','amount','account','order_text']

