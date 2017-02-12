from django.contrib import admin

# Register your models here.
from .models import Fill, Order

class FillInline(admin.TabularInline):
    model = Fill
    extra = 3

class OrderAdmin(admin.ModelAdmin):
    fieldSets = [
        (None,               {'fields': ['order_text']}),
        ('Date information', {'fields': ['pub_date']}),
    ]
    inlines = [FillInline]
    list_display = ('order_text', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['order_text']

admin.site.register(Order,OrderAdmin)
admin.site.register(Fill)

