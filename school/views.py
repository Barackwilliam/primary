# school/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse, Http404
from django.db.models import Sum, Avg
from django.conf import settings
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import math

from .models import Student, ClassRoom, Subject, Mark, Term, Result
from .forms import LoginForm, StudentForm, SubjectForm, MarkForm, SelectClassTermForm, SMSForm

# ---------- AUTH ----------
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


# ---------- DASHBOARD ----------
@login_required
def dashboard(request):
    total_students = Student.objects.count()
    total_classes = ClassRoom.objects.count()
    return render(request, "dashboard.html", {
        "total_students": total_students,
        "total_classes": total_classes
    })


# ---------- STUDENTS ----------
@login_required
def student_list(request):
    students = Student.objects.all()
    return render(request, "students_list.html", {"students": students})
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import StudentForm

@login_required
def student_add(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully!")
            return redirect("student_list")  # Badilisha na URL yako ya list
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = StudentForm()
    return render(request, "add_student.html", {"form": form})


# ---------- ENTER MARKS (STEP 5 + STEP 6 calculations) ----------
@login_required
def enter_marks(request):
    """
    Page to select class & term first, then show table and handle posted marks.
    URL serves both selection and the marks entry form.
    """
    if request.method == "POST" and "save_marks" in request.POST:
        # Saving marks form submission
        class_id = request.POST.get("class_room")
        term_id = request.POST.get("term")
        classroom = get_object_or_404(ClassRoom, id=class_id)
        term = get_object_or_404(Term, id=term_id)
        students = classroom.students.all()
        subjects = classroom.academic_level.subjects.all()

        # Save marks
        for student in students:
            for subject in subjects:
                key = f"score_{student.id}_{subject.id}"
                value = request.POST.get(key)
                if value is not None and value != "":
                    try:
                        score = float(value)
                        if score < 0:
                            continue
                    except ValueError:
                        continue
                    Mark.objects.update_or_create(
                        student=student, subject=subject, term=term,
                        defaults={"score": score}
                    )
        # After saving marks compute results
        compute_results_for_class_term(classroom, term)
        messages.success(request, "Marks saved and results computed successfully!")
        return redirect("enter_marks")

    # GET or initial selection
    select_form = SelectClassTermForm(request.GET or None)
    class_room = None
    term = None
    students = []
    subjects = []
    if 'class_room' in request.GET and 'term' in request.GET:
        try:
            class_room = ClassRoom.objects.get(pk=request.GET.get('class_room'))
            term = Term.objects.get(pk=request.GET.get('term'))
            students = class_room.students.all()
            subjects = class_room.academic_level.subjects.all()
        except ClassRoom.DoesNotExist:
            class_room = None

    return render(request, "enter_marks.html", {
        "select_form": select_form,
        "class_room": class_room,
        "term": term,
        "students": students,
        "subjects": subjects,
    })


def compute_results_for_class_term(classroom, term):
    """
    Compute totals, averages and positions for all students in classroom for a term.
    Stores results in Result model.
    """
    students = classroom.students.all()
    subjects = list(classroom.academic_level.subjects.all())

    # 1) compute total & average per student
    results_list = []
    for student in students:
        marks_qs = Mark.objects.filter(student=student, term=term, subject__in=subjects)
        agg = marks_qs.aggregate(total=Sum('score'), avg=Avg('score'))
        total = agg['total'] or 0
        avg = agg['avg'] or 0
        if marks_qs.count() == 0:
            avg = 0
        # Save or update Result record
        result_obj, created = Result.objects.update_or_create(
            student=student, term=term,
            defaults={"total": total, "average": avg}
        )
        results_list.append(result_obj)

    # 2) compute positions (descending by total)
    # rank handling: ties get same position (dense ranking)
    ordered = sorted(results_list, key=lambda r: r.total, reverse=True)
    position = 0
    last_total = None
    dense_rank = 0
    for r in ordered:
        position += 1
        if last_total is None or r.total != last_total:
            dense_rank += 1
            last_total = r.total
        r.position = dense_rank
        r.grade = r.compute_grade()
        r.save()


# ---------- REPORT generation (STEP 7) ----------
@login_required
def reports(request):
    """
    Shows form to select class & term and generate list of students with results.
    """
    if request.method == "POST":
        form = SelectClassTermForm(request.POST)
        if form.is_valid():
            classroom = form.cleaned_data['class_room']
            term = form.cleaned_data['term']
            # Ensure results computed
            compute_results_for_class_term(classroom, term)
            results = Result.objects.filter(student__class_room=classroom, term=term).select_related('student').order_by('position')
            return render(request, "reports_list.html", {
                "classroom": classroom,
                "term": term,
                "results": results
            })
    else:
        form = SelectClassTermForm()
    return render(request, "reports.html", {"form": form})


@login_required
def report_pdf(request, class_id, term_id, student_id=None):
    """
    Generate PDF: if student_id given -> individual; otherwise whole class booklet
    """
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    term = get_object_or_404(Term, pk=term_id)
    # ensure results present
    compute_results_for_class_term(classroom, term)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def draw_student_report(y_start, student, result):
        x_margin = 40
        y = y_start
        p.setFont("Helvetica-Bold", 14)
        p.drawString(x_margin, y, f"SIDAY SCHOOL - Student Report")
        y -= 20
        p.setFont("Helvetica", 10)
        p.drawString(x_margin, y, f"Student: {student.full_name}")
        p.drawRightString(width - x_margin, y, f"Adm#: {student.admission_number}")
        y -= 15
        p.drawString(x_margin, y, f"Class: {student.class_room.name}")
        p.drawRightString(width - x_margin, y, f"Term: {term.name} {term.academic_year}")
        y -= 20

        # marks table
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_margin, y, "Subject")
        p.drawRightString(width - 200, y, "Score")
        y -= 12
        p.setFont("Helvetica", 10)
        subjects = student.class_room.academic_level.subjects.all()
        for s in subjects:
            mark = Mark.objects.filter(student=student, term=term, subject=s).first()
            score = mark.score if mark else 0
            p.drawString(x_margin, y, s.name)
            p.drawRightString(width - 200, y, str(score))
            y -= 12

        y -= 8
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_margin, y, f"Total: {result.total}")
        p.drawString(x_margin + 150, y, f"Average: {round(result.average,2)}")
        p.drawRightString(width - x_margin, y, f"Position: {result.position}   Grade: {result.grade}")
        y -= 25
        p.setFont("Helvetica", 10)
        p.drawString(x_margin, y, "Comments:")
        y -= 40
        p.rect(x_margin, y, width - 2 * x_margin, 60)
        return y - 80

    # whole class or single student
    if student_id:
        student = get_object_or_404(Student, pk=student_id, class_room=classroom)
        result = Result.objects.get(student=student, term=term)
        y = height - 60
        draw_student_report(y, student, result)
        p.showPage()
    else:
        students = classroom.students.all().order_by('admission_number')
        for student in students:
            try:
                result = Result.objects.get(student=student, term=term)
            except Result.DoesNotExist:
                result = Result(student=student, term=term, total=0, average=0, position=None, grade="")
            y = height - 60
            draw_student_report(y, student, result)
            p.showPage()

    p.save()
    buffer.seek(0)
    filename = f"report_{classroom.name}_{term.name}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)
    
