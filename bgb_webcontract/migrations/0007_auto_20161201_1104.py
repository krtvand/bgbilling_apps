# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-01 08:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bgb_webcontract', '0006_auto_20161201_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='full_name',
            field=models.CharField(max_length=200, verbose_name='ФИО без сокращений'),
        ),
        migrations.AlterField(
            model_name='contract',
            name='position',
            field=models.CharField(max_length=200, verbose_name='Должность'),
        ),
        migrations.AlterField(
            model_name='department',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Факультет/Подразделение'),
        ),
        migrations.AlterField(
            model_name='request',
            name='it_manager_email',
            field=models.EmailField(max_length=254, verbose_name='Email заявителя'),
        ),
        migrations.AlterField(
            model_name='request',
            name='it_manager_fullname',
            field=models.CharField(max_length=200, verbose_name='ФИО заявителя полностью'),
        ),
        migrations.AlterField(
            model_name='request',
            name='it_manager_position',
            field=models.CharField(max_length=200, verbose_name='Должность заявителя'),
        ),
    ]