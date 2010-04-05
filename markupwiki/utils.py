'''
    utilities for wikifying text
'''

import re
from django.core.urlresolvers import reverse

link_re = re.compile('\[\[(?P<link>.*?)(?:\|(?P<name>.*?))?\]\]')

__sample_content = '''
    this is a sample

    [[testlink]]

    [[testlink|with a name]]

    [[another test link]]

    [[multi
    line]]
'''

def link_repl_func(match_obj):
    gd = match_obj.groupdict()
    name = gd['name'] or gd['link']
    name = name.strip()
    link = reverse('view_article', args=[gd['link'].strip()])
    return '<a href="%s">%s</a>' % (link, name)

def make_wiki_links(text):
    return link_re.sub(link_repl_func, text)

def wikify_markup_wrapper(f):
    if not hasattr(f, 'wikified_markup'):
        new_f = lambda text: make_wiki_links(f(text))
        new_f.wikified_markup = True
        return new_f
    return f
