from django.contrib import admin

# Register your models here.
from .models import Fill, Order, Asset

#class AssetInline(admin.TabularInline):
#    model = Asset
#    extra = 3

class OrderAdmin(admin.ModelAdmin):
    fieldSets = [
        (None,               {'fields': ['order_text', 'asset', 'amount']}),
        ('Date information', {'fields': ['pub_date']}),
    ]
    #inlines = [AssetInline]
    list_display = ('order_text', 'pub_date', 'was_published_recently', 'asset', 'amount')
    list_filter = ['pub_date']
    search_fields = ['order_text', 'asset.asset_symbol']

#class FillAdmin(admin.ModelAdmin):
#    inlines = [AssetInline]

admin.site.register(Order,OrderAdmin)
admin.site.register(Fill)
admin.site.register(Asset)
