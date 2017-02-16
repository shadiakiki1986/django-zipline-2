from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime

from django.urls import reverse
from .asset import Asset

from .zlmodel import ZlModel

# Create your models here.

class Fill(models.Model):
    # 2017-01-12: unlink orders from fills and use zipline engine to perform matching
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fill_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    fill_qty = models.IntegerField(default=0)
    fill_price = models.FloatField(default=0)
    pub_date = models.DateTimeField('date published',default=timezone.now)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "%s, %s, %s (%s)" % (self.asset.asset_symbol, self.fill_qty, self.fill_price, self.fill_text)

    def has_unused(self):
      return self.asset.id in ZlModel.zl_unused
