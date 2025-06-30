from django.urls import path, include
from rest_framework import routers
from .views import BusinessApiViewSet, KnowledgeBaseViewSet, SanusiBusinessViewSet, InventoryViewSet, CategoryViewSet, \
    OrderViewSet

router = routers.DefaultRouter()
router.register("business", BusinessApiViewSet, basename="business")
router.register(
    r"business/(?P<company_id>[^/]+)/knowledge-base",
    KnowledgeBaseViewSet,
    basename="knowledge-base",
)
router.register(r"sanusi-business", SanusiBusinessViewSet, basename="sanusi_business")
router.register(r"(?P<company_id>[^/]+)/inventory", InventoryViewSet, basename="inventory")
router.register(r"(?P<company_id>[^/]+)/category", CategoryViewSet, basename="category")
router.register(r"(?P<company_id>[^/]+)/order", OrderViewSet, basename="order")

