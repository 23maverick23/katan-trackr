from django.db import models
from django.db.models.functions import Lower, Length


class OrderedEditionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by(Lower('game_type'), Length('game_type'))
