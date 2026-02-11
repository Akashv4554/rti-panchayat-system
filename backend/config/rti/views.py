from django.shortcuts import render, get_object_or_404,redirect
from .models import RTIRequest, RTIResponse, AnalystReview, PanchayatOffice
from django.db.models import Count,Q
from .forms import RTIForm
from django.core.paginator import Paginator
from django.db.models import Q
from .models import RTIRequest, PanchayatOffice
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework import generics
from .serializers import RTISerializer
from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm

def is_analyst(user):
    return user.groups.filter(name='analyst').exists()

class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomLoginForm

class RTIListAPI(generics.ListCreateAPIView):
    queryset = RTIRequest.objects.all()
    serializer_class = RTISerializer

def rti_list(request):
    query = request.GET.get('q', '')
    panchayat_id = request.GET.get('panchayat', '')
    status = request.GET.get('status', '')

    rti_requests = RTIRequest.objects.all().order_by('-date_filed')

    # 🔍 Search filter
    if query:
        rti_requests = rti_requests.filter(
            Q(reference_number__icontains=query) |
            Q(applicant_name__icontains=query) |
            Q(subject__icontains=query)
        )

    # 🏛 Filter by Panchayat
    if panchayat_id:
        rti_requests = rti_requests.filter(panchayat_id=panchayat_id)

    # 📊 Filter by Review Status
    if status:
        rti_requests = rti_requests.filter(
            rtiresponse__analystreview__status=status
        )

    panchayats = PanchayatOffice.objects.all()

    paginator = Paginator(rti_requests, 5)  # 5 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    sort = request.GET.get('sort', '')

    if sort == 'date_asc':
        rti_requests = rti_requests.order_by('date_filed')
    elif sort == 'date_desc':
     rti_requests = rti_requests.order_by('-date_filed')
    elif sort == 'status':
        rti_requests = rti_requests.order_by('rtiresponse__analystreview__status')


    return render(request, 'rti/rti_list.html', {
        'page_obj': page_obj,
        'query': query,
        'panchayats': panchayats,
        'selected_panchayat': panchayat_id,
        'selected_status': status,
        'selected_sort': sort,
    })



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

@login_required
@user_passes_test(is_analyst)
def dashboard(request):
    total_rti = RTIRequest.objects.count()
    total_responses = RTIResponse.objects.count()
    delayed_responses = RTIResponse.objects.filter(is_delayed=True).count()

    review_stats = list(
        AnalystReview.objects.values('status')
        .annotate(count=Count('status'))
    )

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