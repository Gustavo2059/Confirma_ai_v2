from django.contrib import admin
from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'created_at')
    search_fields = ('name', 'location')

admin.site.register(Event, EventAdmin)
