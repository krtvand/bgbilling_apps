# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-01 10:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bgb_webcontract', '0008_auto_20161201_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='login',
            field=models.CharField(blank=True, default=None, max_length=10),
        ),
    ]