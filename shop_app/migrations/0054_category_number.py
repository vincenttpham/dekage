# Generated by Django 2.2 on 2021-02-22 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0053_auto_20210221_2154'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='number',
            field=models.IntegerField(default=0),
        ),
    ]