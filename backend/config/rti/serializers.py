from rest_framework import serializers
from .models import RTIRequest

class RTISerializer(serializers.ModelSerializer):
    class Meta:
        model = RTIRequest
        fields = '__all__'

