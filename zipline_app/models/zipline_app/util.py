import hashlib

# Create your models here.

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()
