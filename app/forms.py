from django import forms
from .models import Lesson

class BookingForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Например: готовлюсь к пробнику в марте',
                'maxlength': '200'
            }),
        }
        labels = {
            'comment': 'Комментарий к занятию',
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if len(comment) > 200:
            raise forms.ValidationError("Комментарий не может быть длиннее 200 символов.")
        return comment