from django import template

register = template.Library()

register.filter('strftime', lambda value, arg: value.strftime(arg))
