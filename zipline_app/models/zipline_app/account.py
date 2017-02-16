from __future__ import unicode_literals

from django.db import models
class Account(models.Model):
    account_symbol = models.CharField(max_length=20)
    def __str__(self):
      return self.account_symbol
