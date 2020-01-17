![Katan Trackr - Let's Settle This](https://raw.githubusercontent.com/23maverick23/katan-trackr/master/scores/static/scores/images/logo_large.png)

A Django web app for tracking Settlers of Catan game play.

## Development

To run `heroku local web` with more of a _watch_ aspect, you can use `nodemon` and the command below. This will allow you to make changes to the source while reloading the heroku app locally. This is aliased as `heroku_local` to make it easier to remember.

```bash
nodemon --exec "heroku local web" --signal SIGTERM
```

The following aliases are also available to make them easier to remember while in the shell.

```bash
# dj_serve
python manage.py runserver

# dj_make
python manage.py makemigrations

# dj_migrate
python manage.py migrate

# dj_shell
python manage.py shell

# dj_dbshell
python manage.py dbshell

```

If possible, remember to mirror `.env` and `.envrc` for use locally and within heroku.
