from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpf', 'email', 'role', 'phone')
    search_fields = ('name', 'cpf', 'email', 'role')


admin.site.register(Profile, ProfileAdmin)