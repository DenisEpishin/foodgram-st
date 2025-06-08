from django.urls import path
from .views import (UserMeView, UsersView, LoginView, LogoutView, AvatarView,
                    PasswordView, UserInfoView, SubscriptionView, SubscribeView)


urlpatterns = [
    path('', UsersView.as_view()),
    path('<int:user_id>/', UserInfoView.as_view()),
    path('<int:user_id>/subscribe/', SubscribeView.as_view()),
    path('subscriptions/', SubscriptionView.as_view()),
    path('token/login/', LoginView.as_view()),
    path('token/logout/', LogoutView.as_view()),
    path('me/', UserMeView.as_view()),
    path('me/avatar/', AvatarView.as_view()),
    path('set_password/', PasswordView.as_view())
]

