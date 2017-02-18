from django.urls import  reverse_lazy
from django.views import generic
from ...models.zipline_app.zipline_app import Asset
from ...utils import redirect_index_or_local

class AssetCreate(generic.CreateView):
  model = Asset
  fields = ['asset_symbol','asset_name','asset_exchange']
  template_name = 'zipline_app/asset/asset_form.html'

  def get_success_url(self):
    return redirect_index_or_local(self,'zipline_app:assets-list')

# inheriting from create+get_context with asset_list instead of inheriting from listview
# so that I can have the inline in create
# http://stackoverflow.com/a/12883683/4126114
class AssetList(AssetCreate):
  template_name = 'zipline_app/asset/asset_list.html'
  def get_context_data(self, *args, **kwargs):
    context = super(AssetList, self).get_context_data(*args, **kwargs)
    context["asset_list"] = Asset.objects.all()
    return context

class AssetDelete(generic.DeleteView):
    model = Asset
    success_url = reverse_lazy('zipline_app:assets-list')
    template_name = 'zipline_app/asset/asset_confirm_delete.html'
