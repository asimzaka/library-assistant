# Generated by Django 5.1 on 2024-08-20 06:49

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libraryapi', '0007_userfavorite'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='vector',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), blank=True, null=True, size=384),
        ),
    ]
