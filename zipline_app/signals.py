from django.dispatch import Signal
order_cancelled = Signal(providing_args=["id"])
