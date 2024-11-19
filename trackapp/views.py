from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
import csv
from .forms import UploadCSVForm, CreateQRCodeForm
from .models import Item, QRCode, Transaction
from django.shortcuts import redirect, render
import re
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import chardet 
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib.auth import logout
from django.db.models import Count
import pandas as pd
from django.db.models import F
from django.utils.timezone import make_naive
import traceback
from django.db.models import Max, Case, When, CharField, DateTimeField
import datetime


def get_item_by_qr(request):
    
    try:
        qr_string = request.GET.get('qr_string')
        match = re.match(r'(.+)-(.+)', qr_string)
        mcode, item_code = match.groups()
        item = Item.objects.get(item_code=item_code)
        return JsonResponse({"success": True, "item_title": item.description})
    except :
        return JsonResponse({"success": False, "error": "Item not found"})
    
@login_required
def home(request):
    return render(request, "home.html")


@login_required
def fcg_scan_qr(request):
    if not request.user.groups.filter(name='fg').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    if request.method == "POST":
        try:
            qr_string = request.POST.get("qr_string")  # the scanned QR value.
            match = re.match(r"(.+)-(.+)", qr_string)
            mcode, item_code = match.groups()

        
            item = Item.objects.get(item_code=item_code)

            # Check if the item code from the QR is in the items table.
            if not item:
                messages.error(request, f"Item with code {item_code} is not recognized.")
                return render(request, "scan_fcg.html")

            qr, created = QRCode.objects.get_or_create(
                item=item, mcode=mcode, qr_string=qr_string
            )
            if created :
                # Increment the FCG count
                item.moq_mail_flag = True
                item.count_fcg += 1
                item.save()

                # Create transaction
                Transaction.objects.create(item=item, mcode=qr, state="FCG")

                messages.success(request, f"Scanned QR for {item_code}. Added to FCG state.")
            else :
                messages.info(request, f"QR Code for {item_code} is already added.")
        except :
            try :
                messages.error(request, f"Item {item_code} does not exist.")
            except :
                messages.error(request, f"Item  does not exist.")
        
        return render(request, "scan_fcg.html")

    return render(request, "scan_fcg.html")

import qrcode
from fpdf import FPDF
import os

@login_required
def generate_qr(request):
    if not request.user.groups.filter(name='qrcodegenerate').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    
    if request.method == "POST":
        form = CreateQRCodeForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data["item"]
            mcode = form.cleaned_data["mcode"]
            qr_string = f"{mcode}-{item.item_code}"

            # Generate QR with `qrcode` lib
            qr = qrcode.QRCode(box_size=8)
            img = qr.add_data(qr_string)
            img = qr.make_image(fill_color="black", back_color="white")

            # Save the image temporarily
            unique_filename = qr_string.replace("/", "")
            img_filename = f"{unique_filename}.png"
            img.save(img_filename)

            # Generate the PDF
            pdf = FPDF("P", "mm", (25, 25))
            pdf.add_page()
            pdf.set_font("Arial", size=2)
            pdf.text(2, 22, txt=f"Unique code: {qr_string}")
            pdf.image(img_filename, x=2, y=0, w=20, h=20)
            pdf_filename_short = f"{unique_filename}.pdf"
            pdf.output(pdf_filename_short)

            # Create QRCode entry in DB
            QRCode.objects.create(item=item, mcode=mcode, qr_string=qr_string)

            # Delete the temporary image
            os.remove(img_filename)

            return redirect("view_pdf", filename=pdf_filename_short)
    else:
        form = CreateQRCodeForm()
    return render(request, "generate_qr.html", {"form": form})


from django.http import FileResponse

@login_required
def view_pdf(request, filename):
    return FileResponse(open(filename, "rb"), content_type="application/pdf")


@login_required
def export_screen(request):
    if not request.user.groups.filter(name='fg').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    if request.method == "POST":
        try:
            qr_string = request.POST.get("qr_string")
            transport_mode = request.POST.get("transport_mode")
            invoice_number = request.POST.get("invoice_number")
            invoice_date = request.POST.get("invoice_date")
            value = request.POST.get("value")

            match = re.match(r"(.+)-(.+)", qr_string)
            mcode, item_code = match.groups()

            item = Item.objects.get(item_code=item_code)
            qr = QRCode.objects.get(item=item, mcode=mcode, qr_string=qr_string)

            # Check the state of QR code before proceeding
            last_transaction = Transaction.objects.filter(mcode=qr).order_by('-id').first()

            if last_transaction:
                # For instance, if you are scanning in "Export India"
                if last_transaction.state != "FCG":  
                    raise Exception(f"QR code is in state {last_transaction.state}, not allowed to scan in 'Export India'.")
                # Add more conditions as per your requirements for each state

            # Decrease from FCG
            item.count_fcg -= 1
            item.count_transit += 1
            item.save()

            # Create transaction for transit
            Transaction.objects.create(
                item=item,
                mcode=qr,
                state="TRANSIT",
                mode_of_transport=transport_mode,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                value=value,
            )

            messages.success(request, f'Exported {item_code} via {transport_mode}.')
        
        except Item.DoesNotExist:
            messages.error(request, "Item Does Not Exist")
        except Exception as e: # general exception to catch all errors
            messages.error(request, f"Error: {e}")

        return redirect('export_screen')  # Replace 'export_screen' with the name of the URL pattern for this view

    return render(request, "export.html")



