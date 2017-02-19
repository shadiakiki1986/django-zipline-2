from django.urls import  reverse_lazy
from django.views import generic
from django.contrib import messages
from ...models.zipline_app.account import Account
from ...utils import redirect_index_or_local

class AccountCreate(generic.CreateView):
  model = Account
  fields = ['account_symbol']
  template_name = 'zipline_app/account/account_form.html'

  def get_success_url(self):
    messages.add_message(self.request, messages.INFO, "Successfully created account: %s" % self)
    return redirect_index_or_local(self,'zipline_app:accounts-list')

# inheriting from create+get_context with account_list instead of inheriting from listview
# so that I can have the inline in create
# http://stackoverflow.com/a/12883683/4126114
class AccountList(AccountCreate):
  template_name = 'zipline_app/account/account_list.html'
  def get_context_data(self, *args, **kwargs):
    context = super(AccountList, self).get_context_data(*args, **kwargs)
    context["account_list"] = Account.objects.all()
    return context

class AccountDelete(generic.DeleteView):
    model = Account
    success_url = reverse_lazy('zipline_app:accounts-list')
    template_name = 'zipline_app/account/account_confirm_delete.html'
