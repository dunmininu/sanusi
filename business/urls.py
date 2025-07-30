from rest_framework import routers
from .views import (
    BusinessApiViewSet,
    KnowledgeBaseViewSet,
    SanusiBusinessViewSet,
    InventoryViewSet,
    CategoryViewSet,
    OrderViewSet,
    BusinessCustomerStatsView,
    BusinessProductStatsView,
    BusinessOrderStatsView,
)

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

router.register(
    r"(?P<company_id>[^/]+)/statistics",
    BusinessCustomerStatsView,
    basename="business_customer_statistics",
)

router.register(
    r"(?P<company_id>[^/]+)/statistics",
    BusinessProductStatsView,
    basename="business_product_statistics",
)

router.register(
    r"(?P<company_id>[^/]+)/statistics",
    BusinessOrderStatsView,
    basename="business_order_statistics",
)
