import hashlib
from django.urls import  reverse_lazy
from os import getenv

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

def redirect_index_or_local(myself,local):
  source = myself.request.POST.get('source')
  if source is not None:
    return reverse_lazy('zipline_app:blotter-%s'%source)
  return reverse_lazy(local)

import datetime
from django.utils import timezone
from django.contrib.auth.models import User

def now_minute():
  ts=timezone.now()
  ts = chopSeconds(ts)
  return ts

def chopSeconds(ts:datetime):
  #ts -= datetime.timedelta(seconds=ts.second, microseconds=ts.microsecond)
  #return ts
  return ts.replace(second=0, microsecond=0)

def myTestLogin(client):
  password = 'glass onion'
  user = User.objects.create_user(username='john', email='jlennon@beatles.com', password=password)
  response = client.login(username=user.username, password=password, follow=True)
  return user

def getenv_or_fail(envName: str):
  value = getenv(envName)
  if value is None:
    raise Exception("Environment variable undefined: '%s'" % envName)
  return value
