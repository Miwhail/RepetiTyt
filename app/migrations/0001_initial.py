import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='ФИО')),
                ('email', models.EmailField(max_length=100, unique=True, verbose_name='Электронная почта')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': 'Клиенты',
                'ordering': ['full_name'],
            },
        ),
        migrations.CreateModel(
            name='LessonSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('start_time', models.TimeField(verbose_name='Начало')),
                ('end_time', models.TimeField(verbose_name='Окончание')),
                ('status', models.CharField(choices=[('free', 'Свободно'), ('booked', 'Забронировано'), ('blocked', 'Заблокировано')], default='free', max_length=10, verbose_name='Статус окна')),
            ],
            options={
                'verbose_name': 'Слот в расписании',
                'verbose_name_plural': 'Слоты в расписании',
                'ordering': ['-date', 'start_time'],
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Название предмета')),
                ('is_active', models.BooleanField(default=True, verbose_name='Показывать в каталоге')),
            ],
            options={
                'verbose_name': 'Предмет',
                'verbose_name_plural': 'Предметы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Стоимость занятия')),
                ('status', models.CharField(choices=[('planned', 'Запланировано'), ('completed', 'Проведено'), ('cancelled', 'Отменено')], default='planned', max_length=10, verbose_name='Статус занятия')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='app.client', verbose_name='Клиент')),
                ('slot', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='lesson', to='app.lessonslot', verbose_name='Слот')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='app.subject', verbose_name='Предмет')),
            ],
            options={
                'verbose_name': 'Занятие',
                'verbose_name_plural': 'Занятия',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Cancellation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=200, verbose_name='Причина отмены')),
                ('cancelled_by', models.CharField(choices=[('client', 'Клиент'), ('tutor', 'Репетитор')], default='client', max_length=10, verbose_name='Кто отменил')),
                ('created_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата отмены')),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='cancellation', to='app.lesson', verbose_name='Занятие')),
            ],
            options={
                'verbose_name': 'Отмена занятия',
                'verbose_name_plural': 'Отмены занятий',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Tutor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='ФИО')),
                ('email', models.EmailField(max_length=100, unique=True, verbose_name='Электронная почта')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('experience_years', models.PositiveSmallIntegerField(default=1, verbose_name='Опыт (лет)')),
                ('rating', models.FloatField(default=4.0, verbose_name='Рейтинг')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Репетитор',
                'verbose_name_plural': 'Репетиторы',
                'ordering': ['full_name'],
                'constraints': [models.CheckConstraint(condition=models.Q(('rating__gte', 1.0), ('rating__lte', 5.0)), name='app_tutor_rating_range')],
            },
        ),
        migrations.AddField(
            model_name='lessonslot',
            name='tutor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='app.tutor', verbose_name='Репетитор'),
        ),
        migrations.CreateModel(
            name='TutorSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate_per_hour', models.DecimalField(decimal_places=2, max_digits=7, verbose_name='Ставка за час')),
                ('moderation_status', models.CharField(choices=[('pending', 'На модерации'), ('approved', 'Одобрена'), ('rejected', 'Отклонена')], default='pending', max_length=10, verbose_name='Статус модерации')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_cards', to='app.subject', verbose_name='Предмет')),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject_cards', to='app.tutor', verbose_name='Репетитор')),
            ],
            options={
                'verbose_name': 'Анкета репетитора по предмету',
                'verbose_name_plural': 'Анкеты репетиторов по предметам',
                'ordering': ['tutor__full_name', 'subject__name'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Сумма')),
                ('method', models.CharField(choices=[('card', 'Картой'), ('sbp', 'СБП'), ('cash', 'Наличные')], default='card', max_length=10, verbose_name='Способ оплаты')),
                ('status', models.CharField(choices=[('paid', 'Оплачено'), ('pending', 'Ожидает оплаты'), ('refunded', 'Возврат')], default='pending', max_length=10, verbose_name='Статус оплаты')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата оплаты')),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='payment', to='app.lesson', verbose_name='Занятие')),
            ],
            options={
                'verbose_name': 'Оплата',
                'verbose_name_plural': 'Оплаты',
                'ordering': ['-id'],
                'constraints': [models.CheckConstraint(condition=models.Q(('amount__gt', 0)), name='app_payment_amount_positive')],
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(verbose_name='Оценка')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий')),
                ('created_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата отзыва')),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='review', to='app.lesson', verbose_name='Занятие')),
            ],
            options={
                'verbose_name': 'Отзыв о занятии',
                'verbose_name_plural': 'Отзывы о занятиях',
                'ordering': ['-id'],
                'constraints': [models.CheckConstraint(condition=models.Q(('rating__gte', 1), ('rating__lte', 5)), name='app_review_rating_range')],
            },
        ),
        migrations.AddConstraint(
            model_name='lesson',
            constraint=models.CheckConstraint(condition=models.Q(('price__gt', 0)), name='app_lesson_price_positive'),
        ),
        migrations.AddConstraint(
            model_name='lessonslot',
            constraint=models.CheckConstraint(condition=models.Q(('start_time__lt', models.F('end_time'))), name='app_slot_time_valid'),
        ),
        migrations.AddConstraint(
            model_name='lessonslot',
            constraint=models.UniqueConstraint(fields=('tutor', 'date', 'start_time'), name='app_slot_unique_tutor_datetime'),
        ),
        migrations.AddConstraint(
            model_name='tutorsubject',
            constraint=models.CheckConstraint(condition=models.Q(('rate_per_hour__gte', 300), ('rate_per_hour__lte', 10000)), name='app_tutorsubject_rate_range'),
        ),
        migrations.AddConstraint(
            model_name='tutorsubject',
            constraint=models.UniqueConstraint(fields=('tutor', 'subject'), name='app_tutorsubject_unique_pair'),
        ),
    ]
