# django-zipline
(WIP)  A Django app that wraps the Zipline library

At the time of this writing (2017-02-16),
I'm focusing on wrapping the blotter object for usage in trading in finance.
The app's structure is similar to the zipline library structure,
so that this library can easily be extended to include more zipline objects along the line.

If there are lingering references to `blotter-finance` in the code or docs,
it's because that's what I named the project at first.

## Features
Version 0.0.1
- add/del order/fill
- zipline as matching engine between orders/fills
- fill can match order before/after it
- side-by-side view, consecutive view

Also check [[CHANGELOG.md]]

## Installation
```bash
pew new DJANGO_ZIPLINE
pip3 install -r requirements.txt # Django datetime zipline
```

Apply patch from https://github.com/quantopian/zipline/pull/1683 if not already merged and usable

```bash
python3 manage.py migrate
python3 manage.py test zipline_app
python3 manage.py createsuperuser
```
Reference
* [creating an admin user](https://docs.djangoproject.com/en/1.10/intro/tutorial02/#creating-an-admin-user)

## Usage
```bash
python3 manage.py runserver 0.0.0.0:8000
```

## Testing
```bash
pew workon DJANGO_ZIPLINE
POLLS_LOG_LEVEL=DEBUG python manage.py test zipline_app
```
where the `POLLS_LOG_LEVEL` env variable is the django log level desired
as documented [here](https://docs.djangoproject.com/en/1.10/topics/logging/#loggers)
(default in `settings.py` is INFO)

If running tests manually, could benefit from
* http://stackoverflow.com/questions/24011428/django-core-exceptions-improperlyconfigured-requested-setting-caches-but-setti#27455703
* http://stackoverflow.com/questions/26276397/django-1-7-upgrade-error-appregistrynotready-apps-arent-loaded-yet#26278999

To access deeper namespace, use
```bash
> python manage.py test zipline_app # will not test anything because I dont use tests.py anymore
> python manage.py test zipline_app.tests # will test everything

> python manage.py test zipline_app.tests.zipline_app.test_asset # will test only asset
> python manage.py test zipline_app.tests.zipline_app.test_zipline_app
> python manage.py test zipline_app.tests.zipline_app.test_matcher
> python manage.py test zipline_app.tests.zipline_app.test_zlmodel
> python manage.py test ...
```
## Under the hood
* [django](https://www.djangoproject.com/)
* [zipline](https://github.com/quantopian/zipline/)
  * [zipline/finance/order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)
* [django-bootstrap3](https://github.com/dyve/django-bootstrap3)

### Django
Following the [django tutorial](https://docs.djangoproject.com/en/1.10/intro/tutorial01/)
```bash
pew workon DJANGO_ZIPLINE
mkdir django-zipline
cd django-zipline
git init
django-admin startproject project
mv project/* .
git add *
```

When a model is modified:
```bash
python manage.py makemigrations zipline_app
python manage.py migrate
```

### Zipline
* `pip3 install zipline` currently takes a long time (more than 15 mins on aws ec2)
* [Order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)
* [Blotter](https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123)
  * Line 123 shows usage for `Order`
  * Checks [test_blotter.py](https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/tests/test_blotter.py)
  * will require an `AssetFinder` class .. I'll probably need to override this with my own class linking assets from marketflow? (what abuot new assets?)
