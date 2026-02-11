from django.contrib import admin
from .models import PanchayatOffice, RTIRequest, RTIResponse, AnalystReview

admin.site.register(PanchayatOffice)
admin.site.register(RTIRequest)
admin.site.register(RTIResponse)
admin.site.register(AnalystReview)
