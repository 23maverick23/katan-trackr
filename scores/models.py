import uuid
from datetime import time, timedelta

from django.db import models
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

from .managers import OrderedEditionManager

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class Player(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ('first_name', )
        verbose_name = 'player'
        verbose_name_plural = 'players'

    def __str__(self):
        return self.get_short_name()

    def get_full_name(self):
        full_name = '{} {}'.format(self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        if not self.first_name or not self.last_name:
            return self.email.split('@')[0]

        short_name = '{} {}'.format(self.first_name, self.last_name[0])
        return short_name.strip()

    def num_games_played(self):
        num_games = Scoresheet.objects.filter(is_active=True, player=self.pk).count()
        return num_games

    def num_games_won(self):
        num_games = Game.objects.filter(is_active=True, winning_scoresheet__player=self.pk).count()
        return num_games

    def num_games_lost(self):
        return self.num_games_played() - self.num_games_won()

    def win_loss_per(self):
        per = 0
        if self.num_games_played() > 0:
            per = (self.num_games_won() / self.num_games_played()) * 100
        return "{0:.0f}%".format(per)

    def last_played(self):
        return Scoresheet.objects.filter(is_active=True).order_by('-game__date_start')[0].game.date_start

    def duration_played(self):
        sum_duration = Scoresheet.objects.filter(is_active=True, player=self.pk).aggregate(sum=Sum('game__duration'))
        return sum_duration



class Location(BaseModel):
    name = models.CharField("location's nickname", max_length=30, blank=False, null=False)
    latitude = models.CharField(max_length=15, blank=True)
    longitude = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ('name', )

    def __str__(self):
        return self.name

    def lon_lat(self):
        lat_lon_str = '{}, {}'.format(self.longitude, self.latitude)
        return lat_lon_str.strip()

    def games_played(self):
        num_games = Game.objects.filter(is_active=True, location=self.pk).count()
        return num_games

    def duration_played(self):
        sum_duration = Game.objects.filter(is_active=True, location=self.pk).aggregate(sum=Sum('duration'))
        return sum_duration


class Edition(BaseModel):
    TWO = '24'
    FOUR = '34'
    SIX = '56'
    EDITION_PLAYERS = [
        (TWO, '2-4'),
        (FOUR, '3-4'),
        (SIX, '5-6')
    ]
    BASE = 'B'
    EXPANSION = 'E'
    COMBO = 'M'
    EDITION_TYPE = [
        (BASE, 'Base Game'),
        (EXPANSION, 'Expansion'),
        (COMBO, 'Expansion Combination')
    ]
    name = models.CharField("edition's nickname", max_length=75, blank=False, null=False)
    description = models.TextField("description", blank=False, null=False)
    game_type = models.CharField("edition type", max_length=1, choices=EDITION_TYPE, default=BASE,
                                 blank=False, null=False)
    max_players = models.CharField("max player count", max_length=3, choices=EDITION_PLAYERS,
                                   default=FOUR, blank=False, null=False)
    duration = models.CharField("duration", max_length=30, blank=False, null=False)
    points = models.IntegerField("VPs to win", blank=False, null=False)
    image_tag = models.CharField("image tag", max_length=30, blank=True, null=True)
    skills = models.TextField("skills", blank=True, null=True)
    rules_url = models.URLField("rules url", blank=True, null=True)

    class Meta:
        ordering = ('game_type', )

    objects = models.Manager()
    ordered_objects = OrderedEditionManager()

    def __str__(self):
        return "{} ({})".format(self.name, self.get_game_type_display())

    def short_description(self):
        return "{} players, {}, {} VPs to win".format(self.get_max_players_display(),
                                                      self.duration, self.points)

    def games_played(self):
        num_games = Game.objects.filter(is_active=True, edition=self.pk).count()
        return num_games

    def duration_played(self):
        sum_duration = Game.objects.filter(is_active=True, edition=self.pk).aggregate(sum=Sum('duration'))
        return sum_duration


class Game(BaseModel):
    number = models.IntegerField(default=1, editable=False, blank=False, null=False)
    date_start = models.DateTimeField('Date', default=timezone.now, blank=False, null=False)
    date_finish = models.DateTimeField('Finished', default=timezone.now, blank=False, null=False)
    duration = models.DurationField('Duration', default=timedelta, editable=False, blank=False, null=False)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, blank=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=False)
    # TODO: Look into the limit_choices_to filter the values to only "available" scorecards
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.limit_choices_to
    winning_scoresheet = models.ForeignKey('Scoresheet', on_delete=models.CASCADE,
                                           blank=True, null=True,
                                           verbose_name="Winning scoresheet",
                                           related_name="winning_scoresheet")

    class Meta:
        ordering = ('-number', )

    def save(self, *args, **kwargs):
        # This means that the model isn't saved to the database yet
        if self._state.adding:
            # Get the maximum display_id value from the database
            last_num = Game.objects.all().aggregate(largest=models.Max('number'))['largest']

            # aggregate can return None! Check it first.
            # If it isn't none, just use the last ID specified (which should be the greatest) and add one to it
            if last_num is not None:
                self.number = last_num + 1

        self.duration = self.date_finish - self.date_start

        super(Game, self).save(*args, **kwargs)

    def get_formatted_number(self):
        return "{0:0=3d}".format(self.number)
    get_formatted_number.short_description = 'game number'

    def get_time_of_day(self):
        hour = self.date_start.hour
        return (
            "morning" if 5 <= hour <= 11
            else
            "afternoon" if 12 <= hour <= 17
            else
            "evening" if 18 <= hour <= 22
            else
            "night"
        )

    def get_display_name(self):
        tz_date_start = timezone.localtime(self.date_start)
        game_str = "{} {}".format(
            tz_date_start.strftime('%A'), self.get_time_of_day().capitalize()
        )
        return game_str

    def __str__(self):
        return self.get_display_name()

    def get_duration(self):
        # tdelta = self.date_finish - self.date_start
        return self.duration

    def get_scoresheets_count(self):
        return Scoresheet.objects.filter(is_active=True).filter(game_id=self.pk).count()


class Scoresheet(BaseModel):
    RED = 'RD'
    BLUE = 'BL'
    WHITE = 'WH'
    ORANGE = 'OR'
    GREEN = 'GR'
    BROWN = 'BR'
    PINK = 'PK'
    YELLOW = 'YL'
    PLAYER_COLORS = [
        (RED, 'Red'),
        (BLUE, 'Blue'),
        (WHITE, 'White'),
        (ORANGE, 'Orange'),
        (GREEN, 'Green'),
        (BROWN, 'Brown'),
        (PINK, 'Pink'),
        (YELLOW, 'Yellow')
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, blank=False)
    # TODO: Look into the limit_choices_to filter the values to only "available" players
    # https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.limit_choices_to
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False)
    color = models.CharField("player's color", max_length=2, choices=PLAYER_COLORS, default=RED, blank=False)
    start_position = models.IntegerField("initial placement position", default=1, blank=True)
    total_points = models.IntegerField("total victory points", default=0, blank=True)
    num_settlements = models.IntegerField("number of settlements", default=0, blank=True)
    num_cities = models.IntegerField("number of cities", default=0, blank=True)
    num_vpcards = models.IntegerField("VPs from cards", default=0, blank=True)
    num_chits = models.IntegerField("number of chits", default=0, blank=True)
    longest_road = models.BooleanField("longest road card", default=False, blank=False)
    largest_army = models.BooleanField("largest army card", default=False, blank=False)
    metro_science = models.BooleanField("science metropolis", default=False, blank=False)
    metro_politics = models.BooleanField("politics metropolis", default=False, blank=False)
    metro_trade = models.BooleanField("trade metropolis", default=False, blank=False)
    merchant = models.BooleanField("merchant VP", default=False, blank=False)
    harbormaster = models.BooleanField("harbormaster VP", default=False, blank=False)


    class Meta:
        ordering = ('-total_points', )

    def get_display_name(self):
        score_str = "{} ({} VPs)".format(self.player.get_full_name(), self.total_points)
        return score_str

    def __str__(self):
        return self.get_display_name()
