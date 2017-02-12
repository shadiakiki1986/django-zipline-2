#from django.shortcuts import render
# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Order, Fill
from django.utils import timezone
from .matcher import Matcher
from testfixtures import TempDirectory

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_order_list'

    def get_queryset(self):
        """Return the last five published orders."""
        return Order.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')#[:5]

    # Can I have multiple lists in a Django generic.ListView?
    # http://stackoverflow.com/a/18813102/4126114
    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        """Return the last five published fills."""
        context['latest_fill_list'] = Fill.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')#[:5]

        # run matching engine
        with TempDirectory() as tempdir:
          matcher = Matcher()

          sid = [x.fill_sid for x in Fill.objects.all()]
          sid = set(sid)
          fills = {x: pd.DataFrame({}) for x in sid}
          print("sid, fills", sid, fills)
          for x in sid:
            sub = [z for z in Fill.objects.all() if z.fill_sid==x]
            fills[x]["close"] = [y.fill_price for y in sub]
            fills[x]["volume"] = [y.fill_volume for y in sub]
            fills[x]["dt"] = [y.pub_date for y in sub]
            fills[x].set_index("dt")

          print("data: %s" % (fills))
        
          all_minutes = matcher.fills2minutes(fills)
          equity_minute_reader = matcher.fills2reader(tempdir, all_minutes, fills)
         
          orders = [
            {"dt": x.pub_date, "sid": x.order_sid, "amount": x.order_qty, "style": MarketOrder()}
            for x in Order.objects.all()
          ]
          blotter = matcher.orders2blotter(orders)
          bd = matcher.blotter2bardata(equity_minute_reader, blotter)
          all_closed, all_txns = matcher.match_orders_fills(blotter, bd, all_minutes, fills)
          context["zl_open"  ] = blotter.open_orders
          context["zl_closed"] = all_closed
          context["zl_txns"  ] = [txn.to_dict() for txn in all_txns]
     
        return context 

class DetailView(generic.DetailView):
    model = Order
    template_name = 'polls/detail.html'
    def get_queryset(self):
        """
        Excludes any orders that aren't published yet.
        """
        return Order.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Order
    template_name = 'polls/results.html'

def vote(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    try:
        selected_fill = order.fill_set.get(pk=request.POST['fill'])
    except (KeyError, Fill.DoesNotExist):
        # Redisplay the order voting form.
        return render(request, 'polls/detail.html', {
            'order': order,
            'error_message': "You didn't select a fill.",
        })
    else:
        selected_fill.votes += 1
        selected_fill.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(order.id,)))
