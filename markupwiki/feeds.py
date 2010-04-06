from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from markupwiki.models import Article, ArticleVersion

class LatestEditsFeed(Feed):
    title = 'Recent Changes'
    link = '/'
    description = 'Latest Changes to Wiki Articles'

    def items(self):
        return ArticleVersion.objects.order_by('-timestamp').select_related()[:20]

    def item_title(self, item):
        return unicode(item)

    def item_description(self, item):
        return unicode(item.body)

    def item_link(self, item):
        return item.get_absolute_url()


class LatestArticleEditsFeed(Feed):

    def get_object(self, request, title):
        return get_object_or_404(Article, title=title)

    def title(self, obj):
        return 'Recent changes to %s' % obj

    def description(self, obj):
        return 'Recent changes made to %s' % obj

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.versions.order_by('-timestamp').select_related()[:20]

    def item_title(self, item):
        return unicode(item)

    def item_description(self, item):
        return unicode(item.body)

    def item_link(self, item):
        return item.get_absolute_url()
