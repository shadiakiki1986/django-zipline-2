from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
import datetime
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator

from .asset import Asset
from .zlmodel import ZlModel
from .order import Order
from .side import LONG, FILL_SIDE_CHOICES, validate_nonzero, PositiveFloatFieldForm
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from ...utils import now_minute, chopSeconds
from django.contrib.auth.models import User

class PositiveFloatFieldModel(models.FloatField):
  def formfield(self, **kwargs):
    defaults = {'form_class': PositiveFloatFieldForm}
    defaults.update(kwargs)
    return super(PositiveFloatFieldModel, self).formfield(**defaults)

class Fill(models.Model):
    # 2017-03-17: relink fill to order as a "dedicated to order" field
    # 2017-01-12: unlink orders from fills and use zipline engine to perform matching
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    dedicated_to_order = models.OneToOneField(Order, null=True, blank=True, verbose_name="Order", on_delete=models.SET_NULL)

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
    pub_date = models.DateTimeField('date published',default=now_minute)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True)
    tt_order_key = models.CharField(max_length=20, blank=True)

    fill_side = models.CharField(
      max_length=1,
      choices=FILL_SIDE_CHOICES,
      default=LONG,
      verbose_name="Side"
    )
    user = models.ForeignKey(User, null=True, default=None)

    def fill_qty_signed(self):
      return self.fill_qty_unsigned * (+1 if self.fill_side==LONG else -1)

    def __str__(self):
        return "%s, %s %s, %s (%s, %s)%s" % (
          self.asset.asset_symbol, self.fill_side, self.fill_qty_unsigned, self.fill_price, self.tt_order_key, self.fill_text,
          "" if self.dedicated_to_order is None else " - dedicated to %s"%self.dedicated_to_order
        )

    def has_unused(self):
      if self.dedicated_to_order is not None:
        return False
      return self.asset.id in ZlModel.zl_unused

    # validating a model
    # https://docs.djangoproject.com/en/1.10/ref/models/instances/#django.db.models.Model.clean
    def clean(self):
      # drop seconds from pub_date
      self.pub_date = chopSeconds(self.pub_date)

      # check that linked order matches with local properties
      if self.dedicated_to_order is not None:
        errors = {}
        if self.fill_side!=self.dedicated_to_order.order_side:
          errors['fill_side']=_('Dedicated fill side doesnt match with order')
        if self.fill_qty_unsigned!=self.dedicated_to_order.amount_unsigned:
          errors['fill_qty_unsigned']=_('Dedicated fill qty doesnt match with order')
        if self.asset!=self.dedicated_to_order.asset:
          errors['asset']=_('Dedicated fill asset doesnt match with order')
        if self.pub_date!=self.dedicated_to_order.pub_date:
          errors['pub_date']=_(
            'Dedicated fill date (%s) doesnt match with order (%s)'
            %(
              self.pub_date,
              self.dedicated_to_order.pub_date
            )
          )
        if len(errors)>0:
          raise ValidationError(errors)

# using get_success_url
#    def get_absolute_url(self):
#      return reverse('zipline_app:fills-list') # TODO rename to fills
#      return reverse('zipline_app:fills-list', kwargs={'pk': self.pk})
