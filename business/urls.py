from django.urls import path, include
from rest_framework import routers
from .views import BusinessApiViewSet, KnowledgeBaseViewSet, EnifBusinessViewSet

router = routers.DefaultRouter()
router.register("business", BusinessApiViewSet, basename="business")
router.register(
    r"business/(?P<company_id>\w+)/knowledge-base",
    KnowledgeBaseViewSet,
    basename="knowledge-base",
)
router.register(r"enif-business", EnifBusinessViewSet, basename="enif_business")
