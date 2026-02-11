from django.shortcuts import render, get_object_or_404,redirect
from .models import RTIRequest, RTIResponse, AnalystReview
from django.db.models import Count
from .forms import RTIForm

def rti_list(request):
    rti_requests = RTIRequest.objects.all().order_by('-date_filed')
    return render(request, 'rti/rti_list.html', {'rti_requests': rti_requests})


def rti_detail(request, pk):
    rti = get_object_or_404(RTIRequest, pk=pk)
    return render(request, 'rti/rti_detail.html', {'rti': rti})

def dashboard(request):
    total_rti = RTIRequest.objects.count()
    total_responses = RTIResponse.objects.count()
    delayed_responses = RTIResponse.objects.filter(is_delayed=True).count()
    vague_count = AnalystReview.objects.filter(status='VAGUE').count()
    denied_count = AnalystReview.objects.filter(status='DENIED').count()

    context = {
        'total_rti': total_rti,
        'total_responses': total_responses,
        'delayed_responses': delayed_responses,
        'vague_count': vague_count,
        'denied_count': denied_count,
    }

    return render(request, 'rti/dashboard.html', context)

def create_rti(request):
    if request.method == 'POST':
        form = RTIForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rti_list')
    else:
        form = RTIForm()

    return render(request, 'rti/create_rti.html', {'form': form})