from __future__ import unicode_literals
from future.builtins import super

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import info, error

from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.views.generic import (ListView, CreateView, DetailView,
    DeleteView, UpdateView)

from mezzanine.conf import settings
from mezzanine.generic.models import ThreadedComment
from mezzanine.utils.views import paginate

from drum.links.forms import LinkForm
from drum.links.models import Link, LinkCategory
from drum.links.utils import order_by_score


EXTRACT_LINKS = getattr(settings, "EXTRACT_LINKS", False)
if EXTRACT_LINKS:
    import extraction
    import urllib2


class UserFilterView(ListView):
    """
    List view that puts a ``profile_user`` variable into the context,
    which is optionally retrieved by a ``username`` urlpattern var.
    If a user is loaded, ``object_list`` is filtered by the loaded
    user. Used for showing lists of links and comments.
    """

    def get_context_data(self, **kwargs):
        context = super(UserFilterView, self).get_context_data(**kwargs)
        try:
            username = self.kwargs["username"]
        except KeyError:
            profile_user = None
        else:
            users = User.objects.select_related("profile")
            lookup = {"username__iexact": username, "is_active": True}
            profile_user = get_object_or_404(users, **lookup)
            qs = context["object_list"].filter(user=profile_user)
            context["object_list"] = qs
        context["profile_user"] = profile_user
        context["no_data"] = ("Whoa, there's like, literally no data here, "
                              "like seriously, I totally got nothin.")
        return context


class ScoreOrderingView(UserFilterView):
    """
    List view that optionally orders ``object_list`` by calculated
    score. Subclasses must defined a ``date_field`` attribute for the
    related model, that's used to determine time-scaled scoring.
    Ordering by score is the default behaviour, but can be
    overridden by passing ``False`` to the ``by_score`` arg in
    urlpatterns, in which case ``object_list`` is sorted by most
    recent, using the ``date_field`` attribute. Used for showing lists
    of links and comments.
    """

    def get_context_data(self, **kwargs):
        context = super(ScoreOrderingView, self).get_context_data(**kwargs)
        qs = context["object_list"]
        context["by_score"] = self.kwargs.get("by_score", True)
        if context["by_score"]:
            qs = order_by_score(qs, self.score_fields, self.date_field)
        else:
            qs = qs.order_by("-" + self.date_field)
        context["object_list"] = paginate(qs, self.request.GET.get("page", 1),
            settings.ITEMS_PER_PAGE, settings.MAX_PAGING_LINKS)
        context["title"] = self.get_title(context)
        return context


class LinkView(object):
    """
    List and detail view mixin for links - just defines the correct
    queryset.
    """
    def get_queryset(self):
        return Link.objects.published().select_related("user", "user__profile")


class LinkList(LinkView, ScoreOrderingView):
    """
    List view for links, which can be for all users (homepage) or
    a single user (links from user's profile page). Links can be
    order by score (homepage, profile links) or by most recently
    created ("newest" main nav item).
    """

    date_field = "publish_date"
    score_fields = ["rating_sum", "comments_count"]

    def get_title(self, context):
        if context["by_score"]:
            return ""  # Homepage
        if context["profile_user"]:
            return "Links by %s" % context["profile_user"].profile
        else:
            return "Newest"


class LinkCreate(CreateView):
    """
    Link creation view - assigns the user to the new link, as well
    as setting Mezzanine's ``gen_description`` attribute to ``False``,
    so that we can provide our own descriptions.
    """

    form_class = LinkForm
    model = Link

    def form_valid(self, form):
        if form.instance.link:
            if EXTRACT_LINKS:
                html = urllib2.build_opener().open(form.instance.link).read()
                extracted = extraction.Extractor().extract(html, source_url=form.instance.link)

                if not form.instance.title:
                    form.instance.title = extracted.title

                if not form.instance.description:
                    form.instance.description = extracted.description

                if not form.instance.image:
                    form.instance.image = extracted.image

                if extracted.images:
                    form.instance.extra_images = ','.join(extracted.images)

                form.instance.extra_data = ','.join(extracted.titles + extracted.descriptions + extracted.urls)

            hours = getattr(settings, "ALLOWED_DUPLICATE_LINK_HOURS", None)
            if hours:
                lookup = {
                    "link": form.instance.link,
                    "publish_date__gt": now() - timedelta(hours=hours),
                }
                try:
                    link = Link.objects.get(**lookup)
                except Link.DoesNotExist:
                    pass
                else:
                    error(self.request, "Link exists")
                    return redirect(link)

        form.instance.user = self.request.user
        form.instance.gen_description = False
        info(self.request, "Link created")
        return super(LinkCreate, self).form_valid(form)


class LinkDetail(LinkView, DetailView):
    """
    Link detail view - threaded comments and rating are implemented
    in its template.
    """
    pass


class CommentList(ScoreOrderingView):
    """
    List view for comments, which can be for all users ("comments" and
    "best" main nav items) or a single user (comments from user's
    profile page). Comments can be order by score ("best" main nav item)
    or by most recently created ("comments" main nav item, profile
    comments).
    """

    date_field = "submit_date"
    score_fields = ["rating_sum"]

    def get_queryset(self):
        qs = ThreadedComment.objects.filter(is_removed=False, is_public=True)
        select = ["user", "user__profile"]
        prefetch = ["content_object"]
        return qs.select_related(*select).prefetch_related(*prefetch)

    def get_title(self, context):
        if context["profile_user"]:
            return "Comments by %s" % context["profile_user"].profile
        elif context["by_score"]:
            return "Best comments"
        else:
            return "Latest comments"


class CategoryList(LinkList):
    def get_queryset(self):
        qs = super(CategoryList, self).get_queryset()
        slug = self.kwargs.get("slug", None)

        if slug:
            qs = qs.filter(category__slug=slug)

        return qs


class TagList(LinkList):
    def get_queryset(self):
        qs = super(TagList, self).get_queryset()
        slug = self.kwargs.get("slug", None)

        if slug:
            qs = qs.filter(tags__slug__in=[slug]).distinct()

        return qs
