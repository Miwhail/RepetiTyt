from django.db import models, transaction
from django.db.models import F, Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import datetime, timedelta


def validate_file_size(f):
    if f.size > 5 * 1024 * 1024:
        raise ValidationError('Файл больше 5 МБ — уменьшите скан.')


def db_check(condition, name):
    try:
        return models.CheckConstraint(condition=condition, name=name)
    except TypeError:
        return models.CheckConstraint(check=condition, name=name)


class Subject(models.Model):
    name = models.CharField(verbose_name="Название предмета", max_length=100, unique=True)
    is_active = models.BooleanField(verbose_name="Показывать в каталоге", default=True)

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tutor_profile", null=True, blank=True)
    full_name = models.CharField(verbose_name="ФИО", max_length=150)
    email = models.EmailField(verbose_name="Электронная почта", max_length=100, unique=True)
    phone = models.CharField(verbose_name="Телефон", max_length=20)
    experience_years = models.PositiveSmallIntegerField(verbose_name="Опыт (лет)", default=1)
    rating = models.FloatField(verbose_name="Рейтинг", default=4.0)
    is_active = models.BooleanField(verbose_name="Активен", default=True)

    class Meta:
        verbose_name = "Репетитор"
        verbose_name_plural = "Репетиторы"
        ordering = ['full_name']
        constraints = [
            db_check(Q(rating__gte=1.0, rating__lte=5.0), "app_tutor_rating_range"),
        ]

    def __str__(self):
        return self.full_name


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile", null=True, blank=True)
    full_name = models.CharField(verbose_name="ФИО", max_length=150)
    email = models.EmailField(verbose_name="Электронная почта", max_length=100, unique=True)
    phone = models.CharField(verbose_name="Телефон", max_length=20)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class EducationDocument(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="documents", verbose_name="Репетитор")
    title = models.CharField(verbose_name="Название ВУЗа/документа", max_length=200)
    file = models.FileField(
        verbose_name="Скан диплома",
        upload_to="diplomas/",
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), validate_file_size],
    )
    is_verified = models.BooleanField(verbose_name="Проверен модератором", default=False)

    class Meta:
        verbose_name = "Документ об образовании"
        verbose_name_plural = "Документы об образовании"

    def __str__(self):
        return f"{self.title} - {self.tutor.full_name}"


class TutorSubject(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="subject_cards", verbose_name="Репетитор")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="tutor_cards", verbose_name="Предмет")
    rate_per_hour = models.DecimalField(verbose_name="Ставка за час", max_digits=7, decimal_places=2)
    moderation_status = models.CharField(verbose_name="Статус модерации", max_length=10, default="pending", choices=[("pending", "На модерации"), ("approved", "Одобрена"), ("rejected", "Отклонена")])

    class Meta:
        verbose_name = "Анкета репетитора по предмету"
        verbose_name_plural = "Анкеты репетиторов по предметам"
        ordering = ['tutor__full_name', 'subject__name']
        constraints = [
            db_check(Q(rate_per_hour__gte=300, rate_per_hour__lte=10000), "app_tutorsubject_rate_range"),
            models.UniqueConstraint(fields=['tutor', 'subject'], name="app_tutorsubject_unique_pair"),
        ]

    def __str__(self):
        return f"{self.tutor} — {self.subject}"


class LessonSlot(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="slots", verbose_name="Репетитор")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Начало")
    end_time = models.TimeField(verbose_name="Окончание")
    status = models.CharField(verbose_name="Статус окна", max_length=10, default="free", choices=[("free", "Свободно"), ("booked", "Забронировано"), ("blocked", "Заблокировано")])

    class Meta:
        verbose_name = "Слот в расписании"
        verbose_name_plural = "Слоты в расписании"
        ordering = ['-date', 'start_time']
        constraints = [
            db_check(Q(start_time__lt=F("end_time")), "app_slot_time_valid"),
            models.UniqueConstraint(fields=['tutor', 'date', 'start_time'], name="app_slot_unique_tutor_datetime"),
        ]

    def __str__(self):
        return f"{self.tutor} — {self.date}, {self.start_time}"


