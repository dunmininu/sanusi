from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation, get_user_model

from rest_framework import serializers

from accounts.models import EmailAddress

User = get_user_model()

def validate_user_password_attribute_similarity(password, user):
    if settings.DEBUG:
        return

    try:
        validator = password_validation.UserAttributeSimilarityValidator()
        validator.validate(password, user)
    except ValidationError as e:
        raise serializers.ValidationError({"password": e.messages})

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField()

    def email_address_exists(self, email):
        user_exists = User.objects.filter(email__iexact=email).exists()
        if not user_exists:
            user_exists = EmailAddress.objects.filter(email__iexact=email)
        return user_exists

    def validate_email(self, value):
        if self.email_address_exists(value):
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value
    

    def save(self):
        email = self.validated_data['email']
        password = self.validated_data['password']


        user = User(email=email)
        user.set_password(password)
        validate_user_password_attribute_similarity(password, user)
        user.save()
        EmailAddress.objects.create(
            user=user, email=user.email, is_primary=True, is_verified=False
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    model = User
    fields = [
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "date_joined",
        "is_active",
    ]
    