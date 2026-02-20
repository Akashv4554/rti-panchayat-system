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

from django.db import models
from django.contrib.auth.models import User


class Appeal(models.Model):
    APPEAL_TYPE_CHOICES = [
        ('FIRST', 'First Appeal'),
        ('SECOND', 'Second Appeal'),
    ]

    STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('UNDER_REVIEW', 'Under Review'),
    ('DECIDED', 'Decided'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Link to RTI (required for First Appeal)
    rti_request = models.ForeignKey(
        'RTIRequest',   # replace with your actual RTI model name
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Link to First Appeal (required for Second Appeal)
    parent_appeal = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    appeal_type = models.CharField(max_length=10, choices=APPEAL_TYPE_CHOICES)
    reference_number = models.CharField(max_length=100)
    date_filed = models.DateField()

    request_pdf = models.FileField(upload_to='appeals/requests/')
    response_pdf = models.FileField(upload_to='appeals/responses/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    

    def clean(self):

        # FIRST APPEAL VALIDATION
        if self.appeal_type == 'FIRST':

            if not self.rti_request:
                raise ValidationError("First Appeal must be linked to an RTI Request.")

            # ✅ 30-day condition
            if self.rti_request.date_filed:
                allowed_date = self.rti_request.date_filed + timedelta(days=30)
                if timezone.now().date() < allowed_date:
                    raise ValidationError("First Appeal can only be filed after 30 days from RTI filing date.")

            # ✅ Prevent duplicate FIRST appeal
            if Appeal.objects.filter(
                rti_request=self.rti_request,
                appeal_type='FIRST'
            ).exclude(pk=self.pk).exists():
                raise ValidationError("First Appeal already filed for this RTI.")

            self.parent_appeal = None

        # SECOND APPEAL VALIDATION
        if self.appeal_type == 'SECOND':

            if not self.parent_appeal:
                raise ValidationError("Second Appeal must be linked to a First Appeal.")

            if self.parent_appeal.appeal_type != 'FIRST':
                raise ValidationError("Second Appeal must link to a First Appeal only.")

            self.rti_request = None