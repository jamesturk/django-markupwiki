from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from markupfield.fields import MarkupField

DEFAULT_MARKUP_TYPE = getattr(settings, 'MARKUPWIKI_DEFAULT_MARKUP_TYPE', 'plain')

PUBLIC, LOCKED, DELETED = range(3)
ARTICLE_STATUSES = (
    (PUBLIC, 'Public'),     # public - no restrictions on viewing/editing
    (LOCKED, 'Locked'),     # locked - only admins can edit
    (DELETED, 'Deleted'),   # deleted - display deleted page
)

class Article(models.Model):
    title = models.CharField(max_length=50)
    creator = models.ForeignKey(User, related_name='wiki_articles')
    status = models.IntegerField(choices=ARTICLE_STATUSES, default=PUBLIC)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('view_article', args=[self.title])

    def is_public(self):
        return self.status == PUBLIC

    def is_locked(self):
        return self.status == LOCKED

    def is_deleted(self):
        return self.status == DELETED

    def is_editable_by_user(self, user):
        if self.status in (LOCKED, DELETED):
            return user.is_staff
        else:
            return user.is_authenticated()


class ArticleVersion(models.Model):
    article = models.ForeignKey(Article, related_name='versions')
    author = models.ForeignKey(User, related_name='article_versions')
    number = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    removed = models.BooleanField(default=False)
    body = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)

    class Meta:
        ordering = ['timestamp']
        get_latest_by = 'timestamp'

    def __unicode__(self):
        return unicode(self.article)

    def get_absolute_url(self):
        return reverse('article_version', args=[self.article.title, self.number])
