from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing_page, name='home'),

    path('statistics/', views.statistics_page, name='statistics'),

<<<<<<< HEAD
    path('locations/', views.location_page, name='locations'),

    path('editions/', views.edition_list, name='editions'),
=======
    path('editions/', views.edition_page, name='editions'),

    path('locations/', views.location_page, name='locations'),
>>>>>>> Adding Django app files

    path('players/', views.player_list, name='players'),
    path('players/profile/<player>', views.player_profile_page, name='player-profile'),

    path('games/', views.game_list, name='games'),

    path('scoresheets/', views.scoresheet_list, name='scoresheets'),
    path('scoresheets/game/<game>', views.scoresheet_list, name='game-scoresheets'),
]
