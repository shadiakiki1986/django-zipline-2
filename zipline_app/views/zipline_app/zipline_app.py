#from django.shortcuts import render
# Create your views here.

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from ...models.zipline_app.zipline_app import Order, Fill

class IndexView(generic.base.TemplateView):
    template_name = 'zipline_app/index.html'

class ResultsView(generic.DetailView):
    model = Order
    template_name = 'zipline_app/results.html'

def vote(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    try:
        selected_fill = order.fill_set.get(pk=request.POST['fill'])
    except (KeyError, Fill.DoesNotExist):
        # Redisplay the order voting form.
        return render(request, 'zipline_app/order/order_detail.html', {
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
