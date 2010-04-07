import time
from django.core.cache import cache
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from markupwiki.models import Article, PUBLIC, LOCKED, DELETED
from markupwiki import models


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


models.WRITE_LOCK_SECONDS = 3

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
        time.sleep(4)
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
