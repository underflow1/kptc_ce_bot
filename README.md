# kptc_ce_bot
The bot asks to choose a location and offers to upload a photo, after that it saves the picture and information about who, when and which location was added the photo.
When new user start to interact with bot, it adds user to the database.
# How to run
Clone:
``` bash
git clone git@github.com:underflow1/kptc_ce_bot.git
cd kptc_ce_bot
```
Create virtual environment and install all requirements:
``` bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -r requirements.txt
```
Create necessary folders
``` bash
mkdir temp photos
```
Create `.env` file prepare environment and insert your own values:
``` bash 
cp .env_sample .env
```
Run migrations to setup SQLite database:
``` bash
python manage.py migrate
```
Create superuser to get access to admin panel:
``` bash
python manage.py createsuperuser
```
If you want to open Django admin panel:
``` bash
python manage.py runserver
```
Run bot in polling mode:
``` bash
python manage.py runbot
```
# Interact with bot
If you want to interact with bot you need to add some new locations and allow registered users in Django admin panel