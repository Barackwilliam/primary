from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import School, AcademicLevel, ClassRoom, Subject, Student, Term, Mark, Result
from .forms import StudentForm

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "motto", "phone", "logo_preview")
    search_fields = ("name", "motto", "phone")

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'logo':
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': '76122001cca4add87f02',
            })
        return formfield

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 100px;" />')
        return "No Logo"
    logo_preview.short_description = "Logo Preview"


@admin.register(AcademicLevel)
class AcademicLevelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_level", "class_teacher")
    list_filter = ("academic_level",)
    search_fields = ("name",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "academic_level", "weight")
    list_filter = ("academic_level",)
    search_fields = ("code", "name")

from .forms import StudentForm


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentForm
    list_display = ('admission_number', 'full_name', 'gender', 'class_room', 'parent_name', 'parent_phone')
    list_filter = ('gender', 'class_room')
    search_fields = ('full_name', 'admission_number', 'parent_name', 'parent_phone')


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year")
    list_filter = ("academic_year",)
    search_fields = ("name", "academic_year")


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "score", "grade")
    list_filter = ("term", "subject")
    search_fields = ("student__full_name", "student__admission_number", "subject__name")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "total", "average", "grade", "position")
    list_filter = ("term",)
    search_fields = ("student__full_name", "student__admission_number")
