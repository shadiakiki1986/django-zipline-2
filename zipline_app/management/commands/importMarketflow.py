import logging
from ._mfManager import MfManager
from ...models.zipline_app.asset import Asset
from ...models.zipline_app.account import Account

# https://docs.djangoproject.com/en/1.10/howto/custom-management-commands/
from django.core.management.base import BaseCommand

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

    logger.debug("Django import assets")
    for asset in assets:
      # get/create entity/row/case
      asset, created = Asset.objects.get_or_create(
        asset_symbol=asset['TIT_COD'],
        asset_name=asset['TIT_NOM'],
        asset_exchange='N/A'
      )
      if created:
        logger.debug("Creating new asset: %s"%asset)

    logger.debug("Django import accounts")
    for account in accounts:
      # get/create entity/row/case
      account, created = Account.objects.get_or_create(
        account_symbol=account['CLI_COD'],
        #account_name=account['CLI_NOM_PRE'],
      )
      if created:
        logger.debug("Creating new account: %s"%account)
