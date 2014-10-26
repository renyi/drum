from __future__ import unicode_literals
from future import standard_library
from future.builtins import int

from time import time

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from taggit.managers import TaggableManager

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from mezzanine.core.models import Slugged, Displayable, Ownable
from mezzanine.core.request import current_request
from mezzanine.generic.models import Rating
from mezzanine.generic.fields import RatingField, CommentsField


class LinkCategory(Slugged):
    class Meta:
        verbose_name_plural = "Categories"

    def get_absolute_url(self):
        return reverse("category_list", kwargs={"slug": self.slug})


class Link(Displayable, Ownable):
    category = models.ForeignKey("links.LinkCategory", null=True, blank=True)

    link = models.URLField(null=True, blank=False)
    rating = RatingField()
    comments = CommentsField()
    tags = TaggableManager(blank=True)

    # Extraction metadata
    image = models.URLField(null=True, blank=True)
    show_image = models.BooleanField(default=True)
    extra_images = models.TextField(null=True, blank=True)
    extra_data = models.TextField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse("link_detail", kwargs={"slug": self.slug})

    @property
    def domain(self):
        return urlparse(self.url).netloc

    @property
    def url(self):
        if self.link:
            return self.link
        return current_request().build_absolute_uri(self.get_absolute_url())

    def image_tag(self):
        if self.image:
            return "<img height='100px' src='%s'>" % self.image
        else:
            return ""
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


class Profile(models.Model):

    user = models.OneToOneField("auth.User")
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    karma = models.IntegerField(default=0, editable=False)

    def __unicode__(self):
        return "%s (%s)" % (self.user, self.karma)


@receiver(post_save, sender=Rating)
def karma(sender, **kwargs):
    """
    Each time a rating is saved, check its value and modify the
    profile karma for the related object's user accordingly.
    Since ratings are either +1/-1, if a rating is being edited,
    we can assume that the existing rating is in the other direction,
    so we multiply the karma modifier by 2.
    """
    rating = kwargs["instance"]
    value = int(rating.value)
    if not kwargs["created"]:
        value *= 2
    content_object = rating.content_object
    if rating.user != content_object.user:
        queryset = Profile.objects.filter(user=content_object.user)
        queryset.update(karma=models.F("karma") + value)
