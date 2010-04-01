from django.contrib import admin
from markupwiki.models import Article, ArticleVersion

class VersionInline(admin.TabularInline):
    model = ArticleVersion

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status')
    list_filter = ('status',)
    inlines = [VersionInline]

admin.site.register(Article, ArticleAdmin)
