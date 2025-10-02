from django.contrib import admin
from .models import Ingredient

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'source', 'safety', 'safety_level', 'created_at']
    list_filter = ['category', 'source', 'safety']
    search_fields = ['name', 'category', 'source']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'safety_level', 'safety_color']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'source')
        }),
        ('Safety', {
            'fields': ('safety', 'safety_level', 'safety_color')
        }),
        ('Additional Info', {
            'fields': ('evidence',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )