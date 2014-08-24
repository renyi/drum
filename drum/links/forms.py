
from django.conf import settings
from django.forms.models import modelform_factory
from django.forms import ValidationError

from drum.links.models import Link


BaseLinkForm = modelform_factory(Link, fields=["link", "title", "description"])
LINK_EXTRACTOR = getattr(settings, "LINK_EXTRACTOR", False)


class LinkForm(BaseLinkForm):
    def __init__(self, *args, **kwargs):
        super(LinkForm, self).__init__(*args, **kwargs)
        if LINK_EXTRACTOR:
            self.fields['title'].required = False

    def clean(self):
        link = self.cleaned_data.get("link", None)
        description = self.cleaned_data.get("description", None)

        if not link and not description:
            raise ValidationError("Either a link or description is required")

        return self.cleaned_data
