# Generated by Django 3.2.25 on 2024-04-27 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'ordering': ('author',), 'verbose_name': 'Подписка', 'verbose_name_plural': 'подписки'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('username',), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
        ),
    ]
