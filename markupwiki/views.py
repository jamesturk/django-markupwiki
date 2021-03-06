from difflib import HtmlDiff
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseForbidden
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404
from django.template import RequestContext
from django.utils.functional import wraps
from markupwiki.models import Article, ArticleVersion, PUBLIC, DELETED, LOCKED
from markupwiki.forms import ArticleForm, StaffModerationForm, ArticleRenameForm

CREATE_MISSING_ARTICLE = getattr(settings,
                                 'MARKUPWIKI_CREATE_MISSING_ARTICLES', True)

EDITOR_TEST_FUNC = getattr(settings, 'MARKUPWIKI_EDITOR_TEST_FUNC',
                           lambda u: u.is_authenticated())
MODERATOR_TEST_FUNC = getattr(settings, 'MARKUPWIKI_MODERATOR_TEST_FUNC',
                              lambda u: u.is_staff)

def title_check(view):
    def new_view(request, title, *args, **kwargs):
        newtitle = title.replace(' ', '_')
        if newtitle != title:
            return redirect(request.path.replace(title, newtitle),
                            permanent=True)
        else:
            return view(request, title, *args, **kwargs)
    return wraps(view)(new_view)

@title_check
def view_article(request, title, n=None):
    ''' view an article (or a specific revision of an article)

    if n is specified will show nth revision, otherwise latest will be shown

    if the article does not exist the user will be redirected to the edit page

    Context:
        article     - ``Article`` instance
        version     - ``ArticleVersion`` to display
        mod_form    - ``StaffModerationForm`` instance present if user is staff
        rename_form - ``ArticleRenameForm`` instance present if user is staff

    Template:
        article.html - default template used
    '''

    try:
        article = Article.objects.get(title=title)
    except Article.DoesNotExist:
        if CREATE_MISSING_ARTICLE:
            return redirect('edit_article', title)
        else:
            raise Http404()

    if article.redirect_to_id:
        return redirect(article.redirect_to)

    if n:
        version = article.versions.get(number=n)
    else:
        version = article.versions.latest()
        version.is_latest = True

    # set editable flag on article
    article.editable = article.is_editable_by_user(request.user)

    context = {'article':article, 'version': version}

    if request.user.is_staff:
        context['mod_form'] = StaffModerationForm(instance=article)
        context['rename_form'] = ArticleRenameForm()

    return render_to_response('markupwiki/article.html', context,
                              context_instance=RequestContext(request))

@title_check
@user_passes_test(EDITOR_TEST_FUNC)
def edit_article(request, title):
    ''' edit (or create) an article

        Context:
            title - title of article being edited
            article - article being edited (potentially None)
            form - form to edit article

        Templates:
            edit_article.html - Default template for editing the article.
            locked_article.html - Template shown if editing is locked.
    '''
    try:
        article = Article.objects.get(title=title)
    except Article.DoesNotExist:
        article = None

    # check for staff lock
    if article and not article.is_editable_by_user(request.user):
        return HttpResponseForbidden('not authorized to edit')

    if request.method == 'GET':
        # either get an empty ArticleForm or one based on latest version
        if article:

            if not article.get_write_lock(request.user):
                # set message and redirect
                messages.info(request, 'Someone else is currently editing this page, please wait and try again.')
                return redirect(article)

            version = article.versions.latest()
            form = ArticleForm(data={'body':version.body,
                               'body_markup_type':version.body_markup_type})
        else:
            form = ArticleForm()
    elif request.method == 'POST':
        form = ArticleForm(request.POST)
        user = None if request.user.is_anonymous() else request.user
        
        if form.is_valid():
            if not article:
                # if article doesn't exist create it and start num at 0
                article = Article.objects.create(title=title,
                                                 creator=user)
                num = 0
            else:
                if not article.get_write_lock(request.user):
                    # set message and redirect
                    messages.error(request, 'Your session timed out and someone else is now editing this page.')
                    return redirect(article)

                # otherwise get latest num
                num = article.versions.latest().number + 1

            # create a new version attached to article specified in name
            version = form.save(False)
            version.article = article
            version.author = user
            version.number = num
            version.save()

            article.get_write_lock(user or request, release=True)

            # redirect to view article on save
            return redirect(article)

    return render_to_response('markupwiki/edit_article.html',
                              {'title':title, 'article':article, 'form': form},
                              context_instance=RequestContext(request))


@require_POST
@user_passes_test(MODERATOR_TEST_FUNC)
@title_check
def article_status(request, title):
    ''' POST-only view to update article status (staff-only)
    '''
    article = get_object_or_404(Article, title=title)
    article.status = int(request.POST['status'])
    article.save()

    return redirect(article)

@require_POST
@user_passes_test(MODERATOR_TEST_FUNC)
@title_check
def revert(request, title):
    ''' POST-only view to revert article to a specific revision
    '''
    article = get_object_or_404(Article, title=title)
    revision_id = int(request.POST['revision'])
    revision = get_object_or_404(article.versions, number=revision_id)
    ArticleVersion.objects.create(article=article, author=request.user,
                                  number=article.versions.latest().number,
                                  comment='reverted to r%s' % revision_id,
                                  body=revision.body)

    return redirect(article)

@require_POST
@user_passes_test(MODERATOR_TEST_FUNC)
@title_check
def rename(request, title):
    ''' POST-only view to rename article '''
    article = get_object_or_404(Article, title=title)
    new_title = request.POST['new_title']
    article.title = new_title.replace(' ', '_')
    article.save()
    new_article = Article.objects.create(title=title, creator=request.user,
                                         redirect_to=article)
    return redirect(article)

@title_check
def article_history(request, title):
    article = get_object_or_404(Article, title=title)
    versions = article.versions.filter(removed=False)
    return render_to_response('markupwiki/history.html',
                              {'article':article, 'versions':versions},
                              context_instance=RequestContext(request))

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
    return render_to_response('markupwiki/article_diff.html',
                              {'article': article, 'table':table,
                               'from': from_id, 'to':to_id},
                              context_instance=RequestContext(request))
