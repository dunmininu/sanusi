import hashlib

from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, When
from loguru import logger


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets, generics, mixins, filters
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
from django_filters import FilterSet, NumberFilter
import django_filters

from sanusi_backend.decorators.telemetry import with_telemetry
from sanusi_backend.utils.error_handler import ErrorHandler, LogicException

from .models import Business, Product, Category
from business.private.models import KnowledgeBase, EscalationDepartment
from .serializers import (
    BulkCreateKnowledgeBaseSerializer,
    BusinessSerializer,
    KnowledgeBaseBulkUpdateSerializer,
    KnowledgeBaseDeleteSerializer,
    KnowledgeBaseSerializer,
    SanusiBusinessCreateSerializer,
    InventorySerializer,
    CategorySerializer
)
from sanusi_backend.classes.custom import  CustomPagination, BaseSearchFilter


class BusinessApiViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    lookup_field = "company_id"
    permission_classes = [IsAuthenticated] 

    def get_object(self):
        return get_object_or_404(Business, company_id=self.kwargs.get("company_id"))

    @transaction.atomic
    @with_telemetry(span_name="create_business")
    def create(self, request, *args, current_span=None, **kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                    if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}
            
            # Log request start
            logger.info(
                "Creating business",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "business.id": str(serializer.instance.company_id),
                    "operation.success": True
                })
                
            # Log success
            logger.info(
                "Business created successfully",
                business_id=str(serializer.instance.company_id),
                user_id=str(request.user.id)
            )

            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error creating business: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )


    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "company_id",
                openapi.IN_PATH,
                description="Company ID",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "company_id",
                openapi.IN_PATH,
                description="Company ID",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    @transaction.atomic
    @with_telemetry(span_name="update_business")
    def update(self, request, *args, current_span=None,**kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                        if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}

            # Log request start
            logger.info(
                "update business",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)


            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "business.id": str(serializer.instance.company_id),
                    "operation.success": True
                })
                
            # Log success
            logger.info(
                "Business update successfully",
                business_id=str(serializer.instance.company_id),
                user_id=str(request.user.id)
            )
            return Response(serializer.data)
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error update business: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class KnowledgeBaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for managing knowledge bases for a business.
    """

    serializer_class = KnowledgeBaseSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["is_company_description"]
    permission_classes = [IsAuthenticated] 

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    def get_queryset(self):
        """
        Get all knowledge bases for a specific business.
        """
        if getattr(self, "swagger_fake_view", False):
            # Return an empty queryset when accessed by DRF-YASG for schema generation
            return KnowledgeBase.objects.none()

        business_id = self.kwargs.get("company_id")
        business = get_object_or_404(Business, company_id=business_id)
        return business.business_kb.all()

    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {"knowledgebase_id": self.kwargs["knowledgebase_id"]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            context["company_id"] = self.kwargs["company_id"]
        return context

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a single knowledge base for the specified business.
        """
        business_id = self.kwargs.get("company_id")
        business = get_object_or_404(Business, company_id=business_id)
        if not business:
            raise ValidationError("Business does not exist")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)  # Pass the Business instance
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False, methods=["put"], url_path="(?P<knowledgebase_id>[^/.]+)/update"
    )
    def update_knowledge_base(self, request, *args, **kwargs):
        """
        Update the specified knowledge base for a specific business.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], url_path="(?P<knowledgebase_id>[^/.]+)/retrive"
    )
    def retrieve_knowledge_base(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=no_body)
    @action(
        detail=False,
        methods=["delete"],
        url_path="(?P<knowledgebase_id>[^/.]+)/delete",
    )
    @transaction.atomic
    def delete_knowledgebase(self, request, *args, **kwargs):
        """
        Delete the specified knowledge base for a specific business.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=BulkCreateKnowledgeBaseSerializer,
    )
    def bulk_create(self, request, *args, **kwargs):
        business_id = self.kwargs.get("company_id")
        business = Business.objects.get(company_id=business_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(
        detail=False,
        methods=["put"],
        url_path="bulk_update",
        serializer_class=KnowledgeBaseBulkUpdateSerializer,
    )
    def bulk_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        knowledgebase_data = serializer.validated_data
        knowledgebase_ids = [data["knowledgebase_id"] for data in knowledgebase_data]
        knowledgebase_updates = {
            data["knowledgebase_id"]: {
                "title": data["title"],
                "content": data["content"],
            }
            for data in knowledgebase_data
        }

        # Validate if all knowledgebase_id exist
        for kb_id in knowledgebase_ids:
            try:
                KnowledgeBase.objects.get(knowledgebase_id=kb_id)
            except ObjectDoesNotExist:
                raise ValidationError(f"The knowledgebase_id {kb_id} does not exist.")

        whens_title = [
            When(knowledgebase_id=knowledgebase_id, then=value["title"])
            for knowledgebase_id, value in knowledgebase_updates.items()
        ]

        whens_content = [
            When(knowledgebase_id=knowledgebase_id, then=value["content"])
            for knowledgebase_id, value in knowledgebase_updates.items()
        ]

        KnowledgeBase.objects.filter(knowledgebase_id__in=knowledgebase_ids).update(
            title=Case(*whens_title, output_field=models.CharField()),
            content=Case(*whens_content, output_field=models.TextField()),
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class SanusiBusinessViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SanusiBusinessCreateSerializer
    permission_classes = [IsAuthenticated] 

    @transaction.atomic
    def create(self, request):
        serializer = SanusiBusinessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = serializer.validated_data.get("company_id")
        business_name = serializer.validated_data.get("business_name")
        knowledge_bases = serializer.validated_data.get("knowledge_base")
        instructions = serializer.validated_data.get("instructions")
        escalation_departments = serializer.validated_data.get("escalation_departments")
        token_input = f"{company_id}-{business_name}"
        token = hashlib.sha256(token_input.encode("utf-8")).hexdigest()

        validated_company_id = Business.objects.filter(company_id=company_id).exists()
        if not validated_company_id:
            # Create Business instance
            business = Business.objects.create(
                company_id=company_id,
                name=business_name,
                token=token,
                reply_instructions=instructions,
            )
        else:
            raise Exception("company_id already exists")

        # Create KnowledgeBase instances
        knowledge_base_instances = [
            KnowledgeBase(
                business=business,
                title="Default Title",  # You can update this value
                content=knowledge_base,
            )
            for knowledge_base in knowledge_bases
        ]
        KnowledgeBase.objects.bulk_create(knowledge_base_instances)

        # Create EscalationDepartment instances
        department_instances = [
            EscalationDepartment(
                business=business,
                name=department_name,
            )
            for department_name in escalation_departments
        ]
        EscalationDepartment.objects.bulk_create(department_instances)

        response_data = {
            "company_id": company_id,
            "business_name": business_name,
            "token": token,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)




# For Product model
class ProductFilter(BaseSearchFilter):
    class Meta(BaseSearchFilter.Meta):
        model = Product
        fields = BaseSearchFilter.Meta.fields + ['category', 'category__name', 'sku']

# Add custom relation filters
ProductFilter.add_relation_filter('category', 'category__id', lookup_expr='exact', filter_class=NumberFilter)
ProductFilter.add_relation_filter('category__name', 'category__name')
ProductFilter.add_relation_filter('sku', 'sku')

class InventoryViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    queryset = Product.objects.all()
    serializer_class = InventorySerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated] 

    def get_object(self):
        return get_object_or_404(Product, id=self.kwargs.get("id"))
   
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter
    search_fields = ['name', 'category_name', 'sku']
    ordering_fields = ['date_created', 'last_updated', 'name', 'category_name', 'sku']
    ordering = ['-date_created']  # Default ordering
    pagination_class = CustomPagination
    queryset = Product.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.kwargs.get("company_id")
        if company_id:
            queryset = queryset.filter(business_id=company_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List customers with filtering and pagination
        
        Query Parameters:
        - name: Filter by name (case-insensitive partial match)
        - email: Filter by email (case-insensitive partial match)
        - date_created_after: Filter customers created after this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        - date_created_before: Filter customers created before this date
        - last_updated_after: Filter customers updated after this date
        - last_updated_before: Filter customers updated before this date
        - search: Search across name, email, and phone number
        - ordering: Order by field (prefix with - for descending)
        - page: Page number
        - page_size: Number of items per page (max 100)
        
        Examples:
        /customers/?name=john&email=gmail
        /customers/?date_created_after=2023-01-01&date_created_before=2023-12-31
        /customers/?search=john&ordering=-date_created&page=2&page_size=50
        """
        return super().list(request, *args, **kwargs)
    
    
    @transaction.atomic
    @with_telemetry(span_name="create_product")
    def create(self, request, *args, current_span=None, **kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                        if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}


            # Log request start
            logger.info(
                "Creating product",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)


            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "product.id": str(serializer.instance.id),
                    "operation.success": True
                })
                
            # Log success
            logger.info(
                "product created successfully",
                product_id=str(serializer.instance.id),
                user_id=str(request.user.id)
            )


            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error creating product: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )

    
    @transaction.atomic
    @with_telemetry(span_name="update_product")
    def update(self, request, *args, current_span=None, **kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                        if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}

            # Log request start
            logger.info(
                "Updating product",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "product.id": str(serializer.instance.id),
                    "operation.success": True
                })
               
                
                # Log success
                logger.info(
                    "product updated successfully",
                    product_id=str(serializer.instance.id),
                    user_id=str(request.user.id)
                )


            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error update product: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )

class CategoryViewSet(
    mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated] 

    def get_object(self):
        return get_object_or_404(Product, id=self.kwargs.get("id"))
   
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['date_created', 'last_updated', 'name']
    ordering = ['-date_created']  # Default ordering
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.kwargs.get("id")
        if company_id:
            queryset = queryset.filter(id=id)
        return queryset
    

    def list(self, request, *args, **kwargs):
        """
        List customers with filtering and pagination
        
        Query Parameters:
        - name: Filter by name (case-insensitive partial match)
        - date_created_after: Filter customers created after this date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        - date_created_before: Filter customers created before this date
        - last_updated_after: Filter customers updated after this date
        - last_updated_before: Filter customers updated before this date
        - search: Search across name
        - ordering: Order by field (prefix with - for descending)
        - page: Page number
        - page_size: Number of items per page (max 100)
        
        """
        return super().list(request, *args, **kwargs)
    

    @transaction.atomic
    @with_telemetry(span_name="create_category")
    def create(self, request, *args, current_span=None, **kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                        if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}

            # Log request start
            logger.info(
                "Creating category",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

               
            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "category.id": str(serializer.instance.id),
                    "operation.success": True
                })
                
            # Log success
            logger.info(
                "category created successfully",
                category_id=str(serializer.instance.id),
                user_id=str(request.user.id)
            )


            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error creating category: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )

    
    @transaction.atomic
    @with_telemetry(span_name="update_category")
    def update(self, request, *args, current_span=None, **kwargs):
        try:
            
            # Log sensitive data carefully - avoid logging passwords, tokens, etc.
            safe_data = {k: v for k, v in request.data.items() 
                        if k not in ['password', 'token', 'secret', 'key', 'access', 'refresh']}

            # Log request start
            logger.info(
                "Updating category",
                user_id=str(request.user.id),
                user_email=request.user.email,
                data_keys=list(safe_data.keys())
            )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # Set success attributes using the current span
            if current_span:
                current_span.set_attributes({
                    "category.id": str(serializer.instance.category.id),
                    "operation.success": True
                })
                
            # Log success
            logger.info(
                "category updated successfully",
                category_id=str(serializer.instance.category.id),
                user_id=str(request.user.id)
            )


            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Handle unexpected exceptions
            ErrorHandler.log_and_raise(
                message=f"Unexpected error update category: {str(e)}",
                exception_class=LogicException,
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id)
                }
            )

    
    