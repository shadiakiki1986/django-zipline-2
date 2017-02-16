#from django.shortcuts import render
# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic

from ...models.zipline_app.zipline_app import Order, Fill, ZlModel, Asset

from django.utils import timezone

from django.contrib import messages
from pandas import Timedelta
from numpy import concatenate

class IndexView(generic.ListView):
    template_name = 'zipline_app/index.html'
    context_object_name = 'combined'

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

class DetailView(generic.DetailView):
    model = Order
    template_name = 'zipline_app/detail.html'
    def get_queryset(self):
        """
        Excludes any orders that aren't published yet.
        """
        return Order.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Order
    template_name = 'zipline_app/results.html'

def vote(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    try:
        selected_fill = order.fill_set.get(pk=request.POST['fill'])
    except (KeyError, Fill.DoesNotExist):
        # Redisplay the order voting form.
        return render(request, 'zipline_app/detail.html', {
            'order': order,
            'error_message': "You didn't select a fill.",
        })
    else:
        selected_fill.votes += 1
        selected_fill.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('zipline_app:results', args=(order.id,)))
