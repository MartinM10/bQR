# Generated by Django 4.2.6 on 2024-09-10 11:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0007_rename_qrcode_item_qr_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='qr_code',
            new_name='qrCode',
        ),
    ]
