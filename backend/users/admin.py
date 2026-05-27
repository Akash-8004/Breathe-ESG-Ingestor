from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'tenant', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'tenant')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tenant', {'fields': ('tenant',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Tenant', {'fields': ('tenant',)}),
    )
