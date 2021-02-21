# Generated by Django 2.2 on 2021-02-02 08:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop_app', '0011_auto_20210201_2307'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='username',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='review',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_app.User'),
        ),
    ]
