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
    ''' view an article (or a specific revision of an article)

    if n is specified will show nth revision, otherwise latest will be shown

    if the article does not exist the user will be redirected to the edit page

    Context:
        article - ``Article`` instance
        version - ``ArticleVersion`` to display
        form    - ``ModerationForm`` or ``StaffModerationForm`` instance
                  only present if user is staff or the article creator

    Templates:
        article.html - default template used
        deleted_article.html - template used if article has been deleted
        private_article.html - template used if article is private for user
    '''

    try:
        article = Article.objects.get(title=title)
    except Article.DoesNotExist:
        return redirect('edit_article', title)

    if n:
        version = article.versions.get(number=n)
    else:
        version = article.versions.latest()
        version.is_latest = True

    # set editable flag on article
    article.editable = article.is_editable_by_user(request.user)

    context = {'article':article, 'version': version}


    if request.user.is_staff:
        context['form'] = StaffModerationForm(instance=article)
    elif request.user == article.creator and article.status in (PUBLIC, PRIVATE):
        context['form'] = ModerationForm(instance=article)

    if article.is_deleted():
        return render_to_response('markupwiki/deleted_article.html', context,
                                  context_instance=RequestContext(request))
    elif (article.is_private() and request.user != article.creator
          and not request.user.is_staff):
        return render_to_response('private_article.html', context,
                                  context_instance=RequestContext(request))

    return render_to_response('markupwiki/article.html', context,
                              context_instance=RequestContext(request))

@title_check
@login_required
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

    if article and article.is_locked():
        return render_to_response('locked_article.html', {'article': article})

    if request.method == 'GET':
        # either get an empty ArticleForm or one based on latest version
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
                # if article doesn't exist create it and start num at 0
                article = Article.objects.create(title=title,
                                                 creator=request.user)
                num = 0
            else:
                # otherwise get latest num
                num = article.versions.latest().number + 1

            # create a new version attached to article specified in name
            version = form.save(False)
            version.article = article
            version.author = request.user
            version.number = num
            version.save()

            # redirect to view article on save
            return redirect(article)

    return render_to_response('edit_article.html', {'title':title,
                                                    'article':article,
                                                    'form': form})


@require_POST
@title_check
def article_status(request, title):
    ''' POST-only view to update article status
    '''
    article = get_object_or_404(Article, title=title)
    status = int(request.POST['status'])

    # can only change status to/from locked or deleted if staff
    if article.status in (LOCKED, DELETED) or status in (LOCKED, DELETED):
        perm_test = lambda u,a: u.is_staff
    # can only change status to/from public/private if staff or creator
    elif article.status in (PUBLIC, PRIVATE) or status in (PUBLIC, PRIVATE):
        perm_test = lambda u,a: u.is_staff or u == a.creator

    # check that requrired permissions are met before updating status
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
