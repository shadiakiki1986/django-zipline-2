## Changelog
_Unticked are still TODO_

## [ ] Version 0.1.1
- [ ] move the matching engine to use redis backend
  - something like what is described [here](https://channels.readthedocs.io/en/stable/getting-started.html#running-with-channels)
- [ ] sort by "open" first then by date (remember that main view will be for one day)
- [ ] how about an "email" order button? possibly rename `vote` field and button
- [ ] email notification on order/fill
- [ ] select day on top and show orders/fills for one day
- [ ] alert about eariler days with open orders or unused fills
    - use top right like github alerts?
    - or show side bar like travis?
    - or `django.contrib.messages`?
- [ ] add MF asset name + account name
- [ ] use pusher?
- [ ] broker can edit/delete his/her own fills/orders
- [ ] take frequency up to seconds from minutes (and remove chopSeconds)
  - otherwise constrain the django fields for `pub_date` to be without seconds
  - also default for order `pub_date` to be now (like fill `pub_date`)
- [ ] could also add [django-review](https://github.com/bitlabstudio/django-review)
- [ ] place an order "draft" to allow placing multiple orders and then single-button "publish drafted"
  - allow a user to edit/delete an order only when still a draft
  - same for fills?
  - how are cancels related?
- [ ] unused fills, if closed with correction fills, no longer show up anywhere (as slippage?)
  - or probably should compute slippage from asset''s close?
  - this would require close data (linked from the asset symbol)
  - the symbol would need to be a valid "yahoo finance", "google finance", "blooomberg", "marketflow" symbol
- [ ] delete should be open only to an admin user
  - [ ] add undo for accidental deletes (or display history somewhere)
    - do I still need this if it is only open to an admin user?
    - there will be a "cancel order" button for regular users (which can be followed by a delete)
- [ ] make asset exchange foreign key and display alert if ordering/filling during exchange closed time

## [ ] Version 0.1.0
- [ ] release


## [ ] Version 0.0.3
- [ ] link fills to transactions/orders
  - but `fills_as_dict_df` loses the original IDs (check `test_fills_as_dict_df`)
  - but transactions have no reference from zipline to the fills
  - can it be done by using the asset/timestamp pair as key?
- [ ] username/password
  - single sign-on? (use ldap?)
- [ ] add broker field
- [ ] what about GTC orders and cancel on EOD
- [ ] default landing page at `/`
  - think of github dashboard
  - redirect to log in if not logged in
  - how to manage authentication / authorization
- [ ] how to move to async? Decide between
  - probably no need as of now since the matching engine needs to be re-run completely anyway
  - [django-angular](http://django-angular.readthedocs.io/en/latest/angular-model-form.html)
  - [django-channels](https://channels.readthedocs.io/en/stable/concepts.html)
- [ ] rename my `order_text` and `fill_text` to `...comment`
- [ ] what happens if i delete an account which is referenced in an order
  - [ ] same for asset
- [ ] index in-page create buttons: add way to close them without reloading
- [ ] during loading of page after asset create, block page (display "loading...")
  - might also want to automatically re-open modals if for example the new-fill modal was opened followed by the new-asset modal
- [ ] favicon.ico
- [ ] use order vote as order close
- [ ] fill from index required fills per asset
- [ ] bug: fill that gets its timestamp changed to the same as another fill, then changed back out of that timestamp, disappears from the combined view
- [ ] combine OrderCreate and OrderForm classes? (same for FillCreate/FillForm and others)
- [ ] order list, fills list: order by desc `pub_date`
- [ ] if fill entered before/after order, make it easy to re-attach to order timestamp
- [ ] add "order status" flag: working, closed, ...
  - or should this be implied from the data? (with the default always being "working")
- [ ] inline alert of unmatched fills in side-by-side view has a popup that could display the number of unused fills
  - would this replace the separate section?
- [ ] how to handle the index table when data becomes too much
  - how to truncate the data (do not show past orders that were filled, or past fills that completed an order)
  - keep showing open orders or unused fills
  - etc
- [ ] drop redundant load of css/js from html templates, except base.html
  ```
  {# Load CSS and JavaScript #}
  {% bootstrap_css %}
  {% bootstrap_javascript %}
  ```
- [w] travis-ci.org


## [x] Version 0.0.2
- [x] no need to update zlmodel upon asset changes
- [x] nav bar active page should be changed with jquery upon page load
- [x] UX
  - [x] rename "symbol" on index to "asset" (show name using tooltip?)
  - create in index
    - [x] in-page create account: send django message upon create
    - [x] replace all inline creates with divs that show up when clicking on add new order/fill
      - [x] not to be "bootstrap modal" because user needs to keep sight of orders/fills (same reason why not just going to a new page completely)
      - [x] use same concept as one-line create, but make the form take the whole page width (instead of displaying the order form on the left and the fill form on the right)
      - [x] quantity input too small
      - [x] asset add button unintuitive
      - [x] symbol dropdown is too small
      - [x] send django message when asset/account/order/fill created from index
        - [x] ~~how do multiple django messages sent in one request get displayed?~~
          - I dont have this case ATM
        - [x] also when order/fill deleted
          - assets/accounts to be dealt with separately since they''re not in direct display on the index page (possibly think of a "clean up" button)

- [x] ~~bug: create order at t1, then create at `t2>t1`, then drop the one at t1, but the minute t1 is still there in combined view~~
  - I couldnt reproduce this bug anymore .. so cancelling
- [x] ~~test failing for in-page create account~~
  - doesnt seem to fail anymore
- [x] fill quantity too large yields error: Python int too large to convert to SQLite INTEGER
- [x] more index
  - [x] edit in details
    - this is related to drafting (in version 0.1.1) .. so not sure if should postpone
  - [x] delete buttons are ugly and overlap with timestamp
  - [x] ~~add column explicitly calculated for pending quantities~~
    - display a summary of pending quantities per asset
- [x] bug: when unused fills are negative, they dont show up
- [x] fill price cannot be negative (zipline constraint)
- [x] bug: create fill with qty 0 yields error
- [x] time zones!
  - times not displayed in beirut timezone
  - ~~omitting timezones would yield django error about timezone-naive timestamp uncomparable to timezone-aware timestamp~~
- [x] add section "XX fills required to close open orders"
- [x] replace heart with github logo/link


## [x] Version 0.0.1
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
- [x] add account symbols attached to orders
- [x] UX with [django-bootstrap3](https://github.com/dyve/django-bootstrap3)
  - [x] nav header contrasted with white background
  - [x] side-by-side view: asset, order, fill
  - [x] tabular for printing
- [x] rename project to django-zipline
- [x] move files to match structure of zipline
- [x] new asset: works with generic view form and bootstrap form (was submitting form with jquery but violating csrf)
- [x] ~~add an intermediate "bar data" model between fills and ZlModel to reduce computations~~
  - cancelled since the weighted average close would still require re-computation
- [x] aggregate fills per asset by minute in chopSeconds
- [x] index page
  - [x] order create in page and redirect back to index
  - [x] fill  create in page and redirect back to index
  - [x] asset create in page and redirect back to index
  - [x] delete in page and redirect back to index
  - [x] ~~edit inline~~ link to details in order to edit
- [x] new asset form should check that symbol is not already defined
  - this is a zipline constraint
  - ~~or maybe just open the admin?~~
- [x] bug: if no open orders on A1 and new fill on A1, not getting alerted about unused fill
