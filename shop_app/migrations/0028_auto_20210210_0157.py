# Generated by Django 2.2 on 2021-02-10 01:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0027_review_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='order_id',
            field=models.CharField(max_length=255),
        ),
    ]
