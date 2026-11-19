from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('api/live-search/', views.live_search, name='live_search'),
    path('tutor/<int:pk>/', views.tutor_detail, name='tutor_detail'),
    path('booking/<int:tutor_card_id>/<int:slot_id>/', views.booking_create, name='booking'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('cancel/<int:lesson_id>/', views.cancel_lesson, name='cancel_lesson'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]