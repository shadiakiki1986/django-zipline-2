# finance-blotter
(WIP) Web app serving as an electronic blotter for trading in finance

TODO version 0.1
- [x] django app from tutorial customized to blotter
- [x] use zipline as matching enging
- [x] integrate zipline into django app
- [x] display average price (in red like filled) in original orders view
- [x] original order details page to show transactions filling order
- [x] add nav header
- [x] change architecture of running matching engine: currently re-run if needed on every request
  - change to adding a class with methods `{add,edit,delete}_{order,fill}` being static
  - this class should use [django signals](https://docs.djangoproject.com/en/1.10/ref/signals/):
    - `connection_created` for an initial load of what is in the database (existing `ZlModel.update`)
    - `post_init` for adding orders/fills/assets
    - `post_save` for editing
    - `post_delete` for deleting
- [x] handle more than just asset A1 (WIP .. currently crashes if two assets added, one order per asset added, and then fill added for 2nd asset)
- [x] matcher: test that fills before an order do not fill it
- [x] alert about extra fills
- [x] add account symbols attached to orders
- [ ] polls view: side-by-side, tabular, select day on top and show orders/fills for one day
  - possibly alert about days with unused fills? (use top right like github alerts?)
- [ ] UX (nav header contrasted with white background)
- [ ] hide matching engine table
- [ ] add "working" flag to original order
  - how about an "email" button? possibly rename `vote` field and button
- [ ] add inline create new order/fill/asset on index page
  - or maybe just open the admin?
- [ ] username/password
- [ ] add broker field
- [ ] sort by "open" first then by date (remember that main view will be for one day)
- [ ] what about GTC orders and cancel on EOD
- [ ] default landing page at `/`: think of github dashboard
- ~~link fills to transactions/orders~~
  - ~~but `fills_as_dict_df` loses the original ID's (check `test_fills_as_dict_df`)~~
  - cancelled because transactions have no reference from zipline to the fills

TODO version 0.2
- [ ] add MF asset name + account name
- [ ] use pusher?
- [ ] broker can edit/delete his/her own fills/orders
- [ ] take frequency up to seconds from minutes (and remove chopSeconds)
  - otherwise constrain the django fields for `pub_date` to be without seconds
  - also default for order `pub_date` to be now (like fill `pub_date`)

## Installation
```bash
pew new BLOTTER_FINANCE
pip3 install Django datetime zipline
```

Apply patch from https://github.com/quantopian/zipline/pull/1683 if not already merged and usable

```bash
pip3 manage.py migrate
pip3 manage.py test polls
pip3 manage.py createsuperuser
```
Reference
* [creating an admin user](https://docs.djangoproject.com/en/1.10/intro/tutorial02/#creating-an-admin-user)

## Usage
```bash
cd app
python3 manage.py runserver 0.0.0.0:8000
```

## Testing
```bash
pew workon BLOTTER_FINANCE
cd app
POLLS_LOG_LEVEL=DEBUG python manage.py test polls
```
where the `POLLS_LOG_LEVEL` env variable is the django log level desired
as documented [here](https://docs.djangoproject.com/en/1.10/topics/logging/#loggers)
(default in `settings.py` is INFO)

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
