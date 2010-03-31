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

django-markupwiki depends on django 1.2+, django-markupfield and libraries
for whichever markup options you wish to include.


Settings
========

To best make use of MarkupField you should define the 
``MARKUP_FIELD_TYPES`` setting, a dictionary of strings to callables that 
'render' a markup type::

    import markdown
    from docutils.core import publish_parts

    def render_rest(markup):
        parts = publish_parts(source=markup, writer_name="html4css1")
        return parts["fragment"]

    MARKUP_FIELD_TYPES = {
        'markdown': markdown.markdown,
        'ReST': render_rest,
    }

If you do not define a ``MARKUP_FIELD_TYPES`` then one is provided with the
following markup types available:

html:
    allows HTML, potentially unsafe
plain:
    plain text markup, calls urlize and replaces text with linebreaks
markdown:
    default `markdown`_ renderer (only if `python-markdown`_ is installed)
restructuredtext:
    default `ReST`_ renderer (only if `docutils`_ is installed)
textile:
    default `textile`_ renderer (only if `textile`_ is installed)

.. _`markdown`: http://daringfireball.net/projects/markdown/
.. _`ReST`: http://docutils.sourceforge.net/rst.html
.. _`textile`: http://hobix.com/textile/quick.html
.. _`python-markdown`: http://www.freewisdom.org/projects/python-markdown/
.. _`docutils`: http://docutils.sourceforge.net/
.. _`python-textile`: http://pypi.python.org/pypi/textile


