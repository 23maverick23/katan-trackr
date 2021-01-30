from django.db.models import (Q, Count, Min, Max, Avg, Sum, F, Func, ExpressionWrapper, fields,
                              Case, Value, When, IntegerField)
from django.db.models.functions import (Lower, Length, Extract)
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import (render, get_object_or_404)
from django.utils import timezone

from datetime import (date, timedelta)

from .models import (Player, Game, Edition, Location, Scoresheet)


def to_django_weekday(date):
    return (date.isoweekday() % 7) + 1


def landing_page(request):
    template = 'pages/landing.html'
    context = {"home_active": "active"}
    return render(request, template, context)


def statistics_page(request):
    today = timezone.now()
    today_last_year = timezone.now()-timedelta(days=365)

    games_played = Game.objects.filter(is_active=True)
    games_played_year = games_played.filter(date_start__year=today.year).count()
    games_played_this_month = games_played.filter(date_start__month=today.month, date_start__year=today.year).count()
    games_played_last_month = games_played.filter(date_start__month=today.month-1, date_start__year=today.year).count()

    # Example: add new field 'duration' to queryset
    # Note: this is no longer needed as 'duration' was added to the model
    # duration = ExpressionWrapper(F('date_finish') - F('date_start'), output_field=fields.DurationField())
    # games_with_duration = games_played.annotate(duration=duration)
    game_durations = games_played.aggregate(
                                           max=Max('duration'),
                                           min=Min('duration'),
                                           sum=Sum('duration')
                                           )


    ordered_wins = games_played.order_by('-date_start')
    ordered_wins_not_null = ordered_wins.exclude(winning_scoresheet__isnull=True)
    last_win = ordered_wins_not_null[0]

    ordered_wins_players = ordered_wins.values('winning_scoresheet__player__first_name')
    ordered_wins_players_names = [game['winning_scoresheet__player__first_name'] for game in ordered_wins_players]
    current_win_streak = 1

    # Compare consecutive strings in the array and count number of consequtive elements
    for i, j in zip(ordered_wins_players_names, ordered_wins_players_names[1:]):
        if i == j:
            current_win_streak += 1
        else:
            break

    most_wins_year = games_played.filter(date_start__year=today.year) \
                                 .values('winning_scoresheet__player__first_name') \
                                 .annotate(num_wins=Count('pk')) \
                                 .order_by('-num_wins')

    most_wins_last_year = games_played.filter(date_start__year=today_last_year.year) \
                                      .values('winning_scoresheet__player__first_name') \
                                      .annotate(num_wins=Count('pk')) \
                                      .order_by('-num_wins')

    most_wins_start_position = games_played.values('winning_scoresheet__start_position') \
                                           .annotate(num_wins=Count('winning_scoresheet__start_position')) \
                                           .order_by('-num_wins')

    day_of_week = games_played.values('date_start__week_day') \
                              .annotate(count=Count('date_start__week_day')) \
                              .order_by('-count')

    editions_played = games_played.values('edition__name') \
                                  .annotate(num_editions=Count('edition')) \
                                  .order_by('-num_editions')

    scoresheets = Scoresheet.objects.filter(is_active=True)

    scoresheets_most_settlements = scoresheets.filter(game__date_start__year=today.year) \
                                              .values('player__first_name') \
                                              .annotate(num_times=Sum('num_settlements')) \
                                              .order_by('-num_times') \

    scoresheets_most_cities = scoresheets.filter(game__date_start__year=today.year) \
                                         .values('player__first_name') \
                                         .annotate(num_times=Sum('num_cities')) \
                                         .order_by('-num_times')

    scoresheets_most_metropolises = scoresheets.filter(
                                                Q(game__date_start__year=today.year) & \
                                                Q(metro_science=True) | \
                                                Q(metro_politics=True) | \
                                                Q(metro_trade=True) \
                                                ) \
                                               .values('player__first_name') \
                                               .annotate( \
                                                    num_times=Sum(Case( \
                                                        When(Q(metro_science=True) & Q(metro_politics=True) & Q(metro_trade=True), then=Value(3)), \

                                                        When(Q(metro_science=True) & Q(metro_politics=True) & Q(metro_trade=False), then=Value(2)), \
                                                        When(Q(metro_science=True) & Q(metro_politics=False) & Q(metro_trade=True), then=Value(2)), \
                                                        When(Q(metro_science=False) & Q(metro_politics=True) & Q(metro_trade=True), then=Value(2)), \

                                                        When(Q(metro_science=True) & Q(metro_politics=False) & Q(metro_trade=False), then=Value(1)), \
                                                        When(Q(metro_science=False) & Q(metro_politics=True) & Q(metro_trade=False), then=Value(1)), \
                                                        When(Q(metro_science=False) & Q(metro_politics=False) & Q(metro_trade=True), then=Value(1)), \

                                                        default=Value(0), \
                                                        output_field=IntegerField() \
                                                        ) \
                                                    )) \
                                               .order_by('-num_times')

    scoresheets_points = scoresheets.aggregate(
                                               max=Max('total_points'),
                                               min=Min('total_points'),
                                               avg=Avg('total_points')
                                               )

    scoresheets_longest_road = scoresheets.filter(longest_road=True) \
                                          .values('player__first_name') \
                                          .annotate(num_times=Count('pk')) \
                                          .order_by('-num_times')

    scoresheets_largest_army = scoresheets.filter(largest_army=True) \
                                          .values('player__first_name') \
                                          .annotate(num_times=Count('pk')) \
                                          .order_by('-num_times')

    scoresheets_merchant = scoresheets.filter(merchant=True) \
                                      .values('player__first_name') \
                                      .annotate(num_times=Count('pk')) \
                                      .order_by('-num_times')

    scoresheets_harbormaster = scoresheets.filter(harbormaster=True) \
                                      .values('player__first_name') \
                                      .annotate(num_times=Count('pk')) \
                                      .order_by('-num_times')

    scoresheets_science = scoresheets.filter(metro_science=True) \
                                      .values('player__first_name') \
                                      .annotate(num_times=Count('pk')) \
                                      .order_by('-num_times')

    scoresheets_politics = scoresheets.filter(metro_politics=True) \
                                      .values('player__first_name') \
                                      .annotate(num_times=Count('pk')) \
                                      .order_by('-num_times')

    scoresheets_trade = scoresheets.filter(metro_trade=True) \
                                      .values('player__first_name') \
                                      .annotate(num_times=Count('pk')) \
                                      .order_by('-num_times')

    most_vpcards = scoresheets.values('player__first_name') \
                              .annotate(num_times=Sum('num_vpcards')) \
                              .order_by('-num_times')

    most_chits = scoresheets.values('player__first_name') \
                            .annotate(num_times=Sum('num_chits')) \
                            .order_by('-num_times')

    template = 'pages/statistics.html'
    context = {
        "games_played_year": games_played_year,
        "games_played_this_month": games_played_this_month,
        "games_played_last_month": games_played_last_month,
        "game_durations": game_durations,

        "last_win": last_win,
        "current_win_streak": current_win_streak,
        "most_wins_year": most_wins_year,
        "most_wins_last_year": most_wins_last_year,

        "most_wins_start_position": most_wins_start_position,

        "editions_played": editions_played,
        "day_of_week": day_of_week,

        "scoresheets_most_settlements": scoresheets_most_settlements,
        "scoresheets_most_cities": scoresheets_most_cities,
        "scoresheets_most_metropolises": scoresheets_most_metropolises,

        "scoresheets_points": scoresheets_points,
        "scoresheets_longest_road": scoresheets_longest_road,
        "scoresheets_largest_army": scoresheets_largest_army,
        "scoresheets_merchant": scoresheets_merchant,
        "scoresheets_harbormaster": scoresheets_harbormaster,

        "scoresheets_science": scoresheets_science,
        "scoresheets_politics": scoresheets_politics,
        "scoresheets_trade": scoresheets_trade,

        "most_vpcards": most_vpcards,
        "most_chits": most_chits,

        "statistics_active": "active"
    }
    return render(request, template, context)


