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

  def add_arguments(self, parser):
    parser.add_argument('--debug', action='store_true', dest='debug', default=False, help='show higher verbosity')

  def handle(self, *args, **options):
    h1 = logging.StreamHandler(stream=self.stderr)
    logger.addHandler(h1)
    if options['debug']:
      logger.setLevel(logging.DEBUG)

    with MfManager() as mfMan:
      total = mfMan.assetsCount()
      logger.debug("Django import assets: %s"%total)
      counter = 0
      progress = progressbar.ProgressBar(maxval=total).start()
      for assetMf in mfMan.assetsList():
        counter+=1
        if counter % 100 == 0:
          progress.update(counter)
  
        # get/create entity/row/case
        #logger.debug("get or create: %s"%asset['TIT_COD'])
        assetDj = Asset.objects.filter(
          asset_symbol=assetMf['TIT_COD']
        ).first()
        if assetDj is None:
          assetDj = Asset.objects.create(
            asset_symbol=assetMf['TIT_COD'],
            asset_name=assetMf['TIT_NOM'],
            asset_exchange='N/A'
          )
          logger.debug("Created asset: %s"%assetDj)
        else:
          if assetDj.asset_name!=assetMf['TIT_NOM']:
            assetDj.asset_name=assetMf['TIT_NOM']
            assetDj.save()
            logger.debug("Updated asset: %s"%assetDj)

      progress.finish()
  
  
      total = mfMan.accountsCount()
      logger.debug("Django import accounts: %s"%total)
      counter = 0
      progress = progressbar.ProgressBar(maxval=total).start()
      for accountMf in mfMan.accountsList():
        counter+=1
        if counter % 100 == 0:
          progress.update(counter)
  
        # get/create entity/row/case
        accountDj = Account.objects.filter(
          account_symbol=accountMf['CLI_COD']
        ).first()
        if accountDj is None:
          accountDj = Account.objects.create(
            account_symbol=accountMf['CLI_COD'],
            account_name=accountMf['CLI_NOM_PRE'],
          )
          logger.debug("Created account: %s"%accountDj)
        else:
          if accountDj.account_name!=accountMf['CLI_NOM_PRE']:
            accountDj.account_name=accountMf['CLI_NOM_PRE']
            accountDj.save()
            logger.debug("Updated account: %s"%accountDj)

      progress.finish()
