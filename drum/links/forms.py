
from django.conf import settings
from django.forms.models import modelform_factory
from django.forms import ValidationError

from drum.links.models import Link


LinkForm = modelform_factory(Link, fields=["link"])