@login_required
def ukimport(request):
    if not request.user.groups.filter(name='uk').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    if request.method == "POST":
        try:
            qr_string = request.POST.get("qr_string")
            match = re.match(r"(.+)-(.+)", qr_string)
            mcode, item_code = match.groups()

            item = Item.objects.get(item_code=item_code)
            qr = QRCode.objects.get(item=item, mcode=mcode, qr_string=qr_string)

            last_transaction = Transaction.objects.filter(item=item, mcode=qr).last()

            if not last_transaction or last_transaction.state != "TRANSIT":
                messages.error(request, f"Item {item_code} is not in the 'TRANSIT' state.")
                return render(request, "ukimport.html")

            # Decrease from Transit and increase in UK Inward
            item.count_transit -= 1
            item.count_uk_inward += 1
            item.save()

            # Create transaction for UK import
            Transaction.objects.create(item=item, mcode=qr, state="UK_INWARD")
            messages.success(request, f"Imported to UK: {item_code}.")
        except :
            messages.error(request, f"Item {item_code} does not exist.")
        
        return render(request, "ukimport.html")

    return render(request, "ukimport.html")

@login_required
def ukexport(request):
    if not request.user.groups.filter(name='uk').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    if request.method == "POST":
        print(request.POST)
        ratio = 0
        try:
            qr_string = request.POST.get("qr_string")
            customer_name = request.POST.get('customer_name')
            dispatched_quantity = float(request.POST.get('quantity_dispatched'))
            balance_quantity = float(request.POST.get('quantity_remaining'))

            
            ratio=dispatched_quantity/(dispatched_quantity+balance_quantity)


            match = re.match(r"(.+)-(.+)", qr_string)
            mcode, item_code = match.groups()

            item = Item.objects.get(item_code=item_code)
            qr = QRCode.objects.get(item=item, mcode=mcode, qr_string=qr_string)

            last_transaction = Transaction.objects.filter(item=item, mcode=qr).last()

            if not last_transaction or last_transaction.state not in ("UK_INWARD","UK_DISPATCH"):
                messages.error(request, f"Item {item_code} is not in the 'UK_INWARD' state. and is in {last_transaction.state}")
                return render(request, "ukexport.html")

            # Decrease from UK Inwards
            existing_count=item.count_uk_inward 
            item.count_uk_inward -= ratio*existing_count
            item.count_uk_dispatch += ratio*existing_count 
            item.save()


            # Create transaction for UK export
            Transaction.objects.create(item=item, mcode=qr, state="UK_DISPATCH")
            messages.success(request, f"Exported from UK: {item_code}.")
        except :
            print(traceback.format_exc())
            messages.error(request, f"Item does not exist.")
            return render(request, "ukexport.html")
        if(ratio != 1):
            unique_filename = qr_string.replace("/", "")+".pdf"
            return qr_code_gen(unique_filename)
        else :
            return render(request, "ukexport.html")


        
        
    

    return render(request, "ukexport.html")

from django.shortcuts import render

@login_required
def admin_screen(request):
    if not request.user.groups.filter(name='view').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')

    # Filter items to include only those with transactions
    items = Item.objects.annotate(num_transactions=Count('transaction')).filter(num_transactions__gt=0).prefetch_related("qrcode_set", "transaction_set")

    return render(request, 'admin_screen.html', {'items': items})

    # Calculate the different transaction states for each item
    for item in items:
        item.qrcodes = item.qrcode_set.all()
        transactions = item.transaction_set.all()
        item.transactions_fcg = item.count_fcg  # Count of items in FCG state
        item.transactions_transit = (
            item.count_transit
        )  # Count of items in TRANSIT state
        item.transactions_uk_inward = (
            item.count_uk_inward
        )  # Count of items in UK_INWARD state
        item.transactions_uk_dispatch = transactions.filter(state="UK_DISPATCH").count()

    return render(request, "admin_screen.html", {"items": items})


from django.http import JsonResponse

@login_required
def get_mcodes_for_item(request, item_code):
    item = Item.objects.get(item_code=item_code)
    qr_codes = QRCode.objects.filter(item=item)
    mcode_status = []
    for qr in qr_codes:
        latest_transaction = qr.transaction_set.order_by("-timestamp").first()
        if latest_transaction:
            mcode_status.append(
                {"mcode": qr.mcode, "status": latest_transaction.get_state_display()}
            )
        else:
            mcode_status.append({"mcode": qr.mcode, "status": "No transactions"})
    return JsonResponse({"mcodes_status": mcode_status})




