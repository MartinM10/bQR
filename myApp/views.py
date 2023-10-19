import os
import smtplib
from email.message import EmailMessage
from io import BytesIO
import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseServerError, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from myApp.config import DOMAIN
from ownerQR.settings import EMAIL_HOST_USER, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_PASSWORD
from myApp.forms import CustomUserCreationForm, FormItem, ChangePasswordForm, ChangeProfilePictureForm, \
    EditUserProfileForm, ChangeItemPictureForm
from myApp.models import Item, Customer


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
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    form = AuthenticationForm()
    return render(request=request, template_name='login.html', context={'form': form})


def home(request):
    return render(request, 'home.html')


@login_required
def edit_user_profile(request):
    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirige a la página de perfil
    else:
        form = EditUserProfileForm(instance=request.user)

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

    return render(request, 'change_password.html', {'form': form})


def password_change_success_view(request):
    return render(request, 'password_change_success.html')


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


def register_user(request):
    if request.method == 'POST':
        user_creation_form = CustomUserCreationForm(request.POST)
        if user_creation_form.is_valid():
            customer = user_creation_form.save(commit=False)

            if 'image' in request.FILES:
                image = request.FILES['image']
                # Define la ubicación donde se guardará la imagen
                image_path = f'images/{customer.username}/profile_images/{image.name}'

                # Guarda la imagen en el sistema de archivos usando default_storage
                try:
                    default_storage.save(image_path, ContentFile(image.read()))
                except Exception as e:
                    print("Error al guardar la imagen. Inténtalo de nuevo. ", e.args)
                    return HttpResponseServerError("Error al guardar la imagen. Inténtalo de nuevo.")

                # Asigna la ruta de la imagen al campo correspondiente en el modelo
                customer.image = image_path

            customer.save()

            user = authenticate(username=user_creation_form.cleaned_data['username'],
                                password=user_creation_form.cleaned_data['password1'])

            login(request, user)
            return redirect('home')

    return render(request, 'register.html', context={'form': CustomUserCreationForm})


@login_required
def register_item(request):
    if request.method == 'POST':
        form = FormItem(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            owner_uuid = str(request.user.uuid)
            url = f'{DOMAIN}/scan-qr/{owner_uuid}'
            # url = f'http://localhost:8000/scan-qr/{owner_uuid}'

            # Verifica que se haya proporcionado una imagen
            if 'image' in request.FILES:
                image = request.FILES['image']

                # Verifica que el formato de la imagen sea válido (JPEG o PNG)
                if not image.content_type.startswith('image'):
                    return HttpResponseServerError("El formato de la imagen no es válido. Debe ser JPEG o PNG.")

                # Define la ubicación donde se guardará la imagen
                image_path = f'images/{request.user.username}/items/{image.name}'

                # Guarda la imagen en el sistema de archivos usando default_storage
                try:
                    default_storage.save(image_path, ContentFile(image.read()))
                except Exception as e:
                    print("Error al guardar la imagen. Inténtalo de nuevo. ", e.args)
                    return HttpResponseServerError("Error al guardar la imagen. Inténtalo de nuevo.")

                # Asigna la ruta de la imagen al campo correspondiente en el modelo
                item.image = image_path

            item.save()

            # Generar el código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Guardar la imagen del código QR en el item
            image_io = BytesIO()
            img.save(image_io, 'PNG')
            image_file = SimpleUploadedFile(f'{request.user.username}/qr_codes/{item.name}.png',
                                            image_io.getvalue(), content_type='image/png')
            item.qrCode = image_file

            item.save()
            return redirect('home')
    else:
        form = FormItem()
    return render(request, 'register_item.html', {'form': form})


@login_required()
def edit_profile(request):
    customer = get_object_or_404(Customer, uuid=request.user.uuid)
    if request.method == 'GET':
        context = {'form': EditUserProfileForm(instance=customer)}
        return render(request, 'edit_profile.html', context)

    elif request.method == 'POST':
        form = EditUserProfileForm(request.POST, request.FILES,
                                   instance=customer)  # Asegúrate de incluir `request.FILES` para manejar la imagen.
        if form.is_valid():
            form.save()
            messages.success(request, 'El perfil se ha actualizado correctamente.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrija los siguientes errores:')
            return render(request, 'edit_profile.html', {'form': form})


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

    mensaje = 'Hola, me pongo en contacto contigo para dejarte un comentario acerca de tu item. Un saludo'
    subject = 'Alarma ContactQR'
    success_message = 'Mensaje enviado correctamente. Ya hemos notificado al dueño del QR'

    email_msg = EmailMessage()
    email_msg['from'] = EMAIL_HOST_USER
    email_msg['subject'] = subject
    email_msg['to'] = owner.email
    email_msg.set_content(mensaje)

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    server.send_message(email_msg)
    server.quit()

    # success = None
    """
    try:
        pywhatkit.sendwhatmsg(phone_no=numero_destino, message=mensaje, time_hour=current_time.tm_hour,
                              time_min=current_time.tm_min + 1, wait_time=8)
        print("Envio Exitoso!")
        success = True
        message = 'El mensaje se envió correctamente. Se ha comunicado al owner'
    except Exception as e:
        message = 'Error al intentar comunicar con el owner la imagen. Inténtalo de nuevo.'
        print('ERROR al intentar comunicar ', e.args)

    context = {
        'success': success,
        'message': message
    }
    """
    context = {
        'success': True,
        'message': success_message
    }
    return render(request, 'result_send_message.html', context=context)
