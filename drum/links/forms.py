from __future__ import unicode_literals
from django.conf import settings
from django.forms.models import modelform_factory
from django.forms import ValidationError

from drum.links.models import Link


LINK_ONLY = getattr(settings, "LINK_ONLY", False)

if LINK_ONLY:
    LinkForm = modelform_factory(Link, fields=["link", "category", "tags"])

else:
    BaseLinkForm = modelform_factory(Link, fields=["title", "link", "description", "category", "tags"])

    class LinkForm(BaseLinkForm):
        def clean(self):
            link = self.cleaned_data.get("link", None)
            description = self.cleaned_data.get("description", None)
            if not link and not description:
                raise ValidationError("Either a link or description is required")
            return self.cleaned_data
