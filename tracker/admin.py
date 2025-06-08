from django.contrib import admin
from .models import BrowsingHistory

@admin.register(BrowsingHistory)
class BrowsingHistoryAdmin(admin.ModelAdmin):
    list_display = ('url', 'query', 'time_spent', 'timestamp')
    search_fields = ('url', 'query')
    list_filter = ('timestamp',)
