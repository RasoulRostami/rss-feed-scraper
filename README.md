# Simple RSS Scraper

This is a simple RSS scraper Django application, Users can follow multiple feeds and study the entires. 

### User actions

- Create account
- Update account: update user info and password
- Search and filter RSS Feeds
- Create new RSS feeds
- Follow/ Unfollow RSS feeds
- Add / Remove entries (posts) to bookmark
- Add / Remove entries (posts) to favorite
- Write / Read comments

## Note

- Entries of RSS Feeds update with celery schedule tasks (asynchronously)
- Application is Dockerize and you can use it easily 

## How to start

### Install

pull the git repository

```bash

```

Create custom `.env` file for environment variables. you can copy `env-example` and file you own values

**Note**: Database Information between `docker-compose.yml` (db section)  and `.env` file must have same value
**Recommendation**: You can don't modify the values for develop level

Run docker-compose

```
docker-compose up --build
```

### develop

You can study swagger documents to understand APIs, See request body and response boy
swagger URL: ` localhoust:api-docs/`

### tests

After developing, you can see test coverage with below commands

```
docker exec -it rss_backend coverage run manage.py test
docker exec -it rss_backend coverage html
```

After above command HTML repost will be created in `./htmlcov/index.html` and you can analysis tests
If you encounter with permission denied error while opening HTML files, run below command

```
sudo chown -R $USER:$USER .
```

Now tests cover %95 of project

## Recommendation

Remaining features:

- `Dockerfile` and `docker-compose.yml` Product version
- initial command to fill the database with test data
- Add more detail to `RSSFeed` and Entry model
- Write better mock tests
- Add more detail to celery beat service

