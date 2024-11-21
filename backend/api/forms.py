from django import forms
from .models import Studio

# 予約リクエストモデル
class SearchRequestForm(forms.Form):
    studios = forms.ModelMultipleChoiceField(
        queryset=Studio.objects.all(),
        required=False
    )
    search_start_datetime = forms.DateTimeField(required=True)
    search_end_datetime = forms.DateTimeField(required=True)
    reservation_time = forms.DateTimeField(required=True)
    
    def clean_studios(self):
        studios = self.cleaned_data.get('studios')
        max_choices = 5  # 最大選択数
        if len(studios) > max_choices:
            raise forms.ValidationError(f"最大で{max_choices}件まで選択可能です。")
        return studios
