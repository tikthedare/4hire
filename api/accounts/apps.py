from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from django.db.models.signals import post_migrate

        from accounts import signals  # noqa: F401
        from accounts.staff import ensure_staff_group

        post_migrate.connect(ensure_staff_group, dispatch_uid="accounts.ensure_staff_group")
