# Generated by Django 4.2.7 on 2023-11-06 01:46

from django.db import migrations, models
from loguru import logger
from tqdm import tqdm


def migrate_relationships(apps, schema_editor):
    from users.models import APIdentity, User

    logger.info(f"Migrate user relationship")
    for user in tqdm(User.objects.filter(is_active=True)):
        for target in user.local_following.all():
            user.identity.follow(User.objects.get(pk=target).identity)
        for target in user.local_blocking.all():
            user.identity.block(User.objects.get(pk=target).identity)
        for target in user.local_muting.all():
            user.identity.block(User.objects.get(pk=target).identity)
        user.sync_relationship()
    for user in tqdm(User.objects.filter(is_active=True)):
        for target_identity in user.identity.follow_requesting_identities:
            target_identity.accept_follow_request(user.identity)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_init_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="preference",
            name="mastodon_skip_relationship",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="preference",
            name="mastodon_skip_userinfo",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_relationships),
    ]
