"""jarvis_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings

from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


from business.urls import router as business_router
from chat.urls import router as chat_router

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Jarvis API",
#         default_version="v1",
#         description="API documentation for your project",
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
#     url="https://{}{}".format(settings.ALLOWED_HOSTS[0], settings.API_PREFIX)
#     if not settings.DEBUG
#     else None,
# )


# combine_router = routers.DefaultRouter()
# combine_router.registry.extend(business_router.registry)
# combine_router.registry.extend(chat_router.registry)

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("jarvis/", include("jarvis.urls")),
#     path("", include(combine_router.urls)),
# ]


# if settings.DEBUG:
#     urlpatterns += [
#         re_path(
#             r"^swagger(?P<format>\.json|\.yaml)$",
#             schema_view.without_ui(cache_timeout=0),
#             name="schema-json",
#         ),
#         re_path(
#             r"^swagger/$",
#             schema_view.with_ui("swagger", cache_timeout=0),
#             name="schema-swagger-ui",
#         ),
#         re_path(
#             r"^redoc/$",
#             schema_view.with_ui("redoc", cache_timeout=0),
#             name="schema-redoc",
#         ),
#     ]


schema_view = get_schema_view(
    openapi.Info(
        title="Jarvis API",
        default_version="v1",
        description="API documentation for your project",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url="https://{}{}".format(settings.ALLOWED_HOSTS[0], settings.API_PREFIX)
    if not settings.DEBUG
    else None,
)

combine_router = routers.DefaultRouter()
combine_router.registry.extend(business_router.registry)
combine_router.registry.extend(chat_router.registry)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("jarvis/", include("jarvis.urls")),
    path("", include(combine_router.urls)),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json",
        ),
        re_path(
            r"^swagger/$",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        re_path(
            r"^redoc/$",
            schema_view.with_ui("redoc", cache_timeout=0),
            name="schema-redoc",
        ),
    ]


# Define the info dictionary for Swagger documentation
def swagger_info():
    return openapi.Info(
        title="Your API Title",
        default_version="v1",
        description="Your API Description",
        # Other info fields...
    )
