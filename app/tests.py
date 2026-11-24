from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Client, Lesson, LessonSlot, Subject, Tutor, TutorSubject


class NegativeTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='Математика')
        self.tutor = Tutor.objects.create(
            full_name='Иванов Иван', email='t@example.com', phone='+7 900 000-00-00',
        )
        self.card = TutorSubject.objects.create(
            tutor=self.tutor, subject=self.subject,
            rate_per_hour=1000, moderation_status='approved',
        )
        self.slot = LessonSlot.objects.create(
            tutor=self.tutor, date=date.today() + timedelta(days=1),
            start_time=time(10, 0), end_time=time(11, 0),
        )
        self.user = User.objects.create_user(username='client', password='test12345')
        self.profile = Client.objects.create(
            user=self.user, full_name='Клиент Клиентов',
            email='c@example.com', phone='+7 900 000-00-01',
        )

    def test_missing_tutor_returns_404(self):
        """Обращение к несуществующей записи возвращает 404, а не 500."""
        response = self.client.get('/tutor/99999/')
        self.assertEqual(response.status_code, 404)

    def test_booking_without_login_does_not_leak_form(self):
        """Доступ без прав: неавторизованный не видит форму, а перенаправляется на вход."""
        response = self.client.get(f'/booking/{self.card.pk}/{self.slot.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_invalid_form_creates_no_lesson(self):
        """Форма с неверными данными не создаёт запись и показывает сообщение."""
        self.client.force_login(self.user)
        response = self.client.post(
            f'/booking/{self.card.pk}/{self.slot.pk}/',
            {'comment': 'х' * 250},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertContains(response, 'длиннее 200 символов')

    def test_double_booking_does_not_create_second_lesson(self):
        """Ошибка в середине операции не меняет данные: слот нельзя забронировать дважды."""
        self.client.force_login(self.user)
        first = self.client.post(
            f'/booking/{self.card.pk}/{self.slot.pk}/', {'comment': 'первая'},
        )
        self.assertEqual(Lesson.objects.count(), 1)
        self.slot.status = 'free'
        self.slot.save()
        second = self.client.post(
            f'/booking/{self.card.pk}/{self.slot.pk}/', {'comment': 'вторая'},
        )
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)

    def test_cabinet_on_empty_history_does_not_crash(self):
        """Расчёт на пустой выборке не падает: у нового клиента 0 занятий и 0 рублей."""
        self.client.force_login(self.user)
        response = self.client.get('/cabinet/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_spent'], 0)
