# Generated by Django 3.0.1 on 2020-01-04 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scores', '0002_auto_20200103_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='edition',
            name='image_tag',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='image tag'),
        ),
    ]
