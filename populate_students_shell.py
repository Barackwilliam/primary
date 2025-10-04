import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
django.setup()

from school.models import Student, ClassRoom

first_names = ["Amina", "Juma", "Neema", "Hassan", "Fatuma", "David", "Mary", "John", "Salma", "Mohammed",
               "Hawa", "Ali", "Leah", "Abdallah", "Sophia", "Yusuf", "Rashid", "Mwanajuma", "Patrick", "Grace"]
last_names = ["Mkenda", "Mnyika", "Ngoma", "Kassim", "Moshi", "Jumbe", "Mwanaidi", "Kahigi", "Nguli", "Rashid",
              "Shomari", "Bakari", "Mwanga", "Chuma", "Lukindo", "Nyoni", "Mgonja", "Mahundi", "Massawe", "Khamis"]

def random_phone():
    return f"07{random.randint(1000000, 9999999)}"

def random_dob():
    start = datetime.today() - timedelta(days=14*365)
    end = datetime.today() - timedelta(days=5*365)
    return start + (end - start) * random.random()

classes = list(ClassRoom.objects.all())

for i in range(1, 101):
    first = random.choice(first_names)
    last = random.choice(last_names)
    full_name = f"{first} {last}"
    gender = random.choice(["M", "F"])
    class_room = random.choice(classes)
    admission_number = f"ADM{1000 + i}"
    parent_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    parent_phone = random_phone()
    parent_email = f"{parent_name.replace(' ', '').lower()}@example.com"

    Student.objects.create(
        full_name=full_name,
        admission_number=admission_number,
        date_of_birth=random_dob().date(),
        gender=gender,
        class_room=class_room,
        parent_name=parent_name,
        parent_phone=parent_phone,
        parent_email=parent_email
    )

print("100 Tanzanian students created successfully!")
