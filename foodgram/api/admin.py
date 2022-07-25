from django.contrib import admin
from django.contrib.auth.models import Group

admin.site.site_title = 'FoodGram Administration'
admin.site.site_header = 'FoodGram Administration'
admin.site.index_title = 'FoodGram Administration'

admin.site.unregister(Group)
