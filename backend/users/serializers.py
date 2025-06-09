from backend.constants import MIN_INT, MAX_INT, MAX_IMAGE_SIZE, MB_SIZE
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as Dve
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Recipe
from rest_framework import serializers
from .models import User, Follow


class NewUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]

    def create(self, data):
        try:
            user = User.objects.create_user(
                email=data['email'],
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password']
            )
            return user
        except Exception as e:
            raise serializers.ValidationError(str(e))

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Такой email уже есть.")
        else:
            return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Такой ник уже есть.")
        else:
            return value

    def validate_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user)
        except Dve as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def to_representation(self, instance):
        return {
            'email': instance.email,
            'id': instance.id,
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }


class GetUserSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        r = self.context.get('request')
        if (r and r.user.is_authenticated and
                r.user.follower.filter(following=obj).exists()):
            return True
        return False


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar', ]

    def validate_avatar(self, value):
        try:
            if value.size > MAX_IMAGE_SIZE * MB_SIZE:
                    raise serializers.ValidationError(
                        f"Максимальный размер изображения {MAX_IMAGE_SIZE}Мб.")
        except Dve as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class PasswordSerializer(serializers.ModelSerializer):

    new_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        required=True
    )
    current_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        fields = [
            'new_password',
            'current_password'
        ]

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user)
        except Dve as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate_current_password(self, value):
        user = self.context['request'].user
        if authenticate(username=user.email, password=value):
            return value
        else:
            raise serializers.ValidationError("Неверный старый пароль.")

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class UserRecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class SubscriptionSerializer(GetUserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request:
            r_max = request.query_params.get('recipes_limit')
        else:
            r_max = None
        rows = obj.recipes_of_author.all()
        if r_max:
            try:
                r_max = int(r_max)
                rows = rows[:r_max]
            except ValueError:
                pass
        serialized = UserRecipeSerializer(
            rows, many=True, context=self.context,
        )
        return serialized.data

    def get_recipes_count(self, obj):
        return obj.recipes_of_author.count()


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ['following', ]

    def create(self, data):
        data['follower'] = self.context['request'].user
        return super().create(data)

    def validate(self, data):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({'detail': 'Доступ запрещён.'})
        current_user = request.user
        following = data['following']
        if current_user == following:
            raise serializers.ValidationError(
                {'detail': 'Нельзя подписываться на себя.'}
            )
        if current_user.follower.filter(
                following=following,
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Вы уже подписаны.'}
            )
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.following,
            context=self.context,
        ).data
