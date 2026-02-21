from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import HttpResponseForbidden

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAdminUser

from datetime import timedelta
from django.utils import timezone

from .models import (
    RTIRequest,
    RTIResponse,
    AnalystReview,
    PanchayatOffice,
    FirstAppeal,
    SecondAppeal,
)

from .forms import RTIForm, CustomLoginForm
from .serializers import RTISerializer


# ==========================================
# Utility
# ==========================================

def is_analyst(user):
    return user.groups.filter(name='analyst').exists()


# ==========================================
# API VIEW
# ==========================================

class RTIListAPI(ListCreateAPIView):
    queryset = RTIRequest.objects.all()
    serializer_class = RTISerializer
    permission_classes = [IsAdminUser]


# ==========================================
# LOGIN
# ==========================================

class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomLoginForm


# ==========================================
# RTI LIST VIEW
# ==========================================

def rti_list(request):
    query = request.GET.get('q', '')
    panchayat_id = request.GET.get('panchayat', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', '')

    rti_requests = RTIRequest.objects.all().order_by('-date_filed')

    # 🔍 Search
    if query:
        rti_requests = rti_requests.filter(
            Q(reference_number__icontains=query) |
            Q(applicant_name__icontains=query) |
            Q(subject__icontains=query)
        )

    # 🏛 Panchayat filter
    if panchayat_id:
        rti_requests = rti_requests.filter(panchayat_id=panchayat_id)

    # 📊 Status filter
    if status:
        rti_requests = rti_requests.filter(
            rtiresponse__analystreview__status=status
        )

    # 🔄 Sorting
    if sort == 'date_asc':
        rti_requests = rti_requests.order_by('date_filed')
    elif sort == 'date_desc':
        rti_requests = rti_requests.order_by('-date_filed')
    elif sort == 'status':
        rti_requests = rti_requests.order_by('rtiresponse__analystreview__status')

    panchayats = PanchayatOffice.objects.all()

    return render(request, 'rti/rti_list.html', {
        'rti_requests': rti_requests,
        'query': query,
        'panchayats': panchayats,
        'selected_panchayat': panchayat_id,
        'selected_status': status,
        'selected_sort': sort,
    })


# ==========================================
# RTI DETAIL VIEW
# ==========================================


def rti_detail(request, pk):
    rti = get_object_or_404(RTIRequest, pk=pk)

    response = getattr(rti, "rtiresponse", None)
    review = getattr(response, "analystreview", None) if response else None

    # ---- Appeals ----

    first_appeal = FirstAppeal.objects.filter(
        rti_request=rti
    ).first()

    second_appeal = None
    if first_appeal:
        second_appeal = getattr(first_appeal, "second_appeal", None)

    # 30 day rule
    can_file_first = False
    if rti.date_filed:
        allowed_date = rti.date_filed + timedelta(days=30)
        if timezone.now().date() >= allowed_date and not first_appeal:
            can_file_first = True

    return render(request, 'rti/rti_detail.html', {
        'rti': rti,
        'response': response,
        'review': review,
        'first_appeal': first_appeal,
        'second_appeal': second_appeal,
        'can_file_first': can_file_first,
    })


# ==========================================
# DASHBOARD 
# ==========================================

@login_required
@user_passes_test(is_analyst)
def dashboard(request):

    # --- RTI Stats ---
    total_rti = RTIRequest.objects.count()
    total_responses = RTIResponse.objects.count()
    delayed_responses = RTIResponse.objects.filter(is_delayed=True).count()

    delayed_percentage = 0
    if total_responses > 0:
        delayed_percentage = round((delayed_responses / total_responses) * 100, 2)

    # --- Review Status Chart ---
    review_stats = list(
        AnalystReview.objects.values('status')
        .annotate(count=Count('status'))
    )

    # --- RTI per Panchayat ---
    rti_per_panchayat = list(
        RTIRequest.objects.values('panchayat__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # --- Monthly RTI Trend ---
    monthly_trend = list(
        RTIRequest.objects
        .annotate(month=TruncMonth('date_filed'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # ===============================
    # Appeal Statistics
    # ===============================

    total_first_appeals = FirstAppeal.objects.count()
    total_second_appeals = SecondAppeal.objects.count()

    first_appeal_status = list(
        FirstAppeal.objects.values('status')
        .annotate(count=Count('status'))
    )

    second_appeal_status = list(
        SecondAppeal.objects.values('status')
        .annotate(count=Count('status'))
    )

    return render(request, 'rti/dashboard.html', {
        'total_rti': total_rti,
        'total_responses': total_responses,
        'delayed_responses': delayed_responses,
        'delayed_percentage': delayed_percentage,
        'review_stats': review_stats,
        'rti_per_panchayat': rti_per_panchayat,
        'monthly_trend': monthly_trend,

        # Appeal Data
        'total_first_appeals': total_first_appeals,
        'total_second_appeals': total_second_appeals,
        'first_appeal_status': first_appeal_status,
        'second_appeal_status': second_appeal_status,
    })


# ==========================================
# CREATE RTI
# ==========================================

def create_rti(request):
    if request.method == "POST":
        form = RTIForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "RTI Request created successfully!")
            return redirect("dashboard")
        else:
            print(form.errors)
    else:
        form = RTIForm()

    return render(request, "rti/create_rti.html", {"form": form})


# ==========================================
# FILE FIRST APPEAL
# ==========================================

@login_required
def file_first_appeal(request, pk):
    rti = get_object_or_404(RTIRequest, pk=pk)

    # Prevent duplicate
    if FirstAppeal.objects.filter(rti_request=rti).exists():
        messages.error(request, "First Appeal already filed.")
        return redirect("rti_detail", pk=rti.id)

    # 30-day rule
    allowed_date = rti.date_filed + timedelta(days=30)
    if timezone.now().date() < allowed_date:
        messages.error(request, "You can file First Appeal only after 30 days.")
        return redirect("rti_detail", pk=rti.id)

    if request.method == "POST":
        reference_number = request.POST.get("reference_number")
        request_pdf = request.FILES.get("request_pdf")

        appeal = FirstAppeal(
            rti_request=rti,
            user=request.user,
            reference_number=reference_number,
            request_pdf=request_pdf
        )

        appeal.full_clean()
        appeal.save()

        messages.success(request, "First Appeal filed successfully.")
        return redirect("rti_detail", pk=rti.id)

    return render(request, "rti/file_first_appeal.html", {"rti": rti})


# ==========================================
# FILE SECOND APPEAL
# ==========================================

@login_required
def file_second_appeal(request, pk):
    first_appeal = get_object_or_404(FirstAppeal, pk=pk)

    # Prevent duplicate
    if hasattr(first_appeal, "second_appeal"):
        messages.error(request, "Second Appeal already filed.")
        return redirect("rti_detail", pk=first_appeal.rti_request.id)

    if request.method == "POST":
        reference_number = request.POST.get("reference_number")
        request_pdf = request.FILES.get("request_pdf")

        appeal = SecondAppeal(
            first_appeal=first_appeal,
            user=request.user,
            reference_number=reference_number,
            request_pdf=request_pdf
        )

        appeal.full_clean()
        appeal.save()

        messages.success(request, "Second Appeal filed successfully.")
        return redirect("rti_detail", pk=first_appeal.rti_request.id)

    return render(
        request,
        "rti/file_second_appeal.html",
        {"first_appeal": first_appeal}
    )


from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from django.conf import settings

from django.db.models import Count
from django.db.models.functions import TruncMonth
from io import BytesIO
import matplotlib.pyplot as plt


from django.utils.dateparse import parse_date
from django.utils.timezone import now
from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
import matplotlib.pyplot as plt
import os
from django.conf import settings
import os
from django.contrib.staticfiles import finders
from reportlab.platypus import Image
from reportlab.lib.units import inch



@login_required
@user_passes_test(is_analyst)
def export_dashboard_pdf(request):

    # =========================
    # SAFE DATE HANDLING
    # =========================
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    try:
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None
    except Exception:
        start_date = None
        end_date = None

    # Default: Current Financial Year (April 1 → Today)
    today = date.today()
    if not start_date or not end_date:
        if today.month >= 4:
            start_date = date(today.year, 4, 1)
        else:
            start_date = date(today.year - 1, 4, 1)
        end_date = today

    # =========================
    # BASE QUERYSET
    # =========================
    rti_queryset = RTIRequest.objects.filter(
        date_filed__range=[start_date, end_date]
    )

    # =========================
    # KPI DATA
    # =========================
    total_rti = rti_queryset.count()

    responses_queryset = RTIResponse.objects.filter(
        rti_request__in=rti_queryset
    )

    total_responses = responses_queryset.count()
    delayed_responses = responses_queryset.filter(is_delayed=True).count()

    delayed_percentage = (
        round((delayed_responses / total_responses) * 100, 2)
        if total_responses > 0 else 0
    )

    first_appeals = FirstAppeal.objects.filter(
        rti_request__in=rti_queryset
    )

    second_appeals = SecondAppeal.objects.filter(
        first_appeal__rti_request__in=rti_queryset
    )

    # =========================
    # AGGREGATIONS (FILTERED)
    # =========================
    review_stats = AnalystReview.objects.filter(
    response__rti_request__in=rti_queryset
).values("status").annotate(count=Count("id"))

    first_status = first_appeals.values("status").annotate(count=Count("id"))
    second_status = second_appeals.values("status").annotate(count=Count("id"))

    panchayat_data = rti_queryset.values(
        "panchayat__name"
    ).annotate(count=Count("id")).order_by("-count")

    monthly_data = rti_queryset.annotate(
        month=TruncMonth("date_filed")
    ).values("month").annotate(
        count=Count("id")
    ).order_by("month")

    # =========================
    # PDF RESPONSE
    # =========================
    filename = f"RTI_Report_{start_date}_to_{end_date}.pdf"

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # =========================
    # COVER PAGE
    # =========================
    logo_path = finders.find("images/logo.png")

    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2 * inch, height=2 * inch)
            elements.append(logo)
        except Exception as e:
            # Optional: log error instead of crashing
            print(f"Logo load error: {e}")
    else:
        # Optional fallback (adds spacing so layout stays aligned)
        elements.append(Spacer(1, 0.5 * inch))

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(
        "<b>Department of Rural Development & Panchayat Raj</b>",
        styles["Heading2"]
    ))
    elements.append(Paragraph("RTI Monitoring System", styles["Heading3"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        "<b>Comprehensive Dashboard Report</b>",
        styles["Heading1"]
    ))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(
        f"Date Range: {start_date} to {end_date}",
        styles["Normal"]
    ))

    elements.append(Paragraph(
        f"Generated on: {now().strftime('%d %b %Y %H:%M')}",
        styles["Normal"]
    ))

    elements.append(PageBreak())

    # =========================
    # EXECUTIVE SUMMARY
    # =========================
    elements.append(Paragraph("Executive Summary", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    summary_data = [
        ["Metric", "Value"],
        ["Total RTIs", total_rti],
        ["Total Responses", total_responses],
        ["Delayed Responses", delayed_responses],
        ["Delayed %", f"{delayed_percentage}%"],
        ["First Appeals", first_appeals.count()],
        ["Second Appeals", second_appeals.count()],
    ]

    table = Table(summary_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(table)
    elements.append(PageBreak())

    # =========================
    # CHART GENERATOR
    # =========================
    def create_chart(title, labels, values, chart_type="bar"):
        if not values:
            return None

        plt.figure(figsize=(8, 4))

        if chart_type == "pie":
            plt.pie(values, labels=labels, autopct="%1.1f%%")
        elif chart_type == "line":
            plt.plot(labels, values)
        else:
            plt.bar(labels, values)

        plt.title(title)
        plt.xticks(rotation=45)

        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png")
        plt.close()
        buffer.seek(0)

        return Image(buffer, width=6*inch, height=3*inch)

    # =========================
    # CHART SECTION
    # =========================
    elements.append(Paragraph("Charts Overview", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    charts = [
        ("Analyst Review Status", review_stats, "bar"),
        ("First Appeal Status", first_status, "pie"),
        ("Second Appeal Status", second_status, "pie"),
    ]

    for title, queryset, chart_type in charts:
        data = list(queryset)
        if data:
            labels = [d["status"] for d in data]
            values = [d["count"] for d in data]
            chart = create_chart(title, labels, values, chart_type)
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 0.3 * inch))

    if monthly_data:
        labels = [m["month"].strftime("%b %Y") for m in monthly_data]
        values = [m["count"] for m in monthly_data]
        chart = create_chart("Monthly RTI Trend", labels, values, "line")
        if chart:
            elements.append(chart)

    elements.append(PageBreak())

    # =========================
    # PANCHAYAT TABLE
    # =========================
    elements.append(Paragraph("Panchayat Breakdown", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    p_table_data = [["Panchayat", "RTI Count"]]

    for p in panchayat_data:
        p_table_data.append([
            p["panchayat__name"] or "N/A",
            p["count"]
        ])

    p_table = Table(p_table_data, colWidths=[3*inch, 2*inch])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    elements.append(p_table)

    doc.build(elements)
    return response