# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 18:20
from __future__ import unicode_literals

from django.db import migrations, models
import zipline_app.utils


class Migration(migrations.Migration):

    dependencies = [
        ('zipline_app', '0006_auto_20170318_1954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fill',
            name='pub_date',
            field=models.DateTimeField(default=zipline_app.utils.now_minute, verbose_name='date published'),
        ),
        migrations.AlterField(
            model_name='order',
            name='pub_date',
            field=models.DateTimeField(default=zipline_app.utils.now_minute, verbose_name='date published'),
        ),
    ]