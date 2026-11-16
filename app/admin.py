from django.contrib import admin
from .models import (Subject, Tutor, Client, EducationDocument, TutorSubject,
                     LessonSlot, LessonPackage, StudentBalance, Lesson, 
                     LearningMaterial, Payment, Cancellation, Review)

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'rating', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'email')

@admin.register(EducationDocument)
class EducationDocumentAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'title', 'is_verified')
    list_filter = ('is_verified',)
    list_editable = ('is_verified',)

admin.site.register([Subject, Client, TutorSubject,
                     LessonSlot, LessonPackage, StudentBalance, Lesson, 
                     LearningMaterial, Payment, Cancellation, Review])