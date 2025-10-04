from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Avg

class School(models.Model):
    name = models.CharField(max_length=150)
    motto = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)  # Uploadcare UUID

    def __str__(self):
        return self.name

    def get_og_image_url(self):
        if self.logo:
            return f"https://ucarecdn.com/{self.logo}/-/resize/1200x630/-/format/auto/"
        return ''

    def get_image_url(self):
        if self.logo:
            return f"https://ucarecdn.com/{self.logo}/-/format/jpg/-/quality/smart/"
        return ''


class AcademicLevel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    academic_level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=50)
    class_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="class_teacher")

    def __str__(self):
        return f"{self.name} ({self.academic_level})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    academic_level = models.ForeignKey(AcademicLevel, on_delete=models.CASCADE, related_name="subjects")
    weight = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.academic_level})"



class Student(models.Model):
    GENDER_CHOICES = (("M", "Male"), ("F", "Female"))

    full_name = models.CharField(max_length=150)
    admission_number = models.CharField(max_length=30, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="students")
    parent_name = models.CharField(max_length=150)
    parent_phone = models.CharField(max_length=20)
    parent_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} - {self.admission_number}"


class Term(models.Model):
    name = models.CharField(max_length=50)  # Term 1, Term 2
    academic_year = models.CharField(max_length=20)  # e.g. 2025/2026

    def __str__(self):
        return f"{self.name} - {self.academic_year}"


class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="marks")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        unique_together = ("student", "subject", "term")

    def grade(self):
        if self.score >= 80:
            return "A"
        elif self.score >= 60:
            return "B"
        elif self.score >= 50:
            return "C"
        elif self.score >= 40:
            return "D"
        return "F"

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.term}): {self.score}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="results")
    total = models.FloatField(default=0)
    average = models.FloatField(default=0)
    position = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=2, blank=True)

    class Meta:
        unique_together = ("student", "term")
        ordering = ['-total']

    def compute_grade(self):
        if self.average >= 80:
            return "A"
        elif self.average >= 60:
            return "B"
        elif self.average >= 50:
            return "C"
        elif self.average >= 40:
            return "D"
        return "F"

    def __str__(self):
        return f"{self.student} - {self.term}: {self.total} ({self.average})"
