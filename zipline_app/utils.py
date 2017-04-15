import hashlib
from django.urls import  reverse_lazy
from os import getenv

def md5_wrap(string):
  return hashlib.md5(string.encode('utf-8')).hexdigest()

def redirect_index_or_local(myself,local):
  source = myself.request.POST.get('source')
  if source is not None and source!='':
    return reverse_lazy('zipline_app:%s'%source)
  if type(local) is str:
    return reverse_lazy(local)
  return local

import datetime
from django.utils import timezone
from django.contrib.auth.models import User

def now_minute():
  ts=timezone.now()
  ts = chopSeconds(ts)
  return ts

def chopSeconds(ts:datetime):
  #ts -= datetime.timedelta(seconds=ts.second, microseconds=ts.microsecond)
  #return ts
  return ts.replace(second=0, microsecond=0)

def myTestLogin(client):
  password = 'glass onion'
  user = User.objects.create_user(username='john', email='jlennon@beatles.com', password=password)
  response = client.login(username=user.username, password=password, follow=True)
  return user

def getenv_or_fail(envName: str):
  value = getenv(envName)
  if value is None:
    raise Exception("Environment variable undefined: '%s'" % envName)
  return value

# render template to email body
# https://godjango.com/19-using-templates-for-sending-emails/
from  django.core.mail import send_mail
from django.template.loader import render_to_string, get_template
from django.template import Context
from django.conf import settings

def email_ctx(ctx, template_txt, template_html, subject, logger):
  ctx['domain'] = settings.BASE_URL
  message_plain = render_to_string(template_txt, ctx)
  message_html = get_template(template_html).render(Context(ctx))
  recipients = User.objects.exclude(email='').values_list('email', flat=True)
  logger.debug("recipients: %s"%', '.join(recipients))
  if len(recipients)==0:
    logger.debug("No users with emails to receive")
    return
  res = send_mail(
    subject = settings.EMAIL_SUBJECT_PREFIX + subject,
    message = message_plain,
    from_email = settings.DEFAULT_FROM_EMAIL,
    recipient_list = recipients,
    html_message = message_html
  )
  if res==0:
    logger.debug("Failed to send email")

