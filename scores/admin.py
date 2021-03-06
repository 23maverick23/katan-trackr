from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.forms.models import BaseInlineFormSet
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

# Register your models here.
from .models import Player, Location, Edition, Game, Scoresheet

class BaseAdmin(admin.ModelAdmin):
    pass


class PlayerCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Player
        fields = ('email', )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        player = super(PlayerCreationForm, self).save(commit=False)
        player.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return player


class PlayerChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(
                help_text=("Raw passwords are not stored, so there is no way to see "
                "this user's password, but you can change the password "
                "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = Player
        fields = ('email', 'password', 'is_active')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class PlayerAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = PlayerChangeForm
    add_form = PlayerCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('first_name', 'last_name', 'email', 'is_active')
    list_display_links = ('first_name', 'last_name', 'email')
    list_filter = ('is_active', )
    fieldsets = (
        (None, {'fields': (('first_name', 'last_name'), ('email', 'password'), )}),
        ('Permissions', {'fields': ('is_active', )}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
            }
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

# Now register the new UserAdmin...
admin.site.register(Player, PlayerAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


@admin.register(Location)
class LocationAdmin(BaseAdmin):
    fields = ('name', ('latitude', 'longitude'))
    list_display = ('name', )
    exclude = ('is_active', )


@admin.register(Edition)
class EditionAdmin(BaseAdmin):
    fields = (('name', 'game_type', 'image_tag', 'rules_url', 'skills'), ('description'),
              ('max_players', 'duration', 'points'))
    list_display = ('name', 'game_type', 'image_tag', 'max_players', 'duration', 'points', 'times_played')
    exclude = ('is_active', )

    def times_played(self, obj):
        return obj.games_played()
    times_played.short_description = '# of games played'


class ScoresheetInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        # Provide initial data to the inline form for starting position
        kwargs.update({'initial': [
            { 'start_position': 1, }, {'start_position': 2, }, {'start_position': 3, }, {'start_position': 4, }
        ]})
        super(ScoresheetInlineFormSet, self).__init__(*args, **kwargs)


class ScoresheetInline(admin.TabularInline):
    model = Scoresheet
    max_num = 4
    extra = 4
    exclude = ('is_active', )
    formset = ScoresheetInlineFormSet


@admin.register(Scoresheet)
class ScoresheetAdmin(BaseAdmin):
    fieldsets = (
        (None, {
            'fields': (('game', 'player', 'color', 'start_position'), )
        }),
        ('Base Game', {
            'fields': ('total_points',
                       ('num_settlements', 'num_cities', 'num_vpcards', ),
                       ('longest_road', 'largest_army', ),
                      )
        }),
        ('Seafarers', {
            'fields': ('num_chits', ),
        }),
        ('Cities & Knights', {
            'fields': (
                       ('metro_science', 'metro_politics', 'metro_trade', 'merchant', ),
                      )
        }),
        ('Traders & Barbarians', {
            'fields': ('harbormaster', ),
        }),
    )
    list_display = ('game', 'edition_playd', 'player', 'color', 'total_points')
    exclude = ('is_active', )

    def edition_playd(self, obj):
        game = get_object_or_404(Game, pk=obj.game.pk)
        return game.edition.name
    edition_playd.short_description = 'game edition'


class CustomGameModelForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ('date_start', 'date_finish', 'edition', 'location', 'winning_scoresheet')

    def __init__(self, *args, **kwargs):
        super(CustomGameModelForm, self).__init__(*args, **kwargs)
        self.fields['winning_scoresheet'].queryset = Scoresheet.objects.filter(game_id=self.instance.id)


@admin.register(Game)
class GameAdmin(BaseAdmin):
    form = CustomGameModelForm
    fields = (('date_start', 'date_finish'), ('edition', 'location'), 'winning_scoresheet')
    list_display = ('get_formatted_number', 'game_nickname', 'date_start', 'duration', 'edition', 'location', 'winning_scoresheet')
    exclude = ('is_active', )
    inlines = (ScoresheetInline, )

    def game_nickname(self, obj):
        return obj.get_display_name()
    game_nickname.short_description = 'game nickname'
