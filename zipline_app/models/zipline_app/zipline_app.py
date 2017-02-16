from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime

from six import iteritems

# Django Logging
# https://docs.djangoproject.com/en/1.10/topics/logging/
import logging
logger = logging.getLogger(__name__)

from django.urls import reverse
from .asset import Asset
from .account import Account
from .order import Order
from .zlmodel import ZlModel
from .fill import Fill

# Create your models here.


# https://docs.djangoproject.com/en/1.11/topics/signals/#connecting-receiver-functions
#from django.core.signals import request_started
#request_started.connect(ZlModel.update)

# connecting signals
from django.db.backends.signals import connection_created
class SignalProcessor:
  #def post_init(sender, **kwargs):
  #  print("Signal: %s, %s" % ("post_init", sender.__name__))

  def update_if_mine(sender):
    condition = sender.__name__=="Fill" or sender.__name__=="Order" or sender.__name__=="Asset"
    if condition:
      ZlModel.update()

  def post_save(sender, instance, **kwargs):
    #logger.debug("Signal: %s, %s" % ("post_save", sender))
    if sender.__name__=="Fill": ZlModel.add_fill(instance)
    if sender.__name__=="Order": ZlModel.add_order(instance)
    if sender.__name__=="Asset": ZlModel.add_asset(instance)
    SignalProcessor.update_if_mine(sender)

  def post_delete(sender, instance, **kwargs):
    #print("Signal: %s, %s" % ("post_delete", sender))
    if sender.__name__=="Fill": ZlModel.delete_fill(instance)
    if sender.__name__=="Order": ZlModel.delete_order(instance)
    if sender.__name__=="Asset": ZlModel.delete_asset(instance)
    SignalProcessor.update_if_mine(sender)

  def connection_created(sender, **kwargs):
  #  print("Signal: %s, %s" % ("connection_created", sender))
    ZlModel.init(Fill.objects.all(), Order.objects.all(), Asset.objects.all())
    ZlModel.update()

senders=("zipline_app.Order", "zipline_app.Fill", "zipline_app.Asset")
for sender in senders:
  #models.signals.post_init.connect(SignalProcessor.post_init, sender=sender)
  models.signals.post_save.connect(SignalProcessor.post_save, sender=sender)
  models.signals.post_delete.connect(SignalProcessor.post_delete, sender=sender)
connection_created.connect(SignalProcessor.connection_created)

