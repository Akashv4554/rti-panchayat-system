from django.shortcuts import render, get_object_or_404
from .models import RTIRequest


def rti_list(request):
    rti_requests = RTIRequest.objects.all()
    return render(request, 'rti/rti_list.html', {'rti_requests': rti_requests})


def rti_detail(request, pk):
    rti = get_object_or_404(RTIRequest, pk=pk)
    return render(request, 'rti/rti_detail.html', {'rti': rti})
