# finance-blotter
Web app serving as an electronic blotter for trading in finance

ATM, this is WIP

#Under the hood

* [django](https://www.djangoproject.com/)
* [zipline/finance/order](https://github.com/quantopian/zipline/blob/master/zipline/finance/order.py)

Following the [django tutorial](https://docs.djangoproject.com/en/1.10/intro/tutorial01/)
```bash
pew new FINANCE_BLOTTER -r requirements.txt
django-admin startproject blotter_finance
mv blotter_finance app
```
