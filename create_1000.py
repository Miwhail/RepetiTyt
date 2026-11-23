import random
from datetime import date, time, timedelta

from app.models import Subject, Tutor, TutorSubject, LessonSlot

subjects_obj = []
for name in ['Математика', 'Физика', 'Английский язык', 'Программирование']:
    s, _ = Subject.objects.get_or_create(name=name)
    subjects_obj.append(s)

first = ['Анна', 'Мария', 'Ольга', 'Елена', 'Дмитрий', 'Сергей', 'Иван', 'Павел']
last = ['Иванова', 'Петрова', 'Смирнова', 'Козлова', 'Соколов', 'Морозов', 'Волков', 'Новиков']

created = 0
for i in range(1000):
    tutor = Tutor.objects.create(
        full_name=f'{random.choice(last)} {random.choice(first)}',
        email=f'tutor{i}@example.com',
        phone=f'+7 (9{random.randint(10, 99)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
        experience_years=random.randint(1, 25),
        rating=round(random.uniform(3.5, 5.0), 1),
    )
    TutorSubject.objects.create(
        tutor=tutor,
        subject=random.choice(subjects_obj),
        rate_per_hour=random.randint(800, 5000),
        moderation_status='approved',
    )
    for k in range(3):
        hour = 9 + k * 3
        LessonSlot.objects.create(
            tutor=tutor,
            date=date.today() + timedelta(days=k + 1),
            start_time=time(hour, 0),
            end_time=time(hour + 1, 0),
        )
    created += 1

print(f'Готово: создано {created} репетиторов, {created * 3} слотов')