def comparisons_page(request):
    today = timezone.now()
    today_last_year = timezone.now()-timedelta(days=365)

    games_played = Game.objects.filter(is_active=True)
    games_played_this_year = games_played.filter(date_start__year=today.year).count()
    games_played_last_year = games_played.filter(date_start__year=today_last_year.year).count()
    
    games_played_last_year_to_date = games_played.filter(date_start__year=today_last_year.year, date_start__lte=today_last_year).count()

    games_played_to_date_diff = games_played_this_year - games_played_last_year_to_date
    games_played_to_date_diff_per = (games_played_to_date_diff / games_played_last_year_to_date) * 100

    wins_this_year = games_played.filter(date_start__year=today.year) \
                                 .values('winning_scoresheet__player__first_name') \
                                 .annotate(num_wins=Count('pk')) \
                                 .order_by('-num_wins')

    wins_last_year = games_played.filter(date_start__year=today_last_year.year) \
                                      .values('winning_scoresheet__player__first_name') \
                                      .annotate(num_wins=Count('pk')) \
                                      .order_by('-num_wins')

    wins_last_year_to_date = games_played.filter(date_start__year=today_last_year.year, date_start__lte=today_last_year) \
                                      .values('winning_scoresheet__player__first_name') \
                                      .annotate(num_wins=Count('pk')) \
                                      .order_by('-num_wins')

    wins_last_year_dict = {winner['winning_scoresheet__player__first_name']:[winner['num_wins']] for winner in wins_last_year}
    wins_last_year_to_date_dict = {winner['winning_scoresheet__player__first_name']:winner['num_wins'] for winner in wins_last_year_to_date}
    wins_this_year_dict = {winner['winning_scoresheet__player__first_name']:winner['num_wins'] for winner in wins_this_year}

    for key, value in wins_last_year_dict.items():
        wins_last_year_dict[key].append(wins_this_year_dict.get(key, 0))
        wins_last_year_dict[key].append(wins_last_year_to_date_dict.get(key, 0))

        diff_per = wins_this_year_dict.get(key, 0) * 100 if wins_last_year_to_date_dict.get(key, 0) == 0 else ((wins_this_year_dict.get(key, 0) - wins_last_year_to_date_dict.get(key, 0)) / wins_last_year_to_date_dict.get(key, 0)) * 100
        wins_last_year_dict[key].append(diff_per)


    template = 'pages/comparisons.html'
    context = {
        "games_played_this_year": games_played_this_year,
        "games_played_last_year": games_played_last_year,
        "games_played_last_year_to_date": games_played_last_year_to_date,
        "games_played_to_date_diff_per": games_played_to_date_diff_per,

        "wins_last_year_dict": wins_last_year_dict,

        "comparisons_active": "active"
    }
    return render(request, template, context)


