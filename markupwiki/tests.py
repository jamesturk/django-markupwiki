import time
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.http import HttpRequest
from django.contrib.auth.models import User, AnonymousUser
from markupwiki.models import Article, ArticleVersion, PUBLIC, LOCKED, DELETED
from markupwiki import models
from markupwiki.utils import make_wiki_links, wikify_markup_wrapper
from markupwiki import views

class ArticleTests(TestCase):

    def test_display_title(self):
        a = Article(title='section/name_with_spaces')
        self.assertEquals(a.display_title, 'name with spaces')

    def test_section_name(self):
        a = Article(title='section/name_with_spaces')
        self.assertEquals(a.section_name, 'section')

    def test_is_editable_by_user(self):
        public_article = Article(title='public', status=PUBLIC)
        locked_article = Article(title='locked', status=LOCKED)
        deleted_article = Article(title='deleted', status=DELETED)
        user = User(is_staff=False)
        staff_user = User(is_staff=True)
        anon_user = AnonymousUser()

        # check that anonymous users cannot edit
        self.assertFalse(public_article.is_editable_by_user(anon_user))
        self.assertFalse(locked_article.is_editable_by_user(anon_user))
        self.assertFalse(deleted_article.is_editable_by_user(anon_user))

        # check that user can only edit public articles
        self.assert_(public_article.is_editable_by_user(user))
        self.assertFalse(locked_article.is_editable_by_user(user))
        self.assertFalse(deleted_article.is_editable_by_user(user))

        # check that staff can edit any article
        self.assert_(locked_article.is_editable_by_user(staff_user))
        self.assert_(deleted_article.is_editable_by_user(staff_user))


models.WRITE_LOCK_SECONDS = 1

class ArticleWriteLockTests(TestCase):

    alice = User(id=1, username='alice')
    bob = User(id=2, username='bob')
    article = Article(id=1, title='locktest')

    def setUp(self):
        cache.clear()

    def test_simple_lock(self):
        ''' test that bob can't grab the lock immediately after alice does '''
        alice_initial_lock = self.article.get_write_lock(self.alice)
        bob_immediate_lock = self.article.get_write_lock(self.bob)
        alice_retained_lock = self.article.get_write_lock(self.alice)

        self.assertTrue(alice_initial_lock)
        self.assertFalse(bob_immediate_lock)
        self.assertTrue(alice_retained_lock)

    def test_lock_timeout(self):
        ''' test that the lock times out properly '''
        alice_initial_lock = self.article.get_write_lock(self.alice)
        time.sleep(2)
        bob_wait_lock = self.article.get_write_lock(self.bob)

        self.assertTrue(alice_initial_lock)
        self.assertTrue(bob_wait_lock)

    def test_lock_release(self):
        ''' test that lock is released properly '''
        alice_initial_lock = self.article.get_write_lock(self.alice)
        alice_release_lock = self.article.get_write_lock(self.alice, release=True)
        bob_immediate_lock = self.article.get_write_lock(self.bob)

        self.assertTrue(alice_initial_lock)
        self.assertTrue(alice_release_lock)
        self.assertTrue(bob_immediate_lock)

    def test_release_on_acquire(self):
        ''' test that if release is True on acquire lock is not set '''
        alice_initial_lock = self.article.get_write_lock(self.alice, release=True)
        bob_immediate_lock = self.article.get_write_lock(self.bob)

        self.assertTrue(alice_initial_lock)
        self.assertTrue(bob_immediate_lock)


class WikifyTests(TestCase):

    urls = 'markupwiki.urls'

    def _get_url(self, link, name=None):
        return '<a href="%s">%s</a>' % (reverse('view_article', args=[link]),
                                        name or link)

    def test_make_wiki_links_simple(self):
        result = make_wiki_links('[[test]]')
        self.assertEquals(result, self._get_url('test'))
        result = make_wiki_links('[[two words ]]')
        self.assertEquals(result, self._get_url('two words'))
        result_ws = make_wiki_links('[[ test ]]')
        self.assertEquals(result_ws, self._get_url('test'))

    def test_make_wiki_links_named(self):
        result = make_wiki_links('[[test|this link has a name]]')
        self.assertEquals(result, self._get_url('test', 'this link has a name'))

    def test_wikify_markup_wrapper(self):
        wrapped_upper_filter = wikify_markup_wrapper(lambda text: text.upper())

        result = wrapped_upper_filter('[[test]]')
        self.assertEquals(result, self._get_url('TEST'))

    def test_wikify_markup_wrapper_double_wrap(self):
        ''' ensure that wrapped functions can't be double wrapped '''
        wrapped_upper_filter = wikify_markup_wrapper(lambda text: text.upper())
        self.assertEquals(wrapped_upper_filter,
                          wikify_markup_wrapper(wrapped_upper_filter))


class ViewArticleTests(TestCase):

    urls = 'markupwiki.urls'

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@admin.com',
                                                   'password')
        self.frank = User.objects.create_user('frank', 'frank@example.com',
                                              'password')
        self.test_article = Article.objects.create(title='test',
                                                   creator=self.admin)
        ArticleVersion.objects.create(article=self.test_article,
                                      author=self.admin,
                                      number=0,
                                      body='this is a test')
        ArticleVersion.objects.create(article=self.test_article,
                                      author=self.frank,
                                      number=1,
                                      body='this is an update')
        ArticleVersion.objects.create(article=self.test_article,
                                      author=self.frank,
                                      number=2,
                                      body='this is the final update')
        self.two_word_article = Article.objects.create(title='two_words',
                                                       creator=self.admin)
        ArticleVersion.objects.create(article=self.two_word_article,
                                      author=self.frank,
                                      number=0,
                                      body='this article title has a space')

    def test_normal(self):
        ''' test accessing an article without a version specified '''
        resp = self.client.get('/test/')
        self.assertContains(resp, 'this is the final update')

    def test_specific_version(self):
        ''' test accessing a specific version of an article '''
        resp = self.client.get('/test/history/1/')
        self.assertContains(resp, 'this is an update')

    def test_name_with_spaces(self):
        ''' test that a name with spaces is properly converted into a name with underscores '''
        resp = self.client.get('/two words/')
        self.assertRedirects(resp, '/two_words/', status_code=301)

    def test_redirect(self):
        ''' test that a 302 is given for any article with a redirect_to '''
        redirect = Article.objects.create(title='redirect', creator=self.admin,
                                         redirect_to=self.test_article)
        resp = self.client.get('/redirect/')
        self.assertRedirects(resp, '/test/', status_code=302)

    def test_missing_edit(self):
        ''' test that a 302 is given to the edit page if CREATE_MISSING_ARTICLE is True '''
        views.CREATE_MISSING_ARTICLE = True
        self.client.login(username='frank', password='password')
        resp = self.client.get('/newpage/')
        self.assertRedirects(resp, '/newpage/edit/', status_code=302)

    def test_missing_404(self):
        ''' test that a 404 is given if CREATE_MISSING_ARTICLE is False '''
        views.CREATE_MISSING_ARTICLE = False
        self.client.login(username='frank', password='password')
        resp = self.client.get('/newpage/')
        self.assertContains(resp, '', status_code=404)

    def test_staff_forms(self):
        ''' ensure that only admins can see the admin form '''

        # make sure a normal user doesn't see the admin form
        self.client.login(username='frank', password='password')
        resp = self.client.get('/test/')
        self.assertNotContains(resp, '<label for="id_status">')

        # ...but an admin does
        self.client.login(username='admin', password='password')
        resp = self.client.get('/test/')
        self.assertContains(resp, '<label for="id_status">')

