import hashlib
from django.urls import  reverse_lazy

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

def redirect_index_or_local(myself,local):
  source = myself.request.POST.get('source')
  if source == 'combined': # is not None
    return reverse_lazy('zipline_app:blotter-sideBySide')
  return reverse_lazy(local)

import datetime
from django.utils import timezone

def now_minute():
  ts=timezone.now()
  ts = chopSeconds(ts)
  return ts

def chopSeconds(ts:datetime):
  #ts -= datetime.timedelta(seconds=ts.second, microseconds=ts.microsecond)
  #return ts
  return ts.replace(second=0, microsecond=0)