@login_required
def upload_item_and_moq(request):
    if not request.user.groups.filter(name='upload').exists():
        login_url = reverse('agent_login')
        next_url = request.get_full_path()
        return redirect(f'{login_url}?next={next_url}')
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["file"]
            # First, read the file to bytes, then detect the encoding
            file_content = csv_file.read()
            detected_encoding = chardet.detect(file_content[:1000])  # Check first 1000 bytes to guess the encoding

            # Decode the file using the detected encoding, if chardet is confident enough; otherwise, use utf-8 and ignore errors
            confidence = detected_encoding.get("confidence", 0)
            if confidence > 0.5:
                encoding = detected_encoding['encoding']
            else:
                encoding = 'utf-8'

            # Decode the entire file with the chosen encoding
            try:
                decoded_file = file_content.decode(encoding).splitlines()
            except UnicodeDecodeError:
                # If there's still a Unicode error, ignore those characters
                decoded_file = file_content.decode('utf-8', errors='ignore').splitlines()

            reader = csv.DictReader(decoded_file)

            for row in reader:
                item_code = row["Item Code"]
                description = row.get("Item Description", "")  # Defaults to empty string if not present
                moq = int(row.get("moq", 0))  # Defaults to 0 if not present

                # Try to get the existing item by item_code
                item, created = Item.objects.get_or_create(item_code=item_code)

                # Update fields
                item.description = description
                item.moq = moq
                item.save()

            return HttpResponse("CSV uploaded and processed.")
    else:
        form = UploadCSVForm()

    # Adjust the template name if needed
    return render(request, "upload.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        # Get the 'next' parameter from the request
        next_url = self.request.GET.get('next')

        # If 'next' parameter exists and is not None, redirect to it
        if next_url:
            return next_url
        
        # Otherwise, return the default success URL (you can customize this)
        return reverse_lazy('home') 

def agent_logout(request):
    logout(request)
    return redirect(reverse_lazy('home')) 


@login_required
def download_excel(request):
    # Query your models and prepare data for items
    items = Item.objects.annotate(
        fg_stock=F('count_fcg'),
        transit_stock=F('count_transit'),
        uk_fg_stock=F('count_uk_inward'),
        uk_dispatch_stock=F('count_uk_dispatch')
    ).values(
        'item_code', 'description', 'moq', 'fg_stock', 'transit_stock', 'uk_fg_stock', 'uk_dispatch_stock'
    )

    transactions = (Transaction.objects
        .values('mcode__mcode')
        .annotate(
            qty=F('value'),
            fg_stock_date=Max(Case(When(state='FCG', then='timestamp'), output_field=DateTimeField())),
            export_india_date=Max(Case(When(state='TRANSIT', then='timestamp'), output_field=DateTimeField())),
            uk_inwards_date=Max(Case(When(state='UK_INWARD', then='timestamp'), output_field=DateTimeField())),
            uk_dispatch_date=Max(Case(When(state='UK_DISPATCH', then='timestamp'), output_field=DateTimeField())),
            invoice_number=Max(Case(When(state='TRANSIT', then='invoice_number'), output_field=CharField())),
        )
        .values(
            'item__item_code', 'item__description', 'mcode__mcode', 'qty',
            'fg_stock_date', 'export_india_date', 'uk_inwards_date', 'uk_dispatch_date', 'invoice_number'
        )
    )



    # Convert timezone-aware datetimes to timezone-naive
    for transaction in transactions:
        for field in ['fg_stock_date', 'export_india_date', 'uk_inwards_date', 'uk_dispatch_date']:
            if transaction[field] and transaction[field].tzinfo:
                transaction[field] = make_naive(transaction[field])

    # Convert to pandas DataFrame
    df_items = pd.DataFrame(items)
    df_transactions = pd.DataFrame(transactions)

    # Create a Pandas Excel writer using openpyxl as the engine
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inventory_data.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df_items.to_excel(writer, index=False, sheet_name='Items')
        df_transactions.to_excel(writer, index=False, sheet_name='Transactions')

    return response


def qr_code_gen(qr_string):
        qr = qrcode.QRCode(box_size=8)
        img = qr.add_data(qr_string)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save the image temporarily
        unique_filename = qr_string
        img_filename = f"{unique_filename}.png"
        img.save(img_filename)

        # Generate the PDF
        pdf = FPDF("P", "mm", (25, 25))
        pdf.add_page()
        pdf.set_font("Arial", size=2)
        pdf.text(2, 22, txt=f"Unique code: {qr_string}")
        pdf.image(img_filename, x=2, y=0, w=20, h=20)
        pdf_filename_short = f"{unique_filename}.pdf"
        pdf.output(pdf_filename_short)

        # Delete the temporary image
        os.remove(img_filename)

        return redirect("view_pdf", filename=pdf_filename_short)