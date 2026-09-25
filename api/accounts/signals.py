from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import Profile, User


@receiver(pre_save, sender=User)
def sync_profile_email(sender, instance, **kwargs):
    if not instance.pk:
        return
    Profile.objects.filter(user_id=instance.pk).update(email=instance.email)


@receiver(post_save, sender=User)
def ensure_profile_email_on_create(sender, instance, created, **kwargs):
    if created:
        return
    Profile.objects.filter(user_id=instance.pk).update(email=instance.email)
