from django.conf.urls.defaults import *

WIKI_REGEX = r'^(?P<title>[\w\s]+)'

urlpatterns = patterns('markupwiki.views',
    url(WIKI_REGEX + '/$', 'view_article', name='view_article'),
    url(WIKI_REGEX + '/edit/$', 'edit_article', name='edit_article'),
    url(WIKI_REGEX + '/update_status/$', 'article_status',
        name='update_article_status'),
    url(WIKI_REGEX + '/history/$', 'article_history', name='article_history'),
    url(WIKI_REGEX + '/history/(?P<n>\d+)/$', 'view_article', name='article_version'),
    url(WIKI_REGEX + '/diff/$', 'article_diff', name='article_diff'),
)
