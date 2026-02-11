from django import forms
from .models import RTIRequest

class RTIForm(forms.ModelForm):
    class Meta:
        model = RTIRequest
        fields = [
            'reference_number',
            'applicant_name',
            'date_filed',
            'subject',
            'panchayat'
        ]
