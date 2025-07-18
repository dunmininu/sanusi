from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation, get_user_model

from rest_framework import serializers

from accounts.models import EmailAddress
import logging

logger = logging.getLogger(__name__)

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
    first_name = serializers.CharField(required=True, min_length=3)
    last_name = serializers.CharField(required=True, min_length=3)
    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def email_address_exists(self, email):
        user_exists = User.objects.filter(email__iexact=email).exists()
        if not user_exists:
            user_exists = EmailAddress.objects.filter(email__iexact=email).exists()
        return user_exists

    def validate_email(self, value):
        if self.email_address_exists(value):
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        try:
            password_validation.validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """Validate that passwords match"""
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        return attrs

    def save(self):
        email = self.validated_data["email"]
        password = self.validated_data["password"]
        first_name = self.validated_data["first_name"]
        last_name = self.validated_data["last_name"]

        user = User(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        validate_user_password_attribute_similarity(password, user)
        user.save()
        EmailAddress.objects.create(
            user=user, email=user.email, is_primary=True, is_verified=False
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    onboarding_progress = serializers.SerializerMethodField()
    onboarding_completion_percentage = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "date_joined",
            "is_active",
            "businesses",
            "settings",
            "step", 
            "complete_on_boarding",
            "onboarding_progress", 
            "onboarding_completion_percentage"
        ]

        read_only_fields = [
            "id",
            "is_staff",
            "date_joined",
            "is_active",
            "businesses",
        ]
    def get_onboarding_progress(self, obj):
        return obj.get_onboarding_progress()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            # Check if user exists
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")

            # Check if user is active
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

        return attrs
    
class OnboardingUpdateSerializer(serializers.Serializer):
    step = serializers.IntegerField(min_value=1, max_value=7)

class OnboardingProgressSerializer(serializers.Serializer):
    current_step = serializers.IntegerField()
    total_steps = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    is_complete = serializers.BooleanField()
    remaining_steps = serializers.IntegerField()