from django.core.mail import send_mail
from django.conf import settings
# import pywhatkit as kit  
import os

if os.environ.get('DJANGO_ENV') != 'production':
    import pywhatkit as kit
@login_required
def sms_view(request):
    if request.method == "POST":
        form = SMSForm(request.POST)
        if form.is_valid():
            class_room = form.cleaned_data['class_room']
            message = form.cleaned_data['message']
            send_via = form.cleaned_data['send_via']

            parents = class_room.students.all().values('parent_name', 'parent_phone', 'full_name', 'parent_email')
            recipients = [
                {
                    'name': p['parent_name'],
                    'phone': p['parent_phone'],
                    'student': p['full_name'],
                    'email': p.get('parent_email', None)
                }
                for p in parents
            ]

            send_results = []

            # ---------- WhatsApp ----------
            if send_via == "whatsapp":
                for r in recipients:
                    try:
                        # pywhatkit needs time and opens browser
                        kit.sendwhatmsg_instantly(
                            r['phone'],
                            f"Habari {r['name']}, {message}"
                        )
                        send_results.append((r['phone'], "whatsapp sent"))
                    except Exception as e:
                        send_results.append((r['phone'], f"error: {e}"))

            # ---------- Email ----------
            elif send_via == "email":
                for r in recipients:
                    if r['email']:
                        try:
                            send_mail(
                                subject=f"Taarifa kwa mzazi: {r['student']}",
                                message=f"Mpendwa {r['name']},\n\n{message}\n\nShukrani.",
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[r['email']],
                                fail_silently=False,
                            )
                            send_results.append((r['email'], "email sent"))
                        except Exception as e:
                            send_results.append((r['email'], f"error: {e}"))

            # ---------- Console fallback ----------
            else:
                for r in recipients:
                    print(f"[FALLBACK] To: {r['name']} ({r['phone']}) -> {message}")
                    send_results.append((r['phone'], "console"))

            messages.success(request, f"Messages processed for {len(send_results)} parents via {send_via}.")
            return redirect("sms")
    else:
        form = SMSForm()

    return render(request, "sms.html", {"form": form})

@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "subjects_list.html", {"subjects": subjects})


from .forms import SubjectForm

@login_required
def subject_add(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject added successfully!")
            return redirect("subject_list")   # 👈 kurudi kwenye list baada ya save
    else:
        form = SubjectForm()
    return render(request, "add_subject.html", {"form": form})
