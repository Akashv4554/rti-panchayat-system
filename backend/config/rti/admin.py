from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from .models import (
    PanchayatOffice,
    RTIRequest,
    RTIResponse,
    AnalystReview,
    FirstAppeal,
    SecondAppeal
)

admin.site.register(PanchayatOffice)
admin.site.register(RTIRequest)
admin.site.register(RTIResponse)
admin.site.register(AnalystReview)
admin.site.register(FirstAppeal)
admin.site.register(SecondAppeal)

def is_analyst(user):
    return user.groups.filter(name='Analyst').exists()

