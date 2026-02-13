from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404,redirect
from .models import RTIRequest, RTIResponse, AnalystReview, PanchayatOffice
from django.db.models import Count,Q
from .forms import RTIForm
from django.core.paginator import Paginator
from .models import RTIRequest, PanchayatOffice
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework import generics
from .serializers import RTISerializer
from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm
from django.db.models.functions import TruncMonth
from django.http import HttpResponseForbidden
from django.contrib import messages
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView

def is_analyst(user):
    return user.groups.filter(name='analyst').exists()

class RTIListAPI(ListAPIView):
    queryset = RTIRequest.objects.all()
    serializer_class = RTISerializer
    permission_classes = [IsAdminUser]

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


@login_required
def rti_detail(request, pk):
    rti = get_object_or_404(RTIRequest, pk=pk)

    # Optional: Role-based restriction
    # Example:
    # if request.user.role not in ["admin", "analyst"]:
    #     return HttpResponseForbidden("You are not allowed to view this RTI.")

    response = getattr(rti, "rtiresponse", None)
    review = getattr(response, "analystreview", None) if response else None

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

    # ✅ Delayed Percentage
    delayed_percentage = 0
    if total_responses > 0:
        delayed_percentage = round((delayed_responses / total_responses) * 100, 2)

    # ✅ Review Status Chart
    review_stats = list(
        AnalystReview.objects.values('status')
        .annotate(count=Count('status'))
    )

    # ✅ RTI per Panchayat Chart
    rti_per_panchayat = list(
        RTIRequest.objects.values('panchayat__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # ✅ Monthly RTI Trend Chart
    monthly_trend = list(
        RTIRequest.objects
        .annotate(month=TruncMonth('date_filed'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    return render(request, 'rti/dashboard.html', {
        'total_rti': total_rti,
        'total_responses': total_responses,
        'delayed_responses': delayed_responses,
        'delayed_percentage': delayed_percentage,
        'review_stats': review_stats,
        'rti_per_panchayat': rti_per_panchayat,
        'monthly_trend': monthly_trend,
    })


def create_rti(request):
    if request.method == "POST":
        form = RTIForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "RTI Request created successfully!")
            return redirect("dashboard")  # or redirect("/")
        else:
            print(form.errors)  # Debug errors in terminal
    else:
        form = RTIForm()

    return render(request, "rti/create_rti.html", {"form": form})


