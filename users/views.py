from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, GenericAPIView
from users.models import CustomUser
from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
# from .models import ConfirmationCode
import random
import string
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import CustomTokenObtainSerializer
from django.core.cache import cache
from users.tasks import send_otp_email



class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                is_active=False
            )

            code = ''.join(random.choices(string.digits, k=6))
            cache.set(f"confirm_code:{user.id}", code, timeout=300)
            send_otp_email.delay(email, code)


        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'user_id': user.id,
                'confirmation_code': code
            }
        )


class AuthorizationAPIView(GenericAPIView):  
    serializer_class = AuthValidateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={'error': 'неверный email или пароль'}
            )
        if not user.check_password(password):
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={'error': 'неверный email или пароль'}
            )
        if not user.is_active:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={'error': 'аккаунт не подтверждён'}
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(data={'key': token.key})


class ConfirmUserAPIView(GenericAPIView): 
    serializer_class = ConfirmationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        code = serializer.validated_data['code']

        user = CustomUser.objects.get(id=user_id)
        key = f'confirm_code:{user_id}'
        cached_code = cache.get(key)

        if cached_code is None:
            return Response({'error': 'Код подтверждения не найден или истёк'}, status=status.HTTP_400_BAD_REQUEST)
        if cached_code != code:
            return Response({'error': 'Неверный код'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.is_active = True
            user.save()
            cache.delete(key)
            token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'User аккаунт успешно активирован',
            'key': token.key
        })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer