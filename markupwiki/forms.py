from django import forms
from markupwiki.models import Article, ArticleVersion, PUBLIC, PRIVATE

class ArticleForm(forms.ModelForm):
    class Meta:
        model = ArticleVersion
        fields = ['body', 'body_markup_type']

class StaffModerationForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['status']

class ModerationForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['status']
    status = forms.ChoiceField(choices=((PUBLIC, 'Public'),
                                        (PRIVATE, 'Private')))
