# finance-blotter
(WIP) Web app serving as an electronic blotter for trading in finance

## Installation
```bash
pew new BLOTTER_FINANCE
pip3 install Django datetime zipline
```

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

## Under the hood

* [django](https://www.djangoproject.com/)
* [zipline/finance/order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)


### Django
Following the [django tutorial](https://docs.djangoproject.com/en/1.10/intro/tutorial01/)
```bash
pew workon BLOTTER_FINANCE
django-admin startproject blotter_finance
mv blotter_finance app
```

In [admin user](https://docs.djangoproject.com/en/1.10/intro/tutorial02/#creating-an-admin-user): Admin: admin, `!@#$%^&*`

Finished at [Writing your first Django app, part 7](https://docs.djangoproject.com/en/1.10/intro/tutorial07/)


When a model is modified:
```bash
python manage.py makemigrations polls
python manage.py migrate
```

### Zipline
* `pip3 install zipline` currently takes a long time (more than 15 mins on aws ec2)
* [Order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)
* [Blotter](https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/zipline/finance/blotter.py#L123)
  * Line 123 shows usage for `Order`
  * Checks [test_blotter.py](https://github.com/quantopian/zipline/blob/3350227f44dcf36b6fe3c509dcc35fe512965183/tests/test_blotter.py)
  * will require an `AssetFinder` class .. I'll probably need to override this with my own class linking assets from marketflow? (what abuot new assets?)
