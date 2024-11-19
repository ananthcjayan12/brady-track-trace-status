from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Item
from .email.send_email import MailSender


@receiver(post_save, sender=Item)
def check_moq(sender, instance, **kwargs):
    # instance is the actual Item object being saved
    if instance.count_fcg < instance.moq and instance.moq_mail_flag == True:
        mail = MailSender(
            "ananthcjayan@srshti.co.in",
            "Olapeepi@2468",
            "premium179.web-hosting.com",
            465,
        )
        mail.send_mail_without_attachment(
            "ananthcjayan@gmail.com",
            "Low FCG Count Alert",
            f"The FCG count for item {instance.item_code} is below the MOQ.",
        )

        instance.moq_mail_flag = False
        instance.save()
