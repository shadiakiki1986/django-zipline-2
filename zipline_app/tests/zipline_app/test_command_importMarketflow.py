from django.test import TestCase
from unittest.mock import patch

# Testing management commands
# https://docs.djangoproject.com/en/1.10/topics/testing/tools/#management-commands
from django.core.management import call_command
from django.utils.six import StringIO

class ImportMarketflowCommandTests(TestCase):
  def setUp(self):
    patcher = patch('zipline_app.management.commands.importMarketflow.MfManager')
    self.addCleanup(patcher.stop)
    mock = patcher.start()
    instance = mock.return_value
    instance.assets.return_value = [
      {'TIT_COD':'asset 1', 'TIT_NOM':'name of asset 1'},
      {'TIT_COD':'asset 2', 'TIT_NOM':'name of asset 2'},
    ]
    instance.accounts.return_value = [
      {'CLI_COD':'account 1', 'CLI_NOM_PRE':'name of account 1'},
      {'CLI_COD':'account 2', 'CLI_NOM_PRE':'name of account 2'},
    ]

  def testMain(self):
    with StringIO() as out, StringIO() as err:
      call_command('importMarketflow', stderr=err, stdout=out, debug=True)
      self.assertIn('Django import', err.getvalue())

