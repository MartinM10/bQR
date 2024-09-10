import os
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
    ChangeItemPictureForm, NotificationPreferenceForm, EditProfileForm
from myApp.models import Item, Customer
from .models import Notification, NotificationPreference, SubscriptionPlan
from .utils import send_notification, generate_styled_qr
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.hashers import make_password


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
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:3]
    total_notifications = Notification.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    subscription_type = request.user.get_subscription_type()
    is_premium = subscription_type != "FREE"

    context = {
        'notifications': notifications,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'subscription_type': subscription_type,
        'is_premium': is_premium,
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
    if request.method == 'POST':
        form = FormItem(request.POST, request.FILES)
        if form.is_valid():
            current_items_count = Item.objects.filter(owner=request.user).count()
            if current_items_count < request.user.subscription_plan.max_items:
                item = form.save(commit=False)
                item.owner = request.user

                # Save the item image
                if 'image' in request.FILES:
                    item.image = request.FILES['image']

                item.save()

                # Generate the QR code
                owner_uuid = str(request.user.uuid)
                url = f'{DOMAIN}/scan-qr/{owner_uuid}'
                qr_image = generate_styled_qr(url, item.name)

                # Save the QR code image
                qr_filename = f'{item.name}_qr.png'
                item.qrCode.save(qr_filename, ContentFile(qr_image), save=True)

                messages.success(request, 'Item registrado exitosamente.')
                return redirect('home')
            else:
                messages.error(request,
                               'Has alcanzado el límite de items para tu plan actual. Considera actualizar tu plan.')
    else:
        form = FormItem()
    return render(request, 'register_item.html', {'form': form})


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
    qr_image_path = item.qrCode.path

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


def scan_qr(request, owner_id):
    owner = get_object_or_404(Customer, uuid=owner_id)

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

            full_message = f"Gravedad: {severity}\nMotivo: {reason}\nMétodo de contacto: {contact_method}\nMensaje: {message}"

            if owner.can_receive_notification():
                if send_notification(owner, full_message, severity, reason):
                    messages.success(request, 'Mensaje enviado correctamente. Ya hemos notificado al dueño del QR')
                else:
                    messages.error(request, 'No se pudo enviar el mensaje. Ocurrió un error inesperado.')
            else:
                messages.error(request,
                               'No se pudo enviar el mensaje. El dueño del QR no puede recibir notificaciones en este momento.')

            return redirect('scan_qr', owner_id=owner_id)
    else:
        form = ContactForm(contact_methods=contact_methods)

    context = {
        'owner': owner,
        'form': form,
        'contact_methods': contact_methods,
        'is_premium': owner.subscription_plan and owner.subscription_plan.name != 'FREE',
        'can_modify_notification_hours': owner.subscription_plan and owner.subscription_plan.can_modify_notification_hours if owner.subscription_plan else False,
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