class LessonPackage(models.Model):
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="packages", verbose_name="Репетитор")
    name = models.CharField(verbose_name="Название пакета", max_length=100)
    lessons_count = models.PositiveIntegerField(verbose_name="Количество уроков")
    price = models.DecimalField(verbose_name="Цена пакета", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Пакет занятий"
        verbose_name_plural = "Пакеты занятий"

    def __str__(self):
        return f"{self.name} от {self.tutor.full_name}"


class StudentBalance(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="balances", verbose_name="Ученик")
    package = models.ForeignKey(LessonPackage, on_delete=models.CASCADE, verbose_name="Пакет")
    lessons_left = models.PositiveIntegerField(verbose_name="Остаток уроков", default=0)

    class Meta:
        verbose_name = "Баланс уроков"
        verbose_name_plural = "Балансы уроков"

    def __str__(self):
        return f"{self.client.full_name} — осталось {self.lessons_left}"


class Lesson(models.Model):
    slot = models.OneToOneField(LessonSlot, on_delete=models.PROTECT, related_name="lesson", verbose_name="Слот")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="lessons", verbose_name="Клиент")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lessons", verbose_name="Предмет")
    package = models.ForeignKey(LessonPackage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Оплачено пакетом")
    price = models.DecimalField(verbose_name="Стоимость занятия", max_digits=8, decimal_places=2)
    status = models.CharField(verbose_name="Статус занятия", max_length=10, default="planned", choices=[("planned", "Запланировано"), ("completed", "Проведено"), ("cancelled", "Отменено")])
    comment = models.TextField(verbose_name="Комментарий", blank=True, default="")

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        ordering = ['-id']
        constraints = [
            db_check(Q(price__gt=0), "app_lesson_price_positive"),
        ]

    def __str__(self):
        return f"Занятие {self.pk} — {self.subject}, {self.slot.tutor.full_name}"


class LearningMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials", verbose_name="Занятие")
    title = models.CharField(verbose_name="Название материала", max_length=200)
    file_url = models.URLField(verbose_name="Ссылка на материал")

    class Meta:
        verbose_name = "Учебный материал"
        verbose_name_plural = "Учебные материалы"

    def __str__(self):
        return self.title


class Payment(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.PROTECT, related_name="payment", verbose_name="Занятие")
    amount = models.DecimalField(verbose_name="Сумма", max_digits=8, decimal_places=2)
    method = models.CharField(verbose_name="Способ оплаты", max_length=10, default="card", choices=[("card", "Картой"), ("sbp", "СБП"), ("cash", "Наличные")])
    status = models.CharField(verbose_name="Статус оплаты", max_length=10, default="pending", choices=[("paid", "Оплачено"), ("pending", "Ожидает оплаты"), ("refunded", "Возврат")])
    paid_at = models.DateTimeField(verbose_name="Дата оплаты", null=True, blank=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"
        ordering = ['-id']
        constraints = [
            db_check(Q(amount__gt=0), "app_payment_amount_positive"),
        ]

    def __str__(self):
        return f"Оплата занятия №{self.lesson_id}"


class Cancellation(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.PROTECT, related_name="cancellation", verbose_name="Занятие")
    reason = models.CharField(verbose_name="Причина отмены", max_length=200)
    cancelled_by = models.CharField(verbose_name="Кто отменил", max_length=10, default="client", choices=[("client", "Клиент"), ("tutor", "Репетитор")])
    created_at = models.DateTimeField(verbose_name="Дата отмены", auto_now_add=True)

    class Meta:
        verbose_name = "Отмена занятия"
        verbose_name_plural = "Отмены занятий"
        ordering = ['-id']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            lesson = self.lesson

            if lesson.status == 'planned':
                if self.cancelled_by == 'client':
                    lesson_dt = datetime.combine(lesson.slot.date, lesson.slot.start_time)
                    lesson_dt = timezone.make_aware(lesson_dt) if timezone.is_naive(lesson_dt) else lesson_dt

                    if (lesson_dt - timezone.now()) < timedelta(hours=24):
                        lesson.status = 'completed'
                        if lesson.package:
                            StudentBalance.objects.filter(
                                client=lesson.client,
                                package=lesson.package,
                                lessons_left__gt=0
                            ).update(lessons_left=F('lessons_left') - 1)
                    else:
                        lesson.status = 'cancelled'
                else:
                    lesson.status = 'cancelled'

                lesson.save()

                if lesson.status == 'cancelled':
                    lesson.slot.status = 'free'
                    lesson.slot.save()

            super().save(*args, **kwargs)

    def __str__(self):
        return f"Отмена занятия №{self.lesson_id}"


class Review(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.PROTECT, related_name="review", verbose_name="Занятие")
    rating = models.PositiveSmallIntegerField(verbose_name="Оценка")
    comment = models.TextField(verbose_name="Комментарий", blank=True, default="")
    created_at = models.DateTimeField(verbose_name="Дата отзыва", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв о занятии"
        verbose_name_plural = "Отзывы о занятиях"
        ordering = ['-id']
        constraints = [
            db_check(Q(rating__gte=1, rating__lte=5), "app_review_rating_range"),
        ]

    def __str__(self):
        return f"Отзыв на занятие №{self.lesson_id}"
