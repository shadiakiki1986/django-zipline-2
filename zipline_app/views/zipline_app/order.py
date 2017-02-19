from django.views import generic
from django.utils import timezone
from django.contrib import messages
from ...models.zipline_app.zipline_app import Order, Fill, ZlModel, Asset
from ...utils import redirect_index_or_local

class OrderCreate(generic.CreateView):
  model = Order
  fields = ['pub_date','asset','amount','account','order_text']
  template_name = 'zipline_app/order/order_form.html'

  def get_success_url(self):
    # django message levels
    # https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
    messages.add_message(self.request, messages.INFO, "Successfully created order: %s" % self)
    return redirect_index_or_local(self,'zipline_app:orders-list')

# inheriting from create+get_context with order_list instead of inheriting from listview
# so that I can have the inline in create
# http://stackoverflow.com/a/12883683/4126114
class OrderList(OrderCreate):
  template_name = 'zipline_app/order/order_list.html'
  def get_context_data(self, *args, **kwargs):
    context = super(OrderList, self).get_context_data(*args, **kwargs)
    context["order_list"] = Order.objects.all()
    return context

class OrderDelete(generic.DeleteView):
  model = Order
  template_name = 'zipline_app/order/order_confirm_delete.html'
  def get_success_url(self):
    messages.add_message(self.request, messages.INFO, "Successfully deleted order: %s" % self)
    return redirect_index_or_local(self,'zipline_app:orders-list')

class OrderDetailView(generic.DetailView):
    model = Order
    template_name = 'zipline_app/order/order_detail.html'
    def get_queryset(self):
        """
        Excludes any orders that aren't published yet.
        """
        return Order.objects.filter(pub_date__lte=timezone.now())
