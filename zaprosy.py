from django.db.models import Avg, Count, Q
from app.models import Lesson, Subject, Tutor

SEP = "=" * 78

def show(title, orm_text, qs):
    print(SEP)
    print(title)
    print("ORM:", orm_text)
    print("SQL :", qs.query)
    for row in qs[:10]:
        print("    ", row)
    print()

qs1 = (Lesson.objects.filter(status="planned", price__gte=1200)
       .select_related("slot__tutor", "subject", "client").order_by("slot__date"))
show("1. Фильтрация: запланированные занятия дороже 1200 руб.",
     'Lesson.objects.filter(status="planned", price__gte=1200).select_related(...)', qs1)

qs2 = Tutor.objects.filter(is_active=True).order_by("-rating")[:5]
print(SEP)
print("2. Сортировка: топ-5 репетиторов по рейтингу")
print("ORM: Tutor.objects.filter(is_active=True).order_by('-rating')[:5]")
print("SQL :", qs2.query)
for t in qs2:
    print("    ", t.full_name, "-", t.rating)
print()

qs3 = Subject.objects.annotate(n_lessons=Count("lessons"), avg_price=Avg("lessons__price"))
print(SEP)
print("3. Агрегация: количество занятий и средняя цена по предметам")
print("ORM: Subject.objects.annotate(n_lessons=Count('lessons'), avg_price=Avg('lessons__price'))")
print("SQL :", qs3.query)
for s in qs3:
    avg = round(s.avg_price, 2) if s.avg_price is not None else "-"
    print(f"    {s.name}: занятий {s.n_lessons}, средняя цена {avg}")
print()

qs4 = (Lesson.objects.filter(status="completed")
       .select_related("slot__tutor", "subject", "client").order_by("slot__date"))
show("4. select_related: проведённые занятия одним запросом",
     'Lesson.objects.filter(status="completed").select_related("slot__tutor", "subject", "client")', qs4)

qs5 = (Subject.objects.annotate(n_tutors=Count("tutor_cards", filter=Q(tutor_cards__moderation_status="approved")))
       .prefetch_related("tutor_cards__tutor").order_by("name"))
print(SEP)
print("5. prefetch_related: одобренные репетиторы по каждому предмету")
print("ORM: Subject.objects.annotate(...).prefetch_related('tutor_cards__tutor')")
print("SQL :", qs5.query)
for s in qs5:
    names = ", ".join(card.tutor.full_name for card in s.tutor_cards.all() if card.moderation_status == "approved")
    print(f"    {s.name} ({s.n_tutors}): {names if names else '-'}")
print()
print(SEP)
print("Все пять запросов выполнены.")
