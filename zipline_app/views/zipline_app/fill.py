from django.urls import  reverse_lazy
from django.views import generic

from ...models.zipline_app.zipline_app import Fill

class FillCreate(generic.CreateView):
  model = Fill
  fields = ['pub_date','asset','fill_qty','fill_price','fill_text']
  template_name = 'zipline_app/fill/fill_form.html'

  def get_success_url(self):
    source = self.request.POST.get('source')
    if source == 'combined': # is not None
      return reverse_lazy('zipline_app:index')
    return reverse_lazy('zipline_app:fills-list')

# inheriting from create+get_context with fill_list instead of inheriting from listview
# so that I can have the inline in create
# http://stackoverflow.com/a/12883683/4126114
class FillList(FillCreate):
  template_name = 'zipline_app/fill/fill_list.html'
  def get_context_data(self, *args, **kwargs):
    context = super(FillList, self).get_context_data(*args, **kwargs)
    context["fill_list"] = Fill.objects.all()
    return context

class FillDelete(generic.DeleteView):
    model = Fill
    success_url = reverse_lazy('zipline_app:fills-list')
    template_name = 'zipline_app/fill/fill_confirm_delete.html'

class FillDetailView(generic.DetailView):
    model = Fill
    template_name = 'zipline_app/fill/fill_detail.html'
    def get_queryset(self):
        """
        Excludes any fills that aren't published yet.
        """
        return Fill.objects.filter(pub_date__lte=timezone.now())