def location_page(request):
    active_locations = Location.objects.filter(is_active=True)

    template = 'pages/locations.html'
    context = {"location_list": active_locations, "locations_active": "active"}
    return render(request, template, context)


def edition_list(request):
    active_editions = Edition.objects.filter(is_active=True) \
                                     .order_by(Lower('game_type').asc(), Length('name').asc())

    template = 'lists/editions.html'
    context = {"edition_list": active_editions, "editions_active": "active"}
    return render(request, template, context)


def player_list(request):
    today = date.today()
    active_players = Player.objects.filter(is_active=True)
    scoresheets = Scoresheet.objects.filter(is_active=True) \
                                    .filter(game__date_start__year=today.year) \
                                    .values('player__first_name') \
                                    .annotate(total_points=Sum('total_points')) \
                                    .order_by('player')
    games = Game.objects.filter(is_active=True) \
                        .filter(date_start__year=today.year) \
                        .values('winning_scoresheet__player__first_name') \
                        .annotate(wins=Count('pk')) \
                        .order_by('winning_scoresheet__player')

    template = 'lists/players.html'
    context = {
        "player_list": active_players,
        "scoresheets": scoresheets,
        "games": games,
        "players_active": "active"
    }
    return render(request, template, context)


def player_profile_page(request, player):
    player = get_object_or_404(Player, pk=player)

    scoresheets = Scoresheet.objects.filter(is_active=True) \
                                    .filter(player=player.pk) \
                                    .order_by('-game__date_start')

    statistics = scoresheets.aggregate(
        highest_score=Max('total_points'),
        lowest_score=Min('total_points'),
        average_score=Avg('total_points'),
        lifetime_points=Sum('total_points')
    )

    last_five = scoresheets[:10]

    class Round(Func):
        function = "ROUND"
        template = "%(function)s(%(expressions)s::numeric, 0)"

    avg_points_by_edition = scoresheets.values('game__edition__name') \
                                       .order_by('game__edition__game_type', 'game__edition__name') \
                                       .annotate(avg=Round(Avg('total_points')))

    other_scoresheets = Scoresheet.objects.filter(is_active=True).exclude(player=player.pk)
    other_avg_points_by_edition = other_scoresheets.values('game__edition__name') \
                                       .order_by('game__edition__game_type', 'game__edition__name') \
                                       .annotate(avg=Round(Avg('total_points')))

    editions = Edition.objects.filter(is_active=True).values('name').order_by(Lower('game_type').asc(), Length('game_type').asc())

    # edition_list = [e['name'] for e in editions] # this produces a list of all editions, which won't work for highcharts
    edition_list = [e['game__edition__name'] for e in avg_points_by_edition]

    my_edition_avg_list = [[edition_list.index(e['game__edition__name']), e['avg']] for e in avg_points_by_edition]

    other_edition_avg_list = [[edition_list.index(e['game__edition__name']), e['avg']] for e in other_avg_points_by_edition]

    # Save for later - this might be able to get "favorite color"
    games_by_color = scoresheets.values('color') \
                                   .annotate(mc=Count('color')) \
                                   .order_by('-mc')

    active_games = Game.objects.filter(is_active=True)
    wins_by_color = active_games.filter(winning_scoresheet__player=player.pk) \
                                .values('winning_scoresheet__color') \
                                .annotate(mc=Count('winning_scoresheet__color')) \
                                .order_by('-mc')

    most_common_start_position = scoresheets.values('start_position') \
                                            .annotate(mc=Count('start_position')) \
                                            .order_by('-mc')

    color_names = dict(Scoresheet.PLAYER_COLORS)
    most_common_color = color_names[games_by_color[0]['color']]


    if not wins_by_color:
        most_winning_color = "N/A"
    else:
        most_winning_color = color_names[wins_by_color[0]['winning_scoresheet__color']]

    paginator = Paginator(scoresheets, 6)
    page = request.GET.get('page')
    player_scoresheets = paginator.get_page(page)

    template = 'pages/player_profile.html'
    context = {
        "player": player,
        "scoresheets": player_scoresheets,
        "page_num": player_scoresheets.number,
        "last_five": last_five,
        "statistics": statistics,
        "edition_list": edition_list,
        "my_edition_avg_list": my_edition_avg_list,
        "other_edition_avg_list": other_edition_avg_list,
        "most_common_color": most_common_color,
        "most_winning_color": most_winning_color,
        "most_common_start_position": most_common_start_position,
        "players_active": "active"
    }
    return render(request, template, context)


def game_list(request):
    active_games = Game.objects.filter(is_active=True).order_by('-number')
    paginator = Paginator(active_games, 6)
    page = request.GET.get('page')
    games = paginator.get_page(page)

    template = 'lists/games.html'
    context = {
        "games": games,
        "page_num": games.number,
        "games_active": "active"
    }
    return render(request, template, context)


def scoresheet_list(request, game=None):
    active_scoresheets = Scoresheet.objects.filter(is_active=True)

    if game:
        active_scoresheets = active_scoresheets.filter(game_id=game)

    active_scoresheets = active_scoresheets.order_by('-game__number', '-total_points')

    paginator = Paginator(active_scoresheets, 12)
    page = request.GET.get('page')
    scoresheets = paginator.get_page(page)

    template = 'lists/scoresheets.html'
    context = {
        "scoresheets": scoresheets,
        "page_num": scoresheets.number,
        "scoresheets_active": "active"
    }
    return render(request, template, context)
