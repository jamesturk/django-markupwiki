=================
django-markupwiki
=================

An implementation of simple markup-agnostic wiki for Django.

markupwiki does not aim to be a full fledged replacement to mediawiki or other
large packages, but instead to provide the most commonly used subset of
functionality.  Pages can be edited, locked, and deleted.  Revisions can be
viewed, reverted, and compared.  If you need much more than that markupwiki
might not be for you.

Requirements
============

django-markupwiki depends on django 1.2+, django-markupfield 1.0.0b+ and
libraries for whichever markup options you wish to include.


Usage
=====

Like any django application, the first step when using django-markupwiki is
to add ``markupwiki`` to your ``INSTALLED_APPS``.

urls
----

To use django-markupwiki's urls you should also add a line like::

    url(r'^wiki/', include('markupwiki.urls')),

to your urlconf.

This will make the following views available (assuming the defined root is /wiki/):

    /wiki/rss/                             - RSS feed of latest changes to wiki
    /wiki/*article*/                       - view the latest version of an article
    /wiki/*article*/rss                    - RSS feed of changes to an article
    /wiki/*article*/edit/                  - edit (or create) an article
    /wiki/*article*/history/               - history view for an article
    /wiki/*article*/history/*revision*/    - view a specific version of an article
    /wiki/*article*/diff/                  - compare a two revisions of an article

settings
--------

django-markupwiki provides a number of optional settings that you may wish to use
to customize the behavior.

``MARKUPWIKI_WRITE_LOCK_SECONDS`` - number of seconds that a user can hold a
write lock (default: 300)

``MARKUPWIKI_CREATE_MISSING_ARTICLES`` - if True when attempting to go to an
article that doesn't exist, user will be redirected to the /edit/ page.  If
False user will get a 404. (default: True)

``MARKUPWIKI_DEFAULT_MARKUP_TYPE`` - default markup type to use
(default: markdown)

``MARKUPWIKI_MARKUP_TYPE_EDITABLE`` - if False user won't have option to change
markup type (default: True)

``MARKUPWIKI_MARKUP_TYPES`` - a tuple of string and callable pairs the 
callable is used to 'render' a markup type.  Example::

    import markdown
    from docutils.core import publish_parts

    def render_rest(markup):
        parts = publish_parts(source=markup, writer_name="html4css1")
        return parts["fragment"]

    MARKUPWIKI_MARKUP_TYPES = (
        ('markdown', markdown.markdown),
        ('ReST', render_rest)
    )

Defaults to ``django-markupfield``'s detected markup types.
