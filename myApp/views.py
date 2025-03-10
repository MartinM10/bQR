import os
import random
import string

from django.utils import timezone
from datetime import time
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from beQR import settings
from myApp.config import DOMAIN, ORGANIZATION_EMAIL
from myApp.forms import ContactForm, CustomUserCreationForm, FormItem, ChangePasswordForm, ChangeProfilePictureForm, \
    ChangeItemPictureForm, NotificationPreferenceForm, EditProfileForm, QRCodeOrderForm, ShippingAddressForm
from myApp.models import Item, Customer, ShippingAddress, QRCodeOrder, Notification, NotificationPreference, \
    SubscriptionPlan, QRCode
from .utils import send_notification, generate_styled_qr
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import cv2
import numpy as np


def create_notification(user, message):
    Notification.objects.create(user=user, message=message)


def logout_request(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('home')


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # messages.info(request, f'You are now logged in as {username}.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    form = AuthenticationForm()
    return render(request=request, template_name='account/login.html', context={'form': form})


@login_required
def home(request):
    items = Item.objects.filter(owner=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:3]
    total_notifications = Notification.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    subscription_type = request.user.get_subscription_type()
    is_premium = subscription_type != "FREE"

    items_without_qr = Item.objects.filter(owner=request.user, qr_code__isnull=True)

    context = {
        'items': items,
        'notifications': notifications,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'subscription_type': subscription_type,
        'is_premium': is_premium,
        'items_without_qr': items_without_qr,
    }
    return render(request, 'home.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado con éxito.')
            return redirect('home')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Actualiza la sesión del usuario
            messages.success(request, 'Tu contraseña ha sido cambiada con éxito.')
            return redirect('password_change_success')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'account/password_reset.html', {'form': form})


def password_change_success_view(request):
    return render(request, 'account/password_change_success.html')


@login_required
def change_profile_picture(request):
    usuario = get_object_or_404(Customer, uuid=request.user.uuid)
    if request.method == 'POST':
        form = ChangeProfilePictureForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirige a la página de perfil

    else:
        form = ChangeProfilePictureForm(instance=usuario)

    return render(request, 'change_profile_picture.html', {'form': form})


@login_required
def change_item_picture(request, item_id):
    item = get_object_or_404(Item, uuid=item_id)

    if request.method == 'POST':
        form = ChangeItemPictureForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirige a la página de perfil
    else:
        form = ChangeItemPictureForm(instance=item)

    return render(request, 'change_item_picture.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = not settings.REQUIRE_EMAIL_VERIFICATION
            user.password = make_password(form.cleaned_data['password1'])

            # Assign the free plan by default
            free_plan = SubscriptionPlan.objects.get(name='FREE')
            user.subscription_plan = free_plan

            user.save()

            if settings.REQUIRE_EMAIL_VERIFICATION and not user.email_verified:
                send_verification_email(request, user)
                messages.info(request, 'Por favor, verifica tu correo electrónico para completar el registro.')
            else:
                messages.success(request, 'Registro completado con éxito.')

            # Authenticate and login the user
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password1'],
                                backend='django.contrib.auth.backends.ModelBackend')
            if user is not None:
                login(request, user)

            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'account/signup.html', {'form': form})


def send_verification_email(request, user):
    if not settings.REQUIRE_EMAIL_VERIFICATION:
        return

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = request.build_absolute_uri(reverse('verify_email', kwargs={'uidb64': uid, 'token': token}))
    subject = 'Verify your email'
    message = f'Please click the link to verify your email: {verification_link}'
    from_email = ORGANIZATION_EMAIL
    send_mail(subject, message, from_email, [user.email], fail_silently=False)


def verify_email(request, uidb64, token):
    if not settings.REQUIRE_EMAIL_VERIFICATION:
        messages.info(request, 'Email verification is not required.')
        return redirect('home')

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Customer.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Customer.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        messages.success(request, 'Your email has been verified.')
    else:
        messages.error(request, 'The verification link was invalid or has expired.')

    return redirect('home')


