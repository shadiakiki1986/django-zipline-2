from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import fields

from .asset import Asset
from .zlmodel import ZlModel

# Django docs: writing validators
# https://docs.djangoproject.com/en/1.10/ref/validators/#writing-validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
def validate_nonzero(value):
    if value == 0:
        raise ValidationError(
            _('Quantity %(value)s is not allowed'),
            params={'value': value},
        )

# Inspired by django.forms.fields.py#FloatField
class PositiveFloatFieldForm(fields.FloatField):
  default_error_messages = {
    'invalid': _('Enter a positive number.'),
  }
  def validate(self, value):
    super(PositiveFloatFieldForm, self).validate(value)
    if value<0:
      raise ValidationError(self.error_messages['invalid'], code='invalid')
    return value

  def widget_attrs(self, widget):
    attrs = super(PositiveFloatFieldForm, self).widget_attrs(widget)
    attrs['min']=0
    return attrs

class PositiveFloatFieldModel(models.FloatField):
  def formfield(self, **kwargs):
    defaults = {'form_class': PositiveFloatFieldForm}
    defaults.update(kwargs)
    return super(PositiveFloatFieldModel, self).formfield(**defaults)

class Fill(models.Model):
    # 2017-01-12: unlink orders from fills and use zipline engine to perform matching
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fill_text = models.CharField(max_length=200, blank=True)
    votes = models.IntegerField(default=0)
    fill_qty_unsigned = models.PositiveIntegerField(
      default=0,
      validators=[MaxValueValidator(1000000), validate_nonzero],
      verbose_name="Qty"
    )
    fill_price = PositiveFloatFieldModel(
      default=0,
      validators=[MaxValueValidator(1000000), MinValueValidator(0), validate_nonzero],
    )
    pub_date = models.DateTimeField('date published',default=timezone.now)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    tt_order_key = models.CharField(max_length=20, blank=True)

    LONG = 'L'
    SHORT = 'S'
    FILL_SIDE_CHOICES = (
      (LONG, 'Long'),
      (SHORT, 'Short')
    )
    fill_side = models.CharField(
      max_length=1,
      choices=FILL_SIDE_CHOICES,
      default=LONG,
      verbose_name="Side"
    )

    def fill_qty_signed(self):
      return self.fill_qty_unsigned * (+1 if self.fill_side==Fill.LONG else -1)

    def __str__(self):
        return "%s, %s %s, %s (%s, %s)" % (self.asset.asset_symbol, self.fill_side, self.fill_qty_unsigned, self.fill_price, self.tt_order_key, self.fill_text)

    def has_unused(self):
      return self.asset.id in ZlModel.zl_unused

# using get_success_url
#    def get_absolute_url(self):
#      return reverse('zipline_app:fills-list') # TODO rename to fills
#      return reverse('zipline_app:fills-list', kwargs={'pk': self.pk})
