from django.db import models


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
