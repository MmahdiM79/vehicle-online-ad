python3 Django-project/manage.py runserver &
cd Django-project/
python3 -m celery -A vehicle_ads worker -l info --pool=solo
