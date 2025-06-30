from rest_framework import routers
from .views import AuthenticationViewSet

router = routers.DefaultRouter()
router.register("auth", AuthenticationViewSet, basename="auth")
