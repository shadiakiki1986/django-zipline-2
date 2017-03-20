import tempfile
from pandas import DataFrame
from django.http import HttpResponse
from os.path import join

# fileresponse from django.views.static import serve
from django.http import FileResponse

class DownloadBuilder:
  def empty_df(self):
    df = DataFrame({
      'Ref': [],
      'Timestamp':[],
      'placed by':[],
      'given by':[],
      'Client Name':[],
      'Side':[],
      'Order Type':[],
      'Qty':[],
      'Security Name':[],
      'Quote':[],
      'Order nbr':[],
      'Status':[]
    })
    return df

  def orders2df(self,orders):
    df = self.empty_df()
    for order in orders:
      df = df.append({
        'Ref': order.id,
        'Timestamp':order.pub_date,
        'placed by':'-',
        'given by':'-',
        'Client Name':order.account.account_symbol,
        'Side':order.order_side,
        'Order Type':'-',
        'Qty':order.amount_unsigned,
        'Security Name':order.asset.asset_symbol,
        'Quote':order.avgPrice(),
        'Order nbr':'-' if order.dedicated_fill() is None else order.dedicated_fill().tt_order_key,
        'Status':'working' if order.filled()!=order.amount_signed() else 'filled'
      },
      ignore_index=True)
    return df

  # Generate temporary file names without creating actual file in Python
  # http://stackoverflow.com/a/26541521/4126114
  def df2xlsx(self,df):
    temp_name = next(tempfile._get_candidate_names())
    temp_name = "%s.xlsx"%temp_name
    default_tmp_dir = tempfile._get_default_tempdir()
    full_name = join(default_tmp_dir, temp_name)
    df.to_excel(
      full_name,
      sheet_name='blotter', index=False,
      # sort columns
      columns=[
        'Ref',
        'Timestamp',
        'placed by',
        'given by',
        'Client Name',
        'Side',
        'Order Type',
        'Qty',
        'Security Name',
        'Quote',
        'Order nbr',
        'Status'
      ]
    )
    return full_name

  # how to download a filefield file in django view
  # http://stackoverflow.com/a/9463976/4126114
  #
  # Telling the browser to treat the response as a file attachment
  # https://docs.djangoproject.com/en/dev/ref/request-response/#telling-the-browser-to-treat-the-response-as-a-file-attachment
  #
  # django.test.Client and response.content vs. streaming_content
  # http://stackoverflow.com/a/26819693/4126114
  def fn2response(self,full_name):
    response = FileResponse(
      open(full_name, 'rb'),
      content_type='application/vnd.ms-excel'
    )
    response['Content-Disposition'] = 'attachment; filename="%s"'%"blotter.xlsx"
    return response
