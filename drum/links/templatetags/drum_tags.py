from __future__ import unicode_literals

from collections import defaultdict
from django.template.defaultfilters import timesince

from mezzanine import template
from mezzanine.generic.models import ThreadedComment

from drum.links.utils import order_by_score
from drum.links.models import LinkCategory
from drum.links.views import CommentList, USER_PROFILE_RELATED_NAME


register = template.Library()


@register.filter
def get_profile(user):
    """
    Returns the profile object associated with the given user.
    """
    return getattr(user, USER_PROFILE_RELATED_NAME)


@register.simple_tag(takes_context=True)
def order_comments_by_score_for(context, link):
    """
    Preloads threaded comments in the same way Mezzanine initially does,
    but here we order them by score.
    """
    comments = defaultdict(list)
    qs = link.comments.visible().select_related(
        "user",
        "user__%s" % (USER_PROFILE_RELATED_NAME)
    )
    for comment in order_by_score(qs, CommentList.score_fields, "submit_date"):
        comments[comment.replied_to_id].append(comment)
    context["all_comments"] = comments
    return ""


@register.filter
def short_timesince(date):
    return timesince(date).split(",")[0]


@register.as_tag
def link_category_list(*args):
    return LinkCategory.objects.all()


@register.as_tag
def latest_comments(limit=5, *args):
    qs = ThreadedComment.objects.filter(is_removed=False, is_public=True)
    return qs.reverse()[:limit]
