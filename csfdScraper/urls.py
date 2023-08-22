from django.urls import path

from csfdScraper.views import views

urlpatterns = [
    path('', views.input_page, name='input_page'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('actor/<int:actor_id>/', views.actor_detail, name='actor_detail'),

]
