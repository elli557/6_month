from django.contrib import admin
from users.models import CustomUser

admin.site.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["id"]