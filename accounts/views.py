from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    OnboardingUpdateSerializer,
    InviteSerializer,
    AcceptInviteSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
import secrets

from loguru import logger
from sanusi_backend.decorators.telemetry import with_telemetry
from sanusi_backend.utils.error_handler import ErrorHandler, LogicException
from sanusi_backend.permissions import HasScopes

from .models import Invite, Role, EmailAddress
from .services.oauth import OAuthService


# Create your views here.
User = get_user_model()


class AuthenticationViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def get_serializer_class(self):
        if self.action == "register":
            return RegisterSerializer
        elif self.action == "profile":
            return UserSerializer
        return self.serializer_class

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully", schema=UserSerializer
            ),
            400: openapi.Response(description="Bad request"),
        },
    )
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get user profile",
        responses={
            200: UserSerializer,
            401: openapi.Response(description="Unauthorized"),
        },
    )
    @action(detail=False, methods=["get"])
    def profile(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Login user",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "token": openapi.Schema(type=openapi.TYPE_STRING),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "businesses": openapi.Schema(type=openapi.TYPE_STRING),
                                "settings": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "default_business": openapi.Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                    },
                                ),
                                "step": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "complete_on_boarding": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                "onboarding_progress": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "total_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "progress_percentage": openapi.Schema(
                                    type=openapi.TYPE_NUMBER
                                ),
                                "is_complete": openapi.Schema(
                                    type=openapi.TYPE_BOOLEAN
                                ),
                                "remaining_steps": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                    },
                                ),
                                "onboarding_completion_percentage": openapi.Schema(
                                    type=openapi.TYPE_NUMBER
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Invalid credentials"),
        },
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            # Authenticate user
            user = authenticate(request, username=email, password=password)

            if user:
                if not user.is_active:
                    return Response(
                        {"error": "Account is disabled"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                user_serializer = UserSerializer(user)

                return Response(
                    {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": user_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Logout user (blacklist refresh token)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Refresh token to blacklist"
                )
            },
            required=["refresh"],
        ),
        responses={
            200: openapi.Response(description="Logged out successfully"),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Unauthorized"),
        },
    )
    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Refresh JWT token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Refresh token"
                )
            },
            required=["refresh"],
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Invalid token"),
        },
    )
    @action(detail=False, methods=["post"])
    def refresh(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            return Response(
                {
                    "access": str(token.access_token),
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        
    @swagger_auto_schema(
    operation_description="Get user onboarding progress",
    responses={
        200: openapi.Response(
            description="Onboarding progress retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "total_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "progress_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                    "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "remaining_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        401: openapi.Response(description="Unauthorized"),
    },
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def onboarding_progress(self, request):
        """Get current user's onboarding progress"""
        user = request.user
        progress = user.get_onboarding_progress()
        
        return Response(progress, status=status.HTTP_200_OK)

    @swagger_auto_schema(
    operation_description="Update user onboarding step",
    request_body=OnboardingUpdateSerializer,
    responses={
        200: openapi.Response(
            description="Onboarding step updated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "progress": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "total_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "progress_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "remaining_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                        },
                    ),
                },
            ),
        ),
        400: openapi.Response(description="Bad request"),
        401: openapi.Response(description="Unauthorized"),
    },
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    @with_telemetry(span_name="update_onboarding_step")
    def update_onboarding_step(self, request, *args, current_span=None, **kwargs):
        """Update user's onboarding step"""
        serializer = OnboardingUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            # Log validation failure
            logger.warning(
                "Onboarding step update failed validation",
                user_id=str(request.user.id),
                user_email=request.user.email,
                errors=serializer.errors,
            )
            ErrorHandler.log_and_raise(
                message=f"Onboarding step update failed validation: {str(serializer.errors)}",
                exception_class=LogicException,
                error_code="VALIDATION_ERROR",
                status_code=400,
                log_level="critical",
                extra_data={"user_id": str(request.user.id)},
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        step = serializer.validated_data["step"]
        user = request.user

        try:
            is_complete = user.update_onboarding_step(step)
            progress = user.get_onboarding_progress()

            message = (
                "Onboarding completed!" if is_complete else f"Step {step} completed successfully"
            )

            # Set telemetry attributes
            if current_span:
                current_span.set_attributes({
                    "onboarding.step": step,
                    "onboarding.is_complete": is_complete,
                    "operation.success": True,
                })

            # Log success
            logger.info(
                "User onboarding step updated",
                user_id=str(user.id),
                step=step,
                is_complete=is_complete,
            )

            return Response(
                {
                    "message": message,
                    "current_step": user.step,
                    "is_complete": is_complete,
                    "progress": progress,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error updating onboarding step: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=400,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(user.id),
                },
            )

            return Response(
                {"error": f"Unexpected error updating onboarding step: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
    @swagger_auto_schema(
    operation_description="Move to next onboarding step",
    responses={
        200: openapi.Response(
            description="Moved to next onboarding step successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "progress": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "current_step": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "total_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "progress_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                            "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "remaining_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                        },
                    ),
                },
            ),
        ),
        400: openapi.Response(description="Bad request - already at max step"),
        401: openapi.Response(description="Unauthorized"),
    },
)
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def next_onboarding_step(self, request):
        """Move user to next onboarding step"""
        user = request.user
        
        if user.step >= user.TOTAL_ONBOARDING_STEPS:
            return Response(
                {"error": "User has already completed all onboarding steps"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        is_complete = user.next_onboarding_step()
        progress = user.get_onboarding_progress()
        
        message = "Onboarding completed!" if is_complete else f"Moved to step {user.step}"
        
        return Response(
            {
                "message": message,
                "current_step": user.step,
                "is_complete": is_complete,
                "progress": progress,
            },
            status=status.HTTP_200_OK,
        )

    # ----------- Invitation & User Management -----------

    required_scopes = ["auth.manage_users"]

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, HasScopes],
    )
    def invite(self, request):
        """Invite a user via email."""
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = secrets.token_urlsafe(48)
        invite = Invite.objects.create(
            email=serializer.validated_data["email"],
            token=token,
            invited_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        roles_ids = serializer.validated_data.get("roles", [])
        if roles_ids:
            invite.roles.set(Role.objects.filter(id__in=roles_ids))

        message = serializer.validated_data.get("message", "")
        send_mail(
            "You're invited",
            message,
            None,
            [invite.email],
            fail_silently=True,
        )
        return Response({"token": invite.token}, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        url_path="accept-invite",
        permission_classes=[AllowAny],
    )
    def accept_invite(self, request):
        """Accept an invitation."""
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        invite = get_object_or_404(Invite, token=token, is_used=False)
        if invite.expires_at < timezone.now():
            return Response({"error": "Invite expired"}, status=400)

        if User.objects.filter(email__iexact=invite.email).exists():
            return Response({"error": "User already exists"}, status=400)

        user = User.objects.create(email=invite.email)
        user.set_password(password)
        user.save()
        EmailAddress.objects.create(user=user, email=user.email, is_primary=True, is_verified=True)
        if invite.roles.exists():
            user.roles.set(invite.roles.all())

        invite.is_used = True
        invite.save(update_fields=["is_used"])

        logger.info("Invite accepted", invite=str(invite.id), user=str(user.id))

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["delete"],
        url_path="users/(?P<user_id>[^/.]+)",
        permission_classes=[IsAuthenticated, HasScopes],
    )
    def remove_user(self, request, user_id=None):
        """Deactivate a user account."""
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"status": "deactivated"}, status=status.HTTP_200_OK)

    # -------- OAuth ---------

    @action(
        detail=False,
        methods=["get"],
        url_path="oauth/(?P<provider>[^/.]+)/init",
        permission_classes=[AllowAny],
    )
    def oauth_init(self, request, provider=None):
        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state
        redirect_uri = request.build_absolute_uri()
        url = OAuthService.get_auth_url(provider, state, redirect_uri)
        return Response({"auth_url": url})

    @action(
        detail=False,
        methods=["get", "post"],
        url_path="oauth/(?P<provider>[^/.]+)/callback",
        permission_classes=[AllowAny],
    )
    def oauth_callback(self, request, provider=None):
        code = request.data.get("code") or request.query_params.get("code")
        state = request.data.get("state") or request.query_params.get("state")
        if state != request.session.get("oauth_state"):
            return Response({"error": "Invalid state"}, status=400)
        redirect_uri = request.build_absolute_uri()
        tokens = OAuthService.exchange_code(provider, code, redirect_uri)
        profile = OAuthService.fetch_profile(provider, tokens.get("access_token"))
        email = profile.get("email")
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": profile.get("given_name", ""),
                "last_name": profile.get("family_name", ""),
            },
        )
        if created:
            EmailAddress.objects.create(
                user=user, email=user.email, is_primary=True, is_verified=True
            )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )
