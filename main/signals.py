from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product

@receiver(post_save, sender=Product)
def clear_product_cache_on_save(sender, instance, **kwargs):
    """Clear product cache when a product is created or updated"""
    cache.delete_pattern("vitachoice:*")

@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    """Clear product cache when a product is deleted"""
    cache.delete_pattern("vitachoice:*")
