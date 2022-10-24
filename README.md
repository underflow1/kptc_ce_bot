# kptc_ce_bot
Бот запрашивает локацию на выбор и предлагает загрузить фото, после чего сохраняет картинку и информацию о том кто, когда и к какой локации добавлено фото
# How to run
clone and setup bot:
``` bash
git clone git@github.com:underflow1/kptc_ce_bot.git
cd kptc_ce_bot
```
Create virtual environment and install all requirements^
``` bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -r requirements.txt
```
create necessary folders
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
add some new locations and allow new users to interact with bot:
``` bash
add ALLOWED_HOSTS in config/settings.py
```
If you want to open Django admin panel which will be located on http://localhost:8000/tgadmin/:
``` bash
python manage.py runserver
```
Run bot in polling mode:
``` bash
python manage.py runbot
```
