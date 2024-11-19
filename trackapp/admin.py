from django.contrib import admin
from .models import Item, QRCode, Transaction

class QRCodeInline(admin.ModelAdmin):
    model = QRCode
    list_display = [
        'item', 
        'mcode', 
        'qr_string', 
        'state'
    ]


class TransactionAdmin(admin.ModelAdmin):
        list_display = [
        'mcode', 
        'item', 
        'state', 
        'timestamp', 
        'invoice_number', 
        'invoice_date',
        'value',
    ]


class ItemAdmin(admin.ModelAdmin):

    
    list_display = [
        'item_code', 
        'description', 
        'count_fcg', 
        'count_transit', 
        'count_uk_inward', 
        'count_uk_dispatch',
        'moq',
        'moq_mail_flag'
    ]

    search_fields = ['item_code', 'description']



admin.site.register(Item, ItemAdmin)
admin.site.register(QRCode,QRCodeInline)
admin.site.register(Transaction,TransactionAdmin)
