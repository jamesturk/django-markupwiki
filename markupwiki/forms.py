from django import forms
from markupwiki.models import Article, ArticleVersion

class ArticleForm(forms.ModelForm):
    class Meta:
        model = ArticleVersion
        fields = ['body', 'body_markup_type']

class StaffModerationForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['status']
