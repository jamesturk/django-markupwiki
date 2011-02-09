import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from markupfield.fields import MarkupField
from markupfield import markup
from markupwiki.utils import wikify_markup_wrapper

DEFAULT_MARKUP_TYPE = getattr(settings, 'MARKUPWIKI_DEFAULT_MARKUP_TYPE',
                              'markdown')
WRITE_LOCK_SECONDS = getattr(settings, 'MARKUPWIKI_WRITE_LOCK_SECONDS', 300)
MARKUP_TYPES = getattr(settings, 'MARKUPWIKI_MARKUP_TYPES',
                       markup.DEFAULT_MARKUP_TYPES)
EDITOR_TEST_FUNC = getattr(settings, 'MARKUPWIKI_EDITOR_TEST_FUNC',
                           lambda u: u.is_authenticated())
MODERATOR_TEST_FUNC = getattr(settings, 'MARKUPWIKI_MODERATOR_TEST_FUNC',
                              lambda u: u.is_staff)

# add make_wiki_links to MARKUP_TYPES
WIKI_MARKUP_TYPES = []
for name, func in MARKUP_TYPES:
    WIKI_MARKUP_TYPES.append((name, wikify_markup_wrapper(func)))

PUBLIC, LOCKED, DELETED = range(3)
ARTICLE_STATUSES = (
    (PUBLIC, 'Public'),     # public - no restrictions on viewing/editing
    (LOCKED, 'Locked'),     # locked - only admins can edit
    (DELETED, 'Deleted'),   # deleted - display deleted page
)

class Article(models.Model):
    title = models.CharField(max_length=200)
    creator = models.ForeignKey(User, related_name='wiki_articles')
    status = models.IntegerField(choices=ARTICLE_STATUSES, default=PUBLIC)
    redirect_to = models.ForeignKey('self', null=True)

    def __unicode__(self):
        return self.title

    @property
    def display_title(self):
        return self.title.rsplit('/',1)[-1].replace('_', ' ')

    @property
    def section_name(self):
        if '/' in self.title:
            return self.title.rsplit('/',1)[0]

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
            return MODERATOR_TEST_FUNC(user)
        else:
            return EDITOR_TEST_FUNC(user)

    def get_write_lock(self, user, release=False):
        cache_key = 'markupwiki_articlelock_%s' % self.id
        lock = cache.get(cache_key)
        if lock:
            if release:
                cache.delete(cache_key)
            return lock == user.id

        if not release:
            cache.set(cache_key, user.id, WRITE_LOCK_SECONDS)
        return True

class ArticleVersion(models.Model):
    article = models.ForeignKey(Article, related_name='versions')
    author = models.ForeignKey(User, related_name='article_versions')
    number = models.PositiveIntegerField()
    body = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE,
                       markup_choices=WIKI_MARKUP_TYPES,
                       escape_html=True)
    comment = models.CharField(max_length=200, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    removed = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        get_latest_by = 'timestamp'

    def __unicode__(self):
        return '%s rev #%s' % (self.article, self.number)

    def get_absolute_url(self):
        return reverse('article_version', args=[self.article.title, self.number])