@login_required
def register_item(request):
    current_items_count = Item.objects.filter(owner=request.user).count()
    can_create_new_item = current_items_count < request.user.subscription_plan.max_items

    if request.method == 'POST':
        if not can_create_new_item:
            messages.error(request, 'Has alcanzado el límite de items para tu plan actual.')
            return redirect('upgrade_to_premium')

        form = FormItem(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, 'Item registrado exitosamente.')
            return redirect('home')
    else:
        form = FormItem()

    return render(request, 'register_item.html', {
        'form': form,
        'can_create_new_item': can_create_new_item
    })


@login_required()
def edit_item(request, item_id=None):
    item = get_object_or_404(Item, uuid=item_id)

    if request.method == 'GET':
        context = {'form': FormItem(instance=item), 'uuid': item_id}
        return render(request, 'register_item.html', context)

    elif request.method == 'POST':
        form = FormItem(request.POST, request.FILES,
                        instance=item)  # Asegúrate de incluir `request.FILES` para manejar la imagen.
        if form.is_valid():
            form.save()
            messages.success(request, 'El item se ha actualizado correctamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrija los siguientes errores:')
            return render(request, 'register_item.html', {'form': form})


@login_required()
def download_qr(request, item_id):
    item = Item.objects.get(uuid=item_id)

    # Obtén la ruta de archivo del campo ImageField 'qr_code'
    qr_image_path = item.qr_code.qr_image.path

    # Verifica si el archivo existe en la ruta proporcionada
    if qr_image_path and os.path.isfile(qr_image_path):
        with (open(qr_image_path, 'rb') as qr_file):
            response = HttpResponse(qr_file.read(), content_type="image/png")
            response["Content-Disposition"] = \
                f"attachment; filename=qr_{item.owner.username}_{item.name}.png"
            return response
    else:
        # En caso de que la ruta del archivo sea inválida o el archivo no exista, puedes devolver una respuesta de
        # error o realizar otra acción apropiada.
        return HttpResponse("El archivo QR no está disponible.", status=404)


def scan_qr(request, qr_uuid):
    try:
        qr = QRCode.objects.get(uuid=qr_uuid)
        if not qr.is_activated:
            return redirect('activate_qr', qr_uuid=qr_uuid)
        elif not qr.is_assigned:
            return redirect('associate_qr_to_item', qr_uuid)
        else:
            return handle_assigned_qr(request, qr.item)
    except QRCode.DoesNotExist:
        try:
            item = Item.objects.get(qr_code__uuid=qr_uuid)
            return handle_assigned_qr(request, item)
        except Item.DoesNotExist:
            return HttpResponse("Invalid QR code", status=404)


def handle_promotional_qr(request, promo_qr):
    if promo_qr.is_used and promo_qr.associated_item:
        return handle_assigned_qr(request, promo_qr.associated_item)
    elif not promo_qr.is_used:
        if request.user.is_authenticated:
            return render(request, 'associate_qr.html', {'promo_qr': promo_qr})
        else:
            return redirect('login')
    else:
        return HttpResponse("This promotional QR code has been used but is not associated with any item.", status=400)


def handle_assigned_qr(request, item):
    owner = item.owner

    try:
        preferences = NotificationPreference.objects.get(user=owner)
    except NotificationPreference.DoesNotExist:
        preferences = None

    contact_methods = []
    show_contact_info = preferences and preferences.show_contact_info_on_scan
    if owner.subscription_plan and owner.subscription_plan.name != 'FREE':
        if preferences.email_notifications:
            contact_methods.append(('email', 'Email', owner.email if show_contact_info else None))
        if preferences.sms_notifications:
            contact_methods.append(('phone', 'Teléfono', owner.phone if show_contact_info else None))
        if preferences.whatsapp_notifications:
            contact_methods.append(('whatsapp', 'WhatsApp', owner.phone if show_contact_info else None))

    if request.method == 'POST':
        form = ContactForm(request.POST, contact_methods=contact_methods)
        if form.is_valid():
            severity = form.cleaned_data['severity']
            reason = form.cleaned_data['reason']
            message = form.cleaned_data['message']
            contact_method = form.cleaned_data.get('contact_method', '')

            if owner.can_receive_notification():
                if send_notification(owner, item, message, severity, reason):
                    messages.success(request, 'Mensaje enviado correctamente. Ya hemos notificado al dueño del QR')
                else:
                    messages.error(request, 'No se pudo enviar el mensaje. Ocurrió un error inesperado.')
            else:
                messages.error(request, 'No se pudo enviar el mensaje. El dueño del QR no puede recibir '
                                        'notificaciones en este momento.')

            return redirect('scan_qr', qr_uuid=item.qr_code.uuid)
    else:
        form = ContactForm(contact_methods=contact_methods)

    can_modify_notification_hours = False
    if owner.subscription_plan and owner.subscription_plan.can_modify_notification_hours:
        can_modify_notification_hours = True

    context = {
        'owner': owner,
        'form': form,
        'contact_methods': contact_methods,
        'is_premium': owner.subscription_plan and owner.subscription_plan.name != 'FREE',
        'can_modify_notification_hours': can_modify_notification_hours,
        'current_time': timezone.localtime(timezone.now()),
        'can_receive_notification': owner.can_receive_notification(),
        'show_contact_info': show_contact_info
    }
    return render(request, 'scan_qr.html', context)


