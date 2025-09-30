from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product

PRODUCT_CACHE_KEY = "product_list_cache"


@receiver(post_save, sender=Product)
def clear_product_cache_on_save(sender, instance, **kwargs):
    """Clear product cache when a product is created or updated"""
    print("Signal: Clearing cache on save/update")
    cache.delete(PRODUCT_CACHE_KEY)


@receiver(post_delete, sender=Product)
def clear_product_cache_on_delete(sender, instance, **kwargs):
    """Clear product cache when a product is deleted"""
    print("Signal: Clearing cache on delete")
    cache.delete(PRODUCT_CACHE_KEY)
