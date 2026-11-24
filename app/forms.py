import re

from django import forms
from .models import Lesson

PHONE_RE = re.compile(r'^\+7 \d{3} \d{3}-\d{2}-\d{2}$')


class BookingForm(forms.ModelForm):
    contact_phone = forms.CharField(
        required=False,
        label='Телефон для связи',
        widget=forms.TextInput(attrs={'placeholder': '+7 900 000-00-00'}),
        help_text='Формат: +7 900 000-00-00',
    )
    call_to_confirm = forms.BooleanField(
        required=False,
        label='Позвонить для подтверждения записи',
    )

    class Meta:
        model = Lesson
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Например: готовлюсь к пробнику в марте',
                'maxlength': '200',
            }),
        }
        labels = {
            'comment': 'Комментарий к занятию',
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        if len(comment) > 200:
            raise forms.ValidationError('Комментарий не может быть длиннее 200 символов.')
        return comment

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone', '').strip()
        if phone and not PHONE_RE.match(phone):
            raise forms.ValidationError('Введите телефон в формате +7 900 000-00-00')
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('call_to_confirm') and not cleaned.get('contact_phone'):
            self.add_error(
                'contact_phone',
                'Укажите телефон в формате +7 900 000-00-00 — он нужен для звонка подтверждения',
            )
        return cleaned
