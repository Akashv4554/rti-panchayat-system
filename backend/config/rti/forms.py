from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import RTIRequest, FirstAppeal, SecondAppeal


# ======================================
# RTI REQUEST FORM
# ======================================

class RTIForm(forms.ModelForm):
    class Meta:
        model = RTIRequest
        fields = '__all__'
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_filed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'panchayat': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()

        file_fields = [
            'original_application',
            'acknowledgement_document',
            'response_document'
        ]

        for field in file_fields:
            file = cleaned_data.get(field)
            if file and not file.name.lower().endswith('.pdf'):
                self.add_error(field, "Only PDF files are allowed.")

        return cleaned_data


# ======================================
# LOGIN FORM
# ======================================

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


# ======================================
# FIRST APPEAL FORM
# ======================================

class FirstAppealForm(forms.ModelForm):
    class Meta:
        model = FirstAppeal
        fields = [
            'rti_request',
            'reference_number',
            'date_filed',
            'request_pdf',
        ]
        widgets = {
            'rti_request': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_filed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        request_pdf = cleaned_data.get("request_pdf")

        if request_pdf and not request_pdf.name.lower().endswith('.pdf'):
            self.add_error("request_pdf", "Only PDF files are allowed.")

        return cleaned_data


# ======================================
# SECOND APPEAL FORM
# ======================================

class SecondAppealForm(forms.ModelForm):
    class Meta:
        model = SecondAppeal
        fields = [
            'first_appeal',
            'reference_number',
            'date_filed',
            'request_pdf',
        ]
        widgets = {
            'first_appeal': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_filed': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        request_pdf = cleaned_data.get("request_pdf")
        first_appeal = cleaned_data.get("first_appeal")

        if request_pdf and not request_pdf.name.lower().endswith('.pdf'):
            self.add_error("request_pdf", "Only PDF files are allowed.")

        if not first_appeal:
            self.add_error(
                "first_appeal",
                "Second appeal must be linked to a First Appeal."
            )

        return cleaned_data