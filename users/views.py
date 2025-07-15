from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import CustomTokenObtainSerializer
from users.models import CustomUser
from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer
)
from .models import ConfirmationCode
import random
import string


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
            confirmation_code = ConfirmationCode.objects.create(
                user=user,
                code=code
            )

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

        with transaction.atomic():
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

            ConfirmationCode.objects.filter(user=user).delete()

        return Response(
            status=status.HTTP_200_OK,
            data={
                'message': 'User аккаунт успешно активирован',
                'key': token.key
            }
        )
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer