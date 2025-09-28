from django.contrib import admin
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    benefits = forms.CharField(widget=forms.Textarea, help_text="Enter one benefit per line")
    key_actives = forms.CharField(widget=forms.Textarea, help_text="Enter one active per line")
    free_from = forms.CharField(widget=forms.Textarea, help_text="Enter one item per line")

    class Meta:
        model = Product
        fields = "__all__"

    def clean_benefits(self):
        return [b.strip() for b in self.cleaned_data["benefits"].splitlines() if b.strip()]

    def clean_key_actives(self):
        return [k.strip() for k in self.cleaned_data["key_actives"].splitlines() if k.strip()]
    
    def clean_free_from(self):
        return [f.strip() for f in self.cleaned_data["free_from"].splitlines() if f.strip()]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ("name", "category", "price", "rating", "review_count", "created_at")
    search_fields = ("name", "subtitle")