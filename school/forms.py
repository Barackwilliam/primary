from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Subject, Mark, Result, ClassRoom, Term

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))



class StudentForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )

    class Meta:
        model = Student
        fields = [
            'full_name', 'admission_number', 'date_of_birth', 'gender',
            'class_room', 'parent_name', 'parent_phone', 'parent_email'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Full Name'})
        self.fields['admission_number'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Admission Number'})
        self.fields['gender'].widget.attrs.update({'class': 'form-select'})
        self.fields['class_room'].widget.attrs.update({'class': 'form-select'})
        self.fields['parent_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parent Name'})
        self.fields['parent_phone'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parent Phone'})
        self.fields['parent_email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parent Email (optional)'})


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'academic_level', 'weight']


class MarkForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ['student', 'subject', 'term', 'score']


class SelectClassTermForm(forms.Form):
    class_room = forms.ModelChoiceField(queryset=ClassRoom.objects.all(), label="Choose class", required=True)
    term = forms.ModelChoiceField(queryset=Term.objects.all(), label="Choose term", required=True)


class SMSForm(forms.Form):
    class_room = forms.ModelChoiceField(queryset=ClassRoom.objects.all(), label="Class", required=True)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Message")
    send_via = forms.ChoiceField(
        choices=(('whatsapp', 'WhatsApp'), ('email', 'Email')),
        initial='whatsaap'
    )
# , ('console', 'Console')