from django import forms
from .models import Business, EscalationDepartment

# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Field, ButtonHolder, Submit


class EscalationDepartmentForm(forms.ModelForm):
    class Meta:
        model = EscalationDepartment
        fields = ["name"]


EscalationDepartmentFormSet = forms.inlineformset_factory(
    Business, EscalationDepartment, form=EscalationDepartmentForm, extra=1
)


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ["name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.escalation_department_formset = EscalationDepartmentFormSet(
            instance=self.instance,
            data=self.data or None,
            prefix="escalation_department",
        )

    def is_valid(self):
        is_valid = super().is_valid()
        is_valid = is_valid and self.escalation_department_formset.is_valid()
        return is_valid

    def save(self, commit=True):
        business = super().save(commit=False)
        if commit:
            business.save()
        self.escalation_department_formset.instance = business
        self.escalation_department_formset.save()
        return business
