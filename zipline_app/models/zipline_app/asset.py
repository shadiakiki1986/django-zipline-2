from __future__ import unicode_literals

from django.db import models

from django.urls import reverse

# Create your models here.

class Asset(models.Model):
    asset_symbol = models.CharField(max_length=20, unique=True)
    asset_exchange = models.CharField(max_length=200)
    asset_name = models.CharField(max_length=200)

    def __str__(self):
        return "%s, %s, %s" % (self.asset_symbol, self.asset_exchange, self.asset_name)

    def str(self):
      return self.__str__()

    def to_dict(self):
        return {
          "symbol": self.asset_symbol,
          "exchange": self.asset_exchange,
          "name": self.asset_name
        }

    def delete(self):
      if self.order_set.count()>0:
        raise ValueError("Cannot delete asset because it is linked to orders")
      if self.fill_set.count()>0:
        raise ValueError("Cannot delete asset because it is linked to fills")

# use get_success_url instead
#    def get_absolute_url(self):
#      return reverse('zipline_app:assets-list') # TODO rename to assets
#      return reverse('zipline_app:assets-list', kwargs={'pk': self.pk})
