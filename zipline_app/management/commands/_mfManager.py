from ...utils import getenv_or_fail
import pymssql

class MfManager:
  def __init__(self, host: str=None, port: str=None, user: str=None, password: str=None, db:str=None):
    self.server   = host     or getenv_or_fail("PYMSSQL_SERVER")  #or "localhost"
    self.port     = port     or getenv_or_fail("PYMSSQL_PORT")    #or "6200"
    self.user     = user     or getenv_or_fail("PYMSSQL_USERNAME")#or "root"
    self.password = password or getenv_or_fail("PYMSSQL_PASSWORD")# or ""
    self.db = db or getenv_or_fail("PYMSSQL_DB")
   
  # get MF names
  # http://pymssql.org/en/stable/pymssql_examples.html
  def __enter__(self):
    self.conn = pymssql.connect(self.server, self.user, self.password, self.db, port=self.port, as_dict=True, charset="latin1")
    return self

  def _execute(self, query:str):
    cursor = self.conn.cursor()
    cursor.execute(query)
    return cursor

  def __exit__(self, exc_type, exc_val, exc):
    self.conn.close()

  def assetsCount(self):
    cursor = self._execute("""
      SELECT
        count(*) as n
      FROM TITRE
    """)
    res = cursor.fetchall()
    return res[0]['n']

  def assetsList(self):
    return self._execute("""
      SELECT
        TIT_COD, TIT_NOM
      FROM TITRE
    """)

  def accountsCount(self):
    cursor = self._execute("""
      SELECT
        count(*) as n
      FROM CLIENT
      where
      CLI_TTU_COD=1 and CLI_CLOSED=0
    """)
    res = cursor.fetchall()
    return res[0]['n']

  def accountsList(self):
    return self._execute("""
      SELECT
        CLI_COD, CLI_NOM_PRE
      FROM CLIENT
      where
      CLI_TTU_COD=1 and CLI_CLOSED=0
    """)

