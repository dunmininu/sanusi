from rest_framework import mixins, viewsets

from django.contrib.auth import get_user_model

from accounts.serializers import RegisterSerializer, UserSerializer

# Create your views here.
User = get_user_model()


class AuthenticationViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
