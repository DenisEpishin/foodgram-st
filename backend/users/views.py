from datetime import datetime
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from .models import User
from .serializers import (NewUserSerializer, GetUserSerializer,
                          AvatarSerializer, PasswordSerializer,
                          SubscriptionSerializer, SubscribeSerializer)


class LoginView(generics.GenericAPIView):

    def post(self, request):
        u = request.data.get('email', None)
        p = request.data.get('password', None)
        if u and p:
            user = authenticate(request, username=u, password=p)
            if user:
                token = AccessToken.for_user(user)
                return Response(
                    {'auth_token': str(token)},
                    status=status.HTTP_200_OK
                )
        return Response(
            {'detail': 'Неверный email или пароль.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            t = str(request.auth)
            access_token = AccessToken(token=t)
            tblack, created = OutstandingToken.objects.get_or_create(
                token=t,
                defaults={
                    'user': request.user,
                    'jti': access_token['jti'],
                    'expires_at': datetime.fromtimestamp(access_token['exp']),
                }
            )
            BlacklistedToken.objects.get_or_create(token=tblack)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TokenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UsersList:
    queryset = User.objects.all()


class UserMeView(UsersList, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetUserSerializer

    def get_object(self):
        return self.request.user


class UsersView(UsersList, generics.ListAPIView):

    def post(self, request):
        serialized = self.get_serializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        return Response(serialized.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NewUserSerializer
        return GetUserSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class UserInfoView(UsersList, generics.RetrieveAPIView):
    serializer_class = GetUserSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'user_id'


class AvatarView(UsersList, generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarSerializer

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            path_to_file = user.avatar.path
            av_storage = user.avatar.storage
            av_storage.delete(path_to_file)
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordView(UsersList, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        serialized = self.get_serializer(data=request.data)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return User.objects.filter(following__follower=self.request.user)


class SubscribeView(generics.CreateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscribeSerializer

    def create(self, request, *args, **kwargs):
        following = get_object_or_404(User, id=kwargs['user_id'])
        serialized = self.get_serializer(data={
            'following': following.id,
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        f_id = kwargs.get('user_id')
        f_user = get_object_or_404(
            User, id=f_id,
        )
        unfollowing, _ = request.user.follower.filter(
            following=f_user,
        ).delete()
        if unfollowing:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'detail': 'Вы не подписчик.'},
                status=status.HTTP_400_BAD_REQUEST
            )
