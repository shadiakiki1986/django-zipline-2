from ...utils import getenv_or_fail
import pymssql

class MfManager:
  def __init__(self, host: str=None, port: str=None, user: str=None, password: str=None):
    self.server   = host     or getenv_or_fail("PYMSSQL_TEST_SERVER")  #or "localhost"
    self.port     = port     or getenv_or_fail("PYMSSQL_TEST_PORT")    #or "6200"
    self.user     = user     or getenv_or_fail("PYMSSQL_TEST_USERNAME")#or "root"
    self.password = password or getenv_or_fail("PYMSSQL_TEST_PASSWORD")# or ""
   
  # get MF names
  # http://pymssql.org/en/stable/pymssql_examples.html
  def _execute(self, query:str):
    conn = pymssql.connect(self.server, self.user, self.password, "Marketflow", port=self.port, as_dict=True, charset="latin1")
    cursor = conn.cursor()
    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res

  def assets(self):
    return self._execute("""
      SELECT -- 21566 had non-utf8 character
        TIT_COD, TIT_NOM
      FROM TITRE
    """)

  def accounts(self):
    return self._execute("""
      SELECT -- top 1000
        CLI_COD, CLI_NOM_PRE
      FROM CLIENT
      where
      CLI_TTU_COD=1 and CLI_CLOSED=0
    """)

