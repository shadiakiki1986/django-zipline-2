import hashlib
from django.urls import  reverse_lazy

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

def redirect_index_or_local(myself,local):
  source = myself.request.POST.get('source')
  if source == 'combined': # is not None
    return reverse_lazy('zipline_app:blotter-sideBySide')
  return reverse_lazy(local)
