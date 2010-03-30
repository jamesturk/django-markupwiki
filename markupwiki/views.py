from difflib import HtmlDiff
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.functional import wraps
from markupwiki.models import Article, PUBLIC, PRIVATE, DELETED, LOCKED
from markupwiki.forms import ArticleForm, StaffModerationForm, ModerationForm

def title_check(view):
    def new_view(request, title, *args, **kwargs):
        newtitle = title.replace(' ', '_')
        if newtitle != title:
            return redirect(request.path.replace(title, newtitle))
        else:
            return view(request, title, *args, **kwargs)
    return wraps(view)(new_view)

@title_check
def view_article(request, title, n=None):
    try:
        article = Article.objects.get(title=title)
    except Article.DoesNotExist:
        return redirect('edit_article', title)

    if n:
        version = article.versions.get(number=n)
    else:
        version = article.versions.latest()

    context = {'article':article, 'version': version}

    if request.user.is_staff:
        context['form'] = StaffModerationForm(instance=article)
    elif request.user == article.creator:
        context['form'] = ModerationForm(instance=article)

    if article.status == DELETED:
        return render_to_response('deleted_article.html', context,
                                  context_instance=RequestContext(request))
    elif (article.status == PRIVATE and request.user != article.creator
          and not request.user.is_staff):
        return render_to_response('private_article.html', context,
                                  context_instance=RequestContext(request))

    return render_to_response('article.html', context,
                              context_instance=RequestContext(request))

@title_check
@login_required
def edit_article(request, title):
    try:
        article = Article.objects.get(title=title)
    except Article.DoesNotExist:
        article = None

    if article.locked:
        return render_to_response('article_locked.html', {'article': article})

    if request.method == 'GET':
        if article:
            version = article.versions.latest()
            form = ArticleForm(data={'body':version.body,
                               'body_markup_type':version.body_markup_type})
        else:
            form = ArticleForm()
    elif request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            if not article:
                article = Article.objects.create(title=title,
                                                 creator=request.user)
                num = 0
            else:
                num = article.versions.latest().number + 1
            version = form.save(False)
            version.article = article
            version.author = request.user
            version.number = num
            version.save()
            return redirect(article)

    return render_to_response('edit_article.html', {'title':title,
                                                    'article':article,
                                                    'form': form})


@require_POST
@title_check
def article_status(request, title):
    article = get_object_or_404(Article, title=title)
    status = int(request.POST['status'])

    if article.status in (LOCKED, DELETED) or status in (LOCKED, DELETED):
        perm_test = lambda u,a: u.is_staff
    elif article.status in (PUBLIC, PRIVATE) or status in (PUBLIC, PRIVATE):
        perm_test = lambda u,a: u.is_staff or u == a.creator

    if perm_test(request.user, article):
        article.status = status
        article.save()
        return redirect(article)
    else:
        return HttpResponseForbidden('access denied')

@title_check
def article_history(request, title):
    article = get_object_or_404(Article, title=title)
    versions = article.versions.filter(removed=False)
    return render_to_response('history.html', {'article':article,
                                               'versions':versions})

@title_check
def article_diff(request, title):
    article = get_object_or_404(Article, title=title)
    from_id = int(request.GET['from'])
    to_id = int(request.GET['to'])
    from_version = article.versions.get(number=from_id)
    to_version = article.versions.get(number=to_id)
    differ = HtmlDiff()
    from_body = from_version.body.raw.split('\n')
    to_body = to_version.body.raw.split('\n')
    table = differ.make_table(from_body, to_body)
    return render_to_response('article_diff.html', {'table':table})
