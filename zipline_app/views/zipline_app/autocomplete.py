from django.views import generic
from ...models.zipline_app.asset import Asset
from ...models.zipline_app.account import Account
from json import dumps
from django.http import HttpResponse

# Autocomplete Input Field In Django Template with Jquery-UI
# http://blog.appliedinformaticsinc.com/autocomplete-input-field-in-django-template-with-jquery-ui/
# code in view which returns json data
class AutoCompleteBaseView(generic.FormView):
  auto_objects = None
#  def filter(self,term):
#    return self.auto_objects.filter(asset_symbol__icontains = term)

  def get(self,request,*args,**kwargs):
    term = request.GET.get("term")
    if term:
      assets = self.filter(term)
    else:
      assets = self.auto_objects.all()

    # limit to first n results
    assets=assets[0:10]

    results = []
    for asset in assets:
      asset_json = {}
      asset_json['id'] = asset.id
      asset_json['label'] = asset.__str__() # .asset_symbol
      asset_json['value'] = asset.id # .asset_exchange
      results.append(asset_json)
    data = dumps(results)
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


class AutoCompleteAssetView(AutoCompleteBaseView):
  auto_objects=Asset.objects
  def filter(self,term):
    return self.auto_objects.filter(asset_symbol__icontains = term)


class AutoCompleteAccountView(AutoCompleteBaseView):
  auto_objects=Account.objects
  def filter(self,term):
    return self.auto_objects.filter(account_symbol__icontains = term)
