# Generated by Django 2.2.16 on 2023-02-18 14:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_auto_20230218_1437'),
    ]

    operations = [
        migrations.RenameField(
            model_name='follow',
            old_name='is_delited',
            new_name='is_deleted',
        ),
    ]
