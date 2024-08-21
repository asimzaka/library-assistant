# Generated by Django 5.1 on 2024-08-19 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libraryapi', '0005_remove_ratingdistribution_book_rating'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='author',
            index=models.Index(fields=['name'], name='libraryapi__name_7e4d5b_idx'),
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['title'], name='libraryapi__title_f57415_idx'),
        ),
    ]
