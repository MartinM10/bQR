from io import BytesIO
from myApp.config import DOMAIN
from myApp.models import Customer, Item, Notification
import qrcode
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

    def create(self, validated_data):
        # Crea una instancia de item con los datos validados
        item = Item.objects.create(**validated_data)

        # Genera el código QR
        url = f'{DOMAIN}/scan-qr/{str(item.owner.uuid)}/'
        # url = f'http://localhost:8000/scan-qr/{item.owner.uuid}'

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Guarda la imagen del código QR en el item
        image_io = BytesIO()
        img.save(image_io, 'PNG')
        image_file = SimpleUploadedFile(f'{str(item.owner.username)}/qr_codes/{item.name}.png',
                                        image_io.getvalue(), content_type='image/png')
        item.qr_code = image_file

        # Guarda el item con el código QR
        item.save()
        return item


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
