# Generated by Django 4.2.6 on 2024-09-10 11:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0006_alter_item_qrcode'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='qrCode',
            new_name='qr_code',
        ),
    ]
