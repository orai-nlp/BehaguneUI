# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.TextField(default=b'')),
                ('lang', models.TextField(default=b'')),
                ('last_fetch', models.TextField(default=b'')),
                ('description', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('keyword_id', models.IntegerField(serialize=False, primary_key=True)),
                ('type', models.CharField(default=b'', max_length=10)),
                ('lang', models.CharField(default=b'', max_length=5)),
                ('category', models.CharField(default=b'', max_length=40)),
                ('subCat', models.CharField(default=b'', max_length=40)),
                ('term', models.TextField(default=b'')),
                ('anchor', models.BooleanField(default=False)),
                ('is_anchor', models.BooleanField(default=False)),
                ('screen_tag', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='Keyword_Mention',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keyword', models.ForeignKey(to='behagunea_app.Keyword')),
            ],
        ),
        migrations.CreateModel(
            name='Mention',
            fields=[
                ('mention_id', models.IntegerField(serialize=False, primary_key=True)),
                ('date', models.TextField(default=b'')),
                ('url', models.TextField(default=b'')),
                ('text', models.TextField(default=b'')),
                ('lang', models.CharField(default=b'', max_length=5)),
                ('polarity', models.CharField(default=b'', max_length=10)),
                ('manual_polarity', models.CharField(default=b'', max_length=10)),
                ('corrected', models.BooleanField(default=False)),
                ('favourites', models.IntegerField(default=0)),
                ('retweets', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('source_id', models.BigIntegerField(serialize=False, primary_key=True)),
                ('type', models.CharField(default=None, max_length=10)),
                ('influence', models.FloatField()),
                ('source_name', models.CharField(max_length=45)),
                ('domain', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='user',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nickname', models.CharField(default=b'', max_length=15)),
                ('firstname', models.TextField(default=b'')),
                ('surname', models.TextField(default=b'')),
                ('email', models.TextField(default=b'')),
                ('affiliation', models.TextField(default=b'')),
                ('keyword_admin', models.BooleanField(default=False)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='User_Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keyword', models.ForeignKey(to='behagunea_app.Keyword')),
                ('user', models.ForeignKey(to='behagunea_app.user')),
            ],
        ),
        migrations.AddField(
            model_name='source',
            name='user',
            field=models.ForeignKey(to='behagunea_app.user', null=True),
        ),
        migrations.AddField(
            model_name='mention',
            name='source',
            field=models.ForeignKey(to='behagunea_app.Source', null=True),
        ),
        migrations.AddField(
            model_name='keyword_mention',
            name='mention',
            field=models.ForeignKey(to='behagunea_app.Mention'),
        ),
        migrations.AddField(
            model_name='feed',
            name='source',
            field=models.ForeignKey(to='behagunea_app.Source'),
        ),
    ]
