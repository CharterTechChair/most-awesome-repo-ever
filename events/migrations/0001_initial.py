# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import events.models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('charterclub', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guests', models.CharField(default=b'[]', max_length=1000, blank=True, validators=[events.models.JSON_validator])),
            ],
            options={
                'ordering': ('member',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Name of the Event', max_length=255, verbose_name=b'Title')),
                ('snippet', models.TextField(help_text=b'To be displayed on the website. (Optional).', verbose_name=b'Description', blank=True)),
                ('image', models.ImageField(help_text=b'To be displayed on the website. (Optional).', null=True, upload_to=b'event_images/', blank=True)),
                ('is_points_event', models.BooleanField(default=False, help_text=b'Do Prospectives who attend get points?', verbose_name=b'Is Point Event:')),
                ('prospective_limit', models.IntegerField(default=0, help_text=b'set 0 to not allow prospectives', verbose_name=b'Prospectives Limit')),
                ('guest_limit', models.IntegerField(default=1, help_text=b'0 = No guests allowed. -1 = As many guests as they can.', verbose_name=b'Guest Limit')),
                ('date', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc), verbose_name=b'Date of Event')),
                ('time', models.TimeField(verbose_name=b'Time of Event')),
                ('signup_end_time', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc))),
                ('prospective_signup_start', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc), blank=True)),
                ('sophomore_signup_start', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc), blank=True)),
                ('junior_signup_start', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc), blank=True)),
                ('senior_signup_start', models.DateField(default=datetime.datetime(2015, 9, 10, 19, 47, 9, 544987, tzinfo=utc), blank=True)),
            ],
            options={
                'ordering': ('title',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Where is the Event Held?', max_length=255)),
                ('limit', models.IntegerField()),
                ('event', models.ForeignKey(to='events.Event')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='entry',
            name='event',
            field=models.ForeignKey(related_name='entry_association', to='events.Event'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entry',
            name='member',
            field=models.ForeignKey(to='charterclub.Member'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='entry',
            name='room',
            field=models.ForeignKey(related_name='entry_association', to='events.Room'),
            preserve_default=True,
        ),
    ]
