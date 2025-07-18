from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    OnboardingUpdateSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from loguru import logger
from sanusi_backend.decorators.telemetry import with_telemetry
from sanusi_backend.utils.error_handler import ErrorHandler, LogicException


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
                                        "progress_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
                                        "is_complete": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        "remaining_steps": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    },
                                ),
                                "onboarding_completion_percentage": openapi.Schema(type=openapi.TYPE_NUMBER),
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
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(user.id),
                },
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        step = serializer.validated_data["step"]
        user = request.user

        try:
            is_complete = user.update_onboarding_step(step)
            progress = user.get_onboarding_progress()

            message = "Onboarding completed!" if is_complete else f"Step {step} completed successfully"

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
