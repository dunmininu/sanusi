from typing import Any, Dict, Iterable, List, Optional

from django.forms.models import model_to_dict
from django.db.models import Model, QuerySet, Q

from .base import BaseAgent


class DynamicDatabaseQueryAgent(BaseAgent):
    """Agent to perform dynamic queries on a Django model."""

    def __init__(self, model: type[Model]):
        self.model = model

    def run(
        self,
        filters: Optional[Dict[str, Any]] = None,
        exclude: Optional[Dict[str, Any]] = None,
        q_objects: Optional[Iterable[Q]] = None,
        values: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Return a list of dictionaries matching the given query parameters."""
        qs: QuerySet = self.model.objects.all()
        if filters:
            qs = qs.filter(**filters)
        if exclude:
            qs = qs.exclude(**exclude)
        if q_objects:
            for q in q_objects:
                qs = qs.filter(q)
        if order_by:
            qs = qs.order_by(*order_by)
        if values:
            return list(qs.values(*values))
        return [model_to_dict(obj) for obj in qs]