@login_required
def upgrade_to_premium(request):
    plans = SubscriptionPlan.objects.all().order_by('price_monthly')

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        # Aquí iría la lógica de pago (por ejemplo, integración con Stripe)
        # Por ahora, simplemente actualizaremos el estado de la suscripción
        request.user.update_subscription(plan)
        messages.success(request, f'¡Felicidades! Has actualizado al plan {plan.name} por {plan.duration_days} días.')
        return redirect('manage_subscription')

    context = {
        'plans': plans,
        'current_plan': request.user.subscription_plan,
    }
    return render(request, 'upgrade_to_premium.html', context)


@login_required
def manage_subscription(request):
    context = {
        'current_plan': request.user.subscription_plan,
        'subscription_end_date': request.user.subscription_end_date,
        'auto_renew': request.user.auto_renew,
    }
    return render(request, 'manage_subscription.html', context)


@login_required
def edit_notification_preferences(request):
    try:
        preferences = NotificationPreference.objects.get(user=request.user)
    except NotificationPreference.DoesNotExist:
        preferences = NotificationPreference(user=request.user)

    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences, user=request.user)
        if form.is_valid():
            notification_schedule = form.cleaned_data.get('notification_schedule')
            if notification_schedule == '24h':
                form.instance.notification_start_time = time(0, 0)
                form.instance.notification_end_time = time(0, 0)
            elif notification_schedule == 'day':
                form.instance.notification_start_time = time(8, 0)
                form.instance.notification_end_time = time(21, 0)
            elif notification_schedule == 'night':
                form.instance.notification_start_time = time(21, 0)
                form.instance.notification_end_time = time(8, 0)
            # For 'custom', use the times provided in the form

            form.save()
            messages.success(request, 'Preferencias de notificación actualizadas correctamente.')
            return redirect('home')
    else:
        initial_data = get_initial_notification_schedule(preferences)
        form = NotificationPreferenceForm(instance=preferences, user=request.user, initial=initial_data)

    return render(request, 'edit_notification_preferences.html', {'form': form})


def get_initial_notification_schedule(preferences):
    start_time = preferences.notification_start_time
    end_time = preferences.notification_end_time

    if start_time == time(0, 0) and end_time == time(0, 0):
        return {'notification_schedule': '24h'}
    elif start_time == time(8, 0) and end_time == time(21, 0):
        return {'notification_schedule': 'day'}
    elif start_time == time(21, 0) and end_time == time(8, 0):
        return {'notification_schedule': 'night'}
    else:
        return {'notification_schedule': 'custom'}


@login_required
def view_all_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'view_all_notifications.html', {'notifications': notifications})


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('home')


@login_required
def toggle_auto_renew(request):
    if request.method == 'POST':
        request.user.auto_renew = not request.user.auto_renew
        request.user.save()
        messages.success(request, 'La configuración de autorenovación ha sido actualizada.')
    return redirect('manage_subscription')


