import time

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from .models import Subject, TutorSubject, LessonSlot, Lesson, Client, Cancellation
from .forms import BookingForm

MAX_ATTEMPTS = 5
BLOCK_SECONDS = 600  



def index(request):
    popular_cards = (
        TutorSubject.objects.select_related('tutor', 'subject')
        .order_by('-tutor__rating')[:6]
    )
    return render(request, 'app/index.html', {'popular_cards': popular_cards})


def how_it_works(request):
    return render(request, 'app/how_it_works.html')


def catalog(request):
    cards = TutorSubject.objects.select_related('tutor', 'subject')

    search = request.GET.get('search', '').strip()
    if search:
        cards = cards.filter(
            Q(tutor__full_name__icontains=search)
            | Q(subject__name__icontains=search)
        )

    subject_id = request.GET.get('subject')
    if subject_id:
        cards = cards.filter(subject_id=subject_id)

    price_min = request.GET.get('price_min')
    if price_min:
        cards = cards.filter(rate_per_hour__gte=price_min)

    price_max = request.GET.get('price_max')
    if price_max:
        cards = cards.filter(rate_per_hour__lte=price_max)

    rating = request.GET.get('rating')
    if rating:
        cards = cards.filter(tutor__rating__gte=rating)

    sort_map = {
        'rating': '-tutor__rating',
        'price_asc': 'rate_per_hour',
        'price_desc': '-rate_per_hour',
        'experience': '-tutor__experience_years',
    }
    sort = request.GET.get('sort')
    if sort in sort_map:
        cards = cards.order_by(sort_map[sort])

    subjects = Subject.objects.filter(is_active=True)
    paginator = Paginator(cards, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'app/catalog.html', {
        'page_obj': page_obj,
        'subjects': subjects,
        'search': search,
    })


def live_search(request):
    q = request.GET.get('q', '').strip()
    if q:
        cards = (
            TutorSubject.objects.select_related('tutor', 'subject')
            .filter(Q(tutor__full_name__icontains=q) | Q(subject__name__icontains=q))[:8]
        )
        html = render_to_string('app/cards_list.html', {'page_obj': cards}, request=request)
        return HttpResponse(html)
    return JsonResponse({'results': []})


def tutor_detail(request, pk):
    tutor_card = get_object_or_404(TutorSubject.objects.select_related('tutor', 'subject'), pk=pk)
    slots = (
        LessonSlot.objects.filter(tutor=tutor_card.tutor, status='free')
        .order_by('date', 'start_time')
    )
    return render(request, 'app/tutor_detail.html', {
        'tutor_card': tutor_card,
        'slots': slots,
    })



@login_required
def booking_create(request, tutor_card_id, slot_id):
    tutor_card = get_object_or_404(TutorSubject, pk=tutor_card_id)
    slot = get_object_or_404(LessonSlot, pk=slot_id, tutor=tutor_card.tutor, status='free')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            client = get_object_or_404(Client, user=request.user)
            lesson = Lesson.objects.create(
                slot=slot,
                client=client,
                subject=tutor_card.subject,
                price=tutor_card.rate_per_hour,
                comment=form.cleaned_data.get('comment', ''),
            )
            slot.status = 'booked'
            slot.save()
            messages.success(request, 'Занятие забронировано!')
            return redirect('app:cabinet')
    else:
        form = BookingForm()

    return render(request, 'app/booking.html', {
        'tutor_card': tutor_card,
        'slot': slot,
        'form': form,
    })


@login_required
def cancel_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('slot'), pk=lesson_id)


    if lesson.client.user_id != request.user.id:
        raise Http404('Занятие не найдено')

    if request.method == 'POST':
        if lesson.status != 'planned':
            messages.error(request, 'Это занятие уже нельзя отменить.')
            return redirect('app:cabinet')
        Cancellation.objects.create(lesson=lesson, reason='Отмена клиентом', cancelled_by='client')
        messages.success(request, 'Занятие отменено.')
        return redirect('app:cabinet')

    return render(request, 'app/cancel_confirm.html', {'lesson': lesson})



@login_required
def cabinet(request):
    client = get_object_or_404(Client, user=request.user)
    lessons = (
        Lesson.objects.filter(client=client)
        .select_related('slot__tutor', 'subject')
        .order_by('-id')
    )
    total_spent = sum(l.price for l in lessons if l.status == 'completed')
    return render(request, 'app/cabinet.html', {
        'lessons': lessons,
        'total_spent': total_spent,
    })



def login_view(request):
    if request.method == 'POST':
        blocked_until = request.session.get('blocked_until', 0)
        if time.time() < blocked_until:
            messages.error(request, 'Слишком много попыток входа. Попробуйте через 10 минут.')
            form = AuthenticationForm()
        else:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                request.session['login_attempts'] = 0
                request.session['blocked_until'] = 0
                user = form.get_user()
                login(request, user)
                messages.success(request, 'Вы вошли в личный кабинет.')
                return redirect('app:cabinet')
            attempts = request.session.get('login_attempts', 0) + 1
            request.session['login_attempts'] = attempts
            if attempts >= MAX_ATTEMPTS:
                request.session['blocked_until'] = time.time() + BLOCK_SECONDS
                request.session['login_attempts'] = 0
                messages.error(request, 'Слишком много неудачных попыток. Вход заблокирован на 10 минут.')
            else:
                messages.error(request, f'Неверный логин или пароль. Осталось попыток: {MAX_ATTEMPTS - attempts}')
    else:
        form = AuthenticationForm()
    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('app:index')
