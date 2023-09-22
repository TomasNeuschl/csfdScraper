# ČSFD Scraper
This Django application will scrape ČSFD for movie data and store it in the database.
Sqlite was used to constraint options given to programmer. More optimal database would be PostgreSQL witch have built in support for search without diacritics.

To set up the project you need to do the following:
- [Install poetry](https://python-poetry.org/docs/) and then run ```poetry install```

If you wish to download data from ČSFD, you need to run:
```shell python manage.py download_data ``` and pass how many pages you want to download. For example:
```shell python manage.py download_data 1 ``` will download 100 best movies.