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
------------

django-markupwiki depends on django 1.2+, django-markupfield 1.0.0b+ and
libraries for whichever markup options you wish to include.


Settings
========


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
