
from django.conf import settings
from django.forms.models import modelform_factory
from django.forms import ValidationError

from drum.links.models import Link


BaseLinkForm = modelform_factory(Link, fields=["link", "title", "description", "image"])

try:
    import extraction
    import urllib2
    LINK_EXTRACTOR = True
except ImportError:
    LINK_EXTRACTOR = False


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

        if LINK_EXTRACTOR:
            title = self.cleaned_data.get("title", None)
            image = self.cleaned_data.get("image", None)

            if link and (not title or not description or not image):
                html = urllib2.build_opener().open(link).read()
                extracted = extraction.Extractor().extract(html, source_url=link)

                if not title and extracted.title:
                    self.cleaned_data["title"] = extracted.title

                if not description and extracted.description:
                    self.cleaned_data["description"] = extracted.description

                if not image and extracted.image:
                    self.cleaned_data["image"] = extracted.image

        return self.cleaned_data
