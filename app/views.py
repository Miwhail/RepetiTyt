from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Tutor, TutorSubject, LessonSlot, Lesson, Client, Subject, Cancellation
from .forms import BookingForm

def index(request):
    popular_tutors = TutorSubject.objects.filter(moderation_status='approved').select_related('tutor', 'subject').order_by('-tutor__rating')[:3]
    return render(request, 'app/index.html', {'popular_tutors': popular_tutors})

def catalog(request):
    tutor_cards = TutorSubject.objects.filter(moderation_status='approved').select_related('tutor', 'subject')

    query = request.GET.get('q', '')
    if query:
        tutor_cards = tutor_cards.filter(
            Q(tutor__full_name__icontains=query) |
            Q(subject__name__icontains=query)
        )

    subject_id = request.GET.get('subject', '')
    if subject_id:
        tutor_cards = tutor_cards.filter(subject_id=subject_id)

    price_min = request.GET.get('price_min', '')
    if price_min:
        tutor_cards = tutor_cards.filter(rate_per_hour__gte=price_min)

    price_max = request.GET.get('price_max', '')
    if price_max:
        tutor_cards = tutor_cards.filter(rate_per_hour__lte=price_max)

    rating = request.GET.get('rating', '')
    if rating:
        tutor_cards = tutor_cards.filter(tutor__rating__gte=rating)

    sort_by = request.GET.get('sort', 'rating_desc')
    if sort_by == 'price_asc':
        tutor_cards = tutor_cards.order_by('rate_per_hour')
    elif sort_by == 'price_desc':
        tutor_cards = tutor_cards.order_by('-rate_per_hour')
    elif sort_by == 'experience':
        tutor_cards = tutor_cards.order_by('-tutor__experience_years')
    else:
        tutor_cards = tutor_cards.order_by('-tutor__rating')

    paginator = Paginator(tutor_cards, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    subjects = Subject.objects.filter(is_active=True)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'query': query,
        'query_params': query_params.urlencode(),
        'current_subject': subject_id,
        'current_price_min': price_min,
        'current_price_max': price_max,
        'current_rating': rating,
        'current_sort': sort_by,
    }
    return render(request, 'app/catalog.html', context)

def live_search(request):
    query = request.GET.get('q', '').strip()
    cards = TutorSubject.objects.filter(moderation_status='approved').select_related('tutor', 'subject')

    if query:
        cards = cards.filter(
            Q(tutor__full_name__icontains=query) |
            Q(subject__name__icontains=query)
        )

    cards = cards.order_by('-tutor__rating')[:20]
    html = render_to_string('app/cards_list.html', {'page_obj': cards}, request=request)
    return JsonResponse({'html': html, 'count': cards.count()})

def tutor_detail(request, pk):
    tutor_card = get_object_or_404(TutorSubject, pk=pk, moderation_status='approved')
    slots = LessonSlot.objects.filter(tutor=tutor_card.tutor, status='free').order_by('date', 'start_time')

    context = {
        'tutor_card': tutor_card,
        'slots': slots,
    }
    return render(request, 'app/tutor_detail.html', context)

def booking_create(request, tutor_card_id, slot_id):
    tutor_card = get_object_or_404(TutorSubject, pk=tutor_card_id, moderation_status='approved')
    slot = get_object_or_404(LessonSlot, pk=slot_id)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('app:login')

        form = BookingForm(request.POST)
        if form.is_valid():
            client, created = Client.objects.get_or_create(user=request.user, defaults={
                'full_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': ''
            })

            with transaction.atomic():
                slot_locked = LessonSlot.objects.select_for_update().get(pk=slot_id)

                if slot_locked.status != 'free' or slot_locked.tutor_id != tutor_card.tutor_id:
                    messages.error(request, 'Этот слот уже занят или недоступен.')
                    return redirect('app:tutor_detail', pk=tutor_card_id)

                slot_locked.status = 'booked'
                slot_locked.save()

                lesson, created = Lesson.objects.update_or_create(
                    slot=slot_locked,
                    defaults={
                        'client': client,
                        'subject': tutor_card.subject,
                        'price': tutor_card.rate_per_hour,
                        'status': 'planned',
                        'comment': form.cleaned_data.get('comment', '')
                    }
                )

                send_mail(
                    'Бронирование подтверждено',
                    f'Вы записались к репетитору {tutor_card.tutor.full_name} на {slot.date} {slot.start_time}.',
                    'noreply@repetitut.ru',
                    [client.email],
                    fail_silently=True,
                )

            messages.success(request, 'Вы успешно записались на занятие!')
            return redirect('app:cabinet')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = BookingForm()

    context = {
        'tutor_card': tutor_card,
        'slot': slot,
        'form': form,
    }
    return render(request, 'app/booking.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('app:cabinet')
    else:
        form = AuthenticationForm()
    return render(request, 'app/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('app:index')

@login_required
def cabinet(request):
    try:
        client = request.user.client_profile
        lessons = Lesson.objects.filter(client=client).select_related('slot__tutor', 'subject').order_by('-slot__date')
    except Client.DoesNotExist:
        lessons = []

    context = {'lessons': lessons}
    return render(request, 'app/cabinet.html', context)

@login_required
def cancel_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id, client__user=request.user)

    if request.method == 'POST' and lesson.status == 'planned':
        Cancellation.objects.update_or_create(
            lesson=lesson,
            defaults={
                'reason': 'Отмена клиентом',
                'cancelled_by': 'client'
            }
        )
        messages.success(request, "Занятие отменено.")

    return redirect('app:cabinet')

def how_it_works(request):
    return render(request, 'app/how_it_works.html')