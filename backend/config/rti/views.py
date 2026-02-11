from django.shortcuts import render, get_object_or_404,redirect
from .models import RTIRequest, RTIResponse, AnalystReview
from django.db.models import Count
from .forms import RTIForm

def rti_list(request):
    rti_requests = RTIRequest.objects.all().order_by('-date_filed')
    return render(request, 'rti/rti_list.html', {'rti_requests': rti_requests})


def rti_detail(request, pk):
    rti = RTIRequest.objects.get(pk=pk)

    response = None
    review = None

    try:
        response = rti.rtiresponse
        review = response.analystreview
    except:
        pass

    return render(request, 'rti/rti_detail.html', {
        'rti': rti,
        'response': response,
        'review': review
    })

def dashboard(request):
    total_rti = RTIRequest.objects.count()
    total_responses = RTIResponse.objects.count()
    delayed_responses = RTIResponse.objects.filter(is_delayed=True).count()

    review_stats = AnalystReview.objects.values('status').annotate(count=Count('status'))

    return render(request, 'rti/dashboard.html', {
        'total_rti': total_rti,
        'total_responses': total_responses,
        'delayed_responses': delayed_responses,
        'review_stats': review_stats,
    })

def create_rti(request):
    if request.method == 'POST':
        form = RTIForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rti_list')
    else:
        form = RTIForm()

    return render(request, 'rti/create_rti.html', {'form': form})