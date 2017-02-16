from django.views import generic

from ...models.zipline_app.zipline_app import Order, Fill, ZlModel, Asset

from django.utils import timezone

from django.contrib import messages

class OrdersOnlyView(generic.ListView):
    template_name = 'zipline_app/ordersOnly.html'
    context_object_name = 'latest_order_list'

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
        context = super(OrdersOnlyView, self).get_context_data(*args, **kwargs)
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

