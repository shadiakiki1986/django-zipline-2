from __future__ import unicode_literals

# Django Logging
# https://docs.djangoproject.com/en/1.10/topics/logging/
import logging
logger = logging.getLogger("zipline_app") #__name__)

from .models.zipline_app.asset import Asset
from .models.zipline_app.account import Account
from .models.zipline_app.order import Order
from .models.zipline_app.zlmodel import ZlModel
from .models.zipline_app.fill import Fill

# https://docs.djangoproject.com/en/1.11/topics/signals/#connecting-receiver-functions
#from django.core.signals import request_started
#request_started.connect(ZlModel.update)

class SignalProcessor:
  #def post_init(sender, **kwargs):
  #  print("Signal: %s, %s" % ("post_init", sender.__name__))

  def post_save(sender, instance, **kwargs):
    logger.debug("Signal: %s, %s" % ("post_save", sender))
    if sender.__name__=="Fill": ZlModel.add_fill(instance)
    if sender.__name__=="Order":
      ZlModel.add_order(instance)
      instance.append_history()
    ZlModel.update()

  def post_delete(sender, instance, **kwargs):
    logger.debug("Signal: %s, %s" % ("post_delete", sender))
    if sender.__name__=="Fill": ZlModel.delete_fill(instance)
    if sender.__name__=="Order": ZlModel.delete_order(instance)
    ZlModel.update()

  def ready(sender, environ, **kwargs):
    if ZlModel.md5 is not None:
      logger.debug("Signal: %s, %s" % ("connection_created", "ignoring since already received"))
      return
    logger.debug("Signal: %s, %s" % ("connection_created", "proceeding with update"))
    ZlModel.init(Fill.objects.all(), Order.objects.all())
    ZlModel.update()

  def order_cancelled(sender, id, **kwargs):
    logger.debug("Order cancelled: %s"%id)
    order = Order.objects.filter(id=id).first()
    if order is not None:
      order.cancel()

