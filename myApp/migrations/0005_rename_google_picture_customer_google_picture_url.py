# Generated by Django 4.2.6 on 2024-09-10 09:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0004_alter_item_qrcode'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='google_picture',
            new_name='google_picture_url',
        ),
    ]
