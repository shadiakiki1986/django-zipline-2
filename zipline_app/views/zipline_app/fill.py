from django.views import generic
from django.utils import timezone
from django.contrib import messages
from ...models.zipline_app.zipline_app import Fill
from ...utils import redirect_index_or_local

class FillCreate(generic.CreateView):
  model = Fill
  fields = [
    'pub_date', 'asset', 'fill_side', 'fill_qty_unsigned', 'fill_price', 'fill_text', 'tt_order_key',
    'dedicated_to_order'
  ]
  template_name = 'zipline_app/fill/fill_form.html'

  def form_valid(self, form):
    fill = form.save(commit=False)
    if self.request.user.is_authenticated():
      fill.user = self.request.user
    return super(FillCreate, self).form_valid(form)

  def get_success_url(self):
    messages.add_message(self.request, messages.INFO, "Successfully created fill: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:fills-list')

# inheriting from create+get_context with fill_list instead of inheriting from listview
# so that I can have the inline in create
# http://stackoverflow.com/a/12883683/4126114
class FillList(FillCreate):
  template_name = 'zipline_app/fill/fill_list.html'
  def get_context_data(self, *args, **kwargs):
    context = super(FillList, self).get_context_data(*args, **kwargs)
    context["fill_list"] = Fill.objects.all()
    form = FillCreate()
    context["fill_form"]=form.get_form_class()
    return context

class FillDelete(generic.DeleteView):
  model = Fill
  template_name = 'zipline_app/fill/fill_confirm_delete.html'
  def get_success_url(self):
    messages.add_message(self.request, messages.INFO, "Successfully deleted fill: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:fills-list')

class FillDetailView(generic.DetailView):
    model = Fill
    template_name = 'zipline_app/fill/fill_detail.html'
    def get_queryset(self):
        """
        Excludes any fills that aren't published yet.
        """
        return Fill.objects.filter(pub_date__lte=timezone.now())


class FillUpdateView(generic.UpdateView):
  model = Fill
  fields = [
    'pub_date', 'asset', 'fill_side', 'fill_qty_unsigned', 'fill_price', 'fill_text', 'tt_order_key',
    'dedicated_to_order'
  ]
  template_name = 'zipline_app/fill/fill_form.html'

  def get_success_url(self):
    # django message levels
    # https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
    messages.add_message(self.request, messages.INFO, "Successfully updated fill: %s" % self.object)
    return redirect_index_or_local(self,'zipline_app:fills-list')

