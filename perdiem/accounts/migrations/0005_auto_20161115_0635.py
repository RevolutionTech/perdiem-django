# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-15 06:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20160623_0657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useravatarurl',
            name='url',
            field=models.URLField(max_length=2000),
        ),
    ]
