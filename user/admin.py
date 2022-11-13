from django.contrib import admin
from user.models import Templates, WA_MSG_Provider, User1

# Register your models here.
# admin.register(User1)


@admin.register(User1)
class siteUsers(admin.ModelAdmin):
    list_display = ("user_name", "email")


@admin.register(WA_MSG_Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("provider_name",)


