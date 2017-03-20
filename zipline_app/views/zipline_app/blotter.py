# Create your views here.

from django.views import generic
from django.utils import timezone
from django.contrib import messages
from pandas import Timedelta
from numpy import concatenate

from ...models.zipline_app.zipline_app import Order, Fill, ZlModel, Asset
from ...forms import OrderForm, FillForm, AssetForm, AccountForm
from ._download_builder import DownloadBuilder

class BlotterBaseView(generic.ListView):
    context_object_name = 'latest_order_list'

    def get_queryset(self):
        """Return orders"""
        return self.get_orders()

    def get_context_data(self, *args, **kwargs):
        context = super(BlotterBaseView, self).get_context_data(*args, **kwargs)

        # append fills
        context['latest_fill_list'] = self.get_fills()

        # append forms
        context["order_form"]=OrderForm()
        context["fill_form"]=FillForm()
        context["asset_form"]=AssetForm()
        context["account_form"]=AccountForm()

        # append source for redirection
        context["source"]=self.source
        return context

    def get_orders(self):
      return Order.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')#[:5]

    def get_fills(self):
      return Fill.objects.filter(
          pub_date__lte=timezone.now()
      ).order_by('-pub_date')#[:5]

class BlotterSideBySideView(BlotterBaseView):
    template_name = 'zipline_app/blotter/sideBySide/index.html'
    source="sideBySide"

    def fills_required_per_asset(self):
      fills = {}
      for order in self.get_orders():
        if order.filled()!=order.amount_signed():
          if order.asset not in fills: fills[order.asset]=0
          fills[order.asset]+=order.amount_signed() - order.filled()
      return fills

    def get_combined(self):
        combined = []
        for minute in sorted(ZlModel.all_minutes, reverse=True):
          minuteP1 = minute + Timedelta(minutes=1)
          orders = self.get_orders()
          orders = orders.filter(
            pub_date__gte=minute,
            pub_date__lt =minuteP1
          )
          fills = self.get_fills()
          fills = fills.filter(
            pub_date__gte=minute,
            pub_date__lt =minuteP1,
          )
          sids_orders = [o.asset.id for o in orders]
          sids_fills  = [f.asset.id for f in fills]
          sids = concatenate((sids_orders,sids_fills))
          sids = sorted(list(set(sids)))
          duos=[]
          for sid in sids:
            asset = Asset.objects.get(id=sid)
            asset_fills = fills.filter(asset=asset)
            asset_orders = orders.filter(asset=asset)
            duos.append({
              "asset": asset,
              "colspan": max(len(asset_orders),len(asset_fills)),
              "orders": asset_orders,
              "fills": asset_fills
            })

          combined.append({
            "minute":minute,
            "duos":duos
          })
        return combined

    def get_context_data(self, *args, **kwargs):
        context = super(BlotterSideBySideView, self).get_context_data(*args, **kwargs)
        context["combined"] = self.get_combined()
        context["zl_unused"] = ZlModel.zl_unused.items()
        context["fills_required_per_asset"]=self.fills_required_per_asset()
        return context

class BlotterConcealedView(BlotterSideBySideView):
    template_name = 'zipline_app/blotter/concealed.html'
    source="concealed"

class BlotterEngineView(BlotterBaseView):
    template_name = 'zipline_app/blotter/engine.html'
    source="engine"

    # Can I have multiple lists in a Django generic.ListView?
    # http://stackoverflow.com/a/18813102/4126114
    def get_context_data(self, *args, **kwargs):
        context = super(BlotterEngineView, self).get_context_data(*args, **kwargs)

        if any(ZlModel.zl_unused):
          #print("add to messages")
          messages.add_message(self.request, messages.ERROR, "You have unused fills.")

        # get matching engine model
        context["zl_open"]=ZlModel.zl_open
        context["zl_closed"]=ZlModel.zl_closed
        context["zl_txns"]=ZlModel.zl_txns
        context["zl_open_keyed"]=ZlModel.zl_open_keyed
        context["zl_unused"] = ZlModel.zl_unused.items()

        return context

class BlotterDownloadView(BlotterBaseView):
  def get(self, *args, **kwargs):
    orders = self.get_orders()
    builder = DownloadBuilder()
    df = builder.orders2df(orders)
    full_name = builder.df2xlsx(df)
    response = builder.fn2response(full_name)
    return response
