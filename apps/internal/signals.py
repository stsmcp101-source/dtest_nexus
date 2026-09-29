from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .icon_memory import remember_icon
from .models import InternalIcon


@receiver(post_save, sender=InternalIcon)
def remember_saved_icon(sender, instance, using, **kwargs):
    key, name = instance.key, instance.image.name
    transaction.on_commit(lambda: remember_icon(key, name), using=using)


@receiver(post_delete, sender=InternalIcon)
def remember_reset_icon(sender, instance, using, **kwargs):
    key = instance.key
    transaction.on_commit(lambda: remember_icon(key, None), using=using)
