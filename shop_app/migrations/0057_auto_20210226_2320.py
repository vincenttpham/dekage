# Generated by Django 2.2 on 2021-02-26 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0056_auto_20210226_2317'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartproduct',
            name='cart',
        ),
        migrations.AddField(
            model_name='cart',
            name='products',
            field=models.ManyToManyField(related_name='cart', to='shop_app.CartProduct'),
        ),
    ]
