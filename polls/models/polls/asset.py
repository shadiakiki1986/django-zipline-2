from __future__ import unicode_literals

from django.db import models

from django.urls import reverse

# Create your models here.

class Asset(models.Model):
    asset_symbol = models.CharField(max_length=20)
    asset_exchange = models.CharField(max_length=200)
    asset_name = models.CharField(max_length=200)

    def __str__(self):
        return "%s, %s, %s" % (self.asset_symbol, self.asset_exchange, self.asset_name)

    def to_dict(self):
        return {
          "symbol": self.asset_symbol,
          "exchange": self.asset_exchange,
          "name": self.asset_name
        }

    def get_absolute_url(self):
      return reverse('polls:assets-list') # TODO rename to assets
#      return reverse('polls:assets-list', kwargs={'pk': self.pk})
