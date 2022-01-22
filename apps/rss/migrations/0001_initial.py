# Generated by Django 3.2.11 on 2022-01-22 21:36

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookmarkedEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Bookmarked entry',
                'verbose_name_plural': 'Bookmarked entries',
                'ordering': ('-create_time',),
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(help_text='Title of the feed', max_length=150)),
                ('url', models.TextField(blank=True, help_text='URL for the HTML for this entry', null=True, validators=[django.core.validators.URLValidator()])),
                ('guid', models.TextField(blank=True, help_text='GUID for the entry, according to the feed', null=True)),
                ('content', models.TextField(blank=True, help_text='description of entry')),
                ('publish_date', models.DateTimeField(blank=True, db_index=True, help_text='when this entry says it was published', null=True)),
                ('bookmark_users', models.ManyToManyField(help_text='Users who have bookmarked the entry', related_name='bookmarked_entries', through='rss.BookmarkedEntry', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Entry',
                'verbose_name_plural': 'Entries',
                'ordering': ('-publish_date', '-create_time'),
            },
        ),
        migrations.CreateModel(
            name='RSSFeed',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(help_text='Title of the feed', max_length=150)),
                ('feed_url', models.TextField(help_text='Link of the feed', unique=True, validators=[django.core.validators.URLValidator()])),
                ('description', models.TextField(help_text='Description of the feed')),
                ('last_update', models.DateTimeField(blank=True, help_text='Last time the feed says it changed', null=True)),
                ('last_checked', models.DateTimeField(blank=True, help_text='Last time we checked the feed', null=True)),
                ('next_check', models.DateTimeField(blank=True, help_text='Next time we need to update posts of feed', null=True)),
                ('last_status', models.IntegerField(blank=True, help_text='Status code of last request', null=True)),
                ('number_of_errors', models.IntegerField(default=0, help_text='Number of errors that have been occurred when updating posts')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='A feed will become inactive when a permanent error occurs')),
            ],
            options={
                'verbose_name': 'RSS Feed',
                'verbose_name_plural': 'RSS Feeds',
                'ordering': ('-last_update', '-last_checked'),
            },
        ),
        migrations.CreateModel(
            name='SeenEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rss.entry')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Seen entry',
                'verbose_name_plural': 'Seen entries',
                'ordering': ('-create_time',),
            },
        ),
        migrations.CreateModel(
            name='RSSFeedFollower',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('feed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rss.rssfeed')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'RSS Feed follower',
                'verbose_name_plural': 'RSS Feed followers',
                'ordering': ('-create_time',),
            },
        ),
        migrations.AddField(
            model_name='rssfeed',
            name='followers',
            field=models.ManyToManyField(help_text='Users who have followed RSS Feed', related_name='feeds', through='rss.RSSFeedFollower', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='FavouritedEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rss.entry')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Favourited entry',
                'verbose_name_plural': 'Favourited entries',
                'ordering': ('-create_time',),
            },
        ),
        migrations.CreateModel(
            name='EntryComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modify_time', models.DateTimeField(auto_now=True)),
                ('body', models.TextField()),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='rss.entry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entry_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Entry comment',
                'verbose_name_plural': 'Entry comments',
                'ordering': ('-create_time',),
            },
        ),
        migrations.AddField(
            model_name='entry',
            name='favourite_users',
            field=models.ManyToManyField(help_text='Users who have favourited the entry', related_name='favorited_entries', through='rss.FavouritedEntry', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entry',
            name='feed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='rss.rssfeed'),
        ),
        migrations.AddField(
            model_name='entry',
            name='seen_users',
            field=models.ManyToManyField(help_text='Users who have seen the entry', related_name='seen_entries', through='rss.SeenEntry', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='bookmarkedentry',
            name='entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rss.entry'),
        ),
        migrations.AddField(
            model_name='bookmarkedentry',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
