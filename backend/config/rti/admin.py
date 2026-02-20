from django.contrib import admin
from .models import PanchayatOffice, RTIRequest, RTIResponse, AnalystReview, Appeal
from django.contrib.auth.decorators import user_passes_test

admin.site.register(PanchayatOffice)
admin.site.register(RTIRequest)
admin.site.register(RTIResponse)
admin.site.register(AnalystReview)
admin.site.register(Appeal)

def is_analyst(user):
    return user.groups.filter(name='Analyst').exists()

