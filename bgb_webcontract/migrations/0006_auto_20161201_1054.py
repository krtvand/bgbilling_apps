# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-01 07:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bgb_webcontract', '0005_auto_20161130_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='full_name',
            field=models.CharField(max_length=200, verbose_name='Полное имя'),
        ),
    ]
