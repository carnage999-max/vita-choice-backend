from django.contrib import admin
from .models import Formula, FormulaItem, Ingredient

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
    
class FormulaItemInline(admin.TabularInline):
    model = FormulaItem
    extra = 1
    autocomplete_fields = ['ingredient']
    fields = ['ingredient', 'dose_value', 'dose_unit', 'notes', 'order']


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'region', 'ingredient_count', 'total_weight_mg', 'created_at']
    list_filter = ['region', 'created_at', 'owner']
    search_fields = ['name', 'owner__username', 'description']
    readonly_fields = ['created_at', 'updated_at', 'ingredient_count', 'total_weight_mg']
    inlines = [FormulaItemInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'name', 'description', 'region')
        }),
        ('Statistics', {
            'fields': ('ingredient_count', 'total_weight_mg')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FormulaItem)    
class FormulaItemAdmin(admin.ModelAdmin):
    list_display = ['formula', 'ingredient', 'dose_value', 'dose_unit', 'order']
    list_filter = ['dose_unit', 'formula__region']
    search_fields = ['formula__name', 'ingredient__name']
    autocomplete_fields = ['formula', 'ingredient']