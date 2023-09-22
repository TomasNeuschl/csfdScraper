from django.shortcuts import render, get_object_or_404
from unidecode import unidecode

from csfdScraper.models import Movie, Actor


def input_page(request):
    filtered_movies = []
    filtered_actors = []

    if request.method == 'GET':
        filter_text = unidecode(request.GET.get('filter_text', ''))

        filtered_movies = Movie.objects.filter(normalized_title__icontains=filter_text).order_by('-year')

        filtered_actors = Actor.objects.filter(normalized_name__icontains=filter_text).order_by('name')

    context = {
        'filter_text': filter_text,
        'filtered_movies': filtered_movies,
        'filtered_actors': filtered_actors,
    }
    return render(request, 'input_page.html', context)


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    return render(request, 'movie_detail.html', {'movie': movie})


def actor_detail(request, actor_id):
    actor = get_object_or_404(Actor, pk=actor_id)
    return render(request, 'actor_detail.html', {'actor': actor})
