from __future__ import unicode_literals

from django.db import models
class Account(models.Model):
    account_symbol = models.CharField(max_length=20, unique=True)
    def __str__(self):
      return self.account_symbol

    def get_absolute_url(self):
      return reverse('zipline_app:accounts-list') # TODO rename to accounts
#      return reverse('zipline_app:accounts-list', kwargs={'pk': self.pk})
