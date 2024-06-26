from django.contrib import admin

# Register your models here.
from .models import Post, Group, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'post', 'pub_date', 'author')
    list_filter = ('pub_date',)
    search_fields = ('text',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Follow)
