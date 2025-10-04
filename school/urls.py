# school/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.student_add, name="student_add"),

    path("enter-marks/", views.enter_marks, name="enter_marks"),  # main marks page (select & enter)
    path("reports/", views.reports, name="reports"),
    path("reports/pdf/<int:class_id>/<int:term_id>/", views.report_pdf, name="report_pdf_class"),
    path("reports/pdf/<int:class_id>/<int:term_id>/<int:student_id>/", views.report_pdf, name="report_pdf_student"),
    path("subjects/", views.subject_list, name="subject_list"),   # 👈 hii ndiyo mpya
    path("subjects/add/", views.subject_add, name="subject_add"),

    path("sms/", views.sms_view, name="sms"),
]
