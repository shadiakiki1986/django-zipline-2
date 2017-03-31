from django.test import TestCase
from .test_zipline_app import create_account, create_asset, create_order, a1, create_fill
from django.urls import reverse
from ...models.zipline_app.fill import Fill
from ...models.zipline_app.zipline_app import ZlModel
from ...models.zipline_app.side import BUY, SELL
from .test_fill import create_fill_from_order
from io import BytesIO
import pandas as pd
from ...utils import myTestLogin

class BlotterDownloadViewsTests(TestCase):
  def setUp(self):
    ZlModel.clear()
    self.acc = create_account("test acc")
    self.ass = create_asset(a1["symbol"],a1["exchange"],a1["name"])
    myTestLogin(self.client)

  def test_get(self):
    o1 = create_order(order_text="random order 1", days=-1,  asset=self.ass, order_side=BUY, amount_unsigned=10,   account=self.acc)
    o2 = create_order(order_text="random order 2", days=-2,  asset=self.ass, order_side=BUY, amount_unsigned=20,   account=self.acc)
    o3 = create_order(order_text="random order 3", days=-3,  asset=self.ass, order_side=BUY, amount_unsigned=30,   account=self.acc)
    f3 = create_fill_from_order(order=o3, fill_price=3, fill_text="fill 3")

    # django test file download
    # http://stackoverflow.com/a/39655502/4126114
    url = reverse('zipline_app:blotter-download')
    response = self.client.get(url, follow=True)
    content = BytesIO(b"".join(response.streaming_content))

    # How to read a .xlsx file using the pandas Library in iPython
    # http://stackoverflow.com/questions/16888888/ddg#16896091
    xl_file = pd.ExcelFile(content)
    dfs = {sheet_name: xl_file.parse(sheet_name) 
              for sheet_name in xl_file.sheet_names}

    # my tests
    self.assertTrue('blotter' in dfs)
    self.assertEqual(len(dfs['blotter']),3)

    self.assertEqual(dfs['blotter']['Status'].tolist(), ['working', 'working', 'filled'])

    # check in order
    df = dfs['blotter']
    self.assertEqual(df[df['Ref']==1]['Status'].tolist()[0], 'working')
    self.assertEqual(df[df['Ref']==2]['Status'].tolist()[0], 'working')
    self.assertEqual(df[df['Ref']==3]['Status'].tolist()[0], 'filled')
