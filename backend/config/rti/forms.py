from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import RTIRequest

class RTIForm(forms.ModelForm):
    class Meta:
        model = RTIRequest
        fields = '__all__'
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_filed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'panchayat': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
