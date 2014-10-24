from __future__ import unicode_literals

from django.contrib import admin
from mezzanine.core.admin import DisplayableAdmin
from drum.links.models import Link, LinkCategory


class LinkAdmin(DisplayableAdmin):

    list_display = ("id", "title", "category", "status", "publish_date",
                    "user", "comments_count", "rating_sum", "image_tag")
    list_display_links = ("id",)
    list_editable = ("status", "category")
    list_filter = ("status", "user__username", "category")
    ordering = ("-publish_date",)

    fieldsets = (
        (None, {
            "fields": ("title", "category", "link", "tags", "status", "publish_date", "user"),
        }),
    )
admin.site.register(Link, LinkAdmin)


class LinkCategoryAdmin(admin.ModelAdmin):

    list_display = ("title", )
    list_display_links = ("title",)
    ordering = ("-title",)

    fieldsets = (
        (None, {
            "fields": ("title", ),
        }),
    )


admin.site.register(LinkCategory, LinkCategoryAdmin)
