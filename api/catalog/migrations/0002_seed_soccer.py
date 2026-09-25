from django.db import migrations


def seed_soccer(apps, schema_editor):
    Sport = apps.get_model("catalog", "Sport")
    CoachRole = apps.get_model("catalog", "CoachRole")
    if Sport.objects.filter(slug="soccer").exists():
        return
    sport = Sport.objects.create(slug="soccer", name="Soccer")
    for slug, name in [
        ("head-coach", "Head coach"),
        ("assistant", "Assistant coach"),
        ("goalkeeper", "Goalkeeper coach"),
        ("youth", "Youth coach"),
        ("fitness", "Fitness coach"),
    ]:
        CoachRole.objects.create(sport=sport, slug=slug, name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_soccer, migrations.RunPython.noop),
    ]
