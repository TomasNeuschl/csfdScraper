import random
import time

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError

from csfdScraper.models import Actor
from csfdScraper.models.movie import Movie


class Command(BaseCommand):
    help = 'Download data from CSFD.cz'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    base_url = 'https://www.csfd.cz'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('pages', type=int)

    def handle(self, *args, **options):
        num_of_pages = options.get('pages')
        if not 1 <= num_of_pages <= 9:
            raise CommandError('Number of pages must be between 1 and 9.')
        page_steps = [1, 100, 200, 300, 400, 500, 600, 700, 800, 900]
        # use one session to keep headers, cookies and more between requests
        with requests.Session() as session:
            session.headers.update(self.headers)
            for page in page_steps[:num_of_pages]:
                self.process_page(page, session)

    def process_page(self, page, session):
        url = f'{self.base_url}/zebricky/filmy/nejlepsi/?from={page}'
        response = self.fetch_url(url, session)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            movie_list = soup.find_all('h3', class_='film-title-norating')
            # iterate through all movies on the page and save them to the database
            for h3_element in movie_list:
                movie, created = self.scrape_movie(h3_element)
                self.stdout.write(self.style.SUCCESS(f'Saved movie: {movie.title} ({movie.year})'))
                # continue to next movie if current movie was not created
                if not movie:
                    continue
                self.process_actors(movie, session)
        else:
            self.stdout.write(self.style.ERROR('Failed to fetch CSFD data'))

    def fetch_url(self, url, session):
        try:
            response = session.get(url)
            if response.status_code == 200:
                return response
            self.stdout.write(self.style.ERROR(f'Failed to fetch data from: {url}'))
        except requests.RequestException as e:
            self.stderr.write(str(e))
        return None

    @staticmethod
    def scrape_movie(h3_element):
        movie_link = h3_element.find('a')['href']
        movie_title = h3_element.find('a', class_='film-title-name').text.strip()
        movie_year = h3_element.find('span', class_='info').text.strip()[1:-1]

        return Movie.objects.update_or_create(
            title=movie_title,
            defaults={'year': movie_year, 'link': movie_link}
        )

    def process_actors(self, movie, session):
        response = self.fetch_url(f'{self.base_url}{movie.link}', session)
        if response:
            movie_soup = BeautifulSoup(response.text, 'html.parser')
            actors_section = movie_soup.find('h4', text='Hrají:').find_parent('div')
            actor_links = actors_section.select('a')

            for actor_link in actor_links:
                actor_name = actor_link.text.strip()
                if actor_name != 'více':
                    actor_url = actor_link['href']
                    actor, _ = Actor.objects.update_or_create(name=actor_name, link=actor_url)
                    actor.movie_set.add(movie)
                    self.stdout.write(self.style.SUCCESS(f'Saved actor: {actor_name}'))

        time.sleep(random.uniform(0.2, 0.5))
