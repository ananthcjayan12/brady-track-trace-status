# models.py

from django.db import models

from django.db import models

class Item(models.Model):
    item_code = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    moq = models.PositiveIntegerField(default=0) 
    moq_mail_flag=models.BooleanField(default=True)
    # Count fields for each state
    count_fcg = models.PositiveIntegerField(default=0)           # For items in FCG
    count_transit = models.PositiveIntegerField(default=0)       # For items in Transit
    count_uk_inward = models.FloatField(default=0)     # For items in UK Import
    count_uk_dispatch = models.FloatField(default=0)   # For items in UK Export

    def __str__(self):
        return f"{self.item_code}"
    def get_mcodes(self):
        return self.qrcode_set.all()




class QRCode(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    mcode = models.CharField(max_length=255)
    qr_string = models.CharField(max_length=255, unique=True) # mcode-itemcode
    STATES = [
    ('FG', 'Finished Goods'),
    ('EXPORT_INDIA', 'Export India'),
    ('UK_INWARDS', 'UK Inwards'),
    ('UK_DISPATCH', 'UK Dispatch')
    ]

    state = models.CharField(
        max_length=15,
        choices=STATES,
    default='FG'
)
    def __str__(self):
        return f"{self.qr_string}"

class Transaction(models.Model):
    MODES = (('SHIP', 'Ship'), ('FLIGHT', 'Flight'))
    STATES = (('FCG', 'FCG'), ('TRANSIT', 'Transit'), ('UK_INWARD', 'UK Inward'), ('UK_DISPATCH', 'UK Dispatch'))
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    mcode = models.ForeignKey(QRCode, on_delete=models.SET_NULL, null=True)
    mode_of_transport = models.CharField(choices=MODES, max_length=10, null=True, blank=True)
    state = models.CharField(choices=STATES, max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    value = models.TextField(default="")
