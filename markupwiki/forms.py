from django.conf import settings
from django import forms
from markupwiki.models import Article, ArticleVersion

MARKUP_TYPE_EDITABLE = getattr(settings, 'MARKUPWIKI_MARKUP_TYPE_EDITABLE', True)

class ArticleForm(forms.ModelForm):
    class Meta:
        model = ArticleVersion
        fields = ['body', 'comment']
        if MARKUP_TYPE_EDITABLE:
            fields.append('body_markup_type')

class StaffModerationForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['status']


class ArticleRenameForm(forms.Form):
    new_title = forms.CharField(label='Rename', max_length=50)
