from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

class PanchayatOffice(models.Model):
    name = models.CharField(max_length=200)
    district = models.CharField(max_length=200)
    state = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RTIRequest(models.Model):
    reference_number = models.CharField(max_length=100, unique=True)
    applicant_name = models.CharField(max_length=200)
    date_filed = models.DateField()
    subject = models.TextField()
    panchayat = models.ForeignKey(PanchayatOffice, on_delete=models.CASCADE)

    # 📄 Original RTI Application
    original_application = models.FileField(
        upload_to='rti/original/',
        null=True,
        blank=True
    )

    # 📩 Acknowledgement Document
    acknowledgement_document = models.FileField(
        upload_to='rti/acknowledgements/',
        null=True,
        blank=True
    )

    acknowledgement_date = models.DateField(null=True, blank=True)

    # 📄 Response Document
    response_document = models.FileField(
        upload_to='rti/responses/',
        null=True,
        blank=True
    )

    response_date = models.DateField(null=True, blank=True)

    @property
    def status(self):
        if self.response_document:
            return "Responded"
        elif self.acknowledgement_document:
            return "Acknowledged"
        else:
            return "Filed"


    def __str__(self):
        return self.reference_number


class RTIResponse(models.Model):
    rti_request = models.OneToOneField(RTIRequest, on_delete=models.CASCADE)
    reply_text = models.TextField()
    date_replied = models.DateField()
    is_delayed = models.BooleanField(default=False)

    def __str__(self):
        return f"Response to {self.rti_request.reference_number}"


class AnalystReview(models.Model):
    STATUS_CHOICES = [
        ('COMPLETE', 'Complete Information'),
        ('VAGUE', 'Vague Reply'),
        ('DENIED', 'Information Denied'),
        ('DELAYED', 'Delayed Response'),
    ]

    response = models.OneToOneField(RTIResponse, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks = models.TextField()

    def __str__(self):
        return self.status


class FirstAppeal(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('DECIDED', 'Decided'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rti_request = models.ForeignKey(
        RTIRequest,
        on_delete=models.CASCADE,
        related_name="first_appeals"
    )

    reference_number = models.CharField(max_length=100)
    date_filed = models.DateField(default=timezone.now)

    request_pdf = models.FileField(upload_to='appeals/first/request/')
    response_pdf = models.FileField(
        upload_to='appeals/first/response/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):

        # ✅ 30-day rule validation
        if self.rti_request.date_filed:
            allowed_date = self.rti_request.date_filed + timedelta(days=30)

            if timezone.now().date() < allowed_date:
                raise ValidationError(
                    "First Appeal can only be filed after 30 days from RTI filing date."
                )

        # ✅ Prevent duplicate first appeal
        if FirstAppeal.objects.filter(
            rti_request=self.rti_request
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                "First Appeal already exists for this RTI."
            )

    def __str__(self):
        return f"First Appeal - {self.reference_number}"



class SecondAppeal(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('DECIDED', 'Decided'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    first_appeal = models.OneToOneField(
        FirstAppeal,
        on_delete=models.CASCADE,
        related_name="second_appeal"
    )

    reference_number = models.CharField(max_length=100)
    date_filed = models.DateField(default=timezone.now)

    request_pdf = models.FileField(upload_to='appeals/second/request/')
    response_pdf = models.FileField(
        upload_to='appeals/second/response/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):

        # Ensure First Appeal exists
        if not self.first_appeal:
            raise ValidationError(
                "Second Appeal must be linked to a First Appeal."
            )

    def __str__(self):
        return f"Second Appeal - {self.reference_number}"


