# Create your views here.

from django.views import generic
from django.utils import timezone
from django.contrib import messages
from pandas import Timedelta
from numpy import concatenate

from ...models.zipline_app.zipline_app import Order, Fill, ZlModel, Asset
from ...forms import OrderForm, FillForm, AssetForm, AccountForm

class BlotterBaseView(generic.ListView):
    def get_context_data(self, *args, **kwargs):
        context = super(BlotterBaseView, self).get_context_data(*args, **kwargs)
        context["order_form"]=OrderForm()
        context["fill_form"]=FillForm()
        context["asset_form"]=AssetForm()
        context["account_form"]=AccountForm()
        context["source"]=self.source
        return context

class BlotterSideBySideView(BlotterBaseView):
    template_name = 'zipline_app/blotter/sideBySide/index.html'
    context_object_name = 'combined'
    source="sideBySide"

    def fills_required_per_asset(self):
      fills = {}
      for order in Order.objects.all():
        if order.filled()!=order.amount_signed():
          if order.asset not in fills: fills[order.asset]=0
          fills[order.asset]+=order.amount_signed() - order.filled()
      return fills

    def get_queryset(self):
        combined = []
        for minute in sorted(ZlModel.all_minutes, reverse=True):
          minuteP1 = minute + Timedelta(minutes=1)
          orders = Order.objects.filter(
            pub_date__gte=minute,
            pub_date__lt =minuteP1
          )
          fills = Fill.objects.filter(
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
        context["zl_unused"] = ZlModel.zl_unused.items()
        context["fills_required_per_asset"]=self.fills_required_per_asset()
        return context

class BlotterConcealedView(BlotterSideBySideView):
    template_name = 'zipline_app/blotter/concealed.html'
    source="concealed"

class BlotterEngineView(BlotterBaseView):
    template_name = 'zipline_app/blotter/engine.html'
    context_object_name = 'latest_order_list'
    source="engine"

    def get_queryset(self):
        """Return the last five published orders."""
        if any(ZlModel.zl_unused):
          #print("add to messages")
          messages.add_message(self.request, messages.ERROR, "You have unused fills.")

        return Order.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')#[:5]

    # Can I have multiple lists in a Django generic.ListView?
    # http://stackoverflow.com/a/18813102/4126114
    def get_context_data(self, *args, **kwargs):
        context = super(BlotterEngineView, self).get_context_data(*args, **kwargs)
        """Return the last five published fills."""
        context['latest_fill_list'] = Fill.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')#[:5]

        # get matching engine model
        context["zl_open"]=ZlModel.zl_open
        context["zl_closed"]=ZlModel.zl_closed
        context["zl_txns"]=ZlModel.zl_txns
        context["zl_open_keyed"]=ZlModel.zl_open_keyed
        context["zl_unused"] = ZlModel.zl_unused.items()

        return context