@login_required
def order_qr_codes(request):
    if request.method == 'POST':
        form = QRCodeOrderForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = calculate_total_price(form.cleaned_data['items'])
            # print(order.total_price)
            order.save()
            form.save_m2m()
            messages.success(request, 'Pedido realizado con éxito.')
            return redirect('home')
    else:
        form = QRCodeOrderForm(user=request.user)

    default_address = ShippingAddress.objects.filter(user=request.user, default=True).first()

    return render(request, 'order_qr_codes.html', {
        'form': form,
        'default_address': default_address,
    })


def calculate_total_price(items):
    # return sum(item.price for item in items)
    return sum(2.99 for item in items)


@login_required
def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Shipping address added successfully.')
            return redirect('manage_shipping_addresses')
    else:
        form = ShippingAddressForm()
    return render(request, 'add_shipping_address.html', {'form': form})


@login_required
def edit_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shipping address updated successfully.')
            return redirect('manage_shipping_addresses')
    else:
        form = ShippingAddressForm(instance=address)
    return render(request, 'edit_shipping_address.html', {'form': form})


@login_required
def delete_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Shipping address deleted successfully.')
    return redirect('manage_shipping_addresses')


@login_required
def set_default_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.default = True
    address.save()
    messages.success(request, 'Default shipping address set successfully.')
    return redirect('manage_shipping_addresses')


