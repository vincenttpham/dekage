# Generated by Django 2.2 on 2021-02-10 01:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0026_auto_20210209_0617'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='order_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
