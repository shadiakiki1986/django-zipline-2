from .models.zipline_app.asset import Asset
from .models.zipline_app.account import Account

# using select2, copied from https://github.com/applegrew/django-select2/blob/master/tests/testapp/forms.py
from django_select2.forms import ModelSelect2Widget
from django.utils.encoding import force_text

class AssetModelSelect2Widget(ModelSelect2Widget):
    model = Asset
    search_fields = [
        'asset_name__icontains',
        'asset_symbol__startswith'
    ]
    def label_from_instance(self, obj):
      return force_text(obj.__str__())

class AccountModelSelect2Widget(ModelSelect2Widget):
    model = Account
    search_fields = [
        'account_name__icontains',
        'account_symbol__startswith'
    ]
    def label_from_instance(self, obj):
      return force_text(obj.__str__())
