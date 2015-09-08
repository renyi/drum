from __future__ import unicode_literals
from django.conf import settings
from django import forms
from django.forms.models import modelform_factory
from django.forms import ValidationError

from drum.links.models import Link


BaseLinkForm = modelform_factory(Link, fields=["link", "title", "description", "category", "tags"])

class LinkForm(BaseLinkForm):
    link = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "off", 
                                                         "placeholder": "http://",
                                                         }),
                           required=False)

    title = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "off", 
                                                         "placeholder": "Leave blank to use original title.",
                                                         }),
                            required=False)

    description = forms.CharField(widget=forms.Textarea(attrs={"autocomplete": "off", 
                                                               "placeholder": "Leave blank to generate from site.",
                                                         }),
                                  required=False)

    def clean(self):
        link = self.cleaned_data.get("link", None)
        description = self.cleaned_data.get("description", None)
        if not link and not description:
            raise ValidationError("Either a link or description is required")
        return self.cleaned_data
