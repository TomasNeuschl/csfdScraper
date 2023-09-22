import random
import time

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from unidecode import unidecode

from csfdScraper.models import Actor
from csfdScraper.models.movie import Movie
from csfdScraper.models.movie_actor_link import MovieActorLink


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
        num_of_movies = options.get('pages')
        if not 1 <= num_of_movies <= 1000:
            raise CommandError('Number of movies must be between 1 and 1000.')
        page_steps = [1, 100, 200, 300, 400, 500, 600, 700, 800, 900]
        # use one session to keep headers, cookies and more between requests
        page = 0
        processed = 0
        with requests.Session() as session:
            session.headers.update(self.headers)
            movies_data = {}
            actors_data = {}
            links_data = []
            while processed != num_of_movies:
                processed, movies, actors, links = self.process_page(page_steps[page], session, num_of_movies,
                                                                     processed)

                # Update the movie and actor dictionaries with new data
                movies_data.update(movies)
                actors_data.update(actors)
                links_data.extend(links)

                page += 1

                # Bulk create movies and actors
            try:
                Movie.objects.bulk_create(movies_data.values())
                Actor.objects.bulk_create(actors_data.values())
            except IntegrityError as e:
                print(f'Data already in database try to delete db and retry')

            # Create MovieActorLink objects using references from dictionaries
            links_to_create = [
                MovieActorLink(movie=movies_data[link['movie_id']], actor=actors_data[link['actor_id']])
                for link in links_data
            ]

            # Bulk create MovieActorLink objects
            MovieActorLink.objects.bulk_create(links_to_create)

    def process_page(self, page, session, num_of_movies, processed):
        url = f'{self.base_url}/zebricky/filmy/nejlepsi/?from={page}'
        response = self.fetch_url(url, session)

        if response:
            movies_to_create = {}
            actors_to_create = {}
            links_to_create = []

            soup = BeautifulSoup(response.text, 'html.parser')
            movie_list = soup.find_all('h3', class_='film-title-norating')

            for h3_element in movie_list:
                print(f'Processing: {processed + 1}/{num_of_movies}')
                movie = self.scrape_movie(h3_element)

                if not movie:
                    continue
                print(f'scraped data for Movie: {movie.title} ({movie.year})')

                # Add movie data to the movies_to_create dictionary
                movies_to_create[movie.id] = movie

                actors, links = self.process_actors(movie, session)

                # Update the actors_to_create dictionary with actor data
                actors_to_create.update(actors)

                # Create links between movies and actors
                for key, actor in actors.items():
                    links_to_create.append({
                        'movie_id': movie.id,
                        'actor_id': key
                    })

                processed += 1

                if processed == num_of_movies:
                    break

            return processed, movies_to_create, actors_to_create, links_to_create

        else:
            self.stdout.write(self.style.ERROR('Failed to fetch CSFD data'))

        return processed, {}, {}, []

    def fetch_url(self, url, session):
        try:
            response = session.get(url)
            if response.status_code == 200:
                time.sleep(random.uniform(0.2, 0.5))
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

        return Movie(
            id=movie_link.split('/')[-2].split('-')[0],
            title=movie_title,
            normalized_title=unidecode(movie_title),
            year=movie_year,
            link=movie_link,
        )

    def process_actors(self, movie, session):
        response = self.fetch_url(f'{self.base_url}{movie.link}', session)
        if response:
            actors_to_create = {}
            links_to_create = []
            movie_soup = BeautifulSoup(response.text, 'html.parser')
            actors_section = movie_soup.find('h4', text='Hrají:').find_parent('div')
            actor_links = actors_section.select('a')

            for actor_link in actor_links:
                actor_name = actor_link.text.strip()
                if actor_name != 'více':
                    actor_url = actor_link['href']

                    # Create a unique key for the actor based on their name and URL
                    actor_id = actor_url.split('/')[-2].split('-')[0]

                    # Add actor data to the actors_data dictionary
                    actors_to_create[actor_id] = Actor(
                        id=actor_id,
                        name=actor_name,
                        normalized_name=unidecode(actor_name),
                        link=actor_url,
                    )

                    # Create a link between the movie and actor
                    links_to_create.append({
                        'movie_id': movie.id,
                        'actor_id': actor_id
                    })
                    print(f'scraped data for Actor: {actor_name}')
            return actors_to_create, links_to_create
