import logging
from ._mfManager import MfManager
from ...models.zipline_app.asset import Asset
from ...models.zipline_app.account import Account

# https://docs.djangoproject.com/en/1.10/howto/custom-management-commands/
from django.core.management.base import BaseCommand

import progressbar

logger = logging.getLogger('FFA Dubai blotter')

class Command(BaseCommand):
  help = """Usage:
         python manage.py importMarketflow --help
         python manage.py importMarketflow --debug
         """

  def __init__(self, *args, **kwargs):
    super(Command, self).__init__(*args, **kwargs)
    self.mfMan = MfManager()

  def add_arguments(self, parser):
    parser.add_argument('--debug', action='store_true', dest='debug', default=False, help='show higher verbosity')

  def handle(self, *args, **options):
    h1 = logging.StreamHandler(stream=self.stderr)
    logger.addHandler(h1)
    if options['debug']:
      logger.setLevel(logging.DEBUG)

    logger.debug("MF assets .. get")
    assets = self.mfMan.assets()
    logger.debug("MF accounts .. get")
    accounts = self.mfMan.accounts()

    total = len(assets)
    logger.debug("Django import assets: %s"%total)
    counter = 0
    progress = progressbar.ProgressBar(maxval=total).start()
    for asset in assets:
      counter+=1
      if counter % 100 == 0:
        progress.update(counter)

      # get/create entity/row/case
      #logger.debug("get or create: %s"%asset['TIT_COD'])
      asset, created = Asset.objects.get_or_create(
        asset_symbol=asset['TIT_COD'],
        asset_name=asset['TIT_NOM'],
        asset_exchange='N/A'
      )
      if created:
        logger.debug("Creating new asset: %s"%asset)
    progress.finish()


    total = len(accounts)
    logger.debug("Django import accounts: %s"%len(accounts))
    counter = 0
    progress = progressbar.ProgressBar(maxval=total).start()
    for account in accounts:
      counter+=1
      if counter % 100 == 0:
        progress.update(counter)

      # get/create entity/row/case
      account, created = Account.objects.get_or_create(
        account_symbol=account['CLI_COD'],
        #account_name=account['CLI_NOM_PRE'],
      )
      if created:
        logger.debug("Creating new account: %s"%account)
    progress.finish()
