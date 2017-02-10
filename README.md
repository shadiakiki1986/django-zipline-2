# finance-blotter
Web app serving as an electronic blotter for trading in finance

ATM, this is WIP

## Usage
```bash
cd app
python3 manage.py runserver 0.0.0.0:8000
```

## Testing
```bash
pew workon BLOTTER_FINANCE
cd app
python manage.py test polls
```

If running tests manually, could benefit from
* http://stackoverflow.com/questions/24011428/django-core-exceptions-improperlyconfigured-requested-setting-caches-but-setti#27455703
* http://stackoverflow.com/questions/26276397/django-1-7-upgrade-error-appregistrynotready-apps-arent-loaded-yet#26278999

#Under the hood

* [django](https://www.djangoproject.com/)
* [zipline/finance/order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)

Following the [django tutorial](https://docs.djangoproject.com/en/1.10/intro/tutorial01/)
```bash
pew new FINANCE_BLOTTER
pip3 install Django datetime
django-admin startproject blotter_finance
mv blotter_finance app
cd app
python3 manage.py runserver 0.0.0.0:8000
...
```

In [admin user](https://docs.djangoproject.com/en/1.10/intro/tutorial02/#creating-an-admin-user): Admin: admin, `!@#$%^&*`

arrived at [Writing your first Django app, part 7](https://docs.djangoproject.com/en/1.10/intro/tutorial07/)
