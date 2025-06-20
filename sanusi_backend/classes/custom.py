
from rest_framework.pagination import PageNumberPagination
from django_filters import FilterSet, CharFilter, DateTimeFilter, NumberFilter

# Custom Pagination Class
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50




class BaseSearchFilter(FilterSet):
    # Common filters that can be reused
    name = CharFilter(field_name='name', lookup_expr='icontains')
    date_created_after = DateTimeFilter(field_name='date_created', lookup_expr='gte')
    date_created_before = DateTimeFilter(field_name='date_created', lookup_expr='lte')
    last_updated_after = DateTimeFilter(field_name='last_updated', lookup_expr='gte')
    last_updated_before = DateTimeFilter(field_name='last_updated', lookup_expr='lte')
    
    class Meta:
        # This will be overridden in child classes
        abstract = True
        fields = [
            'name', 
            'date_created_after', 'date_created_before',
            'last_updated_after', 'last_updated_before'
        ]
        
    @classmethod
    def add_relation_filter(cls, field_name, relation_path, lookup_expr='icontains', filter_class=CharFilter):
        """
        Dynamically add a relation filter
        Usage: ProductFilter.add_relation_filter('category', 'category__name')
        """
        cls.base_filters[field_name] = filter_class(
            field_name=relation_path, 
            lookup_expr=lookup_expr
        )
        cls._meta.fields.append(field_name)