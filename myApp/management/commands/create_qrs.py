from django.core.management.base import BaseCommand
from myApp.models import QRCode
from django.conf import settings
import os
from django.core.files.base import ContentFile
import random
import string

from myApp.utils import generate_styled_qr


class Command(BaseCommand):
    help = 'Creates a specified number of promotional QR codes'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Indicates the number of promotional QRs to create')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        promo_qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(promo_qr_dir, exist_ok=True)

        for i in range(count):
            promo_qr = QRCode.objects.create(
                secret_code=generate_secret_code(),
                is_physical=True,
                is_activated=False,
                is_assigned=False
            )

            url = f'{settings.DOMAIN}/scan-qr/{promo_qr.uuid}'
            qr_image = generate_styled_qr(url, str(promo_qr.uuid))
            qr_filename = f'{promo_qr.uuid}_qr.png'

            # Guardar la imagen del QR
            promo_qr.qr_image.save(qr_filename, ContentFile(qr_image), save=True)

            self.stdout.write(self.style.SUCCESS(f'Created promotional QR with code: {promo_qr.uuid}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} promotional QR codes'))


def generate_secret_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
