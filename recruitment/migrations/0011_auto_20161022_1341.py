# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0010_auto_20161013_1304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prospectiveevententry',
            name='signup_date',
            field=models.DateField(default=datetime.date(2016, 10, 22), blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='prospectivemealentry',
            name='signup_date',
            field=models.DateField(default=datetime.date(2016, 10, 22), blank=True),
            preserve_default=True,
        ),
    ]