@login_required
def manage_shipping_addresses(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    customer = get_object_or_404(Customer, uuid=request.user.uuid)
    default_address = customer.get_default_shipping_address()
    return render(request, 'manage_shipping_addresses.html', {
        'addresses': addresses,
        'default_address': default_address
    })


def decode_qr(image):
    # Convertir la imagen PIL a un array numpy
    np_image = np.array(image)

    # Verificar si la imagen es en escala de grises o en color
    if len(np_image.shape) == 2:
        gray = np_image
    elif len(np_image.shape) == 3:
        # Si es una imagen en color, convertirla a escala de grises
        gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    else:
        raise ValueError("Formato de imagen no soportado")

    # Asegurarse de que la imagen esté en el formato correcto para OpenCV
    gray = np.uint8(gray)

    # Inicializar el detector de QR
    qr_decoder = cv2.QRCodeDetector()

    # Detectar y decodificar el QR
    data, bbox, _ = qr_decoder.detectAndDecode(gray)

    if data:
        return data
    return None


@login_required
def associate_qr(request, item_uuid=None):
    if item_uuid:
        item = get_object_or_404(Item, uuid=item_uuid, owner=request.user)
    else:
        item = None

    if request.method == 'POST':
        secret_code = request.POST.get('secret_code')
        # print(secret_code)

        if not secret_code:
            messages.error(request, 'Por favor, proporcione un código QR válido.')
            return render(request, 'associate_qr.html', {'item': item})

        qr_uuid = secret_code.split('/')[-1]
        # print('extracción del uuid: ', qr_uuid)
        # Remove hyphens from the promo_code
        qr_uuid = qr_uuid.replace('-', '')
        # print(qr_uuid)
        try:
            qr = QRCode.objects.get(uuid=qr_uuid)

            if not qr.is_activated:
                messages.info(request, 'El código QR necesita ser activado primero.')
                return redirect('activate_qr', qr_uuid=qr.uuid)
            elif qr.is_assigned:
                messages.error(request, 'El código QR ya ha sido utilizado.')
            else:
                if item:
                    qr_image_content = None
                    if qr.qr_image:
                        # Get the QR image content
                        qr_image_content = qr.qr_image.read()

                    # Generate a filename for the new QR image
                    filename = f'{secret_code}.png'

                    qr.is_used = True
                    qr.used_by = request.user
                    qr.used_on = timezone.now()
                    qr.save()

                    item.qr_code = qr

                    # Save the QR image to the item
                    item.qr_code.qr_image.save(filename, ContentFile(qr_image_content), save=True)

                    messages.success(request, 'Código QR asociado exitosamente al ítem.')
                    return redirect('home')
                else:
                    return redirect('associate_qr_to_item', qr_uuid=secret_code.code)
        except QRCode.DoesNotExist:
            messages.error(request, 'Código QR no encontrado.')

    return render(request, 'associate_qr.html', {'item': item})


@login_required
def associate_qr_to_item(request, qr_uuid):
    qr = get_object_or_404(QRCode, uuid=qr_uuid, is_physical=True, is_activated=True, is_assigned=False)
    customer = get_object_or_404(Customer, uuid=request.user.uuid)

    if request.method == 'POST':
        item_uuid = request.POST.get('item_uuid')
        if item_uuid == 'new':
            form = FormItem(request.POST, request.FILES)
            # print(request.FILES)
            if form.is_valid():
                item = form.save(commit=False)
                item.owner = request.user
                item.qr_code = qr
                item.save()
                qr.is_assigned = True
                qr.used_by = request.user
                qr.used_on = timezone.now()
                qr.associated_item = item
                qr.save()
                messages.success(request, f'Nuevo ítem creado y asociado con el código QR {qr.uuid}.')
                return redirect('home')
        else:
            item = get_object_or_404(Item, id=item_uuid, owner=request.user)
            item.qr_code = qr
            item.save()
            qr.is_assigned = True
            qr.used_by = request.user
            qr.used_on = timezone.now()
            qr.associated_item = item
            qr.save()
            messages.success(request, f'Código QR {qr.uuid} asociado exitosamente al ítem {item.name}.')
            return redirect('home')

    available_items = Item.objects.filter(owner=request.user, qr_code__isnull=True)
    form = FormItem()

    current_items_count = Item.objects.filter(owner=request.user).count()
    can_create_new_item = current_items_count < customer.subscription_plan.max_items

    return render(request, 'associate_qr_to_item.html', {
        'qr': qr,
        'available_items': available_items,
        'form': form,
        'can_create_new_item': can_create_new_item,
        'current_items_count': current_items_count,
        'subscription_plan': customer.subscription_plan
    })


@login_required
def generate_qr(request, item_uuid):
    item = get_object_or_404(Item, uuid=item_uuid, owner=request.user)

    if not item.qr_code:
        qr_to_assign = QRCode.objects.filter(is_physical=False, is_activated=False, is_assigned=False).first()
        if not qr_to_assign:
            qr_to_assign = QRCode.objects.create(
                is_physical=False,
                is_activated=False,
                is_assigned=False,
                secret_code=''.join(random.choices(string.digits, k=6))
            )

        # Asignar el QR al item
        item.qr_code = qr_to_assign
        item.save()
        qr_to_assign.is_activated = True
        qr_to_assign.is_assigned = True
        qr_to_assign.save()

    url = f'{DOMAIN}/scan-qr/{item.qr_code.uuid}'
    qr_image = generate_styled_qr(url, item.name)
    qr_filename = f'{request.user.username}/{item.name}_qr.png'  # Ruta personalizada

    # Guardar la imagen del QR
    item.qr_code.qr_image.save(qr_filename, ContentFile(qr_image), save=True)
    messages.success(request, 'Código QR generado exitosamente.')

    return redirect('home')


@login_required
def activate_qr(request, qr_uuid):
    qr = get_object_or_404(QRCode, uuid=qr_uuid, is_activated=False)

    if request.method == 'POST':
        subject = 'Activación de Código QR'
        message = f'Tu código secreto para activar el QR es: {qr.secret_code}'
        from_email = ORGANIZATION_EMAIL
        send_mail(subject, message, from_email, [request.user.email], fail_silently=False)
        messages.success(request, 'Se ha enviado un código secreto a tu email.')
        return redirect('enter_secret_code', qr_uuid=qr_uuid)

    return render(request, 'activate_qr.html', {'qr': qr})


@login_required
def enter_secret_code(request, qr_uuid):
    qr = get_object_or_404(QRCode, uuid=qr_uuid, is_activated=False)

    if request.method == 'POST':
        secret_code = request.POST.get('secret_code')
        if secret_code == qr.secret_code:
            qr.is_activated = True
            # qr.activation_email = request.user.email
            qr.save()
            messages.success(request, 'Código QR activado correctamente. Ahora puedes asociar el QR a un item')
            return redirect('associate_qr_to_item', qr_uuid=qr_uuid)
        else:
            messages.error(request, 'Código secreto incorrecto. Inténtalo de nuevo.')

    return render(request, 'enter_secret_code.html', {'qr_uuid': qr_uuid})
