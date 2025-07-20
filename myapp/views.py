from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404,HttpResponseBadRequest
from django.template import loader
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator #reset function 
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from decimal import Decimal
from . tokens import generate_token
import os, json, shutil, csv, re, subprocess
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .code.generate_org import generate_org
from .models import chart, ChartAccess, Image, UserProfile, ClientLead, Cart, CartItem, Order, OrderItem, CompanyInfo, CustomerInfo, Coupon, CouponUsage
from datetime import timedelta, datetime
from django.utils.dateparse import parse_date
import razorpay
from django.urls import reverse
import requests
import uuid
from django.http import HttpResponse
from django.template.loader import get_template
# WeasyPrint import with graceful fallback handling
# This library is optional and used for PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    # WeasyPrint not available - define placeholder classes
    # This allows the application to continue working without PDF generation
    # OSError handles Windows GTK library issues
    WEASYPRINT_AVAILABLE = False
    class HTML:
        def __init__(self, *args, **kwargs):
            pass
        def write_pdf(self):
            return b"PDF generation not available"
    class CSS:
        def __init__(self, *args, **kwargs):
            pass
from django.core.mail import EmailMessage
import io


# Landing page view (public access)
def landing(request):
    """
    Public landing page view that doesn't require authentication
    """
    return render(request, 'landing.html')


# Create your views here.

@login_required
def home(request):
    # Check if user has UserProfile, create if it doesn't exist
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, is_superadmin=False)
    
    if user_profile.is_superadmin or request.user.groups.filter(name='Admin').exists(): 
        charts = chart.objects.all()
        users = User.objects.filter(groups__name="Subscriber")
    elif request.user.groups.filter(name='Sales Partner').exists():
        users = User.objects.filter(userprofile__client_of=request.user).order_by('-date_joined')
        charts = chart.objects.filter(allowed_users__in=users)
    else:    
        charts = chart.objects.filter(allowed_users=request.user)
        users = None
    
    totalpersonCount = 0
    totaldepartmentCount = 0
    totalorgchartCount = 0
    common_department_names = [
    "Human Resources (HR)",
    "Account",
    "Finance",
    "Marketing",
    "Sales",
    "Information Technology (IT)",
    "Operations",
    "Customer Service",
    "Research and Development (R&D)",
    "Legal",
    "Administration",
    "Procurement",
    "Quality Assurance (QA)",
    "Production",
    "Supply Chain",
    "Public Relations (PR)",
    "Facilities Management",
    "Compliance",
    "Project Management",
    "Business Development",
    "Communications"
    ]
    matched_categories = set()
    for i in charts:
        json_items = json.loads(i.departmentNames)
        for item in json_items:
            words = item.split()
            # Check if any word in the item matches any category
            for word in words:
                if word in common_department_names and word not in matched_categories:
                    # Add the matched category to the set
                    matched_categories.add(word)
        totalpersonCount+= i.personCount
    totaldepartmentCount += len(matched_categories)
    totalorgchartCount += len(charts)
    return render(request, "index.html", {"totaldepartmentCount": totaldepartmentCount, "totalpersonCount":totalpersonCount, "totalorgchartCount":totalorgchartCount, "users": users})

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('signup')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('signup')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('signup')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('signup')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        # myuser.is_active = False
        myuser.is_active = False
        myuser.save()
        demo_charts = chart.objects.filter(title__icontains='demo')
        for demo_chart in demo_charts:
            demo_chart.allowed_users.add(myuser)
            demo_chart.save()
        user_profile = UserProfile(user=myuser)
        user_profile.is_superadmin = False
        user_profile.save()
        subscriber_group, _ = Group.objects.get_or_create(name='Subscriber')
        myuser.groups.add(subscriber_group)
        messages.success(request, "Your Account has been created succesfully!! Please check your email to confirm your email address in order to activate your account.")
          # Welcome Email
        subject = "Account Created Successfully!!"
        welcome_context = {
            'name': myuser.first_name,
            'user': myuser,
        }
        welcome_html_content = render_to_string('welcome_email.html', welcome_context)
        
        welcome_email = EmailMessage(
            subject=subject,
            body=welcome_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[myuser.email]
        )
        welcome_email.content_subtype = 'html'
        welcome_email.send(fail_silently=True)
        
        # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your Email Login!!"
        message2 = render_to_string('email_confirmation.html',{
            
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
        email_subject,
        message2,
        settings.EMAIL_SENDER_ID,
        [myuser.email],
        )
        email.fail_silently = True
        email.send()
        
        return redirect('signin')
        
        
    return render(request, "authentication/signup.html")


def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request,myuser)
        messages.success(request, "Your Account has been activated!! Please log in with your credentials")
        return redirect('signin')
    else:
        return render(request,'activation_failed.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            fname = user.first_name
            try:
                user_profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                # If UserProfile doesn't exist, create a blank profile for the user
                user_profile = UserProfile(user=user)
                user_profile.is_superadmin = False  # Assuming default value
                user_profile.save()
            return redirect('home')
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('signin')
    
    return render(request, "authentication/signin.html")

@login_required
def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('signin')



class ExpiringTokenGenerator(PasswordResetTokenGenerator):
    def make_token(self, user):
        token = super().make_token(user)
        expiration_time = timezone.localtime(timezone.now()) + timedelta(hours=24)
        expiration_time = expiration_time.replace(microsecond=0)
        return f"{token}.{expiration_time.timestamp()}"

expiring_token_generator = ExpiringTokenGenerator()

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email')
        pattern = r'^[\w\.-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9\.]+$'
        if not re.match(pattern, email):
            messages.error(request, "Please enter a valid email address!")
            return redirect('password_reset')


        user = User.objects.filter(email=email).first()
        
        if user:
            token = expiring_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
            send_password_reset_email(user, email, reset_link)
            messages.success(request, "Password reset email sent.")
            return render(request, 'password_reset/password_reset.html', {'title':'Password Reset Request Sent'})
        else:
            messages.error(request, "User with this email address does not exist.")
            return redirect('password_reset')
    
    return render(request, 'password_reset/password_reset.html', {'title':'Password Reset'})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and token_valid(user,token):
        if request.method == "POST":
            password = request.POST.get('password')
            confirmpassword = request.POST.get('confirmPassword')

            if password != confirmpassword:
                messages.error(request, "Your passwords does not match!")
                return render(request, 'password_reset/password_reset_confirm.html',{'title': 'Password Reset'})

            pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
            if not re.match(pattern, password):
                messages.error(request, "Please Choose a Strong Password!")
                messages.info(request, "Choose a password with: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/><br/>At least 8 characters. <br/><br/>At least one uppercase letter.<br/>At least one lowercase letter. <br/>At least one digit. <br/>At least one special character")
                return render(request, 'password_reset/password_reset_confirm.html',{'title': 'Password Reset'}) 



            user.set_password(password)
            user.save()
            messages.success(request, "Your password has been reset successfully.")
            return render(request, 'password_reset/password_reset_confirm.html',{'title': 'Password Reset Complete'})
        return render(request, 'password_reset/password_reset_confirm.html',{'title': 'Password Reset'})
    else:
        print("invalid links")
        messages.error(request, "The password reset link is invalid or expired.")
        return redirect('password_reset')

def token_valid(user,token):
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    try:
        expiration_timestamp = float(parts[1])
    except ValueError:
        return False
    
    expiration_datetime = datetime.fromtimestamp(expiration_timestamp)
    if expiration_datetime <= timezone.localtime(timezone.now()).replace(tzinfo=None):
        return False
    token_without_exp = parts[0]
    return expiring_token_generator.check_token(user, token_without_exp)


def send_password_reset_email(user, email, reset_link):
    subject = 'Password Reset Request'
    html_content = render_to_string('password_reset/password_reset_email.html', {'reset_link': reset_link,'user_obj':user})
    
    email_message = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.EMAIL_SENDER_ID,
        to=[email]
    )
    email_message.content_subtype = 'html'
    email_message.send(fail_silently=True)



@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def createorgchart(request):
    charts = chart.objects.order_by('-creation_date')[:5]
    available_users = User.objects.filter(is_staff=False)
    try:
        access_key = UserProfile.objects.get(user=request.user).access_uuid  
    except UserProfile.DoesNotExist:
        access_key = None
    return render(request, "create_orgchart.html",{'charts': charts,'available_users':available_users,'access_key':access_key})


@login_required
def listorgchart(request):
    current_datetime = timezone.localtime(timezone.now())
    is_staff = request.user.is_staff
    try:
        access_key = UserProfile.objects.get(user=request.user).access_uuid  
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
        access_key = user_profile.access_uuid
    ChartAccess.remove_expired_access()
    
    # Check if user has UserProfile, create if it doesn't exist
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, is_superadmin=False)
    
    if user_profile.is_superadmin or request.user.groups.filter(name='Admin').exists():
        charts_data = [{'chart': chart, 'creation_time': chart.creation_date} for chart in chart.objects.all()]

    else:
        demo_charts = chart.objects.filter(title__icontains='demo')
        for demo_chart in demo_charts:
            demo_chart.allowed_users.add(request.user)
            demo_chart.save()
        # Retrieve charts accessible to the current user
        charts_with_access = chart.objects.filter(allowed_users=request.user)

        # Prepare data for rendering
        charts_data = []
        for chart_obj in charts_with_access:
            access = chart_obj.accesses.filter(user=request.user).first()
            if access:
                access_grant_time = access.access_grant_time
                expiration_time = access.expiration_time
                days_remaining = max((expiration_time - current_datetime).days, 0)
            else:
                access_grant_time = None
                expiration_time = None
                days_remaining = None

            charts_data.append({
                'chart': chart_obj,
                'access_grant_time': access_grant_time,
                'expiration_time': expiration_time,
                'days_remaining': days_remaining
            })

    return render(request, "list_orgchart.html", {'charts_data': charts_data, 'access_key':access_key})

@login_required
def myaccount(request):
    user = request.user
    return render(request, "myaccount.html",{ 'user': user})

def view_404(request, exception=None):
    # make a redirect to homepage
    return redirect('home')

@csrf_exempt
def upload_csv(request):
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        user_id = request.POST.get("user_profile")
        user = User.objects.get(id=user_id)
        selected_user, created = UserProfile.objects.get_or_create(user=user)
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({"error": "Invalid file type. Please select a CSV file."}, status=500)
        
        title = csv_file.name.rsplit('.', 1)[0]
        chart_obj = chart.objects.all()
        for chart_title in chart_obj:
            if(chart_title.title==title):
                result=False
                return JsonResponse({'error': "Chart or title name already exists"}, status=500)
        # Process the CSV file (e.g., parse and store data)
        # org_template = "org_template.html"
        # full_html_file_path = os.path.join("myapp", "templates", org_template)
        result, personCount, departmentNames, nodes_json = generate_org(csv_file, title,  selected_user)
        # run_collectstatic()
        if not result:
            return JsonResponse({'error': "Invalid Binding recheck your data"}, status=500)
        
        # pass it to the server
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return str(obj) 
        if result:
            payload = {
                "title": title,
                "personCount": personCount,
                "nodes_json": json.loads(json.dumps(nodes_json, default=convert_numpy))  # Should be serializable (list or JSON string)
            }
            # Create the `chart_data` directory if it doesn't exist
            chart_data_dir = os.path.join(settings.MEDIA_ROOT, "chart_data")
            os.makedirs(chart_data_dir, exist_ok=True)

            def is_title_safe(title):
                # Allow only alphanumeric characters, underscore, dash, and space
                allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- "
                return all(char in allowed_chars for char in title)
            # Generate safe filename
            if not is_title_safe(title):
                return JsonResponse({'message': 'Title contains invalid characters. Allowed: letters, numbers, space, _, -'}, status=400)
            filename = f"{title}.json"
            file_path = os.path.join(chart_data_dir, filename)

            # Save the JSON data to the file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)

            print(f"Chart data saved to: {file_path}")

            
            custom_directory = "csv_files"
            # Construct the path to the file to be deleted
            file_path = os.path.join(settings.MEDIA_ROOT, custom_directory)
            fs = FileSystemStorage(location=file_path)
            filename = fs.save(csv_file.name, csv_file)

            # You can also get the URL of the saved file
            
            # print(file_url)
            # print(personCount, len(np.array(json.loads(departmentNames))))
            current_datetime = timezone.localtime(timezone.now())
            formatted_datetime = current_datetime.strftime(r"%Y-%m-%d %H:%M:%S")
            chart(title=title, creation_date=formatted_datetime, personCount=personCount, departmentNames=departmentNames).save()

            
            response_data = {"message": "CSV file uploaded and processed successfully"}
            return JsonResponse(response_data)

    else:
    # Handle other HTTP methods or no file provided
        return JsonResponse({"message": "Invalid request"}, status=400)
    

# def serve_file(request, file_name):
#     access=False
#     title, _ = os.path.splitext(file_name)
#     if request.user.is_authenticated:
#         user_id = request.user.id
#         # chart_id = get_object_or_404(chart, title=title)
#         user = User.objects.get(id=user_id)
#         chart_ids = chart.objects.filter(allowed_users=user)
#         if (user.is_staff and user.groups.filter(name='Admin')):
#             access=True
#         for charts in chart_ids:
#             if (charts.title==title):
#                 access=True
#     #making sphurti chart link public
#     if 'demo' in file_name.lower():
#         access =True
#     if access:
#         # Specify the directory where the files are stored
#         file_path = os.path.join(settings.BASE_DIR,'myapp','templates','orgcharts', file_name)
        

#         # Check if the file exists
#         if os.path.exists(file_path):
#             template = loader.get_template(f"orgcharts/{file_name}")

#             # Render the HTML file as a web page
#             rendered_html = template.render()

#             # Return the rendered HTML as an HTTP response
#             return HttpResponse(rendered_html)

#         # Return a 404 Not Found response if the file doesn't exist
#         from django.http import Http404
#         raise Http404("File not found")
#     else:
#         return HttpResponse(status=403)
#         # raise HttpResponse(content="Forbidden Access")


@csrf_exempt
@require_POST
def serve_file_testing(request):
    access = False
    data = json.loads(request.body)
    # Get chart_id and user_uuid from POST data
    raw_file_uuid = data.get('chart_id')
    user_uuid = data.get('user_id')

    if not raw_file_uuid or not user_uuid:
        return JsonResponse({'message': 'Missing ChartID or User UUID'}, status=200)
    try:
        file_uuid = uuid.UUID(raw_file_uuid.strip('"').strip())
        user_uuid_obj = uuid.UUID(user_uuid.strip('"').strip())
    except (ValueError, TypeError):
        return JsonResponse({'message': 'Invalid ChartID or User UUID'}, status=200)

    file_name = chart.objects.filter(uuid=file_uuid).values_list('title', flat=True).first()
    if not file_name:
        return JsonResponse({'message': 'Chart Not Found'}, status=200)

    # Get user by userprofile.access_uuid
    try:
        user_profile = UserProfile.objects.get(access_uuid=user_uuid_obj)
        userobj = user_profile.user
    except UserProfile.DoesNotExist:
        return JsonResponse({'message': 'User not found'}, status=200)

    if 'demo' in file_name.lower():
        access = True
    elif userobj.is_staff and userobj.groups.filter(name='Admin').exists():
        access = True
    else:
        chart_ids = chart.objects.filter(allowed_users=userobj)
        for charts in chart_ids:
            if charts.title == file_name:
                access = True
                break
    if '/' in file_name or '..' in file_name:
        return JsonResponse({'access': False, 'message': 'Invalid Company Name'}, status=200)

    full_filename = f"{file_name}.json"
    file_path = os.path.join(settings.MEDIA_ROOT, 'chart_data', full_filename)

    if not os.path.exists(file_path):
        return JsonResponse({'access': False, 'message': 'Chart Not Found.'}, status=200)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return JsonResponse({'access': access, 'chart_title': file_name, 'nodes_data': data['nodes_json']}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'access': False, 'message': 'Failed to parse JSON.'}, status=500)




@require_POST
def serve_file(request):
    """Serve chart data with access control, supporting dual chart system"""
    access = False
    data = json.loads(request.body)
    # Get chart_id from POST data
    raw_file_uuid = data.get('chart_id')

    if not raw_file_uuid:
        return JsonResponse({'message': 'Missing ChartID'}, status=200)
    try:
        file_uuid = uuid.UUID(raw_file_uuid.strip('"').strip())
    except (ValueError, TypeError) as e:
        return JsonResponse({'message': 'Invalid ChartID'}, status=200)
    
    # Get the chart instance
    try:
        chart_instance = chart.objects.get(uuid=file_uuid)
    except chart.DoesNotExist:
        return JsonResponse({'message': 'Chart Not Found'}, status=200)

    # Check if this is a preview request
    is_preview_request = False
    referer = request.META.get('HTTP_REFERER', '')
    preview_mode = data.get('preview_mode', False)
    
    if ('preview-chart' in referer or 
        ('chart/' in referer and '/preview/' in referer) or 
        preview_mode):
        is_preview_request = True
    
    print(f"Request for chart {chart_instance.title}")
    print(f"Referer: {referer}")
    print(f"Preview mode: {preview_mode}")
    print(f"Is preview request: {is_preview_request}")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    # For preview requests, allow anonymous access
    if is_preview_request:
        print(f"Processing preview request for chart {chart_instance.title}")
        # Serve marketplace/preview data for anonymous users
        file_path = chart_instance.get_marketplace_chart_data()
        if not file_path or not os.path.exists(file_path):
            # Fallback to original data if marketplace doesn't exist
            file_path = chart_instance.get_full_chart_data()
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chart_data = json.load(f)
                
                # Include chart metadata in response
                response_data = {
                    'access': True,
                    'chart_title': chart_instance.title,
                    'nodes_data': chart_data.get('nodes_json', []),
                    'is_preview': True,
                    'chart_uuid': str(chart_instance.uuid)
                }
                
                return JsonResponse(response_data, status=200)
            except json.JSONDecodeError:
                return JsonResponse({'access': False, 'message': 'Failed to parse JSON.'}, status=500)
            except Exception as e:
                return JsonResponse({'access': False, 'message': f'Error loading chart: {str(e)}'}, status=500)
        else:
            return JsonResponse({'access': False, 'message': 'Chart data not found'}, status=200)

    # Use request.user for validation (non-preview requests)
    if not request.user.is_authenticated:
        return JsonResponse({'access': False, 'message': 'Authentication required'}, status=200)
    userobj = request.user

    # Check access permissions
    if 'demo' in chart_instance.title.lower():
        access = True
    elif userobj.is_staff and userobj.groups.filter(name='Admin').exists():
        access = True
    elif hasattr(userobj, 'userprofile') and userobj.userprofile.is_superadmin:
        access = True
    else:
        if chart_instance.allowed_users.filter(id=userobj.id).exists():
            access = True

    # Determine which file to serve based on user access and chart configuration
    if access:
        # User has full access - serve original data
        file_path = chart_instance.get_full_chart_data()
        if not file_path or not os.path.exists(file_path):
            # Fallback to marketplace data if original doesn't exist
            file_path = chart_instance.get_marketplace_chart_data()
    else:
        # User doesn't have access - serve preview data for marketplace
        file_path = chart_instance.get_marketplace_chart_data()
    
    if not file_path or not os.path.exists(file_path):
        return JsonResponse({'access': False, 'message': 'Chart data not found.'}, status=200)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Include chart metadata in response
        response_data = {
            'access': access,
            'chart_title': chart_instance.title,
            'nodes_data': data.get('nodes_json', []),
            'is_preview': not access or (chart_instance.has_preview_version and file_path == chart_instance.get_marketplace_chart_data()),
            'chart_uuid': str(chart_instance.uuid)
        }
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'access': False, 'message': 'Failed to parse JSON.'}, status=500)
    except Exception as e:
        return JsonResponse({'access': False, 'message': f'Error loading chart: {str(e)}'}, status=500)

    

@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def delete_file(request, pk):
    try:
        charts = chart.objects.get(pk=pk)
    except chart.DoesNotExist:
        return JsonResponse({'error': "Chart not found"}, status=404)
    
    try: 
        # deleting csv file
        custom_directory = "csv_files"
        json_directory = "chart_data"
        json_filename = f"{charts.title}.json"  
        csv_filename = f"{charts.title}.csv"
        # html_filename = f"{charts.title}.html"
        # save_path = os.path.join(settings.BASE_DIR, 'myapp','templates','orgcharts')
        # Construct the path to the file to be deleted
        csv_file_path = os.path.join(custom_directory, csv_filename)
        # output_csv_path = os.path.join("output_csv", csv_filename)
        json_file_path = os.path.join(json_directory, json_filename)

        # html_file_path = os.path.join(save_path, html_filename)
        # Create a FileSystemStorage instance
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)

        # Check if the file exists before attempting to delete
        if fs.exists(csv_file_path):
            fs.delete(csv_file_path)
        # if fs.exists(output_csv_path):
        #     fs.delete(output_csv_path)
        if fs.exists(json_file_path):
            fs.delete(json_file_path)
        # if os.path.isfile(html_file_path):
        #     os.remove(html_file_path)
        
        charts.delete()
        current_url = request.META.get('HTTP_REFERER')
    except:
        return JsonResponse({'error': "Error Deleting the Chart File"}, status=500)
        # Redirect the user back to the current page
    return redirect(current_url)
    
@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def manage_access(request):
    if request.method == 'POST':
        try:
            chart_ids = request.POST.getlist('chart_ids')
            user_id = request.POST.get('user')
            operation = request.POST.get('operation')
            duration_days = int(request.POST.get('duration', 30))

            user = User.objects.get(pk=user_id)
            for chart_id in chart_ids:
                chart_obj = chart.objects.get(pk=chart_id)
                if operation == 'add':
                    # Grant access for the specified duration
                    ChartAccess.grant_access(user, chart_obj, duration_days)
                    chart_obj.allowed_users.add(user) #need to update
                elif operation == 'remove':
                    # Remove access for the user
                    ChartAccess.revoke_access(user, chart_obj)
                    chart_obj.allowed_users.remove(user) #need to update


            messages.success(request, 'Action successful!')
        except Exception as e:
            messages.error(request, f'{e} Action failed.')  # Optional error message
            
        current_url = request.META.get('HTTP_REFERER')
        return redirect(current_url)

    # If the request method is not POST, render the form
    available_charts = chart.objects.all()
    available_users = User.objects.filter(is_staff=False)
    ChartAccess.remove_expired_access()
    context = {
        'available_charts': available_charts,
        'available_users': available_users,
    }

    return render(request, 'manage_orgcharts.html', context)



@login_required
def view_access(request):
    ChartAccess.remove_expired_access()
    if request.user.userprofile.is_superadmin or request.user.groups.filter(name='Admin').exists():
        available_users = User.objects.all()
    else: 
        available_users = User.objects.filter(userprofile__client_of=request.user)
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        user_per = User.objects.get(id=user_id)
        charts_with_access = chart.objects.filter(allowed_users=user_per)
        current_datetime = timezone.localtime(timezone.now())
            # Prepare data for rendering
        charts_data = []
        for chart_obj in charts_with_access:
            access = chart_obj.accesses.filter(user=user_per).first()
            if access:
                access_grant_time = access.access_grant_time
                expiration_time = access.expiration_time
                days_remaining = max((expiration_time - current_datetime).days, 0)
            else:
                access_grant_time = None
                expiration_time = None
                days_remaining = None

            charts_data.append({
                'chart': chart_obj,
                'access_grant_time': access_grant_time,
                'expiration_time': expiration_time,
                'days_remaining': days_remaining
            })
        return render(request, 'permitted_orgcharts.html', {'charts_data': charts_data,'user_per':user_per,'available_users': available_users})
    
    return render(request,'permitted_orgcharts.html',{'available_users': available_users})
@login_required
def download_all_csv(request):
    import tempfile
    # Define base headers and row keys
    base_headers = [
        'Organization Name', 'Domain', 'Employee Range', 'Department', 'Industry',
        'Solution Offered', 'Primary Address', 'City/Town', 'State/Province',
        'Country/Region', 'Postal Code', 'Seniority Level', 'Job Function',
        'Full Name', 'Designation', 'Linkedin Profile', 'Public Profile',
        'Email Address', 'Boardline Number'
    ]
    base_row_fields = [
        'organization_name', 'domain', 'employee_range', 'department', 'industry',
        'solution_offered', 'primary_address', 'city', 'state',
        'country', 'postal_code', 'seniority_level', 'job_function',
        'name', 'designation', 'linkedin', 'other',
        'email_id', 'boardline_number'
    ]
    import zipfile

    # Superadmin/Admin: download all CSVs as before
    if request.user.userprofile.is_superadmin or request.user.groups.filter(name='Admin').exists():
        src_folder = os.path.join(settings.MEDIA_ROOT, "csv_files")
        charts = chart.objects.all()
        with tempfile.TemporaryDirectory() as temp_dir:
            for chart_ind in charts:
                src_file_path = os.path.join(src_folder, f"{chart_ind.title}.csv")
                if os.path.exists(src_file_path):
                    dst_file_path = os.path.join(temp_dir, f"{chart_ind.title}.csv")
                    shutil.copy2(src_file_path, dst_file_path)
            # Create a zip of all CSVs directly (without including the zip file itself)
            zip_file_path = os.path.join(temp_dir, "all_charts.zip")
            shutil.make_archive(zip_file_path[:-4], 'zip', temp_dir)
            # Instead of zipping the temp_dir (which includes the zip), zip only the CSVs
            zip_buffer_path = os.path.join(temp_dir, "all_charts_final.zip")
            with zipfile.ZipFile(zip_buffer_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in os.listdir(temp_dir):
                    if filename.endswith('.csv'):
                        file_path = os.path.join(temp_dir, filename)
                        zipf.write(file_path, arcname=filename)
            with open(zip_buffer_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="all_charts.zip"'
            return response

    # Normal user: download allowed charts as CSVs generated from JSON (node_type='Person' only)
    else:
        allowed_charts = chart.objects.filter(allowed_users=request.user)
        chart_data_dir = os.path.join(settings.MEDIA_ROOT, "chart_data")
        with tempfile.TemporaryDirectory() as temp_dir:
            for chart_obj in allowed_charts:
                json_file_path = os.path.join(chart_data_dir, f"{chart_obj.title}.json")
                if not os.path.exists(json_file_path):
                    continue
                with open(json_file_path, "r", encoding="utf-8") as f:
                    try:
                        chart_json = json.load(f)
                        nodes = chart_json.get("nodes_json", [])
                    except Exception:
                        continue

                # Filter only node_type == 'Person'
                visible_data = [item for item in nodes if item.get('node_type') == 'Person']

                # Determine dynamic headers
                include_personal_number = any(item.get('personal_number') for item in visible_data)
                custom_fields_count = 0
                for item in visible_data:
                    for i in range(1, 5):
                        if any(item.get(f) for f in [
                            f'custom_heading{i}', f'custom_content{i}', f'custom_link{i}', f'custom_date{i}'
                        ]):
                            if i > custom_fields_count:
                                custom_fields_count = i

                # Build headers
                headers = base_headers[:]
                if include_personal_number:
                    headers.append('Personal Number')
                for i in range(1, custom_fields_count + 1):
                    headers.extend([
                        f'Custom Heading {i}', f'Custom Content {i}', f'Custom Link {i}', f'Custom Date {i}'
                    ])

                # Build CSV rows
                csv_data = [headers]
                for item in visible_data:
                    row = [item.get(key, '') for key in base_row_fields]
                    if include_personal_number:
                        row.append(item.get('personal_number', ''))
                    for i in range(1, custom_fields_count + 1):
                        row.extend([
                            item.get(f'custom_heading{i}', ''),
                            item.get(f'custom_content{i}', ''),
                            item.get(f'custom_link{i}', ''),
                            item.get(f'custom_date{i}', ''),
                        ])
                    csv_data.append(row)

                # Write CSV file
                csv_file_path = os.path.join(temp_dir, f"{chart_obj.title}.csv")
                with open(csv_file_path, "w", encoding="utf-8", newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    for row in csv_data:
                        writer.writerow([(str(cell) if cell is not None else '').replace('"', '""') for cell in row])

            # Zip all CSVs (exclude any zip files)
            zip_buffer_path = os.path.join(temp_dir, "user_charts_final.zip")
            with zipfile.ZipFile(zip_buffer_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in os.listdir(temp_dir):
                    if filename.endswith('.csv'):
                        file_path = os.path.join(temp_dir, filename)
                        zipf.write(file_path, arcname=filename)
            with open(zip_buffer_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="all_charts.zip"'
                return response

@login_required
def download_source(request, chart_id):
    if request.user.userprofile.is_superadmin or request.user.groups.filter(name='Admin').exists():
        chart_instance = get_object_or_404(chart, pk=chart_id)
    else:
        chart_instance = get_object_or_404(chart, pk=chart_id, allowed_users=request.user)

    file_path = os.path.join(settings.MEDIA_ROOT,"csv_files",f"{chart_instance.title}.csv")

    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{chart_instance.title}.csv"'
            return response
    else:
        raise Http404("CSV file not found")

@login_required
@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def upload_image(request):
    if request.method == 'POST':
        image_files = request.FILES.getlist('images')
        for image_file in image_files:
            image_instance = Image(image=image_file)
            image_instance.save()
        # run_collectstatic()
        return redirect('upload_image')
    
    # Get all images ordered by upload date (newest first)
    images_list = Image.objects.all().order_by('-uploaded_at')
    image_count = images_list.count()
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get page number from request, default to 1
    page = request.GET.get('page', 1)
    
    # Set number of images per page (adjust as needed)
    images_per_page = request.GET.get('per_page', 20)  # Allow users to choose per page count
    try:
        images_per_page = int(images_per_page)
        if images_per_page not in [10, 20, 50, 100]:  # Allowed values
            images_per_page = 20
    except (ValueError, TypeError):
        images_per_page = 20
    
    # Create Paginator object
    paginator = Paginator(images_list, images_per_page)
    
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        images = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        images = paginator.page(paginator.num_pages)
    
    context = {
        'images': images,
        'image_count': image_count,
        'images_per_page': images_per_page,
        'page_range': paginator.get_elided_page_range(images.number, on_each_side=2, on_ends=1),
    }
    
    return render(request, 'upload_image.html', context)


@require_POST
@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def delete_images(request):
    data = json.loads(request.body)
    image_ids = data.get('image_ids', [])
    try:    
        for image_id in image_ids:
            # Assuming Image model has a field named 'image' which stores the image path
            image_id = 'img/user/' + image_id  
            image = get_object_or_404(Image, image=image_id)
            image_path = image.image.path
            # print(image_path)
            
            # Delete the image from the media directory
            if os.path.exists(image_path):
                os.remove(image_path)
            # new_image_path = image_path.replace(os.sep + 'media' + os.sep + 'user_uploaded' + os.sep, os.sep + 'static' + os.sep )
            # if os.path.exists(new_image_path):
            #     os.remove(new_image_path)
            
            # Delete the image from the database
            image.delete()

        return JsonResponse({'message': 'Images deleted successfully'})
    except Exception as e:
        return JsonResponse({'message': f'Error deleting images{e}'})

@csrf_exempt 
@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def export_image_urls(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_image_ids = data.get('image_ids', [])
        
       # Prepend 'user_uploaded/' to each image_id
        selected_image_ids = ['img/user/' + image_id for image_id in selected_image_ids]
        
        # Fetch selected images from the database based on image IDs
        images = Image.objects.filter(image__in=selected_image_ids)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="selected_image_urls.csv"'

        writer = csv.writer(response)
        writer.writerow(['Title', 'Image URL'])  # Write header row

        for image in images:
            # Get the image ID (filename)
            image_title = image.filename()
            # Construct the full image URL
            image_url = request.build_absolute_uri(image.image.url)
            # image_url = image_url.replace('/media/user_uploaded/', '/static/')
            image_url = image_url.replace('http://', 'https://')
            writer.writerow([image_title, image_url])  # Write image ID and image URL for each image


        return response
    else:
        return HttpResponse(status=405)

# def run_collectstatic():
#     try:
#         subprocess.check_call(['python3', 'manage.py', 'collectstatic', '--noinput'])
#         return True  # Collectstatic command executed successfully
#     except subprocess.CalledProcessError as e:
#         return False  # Error occurred while executing collectstatic command

@user_passes_test(lambda user: user.is_staff)
def view_profile(request):
    available_users = User.objects.filter(is_staff=False) # Fetch all users
    selected_user = None
    # if request.method == 'POST':
    #     user_id = request.POST.get('user_id')  # Assuming 'username' is the name of your select box field
    #     user = User.objects.get(id=user_id)
    #     selected_user, created = UserProfile.objects.get_or_create(user=user)
    #     if created:
    #         selected_user.past_company1 = ""
    #         selected_user.past_company2 = ""
    #         # Initialize other fields similarly
    #         selected_user.save()
        # return render(request, 'profile.html', {'user_profile': user_profile})
    
    return render(request, 'profile.html', {'available_users': available_users, 'selected_user': selected_user,'edit_mode':False})


@user_passes_test(lambda user: user.is_staff and user.groups.filter(name='Admin'))
def edit_profile(request):
    available_users = User.objects.filter(is_staff=False)
    if request.method == 'POST':
        if request.POST.get('edit_form') == 'True': 
            user_id = request.POST.get('user_id')
            selected_user = None

            if user_id:
                user = User.objects.get(id=user_id)
                selected_user, created = UserProfile.objects.get_or_create(user=user)
                if created:

                    selected_user.past_company1 = ""
                    selected_user.past_company2 = ""
                    # Initialize other fields similarly
                    selected_user.save()
                # Handle form submission and update profile fields manually
        else:
            user_id = request.POST.get('user_id')
            user = User.objects.get(id=user_id)
            selected_user, created = UserProfile.objects.get_or_create(user=user)
            selected_user.past_company1 = request.POST.get('past_company1')
            selected_user.past_company2 = request.POST.get('past_company2')
            selected_user.past_company3 = request.POST.get('past_company3')
            selected_user.past_company4 = request.POST.get('past_company4')
            selected_user.past_company5 = request.POST.get('past_company5')
            selected_user.educational_institute1 = request.POST.get('educational_institute1')
            selected_user.educational_institute2 = request.POST.get('educational_institute2')
            selected_user.educational_institute3 = request.POST.get('educational_institute3')
            selected_user.city = request.POST.get('city')
            selected_user.state = request.POST.get('state')
            selected_user.country = request.POST.get('country')
            # Update other fields similarly
            
            # Save the updated profile
            selected_user.save()
            
        return render(request, 'profile.html', {'available_users': available_users, 'selected_user': selected_user, 'edit_mode': True})
    
    return redirect('view_profile')
    # return render(request, 'profile.html', {'available_users': available_users, 'selected_user': selected_user, 'edit_mode': True})

@login_required
def request_orgchart(request):
    success_message = None
    if request.method == 'POST':
        industry_type = request.POST.get('industry_type')
        company_name = request.POST.get('company_name')
        department_name = request.POST.get('department_name')
        designation = request.POST.get('designation')
        company_websites = request.POST.get('company_url')
        location = request.POST.get('location')
        required_authorities = request.POST.get('required_authorities')
        extra_insights = request.POST.get('extra_insights')
        number_inclusion = request.POST.get('number_inclusion') == 'on'
        try:
            myuser = User.objects.get(pk=request.user.id)
            subject = "New OrgChart Request!!"
            
            # User confirmation email
            user_context = {
                'name': myuser.first_name,
                'user': myuser,
                'industry_type': industry_type,
                'company_name': company_name,
                'department_name': department_name,
                'designation': designation,
                'company_websites': company_websites,
                'location': location,
                'required_authorities': required_authorities,
                'number_inclusion': number_inclusion,
                'extra_insights': extra_insights,
            }
            user_html_content = render_to_string('request_confirmation_email.html', user_context)
            
            user_email = EmailMessage(
                subject=subject,
                body=user_html_content,
                from_email=settings.EMAIL_SENDER_ID,
                to=[myuser.email]
            )
            user_email.content_subtype = 'html'
            user_email.send(fail_silently=True)            # Admin notification email
            admin_context = {
                'user': myuser,  # Pass the full user object
                'user_name': f"{myuser.first_name} {myuser.last_name}".strip() or myuser.username,
                'user_email': myuser.email,
                'industry_type': industry_type,
                'company_name': company_name,
                'department_name': department_name,
                'designation': designation,
                'company_websites': company_websites,
                'location': location,
                'required_authorities': required_authorities,
                'number_inclusion': number_inclusion,
                'extra_insights': extra_insights,
            }
            admin_html_content = render_to_string('admin_request_notification_email.html', admin_context)
            
            admin_email = EmailMessage(
                subject=f"New OrgChart Request from {myuser.first_name}",
                body=admin_html_content,
                from_email=settings.EMAIL_SENDER_ID,
                to=[settings.EMAIL_SENDER_ID]
            )
            admin_email.content_subtype = 'html'
            admin_email.send(fail_silently=True)
            messages.success(request, "Form submitted successfully!")
            return redirect('request_orgchart')
        except Exception as e:
            messages.error(request, "An error occurred during form submission. Please try again.")



    return render(request, 'request_orgchart.html',{'success_message': success_message})


@user_passes_test(lambda user: user.is_staff)
def client_details(request):
    if request.method == 'POST':
        try:
            industry_type = request.POST.get('industry_type')
            company_name = request.POST.get('company_name')
            department_name = request.POST.get('department_name')
            designation = request.POST.get('designation')
            company_websites = request.POST.get('company_url')
            location = request.POST.get('location')
            required_authorities = request.POST.get('required_authorities')
            extra_insights = request.POST.get('extra_insights')
            number_inclusion = request.POST.get('number_inclusion') == 'on'
            client_user_id = request.POST.get('client_user')
            employee_range = request.POST.get('employee_range')
            total_charts_access = request.POST.get('total_charts_access')
            currency = request.POST.get('currency')
            amt_in_currency = request.POST.get('value_in_currency')
            amt_in_inr = request.POST.get('value_in_inr')

            # Retrieve selected user (client)
            client_user = User.objects.get(id=client_user_id)

            if client_user:
                client = ClientLead(
                    user=client_user,
                    lead_of = request.user,
                    org_name = company_name ,
                    org_website =  company_websites,
                    designations =  designation,
                    dept_names =  department_name,
                    industry_types =  industry_type,
                    locations =  location,
                    total_charts = total_charts_access,
                    required_authorities = required_authorities,
                    extra_insighhts = extra_insights,
                    include_contacts = number_inclusion,
                    emp_range = employee_range,
                    currency = currency,
                    amount_in_currency = amt_in_currency,
                    amount_in_inr = amt_in_inr,
                )
                client.save()
                messages.success(request,'Entry Saved Successfully!')
            return redirect('client_details')
        except:
            messages.error(request,'Some Error Occured!')
            return redirect('client_details')
    try:
        if request.user.userprofile.is_superadmin:
            available_users = UserProfile.objects.all()
        else:      
            # Filter clients based on the retrieved UserProfile
            available_users = UserProfile.objects.filter(client_of=request.user)
    except UserProfile.DoesNotExist:
        available_users = None
    # available_users = User.objects.filter(is_staff=False)
    return render(request,'client_details_form.html', {'available_users': available_users })

@user_passes_test(lambda user: user.is_staff)
def client_details_show(request):
    try:
        if request.user.userprofile.is_superadmin:
            leads_data = ClientLead.objects.all()
        else:
            leads_data = ClientLead.objects.filter(lead_of=request.user)
    except  ClientLead.DoesNotExist:
        leads_data  = None
    return render(request,'client_details_show.html', {'leads_data':leads_data })

@user_passes_test(lambda user: user.is_staff)
def update_lead_status(request, lead_id):
    try:
        lead = get_object_or_404(ClientLead, pk=lead_id)
        if request.method == 'POST':
            if 'revenue_share' in request.POST:
                revenue_share = float(request.POST['revenue_share'])
                lead.revenue_share = revenue_share
                lead.save()
            else:
                new_sow = request.POST.get('sow_status')
                new_payment = request.POST.get('payment_status')
                notes = request.POST.get('notes')
                lead.sow_status, lead.payment_status, lead.notes = new_sow, new_payment, notes
                lead.save()

            return redirect('client_details_show')
    except Exception as e:
        return redirect('client_details_show')
    return redirect('client_details_show')

@user_passes_test(lambda user: user.userprofile.is_superadmin)
def delete_lead(request, lead_id):
    try:
        lead = get_object_or_404(ClientLead, pk=lead_id)
        lead.delete()
        return redirect('client_details_show')  
    except ClientLead.DoesNotExist:
        return redirect('client_details_show')  
    except Exception as e:
        return redirect('client_details_show')  
    
@user_passes_test(lambda user: user.userprofile.is_superadmin)
def assign_client_to_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        client_id = request.POST.get('client')
        action = request.POST.get('action')
        clients_list = None
        if action == 'assign':
            if user_id == client_id:
                messages.error(request,"User and client cannot be the same. Please select different users." ) 
            else:
                try:
                    salesuser = User.objects.get(pk=user_id)
                    client = User.objects.get(pk=client_id)

                    # Assign client to user
                    client_profile, created = UserProfile.objects.get_or_create(user=client)
                    client_profile.client_of = salesuser 
                    client_profile.save()

                    messages.success(request, f"Client '{client.username}' assigned to user '{salesuser.username}' successfully.")
                except User.DoesNotExist:
                    messages.error(request,"Invalid user or client selected.") 

        elif action == 'remove':
            try:
                client = User.objects.get(pk=client_id)
                salesuser = User.objects.get(pk=user_id)
                # Remove client from the user's profile
                client_profile = UserProfile.objects.get(user=client)
                client_profile.client_of = None
                client_profile.save()

                messages.success(request, f"Client removed successfully from user '{salesuser.username}'.")
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                messages.error(request, "Invalid user selected.")
        
        elif action == 'view':
            try:
                salesuser = User.objects.get(pk=user_id)
                clients_list = UserProfile.objects.filter(client_of=salesuser)
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                messages.error(request, "Invalid user selected.")
        # Re-render the form with error message
        users = User.objects.filter(is_staff=True)
        clients = User.objects.filter(is_staff=False)  # Exclude selected user from clients
        return render(request, 'assign_clients.html', {'users': users, 'clients': clients,'clients_list':clients_list, 'salesuser':salesuser})

    else:
        # Render the form for GET requests
        users = User.objects.filter(is_staff=True)
        clients = User.objects.filter(is_staff=False)
        return render(request, 'assign_clients.html', {'users': users, 'clients': clients,'clients_list':None})


@user_passes_test(lambda user: user.userprofile.is_superadmin)
def user_operations(request):
    if request.method == 'POST':
        operation = request.POST.get('operation')

        if operation == 'create_user':
            # Process user creation
            username = request.POST.get('username')
            password = request.POST.get('password')
            if username and password:
                if User.objects.filter(username=username):
                    messages.error(request, "Username already exist! Please try some other username.")
                    return redirect('user_operations')
                
                if len(username)>20:
                    messages.error(request, "Username must be under 20 charcters!!")
                    return redirect('user_operations')
                
                if not username.isalnum():
                    messages.error(request, "Username must be Alpha-Numeric!!")
                    return redirect('user_operations')


                # Create user with hashed password
                user = User.objects.create(username=username, password=make_password(password))
                user_profile = UserProfile(user=user)
                user_profile.is_superadmin = False
                user_profile.save()
                demo_charts = chart.objects.filter(title__icontains='demo')
                for demo_chart in demo_charts:
                    demo_chart.allowed_users.add(user)
                    demo_chart.save()
                user.groups.add(Group.objects.get(name='Subscriber'))
                # Optionally, you can redirect to a success URL
                messages.success(request,'User Created Successfully!')
                return redirect('user_operations')

        elif operation == 'deactivate_user':
            # Process user deactivation
            user_id = request.POST.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(pk=user_id)
                    user.is_active = False
                    user.save()
                    # Optionally, you can redirect to a success URL
                    messages.success(request,'User Deactivated Successfully')
                    return redirect('user_operations')
                except User.DoesNotExist:
                    # Handle the case where user ID does not exist
                    pass  # Redirect or render an error message

        elif operation == 'assign_user_groups':
            # Process user group assignment
            user_id = request.POST.get('user')
            group_id = request.POST.get('groups')
            if user_id and group_id:
                try:
                    user = User.objects.get(pk=user_id)
                    user.groups.set(group_id)
                    group = Group.objects.get(pk=group_id) 
                    if group.name =='Admin' or group.name=='Sales Partner':
                        user.is_staff = True
                    else:
                        user.is_staff = False
                    user.save()
                    # Optionally, you can redirect to a success URL
                    messages.success(request,'User Modified Successfully!')
                    return redirect('user_operations')
                except User.DoesNotExist:
                    # Handle the case where user ID does not exist
                    pass  # Redirect or render an error message

    # Fetch users and groups to populate select options
    users = User.objects.all()
    groups = Group.objects.all()

    return render(request, 'user_operations.html', {'users': users, 'groups': groups})


def filter_users_by_group(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        group_id = request.GET.get('group_id')
        print(group_id)
        if group_id:
            # Retrieve users belonging to the selected group
            users = User.objects.filter(groups__id=group_id)

            # Prepare data to send back as JSON
            users_data = [{'id': user.id, 'username': user.username} for user in users]

            return JsonResponse({'users': users_data})
    
    # If no valid data or request method, return empty response or error
    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required
def check_login(request):
    return JsonResponse({'isLoggedIn': True})

def marketplace_dash(request):
    from .models import MarketplaceSettings
    for company in chart.objects.all():
        # print(company.min_employees, company.max_employees)
        company.save()  # This will trigger the updated save method
    # charts_data = [{'chart': chart, 'last_updated': chart.last_updated, } for chart in chart.objects.all()]
    charts_data = chart.objects.all()
    marketplace_settings = MarketplaceSettings.get_current_settings()

    # Get all unique countries and industries for filters
    all_countries = [
    "Afghanistan", "Albania", "Algeria", "American Samoa", "Andorra", "Angola", "Anguilla", "Antarctica",
    "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia",
    "Bosnia and Herzegovina", "Botswana", "Brazil", "British Indian Ocean Territory", "British Virgin Islands",
    "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands",
    "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos Islands", "Colombia", "Comoros",
    "Cook Islands", "Costa Rica", "Croatia", "Cuba", "Curacao", "Cyprus", "Czech Republic", "Democratic Republic of the Congo",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands", "Faroe Islands", "Fiji", "Finland",
    "France", "French Polynesia", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland",
    "Grenada", "Guam", "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hong Kong",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Isle of Man", "Israel", "Italy", "Ivory Coast",
    "Jamaica", "Japan", "Jersey", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos",
    "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macau", "Macedonia",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mayotte", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Montserrat", "Morocco", "Mozambique",
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "Netherlands Antilles", "New Caledonia", "New Zealand",
    "Nicaragua", "Niger", "Nigeria", "Niue", "North Korea", "Northern Mariana Islands", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Pitcairn", "Poland",
    "Portugal", "Puerto Rico", "Qatar", "Republic of the Congo", "Reunion", "Romania", "Russia", "Rwanda",
    "Saint Barthelemy", "Saint Helena", "Saint Kitts and Nevis", "Saint Lucia", "Saint Martin", "Saint Pierre and Miquelon",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Svalbard and Jan Mayen",
    "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tokelau",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu",
    "U.S. Virgin Islands", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Vanuatu", "Vatican", "Venezuela", "Vietnam", "Wallis and Futuna", "Western Sahara", "Yemen", "Zambia", "Zimbabwe"
    ]
    all_industries = [
    "Accounting", "Airlines/Aviation", "Alternative Dispute Resolution", "Alternative Medicine", "Animation",
    "Apparel & Fashion", "Architecture & Planning", "Arts and Crafts", "Automotive", "Aviation & Aerospace",
    "Banking", "Biotechnology", "Broadcast Media", "Building Materials", "Business Supplies and Equipment",
    "Capital Markets", "Chemicals", "Civic & Social Organization", "Civil Engineering", "Commercial Real Estate",
    "Computer & Network Security", "Computer Games", "Computer Hardware", "Computer Networking", "Computer Software",
    "Construction", "Consumer Electronics", "Consumer Goods", "Consumer Services", "Cosmetics", "Dairy", "Defense & Space",
    "Design", "E-Learning", "Education Management", "Electrical/Electronic Manufacturing", "Entertainment",
    "Environmental Services", "Events Services", "Executive Office", "Facilities Services", "Farming", "Financial Services",
    "Fine Art", "Fishery", "Food & Beverages", "Food Production", "Fund-Raising", "Furniture", "Gambling & Casinos",
    "Glass, Ceramics & Concrete", "Government Administration", "Government Relations", "Graphic Design",
    "Health, Wellness and Fitness", "Higher Education", "Hospital & Health Care", "Hospitality", "Human Resources",
    "Import and Export", "Individual & Family Services", "Industrial Automation", "Information Services",
    "Information Technology and Services", "Insurance", "International Affairs", "International Trade and Development",
    "Internet", "Investment Banking", "Investment Management", "Judiciary", "Law Enforcement", "Law Practice",
    "Legal Services", "Legislative Office", "Leisure, Travel & Tourism", "Libraries", "Logistics and Supply Chain",
    "Luxury Goods & Jewelry", "Machinery", "Management Consulting", "Maritime", "Market Research", "Marketing and Advertising",
    "Mechanical or Industrial Engineering", "Media Production", "Medical Devices", "Medical Practice", "Mental Health Care",
    "Military", "Mining & Metals", "Motion Pictures and Film", "Museums and Institutions", "Music", "Nanotechnology",
    "Newspapers", "Nonprofit Organization Management", "Oil & Energy", "Online Media", "Outsourcing/Offshoring",
    "Package/Freight Delivery", "Packaging and Containers", "Paper & Forest Products", "Performing Arts", "Pharmaceuticals",
    "Philanthropy", "Photography", "Plastics", "Political Organization", "Primary/Secondary Education", "Printing",
    "Professional Training & Coaching", "Program Development", "Public Policy", "Public Relations and Communications",
    "Public Safety", "Publishing", "Railroad Manufacture", "Ranching", "Real Estate", "Recreational Facilities and Services",
    "Religious Institutions", "Renewables & Environment", "Research", "Restaurants", "Retail", "Security and Investigations",
    "Semiconductors", "Shipbuilding", "Sporting Goods", "Sports", "Staffing and Recruiting", "Supermarkets",
    "Telecommunications", "Textiles", "Think Tanks", "Tobacco", "Translation and Localization", "Transportation/Trucking/Railroad",
    "Urgent Care", "Utilities", "Venture Capital & Private Equity", "Veterinary", "Warehousing", "Wholesale", "Wine and Spirits",
    "Wireless", "Writing and Editing"
    ]    # Get cart item count for authenticated users
    cart_item_count = 0
    if request.user.is_authenticated:
        try:
            user_cart = Cart.objects.get(user=request.user)
            cart_item_count = user_cart.get_total_items()
        except Cart.DoesNotExist:
            cart_item_count = 0

    return render(request, 'marketplace.html', {
        'charts_data': charts_data,
        'cart_item_count': cart_item_count,
        'all_countries': json.dumps(list(all_countries)),
        'all_industries': json.dumps(list(all_industries)),
        'marketplace_settings': marketplace_settings
    })



def create_payment(request, chart_id):
    # TODO: Update this function to use Razorpay like the cart checkout
    # For now, redirect to cart-based checkout
    selected_chart = get_object_or_404(chart, pk=chart_id)
    
    # Add chart to cart and redirect to cart checkout
    cart, cart_created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, 
        chart=selected_chart,
        defaults={'quantity': 1}    )
    
    if item_created:
        messages.success(request, f'{selected_chart.title} added to cart!')
    else:
        messages.info(request, f'{selected_chart.title} is already in your cart!')
    
    return redirect('cart_checkout')


def execute_payment(request):
    # Redirect single-item payments to cart-based approach
    messages.info(request, 'Please use the cart-based checkout for payments.')
    return redirect('marketplace_dash')

def payment_success(request):
    order = Order.objects.filter(user=request.user).latest('created_at')
    
    # Send confirmation email with invoice
    send_order_confirmation_email(order)
    
    context = {
        'payment_id': order.razorpay_payment_id,
        'order_id': order.razorpay_order_id,
        'total_amount': order.total_amount,
        'transaction_date': order.created_at,
        'purchased_items': order.items.all()
    }
    return render(request, 'cart_success.html', context)

def payment_cancel(request):
    return redirect('marketplace_dash')

@user_passes_test(lambda user: user.userprofile.is_superadmin)
def admin_marketplace(request):
    from .models import MarketplaceSettings
    charts_data = chart.objects.all()
    marketplace_settings = MarketplaceSettings.get_current_settings()
    countries = [
    "Afghanistan", "Albania", "Algeria", "American Samoa", "Andorra", "Angola", "Anguilla", "Antarctica",
    "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia",
    "Bosnia and Herzegovina", "Botswana", "Brazil", "British Indian Ocean Territory", "British Virgin Islands",
    "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands",
    "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos Islands", "Colombia", "Comoros",
    "Cook Islands", "Costa Rica", "Croatia", "Cuba", "Curacao", "Cyprus", "Czech Republic", "Democratic Republic of the Congo",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands", "Faroe Islands", "Fiji", "Finland",
    "France", "French Polynesia", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland",
    "Grenada", "Guam", "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hong Kong",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Isle of Man", "Israel", "Italy", "Ivory Coast",
    "Jamaica", "Japan", "Jersey", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos",
    "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macau", "Macedonia",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mayotte", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Montserrat", "Morocco", "Mozambique",
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "Netherlands Antilles", "New Caledonia", "New Zealand",
    "Nicaragua", "Niger", "Nigeria", "Niue", "North Korea", "Northern Mariana Islands", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Pitcairn", "Poland",
    "Portugal", "Puerto Rico", "Qatar", "Republic of the Congo", "Reunion", "Romania", "Russia", "Rwanda",
    "Saint Barthelemy", "Saint Helena", "Saint Kitts and Nevis", "Saint Lucia", "Saint Martin", "Saint Pierre and Miquelon",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Svalbard and Jan Mayen",
    "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tokelau",
    "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu",
    "U.S. Virgin Islands", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Vanuatu", "Vatican", "Venezuela", "Vietnam", "Wallis and Futuna", "Western Sahara", "Yemen", "Zambia", "Zimbabwe"
    ]
    industries = [
    "Accounting", "Airlines/Aviation", "Alternative Dispute Resolution", "Alternative Medicine", "Animation",
    "Apparel & Fashion", "Architecture & Planning", "Arts and Crafts", "Automotive", "Aviation & Aerospace",
    "Banking", "Biotechnology", "Broadcast Media", "Building Materials", "Business Supplies and Equipment",
    "Capital Markets", "Chemicals", "Civic & Social Organization", "Civil Engineering", "Commercial Real Estate",
    "Computer & Network Security", "Computer Games", "Computer Hardware", "Computer Networking", "Computer Software",
    "Construction", "Consumer Electronics", "Consumer Goods", "Consumer Services", "Cosmetics", "Dairy", "Defense & Space",
    "Design", "E-Learning", "Education Management", "Electrical/Electronic Manufacturing", "Entertainment",
    "Environmental Services", "Events Services", "Executive Office", "Facilities Services", "Farming", "Financial Services",
    "Fine Art", "Fishery", "Food & Beverages", "Food Production", "Fund-Raising", "Furniture", "Gambling & Casinos",
    "Glass, Ceramics & Concrete", "Government Administration", "Government Relations", "Graphic Design",
    "Health, Wellness and Fitness", "Higher Education", "Hospital & Health Care", "Hospitality", "Human Resources",
    "Import and Export", "Individual & Family Services", "Industrial Automation", "Information Services",
    "Information Technology and Services", "Insurance", "International Affairs", "International Trade and Development",
    "Internet", "Investment Banking", "Investment Management", "Judiciary", "Law Enforcement", "Law Practice",
    "Legal Services", "Legislative Office", "Leisure, Travel & Tourism", "Libraries", "Logistics and Supply Chain",
    "Luxury Goods & Jewelry", "Machinery", "Management Consulting", "Maritime", "Market Research", "Marketing and Advertising",
    "Mechanical or Industrial Engineering", "Media Production", "Medical Devices", "Medical Practice", "Mental Health Care",
    "Military", "Mining & Metals", "Motion Pictures and Film", "Museums and Institutions", "Music", "Nanotechnology",
    "Newspapers", "Nonprofit Organization Management", "Oil & Energy", "Online Media", "Outsourcing/Offshoring",
    "Package/Freight Delivery", "Packaging and Containers", "Paper & Forest Products", "Performing Arts", "Pharmaceuticals",
    "Philanthropy", "Photography", "Plastics", "Political Organization", "Primary/Secondary Education", "Printing",
    "Professional Training & Coaching", "Program Development", "Public Policy", "Public Relations and Communications",
    "Public Safety", "Publishing", "Railroad Manufacture", "Ranching", "Real Estate", "Recreational Facilities and Services",
    "Religious Institutions", "Renewables & Environment", "Research", "Restaurants", "Retail", "Security and Investigations",
    "Semiconductors", "Shipbuilding", "Sporting Goods", "Sports", "Staffing and Recruiting", "Supermarkets",
    "Telecommunications", "Textiles", "Think Tanks", "Tobacco", "Translation and Localization", "Transportation/Trucking/Railroad",
    "Urgent Care", "Utilities", "Venture Capital & Private Equity", "Veterinary", "Warehousing", "Wholesale", "Wine and Spirits",
    "Wireless", "Writing and Editing"
    ]
    employee_ranges = [
    "1-10",
    "11-50",
    "51-200",
    "201-500",
    "501-1000",
    "1001-5000",
    "5001-10000",
    "10001+"
    ]
    return render(request, 'admin_marketplace.html', {
        'charts_data': charts_data, 
        'industries': industries, 
        'countries': countries, 
        'employee_ranges': employee_ranges,
        'marketplace_settings': marketplace_settings
    })

@require_POST
def update_chart(request, chart_id):
    selected_chart = get_object_or_404(chart, id=chart_id)

    price = request.POST.get('price')
    last_updated = parse_date(request.POST.get('last_updated'))
    country = request.POST.get('country')
    industry = request.POST.get('industry')
    employee_range = request.POST.get('employee_range')
    status = request.POST.get('status')

    # Update chart fields with the new data
    selected_chart.price = price
    selected_chart.last_updated = last_updated
    selected_chart.country = country
    selected_chart.industry = industry
    selected_chart.employee_range = employee_range
    selected_chart.mp_status = status

    # Save the updated chart
    selected_chart.save()

    messages.success(request, 'Chart details updated successfully!')
    return redirect('admin_marketplace')  # Replace 'chart-list' with the name of your chart listing view


@require_POST
def update_marketplace_settings(request):
    """Update marketplace settings including sample link"""
    from .models import MarketplaceSettings
    
    # Get or create marketplace settings
    settings = MarketplaceSettings.get_current_settings()
    
    # Update settings from form data
    settings.sample_link = request.POST.get('sample_link', settings.sample_link)
    settings.sample_title = request.POST.get('sample_title', settings.sample_title)
    settings.sample_description = request.POST.get('sample_description', settings.sample_description)
    
    # Save the updated settings
    settings.save()
    
    messages.success(request, 'Marketplace settings updated successfully!')
    return redirect('admin_marketplace')


# ======== CART FUNCTIONALITY ========

@login_required
def view_cart(request):
    """View the current user's cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total_price = cart.get_total_price()
    total_items = cart.get_total_items()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,    }
    return render(request, 'cart.html', context)


@login_required
@login_required
def mini_cart(request):
    """Get mini cart data as JSON"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        items = []
        for item in cart_items:
            items.append({
                'chart_id': item.chart.id,
                'name': item.chart.title,
                'price': float(item.chart.price),
                'quantity': item.quantity,
                'country': item.chart.country,
                'industry': item.chart.industry,
                'people_count': item.chart.personCount
            })
        
        return JsonResponse({
            'items': items,
            'total': float(cart.get_total_price()),
            'count': cart.get_total_items()
        })
    except Cart.DoesNotExist:
        return JsonResponse({
            'items': [],
            'total': 0.0,
            'count': 0
        })


@login_required
@require_POST
def add_to_cart(request, chart_id):
    """Add a chart to the cart"""
    try:
        selected_chart = get_object_or_404(chart, id=chart_id, mp_status='Published')
        cart, created = Cart.objects.get_or_create(user=request.user)
          # Check if item already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, 
            chart=selected_chart,
            defaults={'quantity': 1}
        )
        
        if not item_created:
            # Item already exists, just notify user
            messages.info(request, f'{selected_chart.title} is already in your cart!')
        else:
            messages.success(request, f'{selected_chart.title} added to cart!')
            
        return JsonResponse({
            'success': True,
            'message': f'{selected_chart.title} added to cart!' if item_created else f'{selected_chart.title} is already in your cart!',
            'cart_item_count': cart.get_total_items()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding item to cart'
        })


@login_required
def remove_from_cart(request, chart_id):
    """Remove a chart from the cart"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        selected_chart = get_object_or_404(chart, id=chart_id)
        cart_item = get_object_or_404(CartItem, cart=cart, chart=selected_chart)
        
        chart_title = cart_item.chart.title
        cart_item.delete()
        
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{chart_title} removed from cart!',
                'cart_item_count': cart.get_total_items()
            })
        
        messages.success(request, f'{chart_title} removed from cart!')
        return redirect('view_cart')
        
    except Exception as e:
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error removing item from cart'
            })
        messages.error(request, 'Error removing item from cart')
        return redirect('view_cart')


@login_required
def clear_cart(request):
    """Clear all items from the cart"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        cart.items.all().delete()
        
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Cart cleared successfully!',
                'cart_count': 0
            })
            
        messages.success(request, 'Cart cleared successfully!')
    except Exception as e:
        if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error clearing cart'
            })
        messages.error(request, 'Error clearing cart')
        
    return redirect('view_cart')


@login_required
def cart_checkout(request):
    """Handle cart checkout with processing fee calculations"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        if not cart_items:
            messages.error(request, 'Your cart is empty')
            return redirect('view_cart')
            
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty')
        return redirect('view_cart')

    # Get or create customer info
    customer_info, created = CustomerInfo.objects.get_or_create(user=request.user)

    # Calculate pricing with 5.5% processing fee
    subtotal = float(cart.get_total_price())  # USD amount
    processing_fee = round(subtotal * 0.055, 2)  # 5.5% processing fee
    
    # Check for applied coupon and calculate discount
    applied_coupon_data = request.session.get('applied_coupon')
    discount_amount = 0
    coupon_obj = None
    
    if applied_coupon_data:
        try:
            coupon_obj = Coupon.objects.get(id=applied_coupon_data['id'])
            # Re-validate coupon to ensure it's still valid
            charts = [item.chart for item in cart_items]
            is_valid, message = coupon_obj.is_valid(
                user=request.user,
                order_amount=Decimal(str(subtotal)),
                charts=charts
            )
            
            if is_valid:
                discount_amount = float(coupon_obj.calculate_discount(Decimal(str(subtotal))))
                # Update session with recalculated discount
                applied_coupon_data['discount_amount'] = discount_amount
                request.session['applied_coupon'] = applied_coupon_data
            else:
                # Coupon is no longer valid, remove from session
                del request.session['applied_coupon']
                messages.warning(request, f'Coupon is no longer valid: {message}')
                applied_coupon_data = None
                coupon_obj = None
        except Coupon.DoesNotExist:
            # Coupon was deleted, remove from session
            del request.session['applied_coupon']
            messages.warning(request, 'Applied coupon is no longer available.')
            applied_coupon_data = None
    
    total_amount = subtotal + processing_fee - discount_amount
    
    order_id = None
    if request.method == 'POST':
        # Validate billing information
        if not customer_info.company_name or not customer_info.address_line1:
            messages.error(request, 'Please complete your billing information in your profile before proceeding.')
            return redirect('profile')
        
        # Initialize Razorpay client

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
              # Create Razorpay order in USD
            razorpay_order_data = {
                'amount': int(total_amount * 100),  # Amount in cents for USD (after discount)
                'currency': 'USD',
                'receipt': f'cart_{cart.id}_{int(timezone.now().timestamp())}',
                'notes': {
                    'user_id': str(request.user.id),
                    'cart_id': str(cart.id),
                    'subtotal_usd': str(subtotal),
                    'processing_fee_usd': str(processing_fee),
                    'discount_amount': str(discount_amount),
                    'total_usd': str(total_amount),
                    'currency': 'USD',
                    'coupon_code': applied_coupon_data['code'] if applied_coupon_data else '',
                    'coupon_discount': str(discount_amount) if applied_coupon_data else '0'
                }            }
            
            razorpay_order = client.order.create(data=razorpay_order_data)
            order_id = razorpay_order['id']
            
        except Exception as e:
            messages.error(request, f'Error creating payment order: {str(e)}')
            return redirect('cart_checkout')

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'customer_info': customer_info,
        'subtotal': subtotal,
        'processing_fee': processing_fee,
        'discount_amount': discount_amount,
        'total_amount': total_amount,
        'order_id': order_id,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount_in_cents': int(total_amount * 100),  # USD amount in cents (after discount)
        'currency': 'USD',
        'user_email': request.user.email,
        'user_name': request.user.get_full_name() or request.user.username,
        'applied_coupon': applied_coupon_data,
        'coupon_obj': coupon_obj,
    }
    return render(request, 'cart_checkout.html', context)

def execute_cart_payment(request):
    """Verify and execute Razorpay payment for cart items with proper billing and invoice generation"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('view_cart')
    
    try:
        # Get payment details from POST request
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        
        if not all([payment_id, order_id, signature]):
            messages.error(request, 'Payment information not found')
            return redirect('view_cart')
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        # Verify the payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Get cart and items
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = list(cart.items.all())
        
        if not cart_items:
            messages.error(request, 'Cart is empty')
            return redirect('view_cart')        # Get payment details from Razorpay
        payment_details = client.payment.fetch(payment_id)
        amount_paid_usd = payment_details['amount'] / 100  # Convert from cents to dollars
          # Get customer billing information
        customer_info = get_object_or_404(CustomerInfo, user=request.user)
        
        # Calculate amounts for USD payments with processing fee
        subtotal = float(cart.get_total_price())  # Original USD amount
        processing_fee = round(subtotal * 0.055, 2)  # 5.5% processing fee
        
        # Handle coupon if applied
        applied_coupon_data = request.session.get('applied_coupon')
        discount_amount = 0
        coupon_obj = None
        
        if applied_coupon_data:
            try:
                coupon_obj = Coupon.objects.get(id=applied_coupon_data['id'])
                discount_amount = float(applied_coupon_data['discount_amount'])
            except Coupon.DoesNotExist:
                # Coupon was deleted after application, proceed without discount
                discount_amount = 0
                applied_coupon_data = None
        
        total_amount = subtotal + processing_fee - discount_amount
        
        # Create Order record with complete billing information including coupon data
        order_record = Order.objects.create(
            user=request.user,
            order_id=f'ORD-{int(timezone.now().timestamp())}',
            payment_id=payment_id,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            total_amount=total_amount,
            base_amount=subtotal,
            processing_fee=processing_fee,
            discount_amount=discount_amount,
            applied_coupon=coupon_obj,
            coupon_code=applied_coupon_data['code'] if applied_coupon_data else '',
            billing_name=customer_info.company_name or f"{request.user.first_name} {request.user.last_name}".strip(),
            billing_address=customer_info.full_address,
            payment_method='razorpay',
            billing_phone=customer_info.phone,
            currency='USD',
            status='completed',
            items_data=[{
                'chart_id': item.chart.id,
                'chart_title': item.chart.title,
                'price': float(item.chart.price),
                'industry': item.chart.industry,
                'country': item.chart.country
            } for item in cart_items]
        )
        
        # Create OrderItem records
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order_record,
                chart=cart_item.chart,
                price_at_purchase=cart_item.chart.price,
                chart_title_at_purchase=cart_item.chart.title
            )
          # Grant access to all charts in cart
        for cart_item in cart_items:
            ChartAccess.grant_access(request.user, cart_item.chart, 30)
            cart_item.chart.allowed_users.add(request.user)
        
        # Record coupon usage if a coupon was applied
        if coupon_obj and discount_amount > 0:
            CouponUsage.objects.create(
                coupon=coupon_obj,
                user=request.user,
                order=order_record,
                discount_amount=Decimal(str(discount_amount))
            )
            # Update coupon usage count
            coupon_obj.current_uses += 1
            coupon_obj.save()
            
            # Clear applied coupon from session
            if 'applied_coupon' in request.session:
                del request.session['applied_coupon']
        
        # Generate and send invoice
        try:
            success = send_invoice_email(order_record)
        except:
            success = False
          # Clear the cart after successful payment
        cart.items.all().delete()
          # Store purchase details in session for success page
        request.session['purchase_success'] = {
            'items': [{'title': item.chart.title, 'price': float(item.chart.price), 'chart_id': item.chart.id} for item in cart_items],
            'total': float(total_amount),
            'subtotal': float(subtotal),
            'processing_fee': float(processing_fee),
            'discount_amount': float(discount_amount),
            'coupon_code': applied_coupon_data['code'] if applied_coupon_data else '',
            'payment_id': payment_id,
            'order_id': order_record.order_id,
            'razorpay_order_id': order_id
        }
        
        # Success message
        if success:
            messages.success(request, f'Payment successful! Order {order_record.order_id} has been created. Invoice sent to your email.')
        else:
            messages.success(request, f'Payment successful! Order {order_record.order_id} has been created.')
            messages.warning(request, 'Invoice email could not be sent. Please contact support.')
        
        return redirect('cart_success')
        
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('view_cart')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Payment execution error: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment. Please contact support.')
        return redirect('view_cart')


def send_invoice_email(order):
    """Generate and send invoice email with PDF attachment"""
    try:
        # Get company information
        company = CompanyInfo.get_active_company()
        if not company:
            company = CompanyInfo.objects.create()
        
        # Get customer billing information
        customer_info = getattr(order.user, 'customer_info', None)
        
        # Create context for PDF template
        invoice_context = {
            'order': order,
            'order_items': order.order_items.all(),
            'company': company,
            'customer_info': customer_info,
            'invoice_number': f'INV-{order.id:06d}',
            'invoice_date': order.created_at,
        }
        
        # Generate PDF invoice
        template = get_template('invoice_pdf.html')
        html_content = template.render(invoice_context)
        pdf_file = HTML(string=html_content).write_pdf()
        
        # Create context for email template
        email_context = {
            'order': order,
            'company': company,
            'invoice_number': f'INV-{order.id:06d}',
        }
        
        # Generate HTML email content
        email_template = get_template('invoice_email.html')
        email_html_content = email_template.render(email_context)
        
        # Send email with PDF attachment
        subject = f'Invoice #{invoice_context["invoice_number"]} - Your Purchase from {company.name}'
        
        email = EmailMessage(
            subject=subject,
            body=email_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[order.user.email]
        )
        email.content_subtype = 'html'  # Set email content type to HTML
        email.attach(
            f'invoice_{order.order_id}.pdf',
            pdf_file,
            'application/pdf'
        )
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send invoice email for order {order.id}: {str(e)}")
        return False


def cart_success(request):
    """Display cart purchase success page"""
    purchase_data = request.session.get('purchase_success')
    
    if not purchase_data:
        messages.info(request, 'No recent purchase found.')
        return redirect('marketplace_dash')
      # Clear the session data after displaying
    del request.session['purchase_success']
    
    from django.utils import timezone
    context = {
        'purchased_items': purchase_data['items'],
        'total_amount': purchase_data['total'],
        'subtotal': purchase_data.get('subtotal', purchase_data['total']),
        'processing_fee': purchase_data.get('processing_fee', 0),
        'discount_amount': purchase_data.get('discount_amount', 0),
        'coupon_code': purchase_data.get('coupon_code', ''),
        'payment_id': purchase_data['payment_id'],
        'order_id': purchase_data.get('order_id', ''),
        'transaction_date': timezone.now()  # Add current timestamp for transaction date
    }
    
    return render(request, 'cart_success.html', context)



def test_razorpay_connection(request):
    """Test Razorpay API connection for debugging"""
    try:
        from django.http import JsonResponse
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
       

        # Test by creating a minimal order
        test_order_data = {
            'amount': 100,  # Minimum amount in cents
            'currency': 'USD',
            'receipt': f'test_order_{request.user.id}_{timezone.now().timestamp()}',
            'notes': {
                'test': 'connection_test'
            }
        }
        
        order = client.order.create(data=test_order_data)
        
        return JsonResponse({
            'success': True,
            'message': 'Razorpay connection successful',
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'status': order['status']
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Razorpay connection test failed: {str(e)}")
        
        error_details = {'error': str(e)}
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_details = e.response.json()
            except:
                pass
            
        return JsonResponse({
            'success': False,
            'message': 'Razorpay connection failed',
            'error': error_details,
            'error_type': type(e).__name__
        })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_orders(request):
    """Admin view to see all orders and payment details"""
    orders = Order.objects.select_related('user', 'created_by').all().order_by('-created_at')
    
    # Add pagination if needed
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 25)  # Show 25 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,  # This contains the paginated orders
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'admin_orders.html', context)

from decimal import Decimal, ROUND_HALF_UP
@login_required
@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def admin_order_detail(request, order_id):
    """Admin view to see detailed order information"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()
    
    # Calculate amounts properly
    subtotal = float(order.base_amount)
    processing_fee = float(order.processing_fee) 
    discount_amount = float(order.discount_amount) if order.discount_amount else 0
    total = float(order.total_amount)
    
    # Get coupon usage if any
    coupon_usage = None
    if order.applied_coupon:
        try:
            coupon_usage = CouponUsage.objects.get(order=order)
        except CouponUsage.DoesNotExist:
            pass
    
    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'processing_fee': processing_fee,
        'discount_amount': discount_amount,
        'total': total,
        'coupon_usage': coupon_usage,
        'has_coupon': bool(order.applied_coupon or order.coupon_code),
    }
    
    return render(request, 'admin_order_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_payment_dashboard(request):
    """Admin dashboard showing payment statistics"""
    from django.db.models import Sum, Count
    from datetime import datetime, timedelta
    import json
      # Get time range from request, default to 7 days
    time_range = request.GET.get('time_range', '7')
    is_all_time = time_range == 'all'
    
    if is_all_time:
        time_range_days = None
        start_date = None
    else:
        try:
            time_range_days = int(time_range)
        except (ValueError, TypeError):
            time_range_days = 7
        
        # Get current date and calculate date ranges
        today = timezone.now().date()
        start_date = today - timedelta(days=time_range_days)
      # Payment statistics based on time range
    if is_all_time:
        total_revenue = Order.objects.filter(
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    else:
        total_revenue = Order.objects.filter(
            status='completed',
            created_at__date__gte=start_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Order counts based on time range
    if is_all_time:
        total_orders = Order.objects.all().count()
        completed_orders = Order.objects.filter(status='completed').count()
        pending_orders = Order.objects.filter(status='pending').count()
        failed_orders = Order.objects.filter(status='failed').count()
    else:
        total_orders = Order.objects.filter(created_at__date__gte=start_date).count()
        completed_orders = Order.objects.filter(
            status='completed',
            created_at__date__gte=start_date
        ).count()
        pending_orders = Order.objects.filter(
            status='pending',
            created_at__date__gte=start_date
        ).count()
        failed_orders = Order.objects.filter(
            status='failed',
            created_at__date__gte=start_date
        ).count()
    
    # Calculate average order value
    average_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
      # Recent orders based on time range
    if is_all_time:
        recent_orders = Order.objects.all().order_by('-created_at')[:10]
    else:
        recent_orders = Order.objects.filter(
            created_at__date__gte=start_date
        ).order_by('-created_at')[:10]    # Chart data for revenue trend based on time range
    revenue_data = []
    revenue_labels = []
    if is_all_time:
        # For all time data, show yearly data from first order to current year
        first_order = Order.objects.filter(status='completed').order_by('created_at').first()
        if first_order:
            today = timezone.now().date()
            start_year = first_order.created_at.year
            current_year = today.year
            
            # Generate yearly data from first order year to current year
            for year in range(start_year, current_year + 1):
                revenue_labels.append(str(year))
                
                # Calculate start and end dates for the year
                year_start = timezone.datetime(year, 1, 1).date()
                if year == current_year:
                    year_end = today
                else:
                    year_end = timezone.datetime(year, 12, 31).date()
                
                yearly_revenue = Order.objects.filter(
                    status='completed',
                    created_at__date__gte=year_start,
                    created_at__date__lte=year_end
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                revenue_data.append(float(yearly_revenue))
    else:
        # Determine the appropriate date grouping based on time range
        today = timezone.now().date()
        if time_range_days <= 7:
            # Daily data for 7 days or less
            for i in range(time_range_days - 1, -1, -1):
                date = today - timedelta(days=i)
                revenue_labels.append(date.strftime('%m/%d'))
                daily_revenue = Order.objects.filter(
                    status='completed',
                    created_at__date=date
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                revenue_data.append(float(daily_revenue))
        elif time_range_days <= 30:
            # Daily data for 30 days
            for i in range(time_range_days - 1, -1, -1):
                date = today - timedelta(days=i)
                revenue_labels.append(date.strftime('%m/%d'))
                daily_revenue = Order.objects.filter(
                    status='completed',
                    created_at__date=date
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                revenue_data.append(float(daily_revenue))
        elif time_range_days <= 90:
            # Weekly data for 90 days
            weeks = time_range_days // 7
            for i in range(weeks - 1, -1, -1):
                start_week = today - timedelta(days=(i + 1) * 7)
                end_week = today - timedelta(days=i * 7)
                revenue_labels.append(f"{start_week.strftime('%m/%d')}-{end_week.strftime('%m/%d')}")
                weekly_revenue = Order.objects.filter(
                    status='completed',
                    created_at__gte=start_week,
                    created_at__lt=end_week
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                revenue_data.append(float(weekly_revenue))
        else:
            # Monthly data for 365 days
            months = min(12, time_range_days // 30)
            for i in range(months - 1, -1, -1):
                start_month = today.replace(day=1) - timedelta(days=i * 30)
                if i == 0:
                    end_month = today
                else:
                    end_month = today.replace(day=1) - timedelta(days=(i - 1) * 30)
                revenue_labels.append(start_month.strftime('%m/%Y'))
                monthly_revenue = Order.objects.filter(
                    status='completed',
                    created_at__gte=start_month,
                    created_at__lt=end_month
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                revenue_data.append(float(monthly_revenue))
    
    # Chart data for order status based on time range
    status_labels = ['Completed', 'Pending', 'Failed']
    status_data = [completed_orders, pending_orders, failed_orders]
      # Top selling charts based on time range
    from django.db.models import Count, Sum, F
    if is_all_time:
        top_charts = chart.objects.filter(
            orderitem__order__status='completed'
        ).annotate(
            total_sales=Count('orderitem'),
            total_revenue=Sum('orderitem__price_at_purchase')
        ).order_by('-total_sales')[:6]
    else:
        top_charts = chart.objects.filter(
            orderitem__order__status='completed',
            orderitem__order__created_at__date__gte=start_date
        ).annotate(
            total_sales=Count('orderitem'),
            total_revenue=Sum('orderitem__price_at_purchase')
        ).order_by('-total_sales')[:6]
    
    context = {
        'stats': {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'average_order_value': float(average_order_value),
        },
        'recent_orders': recent_orders,
        'top_charts': top_charts,
        'revenue_chart': {
            'labels': json.dumps(revenue_labels),
            'data': json.dumps(revenue_data),
        },
        'status_chart': {
            'labels': json.dumps(status_labels),
            'data': json.dumps(status_data),
        },
        'time_range': time_range,
    }
    
    return render(request, 'admin_payment_dashboard.html', context)

@login_required
@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def generate_order_pdf(request, order_id):
    """Generate PDF invoice for an order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()
      # Get company information
    company = CompanyInfo.get_active_company()
    if not company:
        company = CompanyInfo.objects.create()  # Create default company if none exists
    
    # Create context for PDF template
    context = {
        'order': order,
        'order_items': order_items,
        'company': company,
        'customer_info': getattr(order.user, 'customer_info', None),
        'invoice_number': f'INV-{order.id:06d}',
    }
    
    # Render HTML template
    template = get_template('invoice_pdf.html')
    html_content = template.render(context)
    
    # Generate PDF
    pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf()
    
    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_order_{order.id}.pdf"'
    
    return response

@login_required
@user_passes_test(lambda user: user.is_staff or user.groups.filter(name='Admin').exists())
def email_order_invoice(request, order_id):
    """Email PDF invoice to customer"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()
    
    if not order.user.email:
        messages.error(request, 'Customer email not found.')
        return redirect('admin_order_detail', order_id=order_id)
    if not order.status == 'completed':
        messages.error(request, 'Order status is not completed. Please update first!')
        return redirect('admin_order_detail', order_id=order_id)
    try:
        # Get company information
        company = CompanyInfo.get_active_company()
        if not company:
            company = CompanyInfo.objects.create()  # Create default company if none exists
        
        # Create context for PDF template
        context = {
            'order': order,
            'order_items': order_items,
            'company': company,
            'customer_info': getattr(order.user, 'customer_info', None),
            'invoice_number': f'INV-{order.id:06d}',
        }
        
        # Render HTML template and generate PDF
        template = get_template('invoice_pdf.html')
        html_content = template.render(context)
        pdf = HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf()
        
        # Create context for email template
        email_context = {
            'order': order,
            'company': company,
            'invoice_number': f'INV-{order.id:06d}',
        }
        
        # Generate HTML email content
        email_template = get_template('invoice_email.html')
        email_html_content = email_template.render(email_context)
        
        # Create email
        subject = f'Invoice #{order.id:06d} - Your Purchase from {company.name}'
        
        email = EmailMessage(
            subject=subject,
            body=email_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[order.user.email],
        )
        email.content_subtype = 'html'  # Set email content type to HTML
        
        # Attach PDF
        email.attach(f'invoice_order_{order.id}.pdf', pdf, 'application/pdf')
        
        # Send email
        email.send()
        
        messages.success(request, f'Invoice has been successfully sent to {order.user.email}')
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send invoice email for order {order_id}: {str(e)}")
        messages.error(request, f'Failed to send invoice email: {str(e)}')
    
    return redirect('admin_order_detail', order_id=order_id)

def send_order_confirmation_email(order):
    """Send order confirmation email with invoice PDF"""
    try:
        # Get company information
        company = CompanyInfo.get_active_company()
        if not company:
            company = CompanyInfo.objects.create()
        
        # Create context for email template
        email_context = {
            'order': order,
            'company': company,
        }
        
        # Generate HTML email content
        email_template = get_template('order_confirmation_email.html')
        email_html_content = email_template.render(email_context)
        
        # Generate PDF invoice
        invoice_template = get_template('invoice_pdf.html')
        invoice_context = {
            'order': order,
            'order_items': order.order_items.all(),
            'company': company,
            'customer_info': getattr(order.user, 'customer_info', None),
            'invoice_number': f'INV-{order.id:06d}',
            'invoice_date': order.created_at,
        }
        html_string = invoice_template.render(invoice_context)
        pdf_file = HTML(string=html_string).write_pdf()
        
        # Create email message with PDF attachment
        subject = f'Order Confirmation - {company.name}'
        message = EmailMessage(
            subject=subject,
            body=email_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[order.user.email]
        )
        message.content_subtype = 'html'  # Set email content type to HTML
        
        # Attach PDF
        message.attach(f'invoice_{order.order_id}.pdf', pdf_file, 'application/pdf')
        message.send(fail_silently=True)
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send order confirmation email for order {order.id}: {str(e)}")
        return False

@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def create_manual_order_dashboard(request):
    """Dashboard view to create manual orders - accessible to Admin group only"""
    if request.method == 'POST':
        return process_manual_order_dashboard(request)
    
    # Get available users and charts for the form
    from django.contrib.auth.models import User
    users = User.objects.all().order_by('username')
    charts = chart.objects.all().order_by('title')
    active_coupons = Coupon.objects.filter(status='active').order_by('code')
    
    context = {
        'users': users,
        'charts': charts,
        'active_coupons': active_coupons,
    }
    
    return render(request, 'create_manual_order.html', context)


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def process_manual_order_dashboard(request):
    """Process the manual order creation form from dashboard"""
    from django.utils import timezone
    from django.contrib import messages
    
    try:
        # Get form data
        user_id = request.POST.get('user')
        chart_ids = request.POST.getlist('charts')
        billing_name = request.POST.get('billing_name', '')
        billing_address = request.POST.get('billing_address', '')
        billing_phone = request.POST.get('billing_phone', '')
        payment_method = request.POST.get('payment_method')
        payment_notes = request.POST.get('payment_notes', '')
        send_email = request.POST.get('send_email') == 'on'
        coupon_id = request.POST.get('coupon')  # New coupon field
        
        # Validate required fields
        if not user_id or not chart_ids or not payment_method:
            messages.error(request, 'User, at least one chart, and payment method are required.')
            return redirect('create_manual_order_dashboard')
        
        # Get user and charts
        user = User.objects.get(id=user_id)
        selected_charts = chart.objects.filter(id__in=chart_ids)
        
        # Calculate totals with 5.5% processing fee
        subtotal = sum(float(c.price) for c in selected_charts)
        processing_fee = round(subtotal * 0.055, 2)  # 5.5% processing fee
        
        # Handle coupon application
        discount_amount = 0
        coupon_obj = None        
        if coupon_id:
            try:
                coupon_obj = Coupon.objects.get(id=coupon_id)
                # Validate coupon for the selected user and charts
                is_valid, message = coupon_obj.is_valid(
                    user=user,
                    order_amount=Decimal(str(subtotal)),
                    charts=list(selected_charts)
                )
                
                if is_valid:
                    discount_amount = float(coupon_obj.calculate_discount(Decimal(str(subtotal))))
                else:
                    messages.warning(request, f'Coupon "{coupon_obj.code}" is not valid: {message}. Order created without discount.')
                    coupon_obj = None
            except Coupon.DoesNotExist:
                messages.warning(request, 'Selected coupon not found. Order created without discount.')
                coupon_obj = None
        
        total_amount = subtotal + processing_fee - discount_amount
        
        # Get or create customer info
        customer_info, created = CustomerInfo.objects.get_or_create(
            user=user,
            defaults={
                'company_name': billing_name,
                'address_line1': billing_address,
                'phone': billing_phone,
            }
        )
        
        # Determine order status based on payment method
        if payment_method == 'completed':
            order_status = 'completed'
        else:
            order_status = 'pending'  # For razorpay and bank_transfer
            
        # Create order with admin who created it and coupon information
        order = Order.objects.create(
            user=user,
            created_by=request.user,  # Track which admin created the order
            order_id=f'MANUAL-{int(timezone.now().timestamp())}',
            payment_id=f'manual_{timezone.now().strftime("%Y%m%d_%H%M%S")}',
            total_amount=total_amount,
            base_amount=subtotal,
            processing_fee=processing_fee,
            discount_amount=discount_amount,
            applied_coupon=coupon_obj,
            coupon_code=coupon_obj.code if coupon_obj else '',
            billing_name=billing_name or customer_info.company_name,
            billing_address=billing_address or customer_info.full_address,
            billing_phone=billing_phone or customer_info.phone,
            payment_method = payment_method,
            currency='USD',
            status=order_status,
            items_data=[{
                'chart_id': c.id,
                'chart_title': c.title,
                'price': float(c.price),
                'industry': c.industry,
                'country': c.country
            } for c in selected_charts]
        )
          # Create order items
        for chart_obj in selected_charts:
            OrderItem.objects.create(
                order=order,
                chart=chart_obj,
                price_at_purchase=chart_obj.price,
                chart_title_at_purchase=chart_obj.title
            )
        
        # Record coupon usage if a coupon was applied
        if coupon_obj and discount_amount > 0:
            CouponUsage.objects.create(
                coupon=coupon_obj,
                user=user,
                order=order,
                discount_amount=Decimal(str(discount_amount))
            )
            # Update coupon usage count
            coupon_obj.current_uses += 1
            coupon_obj.save()
            
        # Grant access to charts only if payment is completed
        from .models import ChartAccess
        if payment_method == 'completed':
            for chart_obj in selected_charts:
                ChartAccess.grant_access(user, chart_obj, 30)
                chart_obj.allowed_users.add(user)
        
        # Handle payment method specific actions
        payment_link = None
        if payment_method == 'razorpay':
            # Create Razorpay payment link
            payment_link = create_razorpay_payment_link(order, payment_notes)
        
        # Send appropriate email based on payment method
        if send_email:
            try:
                if payment_method == 'completed':
                    # Send invoice for completed order
                    if send_invoice_email(order):
                        messages.success(request, f'Manual order {order.order_id} created successfully and invoice sent to {user.email}!')
                    else:
                        messages.warning(request, f'Manual order {order.order_id} created successfully but failed to send invoice email.')
                elif payment_method == 'razorpay':
                    # Send payment link email
                    if payment_link and send_payment_link_email(order, payment_link, payment_notes):
                        messages.success(request, f'Manual order {order.order_id} created successfully and Razorpay payment link sent to {user.email}!')
                    else:
                        messages.warning(request, f'Manual order {order.order_id} created successfully but failed to send payment link email.')
                elif payment_method == 'bank_transfer':
                    # Send bank transfer instructions
                    if send_bank_transfer_email(order, payment_notes):
                        messages.success(request, f'Manual order {order.order_id} created successfully and bank transfer instructions sent to {user.email}!')
                    else:
                        messages.warning(request, f'Manual order {order.order_id} created successfully but failed to send bank transfer email.')
            except Exception as e:
                messages.warning(request, f'Manual order {order.order_id} created successfully but error sending email: {str(e)}')
        else:
            messages.success(request, f'Manual order {order.order_id} created successfully!')
        
        return redirect('admin_orders')
        
    except Exception as e:
        messages.error(request, f'Error creating manual order: {str(e)}')
        return redirect('create_manual_order_dashboard')


@login_required
def profile(request):
    """Handle user profile view and updates"""
    customer_info = CustomerInfo.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        if not customer_info:
            customer_info = CustomerInfo(user=request.user)
          # Update customer info fields
        fields = ['company_name', 'address_line1', 
                 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone']
        for field in fields:
            setattr(customer_info, field, request.POST.get(field, ''))
        customer_info.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    context = {
        'customer_info': customer_info,
        'edit_mode': True
    }
    return render(request, 'profile.html', context)



def create_razorpay_payment_link(order, payment_notes=""):
    """Create a Razorpay payment link for manual orders"""
    try:
        import razorpay
        from django.conf import settings
        from django.utils import timezone
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create payment link data
        payment_link_data = {
            'amount': int(float(order.total_amount) * 100),  # Amount in paise
            'currency': order.currency,
            'accept_partial': False,
            'expire_by': int((timezone.now() + timezone.timedelta(days=7)).timestamp()),  # 7 days from now
            'reference_id': order.order_id,
            'description': f'Payment for Order #{order.order_id}',
            'customer': {
                'name': order.customer_name,
                'email': order.user.email,
                'contact': order.billing_phone or '',
            },
            'notify': {
                'sms': True,
                'email': True
            },
            'reminder_enable': True,
            'notes': {
                'order_id': order.order_id,
                'payment_notes': payment_notes,
                'created_by': order.created_by.username if order.created_by else 'system'
            },
            # 'callback_url': f'{getattr(settings, "SITE_URL", "http://localhost:8000")}/orders/{order.id}/',
            # 'callback_method': 'get'
        }
        
        # Create the payment link
        payment_link = client.payment_link.create(payment_link_data)
        
        # Update order with payment link details
        order.razorpay_order_id = payment_link['id']
        order.save()
        
        return payment_link['short_url']
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create Razorpay payment link for order {order.id}: {str(e)}")
        return None


def send_payment_link_email(order, payment_link, payment_notes=""):
    """Send payment link email to customer"""
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        # Get company information
        company = CompanyInfo.get_active_company()
        if not company:
            company = CompanyInfo.objects.create()
        
        subject = f'Payment Required - Order #{order.order_id} from {company.name}'
        
        # Create email context
        email_context = {
            'order': order,
            'company': company,
            'payment_link': payment_link,
            'payment_notes': payment_notes,
        }
        
        # Set payment method to razorpay for this email type
        order.payment_method = 'razorpay'
        
        # Generate HTML email content
        email_html_content = render_to_string('payment_instructions_email.html', email_context)

        email = EmailMessage(
            subject=subject,
            body=email_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[order.user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send payment link email for order {order.id}: {str(e)}")
        return False


def send_bank_transfer_email(order, payment_notes=""):
    """Send bank transfer instructions email to customer"""
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        # Get company information
        company = CompanyInfo.get_active_company()
        if not company:
            company = CompanyInfo.objects.create()
        
        subject = f'Bank Transfer Instructions - Order #{order.order_id} from {company.name}'
        
        # Create email context with payment method specified
        email_context = {
            'order': order,
            'company': company,
            'payment_notes': payment_notes,
        }
        
        # Set payment method to bank_transfer for this email type
        order.payment_method = 'bank_transfer'
        
        # Generate HTML email content
        email_html_content = render_to_string('payment_instructions_email.html', email_context)

        email = EmailMessage(
            subject=subject,
            body=email_html_content,
            from_email=settings.EMAIL_SENDER_ID,
            to=[order.user.email]
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send bank transfer email for order {order.id}: {str(e)}")
        return False


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay payment link webhook notifications"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        import json
        webhook_data = json.loads(request.body.decode('utf-8'))
        event_type = webhook_data.get('event')
        
        if event_type == 'payment_link.paid':
            payment_link_data = webhook_data.get('payload', {}).get('payment_link', {}).get('entity', {})
            payment_data = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            
            payment_id = payment_data.get('id')
            order_id = payment_link_data.get('reference_id')
            
            if order_id and payment_id:
                try:
                    order = Order.objects.get(order_id=order_id)
                    order.razorpay_payment_id = payment_id
                    order.status = 'completed'
                    order.save()
                    
                    # Grant access to charts
                    from .models import ChartAccess
                    for order_item in order.order_items.all():
                        ChartAccess.grant_access(order.user, order_item.chart, 30)
                        order_item.chart.allowed_users.add(order.user)
                    
                    return HttpResponse('Payment processed successfully', status=200)
                except Order.DoesNotExist:
                    return HttpResponse('Order not found', status=404)
        # Payment Link Expired
        elif event_type == 'payment_link.expired':
            payment_link_data = webhook_data.get('payload', {}).get('payment_link', {}).get('entity', {})
            order_id = payment_link_data.get('reference_id')

            if order_id:
                try:
                    order = Order.objects.get(order_id=order_id)
                    order.status = 'expired'
                    order.save()
                    return HttpResponse('Order marked as expired', status=200)
                except Order.DoesNotExist:
                    return HttpResponse('Order not found', status=404)

        # Payment Failed
        elif event_type == 'payment.failed':
            payment_data = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            notes = payment_data.get('notes', {})
            order_id = notes.get('order_id') or notes.get('reference_id')  # depends on how you set notes

            if order_id:
                try:
                    order = Order.objects.get(order_id=order_id)
                    order.status = 'failed'
                    order.save()
                    return HttpResponse('Order marked as failed', status=200)
                except Order.DoesNotExist:
                    return HttpResponse('Order not found', status=404)
        elif event_type == 'payment.refunded':
            refund_data = webhook_data.get('payload', {}).get('refund', {}).get('entity', {})
            payment_id = refund_data.get('payment_id')
            refund_id = refund_data.get('id')
            refund_amount = int(refund_data.get('amount')) / 100  # convert from paise to currency unit

            try:
                order = Order.objects.get(razorpay_payment_id=payment_id)
                order.status = 'refunded'
                order.save()

                # Optionally log the refund
                from .models import RefundLog
                RefundLog.objects.create(
                    order=order,
                    refund_id=refund_id,
                    amount=refund_amount,
                    reason=refund_data.get('notes', {}).get('reason', 'Not specified'),
                    refund_status=refund_data.get('status'),
                )

                return HttpResponse('Order marked as refunded', status=200)
            except Order.DoesNotExist:
                return HttpResponse('Order not found for refund', status=404)

        else:  
            return HttpResponse('Event not handled', status=200)
    except Exception as e:
        return HttpResponse(f'Webhook error: {str(e)}', status=500)

from .models import RefundLog 
from .models import ChartAccess
@login_required
@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def manual_payment_update(request, order_id):
    """Manually update payment status and transaction details"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        transaction_id = request.POST.get('transaction_id', '')
        refund_transaction_id = request.POST.get('refund_transaction_id', '')
        refund_reason = request.POST.get('refund_reason', '')
        try:
            if payment_status:
                old_status = order.status
                order.status = payment_status
                print(order.razorpay_payment_id)
                print(transaction_id)
                order.razorpay_payment_id = transaction_id
                
                order.save()
                if payment_status == 'refunded':
                    RefundLog.objects.create(
                        order=order,
                        refund_id=refund_transaction_id,
                        amount=order.total_amount,
                        reason=refund_reason,
                        refund_status='completed',
                    )
                    # If refunded, reset access to charts
                    for order_item in order.order_items.all():
                        ChartAccess.revoke_access(order.user, order_item.chart)
                        order_item.chart.allowed_users.remove(order.user)
                # If status changed to completed, grant access
                if old_status != 'completed' and payment_status == 'completed':
                    for order_item in order.order_items.all():
                        ChartAccess.grant_access(order.user, order_item.chart, 30)
                        order_item.chart.allowed_users.add(order.user)
                
                messages.success(request, f'Order {order.order_id} payment status updated to {payment_status}')
        except Exception as e:
            print(e)
            messages.error(request, f'Error updating payment status: {str(e)}')
        return redirect('admin_order_detail', order_id=order.id)
    latest_refund = RefundLog.objects.filter(order=order).order_by('-created_at').first()

    context = {
        'order': order,
        'refund_log': latest_refund,

    }
    return render(request, 'manual_payment_update.html', context)


# ================== COUPON MANAGEMENT VIEWS ==================

from .models import Coupon
@csrf_exempt
@login_required
def validate_coupon_ajax(request):
    """AJAX view to validate coupon code"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').upper().strip()
        
        if not coupon_code:
            return JsonResponse({
                'valid': False,
                'message': 'Please enter a coupon code'
            })
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            
            # Get cart information for validation
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                return JsonResponse({
                    'valid': False,
                    'message': 'Your cart is empty'
                })
            
            # Calculate order amount
            order_amount = sum(item.chart.price for item in cart_items)
            
            # Get chart objects for validation
            charts = [item.chart for item in cart_items]
            
            # Validate coupon
            is_valid, message = coupon.is_valid(
                user=request.user,
                order_amount=order_amount,
                charts=charts
            )
            
            if is_valid:
                # Calculate discount
                discount_amount = coupon.calculate_discount(order_amount)
                
                return JsonResponse({
                    'valid': True,
                    'message': f'Coupon applied! You save ${discount_amount:.2f}',
                    'discount_amount': float(discount_amount),
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value),
                    'coupon_name': coupon.name,
                    'coupon_description': coupon.description
                })
            else:
                return JsonResponse({
                    'valid': False,
                    'message': message
                })
                
        except Coupon.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'message': 'Invalid coupon code'
            })
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'message': f'Error validating coupon: {str(e)}'
            })
    return JsonResponse({'valid': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(lambda user: user.groups.filter(name='Admin').exists())
def validate_manual_order_coupon_ajax(request):
    """AJAX view to validate coupon for manual order creation"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        coupon_id = data.get('coupon_id')
        user_id = data.get('user_id')
        chart_ids = data.get('chart_ids', [])
        
        if not coupon_id or not user_id or not chart_ids:
            return JsonResponse({
                'valid': False,
                'message': 'Missing required data'
            })
        
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            user = User.objects.get(id=user_id)
            charts = chart.objects.filter(id__in=chart_ids)
            
            # Calculate order amount
            order_amount = sum(c.price for c in charts)
            
            # Validate coupon
            is_valid, message = coupon.is_valid(
                user=user,
                order_amount=order_amount,
                charts=list(charts)
            )
            
            if is_valid:
                discount_amount = coupon.calculate_discount(order_amount)
                return JsonResponse({
                    'valid': True,
                    'message': f'Coupon is valid! Discount: ${discount_amount:.2f}',
                    'discount_amount': float(discount_amount),
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value),
                    'coupon_code': coupon.code,
                    'coupon_name': coupon.name
                })
            else:
                return JsonResponse({
                    'valid': False,
                    'message': message
                })
                
        except (Coupon.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'valid': False,
                'message': 'Invalid coupon or user'
            })
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'message': f'Error validating coupon: {str(e)}'
            })
    
    return JsonResponse({'valid': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
def apply_coupon_ajax(request):
    """AJAX view to apply coupon to user's session"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').upper().strip()
        
        if not coupon_code:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a coupon code'
            })
        
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            
            # Get cart information
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_items = cart.items.all()
            
            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'message': 'Your cart is empty'
                })
            
            # Calculate order amount
            order_amount = sum(item.chart.price for item in cart_items)
            
            # Get chart objects for validation
            charts = [item.chart for item in cart_items]
            
            # Validate coupon
            is_valid, message = coupon.is_valid(
                user=request.user,
                order_amount=order_amount,
                charts=charts
            )
            
            if is_valid:
                # Calculate discount
                discount_amount = coupon.calculate_discount(order_amount)
                
                # Store coupon in session
                request.session['applied_coupon'] = {
                    'id': coupon.id,
                    'code': coupon.code,
                    'discount_amount': float(discount_amount),
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value)
                }
                
                # Calculate new totals
                processing_fee = order_amount * Decimal('0.055')
                total_after_discount = order_amount - discount_amount + processing_fee
                
                return JsonResponse({
                    'success': True,
                    'message': f'Coupon "{coupon.code}" applied successfully!',
                    'discount_amount': float(discount_amount),
                    'new_total': float(total_after_discount),
                    'processing_fee': float(processing_fee),
                    'coupon_name': coupon.name
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error applying coupon: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
def remove_coupon_ajax(request):
    """AJAX view to remove applied coupon from session"""
    if request.method == 'POST':
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
            request.session.modified = True
            
            # Recalculate totals
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_items = cart.items.all()
            
            if cart_items:
                order_amount = sum(item.chart.price for item in cart_items)
                processing_fee = order_amount * Decimal('0.055')
                total_amount = order_amount + processing_fee
                
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon removed successfully',
                    'new_total': float(total_amount),
                    'processing_fee': float(processing_fee)
                })
        return JsonResponse({
            'success': False,
            'message': 'No coupon applied'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})



@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_coupons(request):
    """Admin view to list all coupons with filtering and pagination"""
    from django.db.models import Q


    
    coupons_list = Coupon.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        coupons_list = coupons_list.filter(status=status_filter)
    
    # Search by code or name
    search_query = request.GET.get('search')
    if search_query:
        coupons_list = coupons_list.filter(
            Q(code__icontains=search_query) | 
            Q(name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(coupons_list, 20)
    page_number = request.GET.get('page')
    coupons = paginator.get_page(page_number)
    
    context = {
        'coupons': coupons,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': Coupon.COUPON_STATUS_CHOICES,
        'discount_type_choices': Coupon.DISCOUNT_TYPE_CHOICES,
    }
    
    return render(request, 'admin_coupons.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_coupon(request):
    """Admin view to create a new coupon"""
    if request.method == 'POST':
        try:
            code = request.POST.get('code', '').upper().strip()
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            discount_type = request.POST.get('discount_type')
            discount_value = Decimal(request.POST.get('discount_value', '0'))
            
            max_uses = request.POST.get('max_uses')
            max_uses_per_user = int(request.POST.get('max_uses_per_user', '1'))
            minimum_order_amount = request.POST.get('minimum_order_amount')
            maximum_discount_amount = request.POST.get('maximum_discount_amount')
            valid_from = request.POST.get('valid_from')
            valid_until = request.POST.get('valid_until')
            new_users_only = request.POST.get('new_users_only') == 'on'
            
            if not code or not name or not discount_type or not valid_from or not valid_until:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'create_coupon.html', get_create_coupon_context())
            
            if Coupon.objects.filter(code=code).exists():
                messages.error(request, f'Coupon code "{code}" already exists.')
                return render(request, 'create_coupon.html', get_create_coupon_context())
            
            # Validate discount value
            if discount_type == 'percentage' and (discount_value < 0 or discount_value > 100):
                messages.error(request, 'Percentage discount must be between 0 and 100.')
                return render(request, 'create_coupon.html', get_create_coupon_context())
            
            if discount_type == 'fixed' and discount_value < 0:
                messages.error(request, 'Fixed discount amount cannot be negative.')
                return render(request, 'create_coupon.html', get_create_coupon_context())
            
            # Parse dates properly
            valid_from_dt = timezone.datetime.fromisoformat(valid_from.replace('T', ' ')).replace(tzinfo=timezone.get_current_timezone())
            valid_until_dt = timezone.datetime.fromisoformat(valid_until.replace('T', ' ')).replace(tzinfo=timezone.get_current_timezone())
            
            if valid_from_dt >= valid_until_dt:
                messages.error(request, 'Valid from date must be before valid until date.')
                return render(request, 'create_coupon.html', get_create_coupon_context())
            
            coupon = Coupon(
                code=code,
                name=name,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                max_uses_per_user=max_uses_per_user,
                valid_from=valid_from_dt,
                valid_until=valid_until_dt,
                new_users_only=new_users_only,
                created_by=request.user,
            )
            
            if max_uses:
                coupon.max_uses = int(max_uses)
            if minimum_order_amount:
                coupon.minimum_order_amount = Decimal(minimum_order_amount)
            if maximum_discount_amount:
                coupon.maximum_discount_amount = Decimal(maximum_discount_amount)
            
            coupon.full_clean()
            coupon.save()
            
            # Handle allowed users
            allowed_user_ids = request.POST.getlist('allowed_users')
            if allowed_user_ids:
                coupon.allowed_users.set(User.objects.filter(id__in=allowed_user_ids))
            
            # Handle applicable charts
            applicable_chart_ids = request.POST.getlist('applicable_charts')
            if applicable_chart_ids:
                coupon.applicable_charts.set(chart.objects.filter(id__in=applicable_chart_ids))
            
            messages.success(request, f'Coupon "{code}" created successfully!')
            return redirect('admin_coupons')
            
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        except Exception as e:
            messages.error(request, f'Error creating coupon: {str(e)}')
        
        return render(request, 'create_coupon.html', get_create_coupon_context())
    
    return render(request, 'create_coupon.html', get_create_coupon_context())


def get_create_coupon_context():
    """Helper function to get context for coupon creation"""
    return {
        'discount_type_choices': Coupon.DISCOUNT_TYPE_CHOICES,
        'status_choices': Coupon.COUPON_STATUS_CHOICES,
        'users': User.objects.all().order_by('username'),
        'charts': chart.objects.all().order_by('title'),
    }


@login_required
@user_passes_test(lambda u: u.is_superuser)
def coupon_detail(request, coupon_id):
    """Admin view to show detailed coupon information"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    usage_history = CouponUsage.objects.filter(coupon=coupon).order_by('-used_at')
    
    # Pagination for usage history
    paginator = Paginator(usage_history, 20)
    page_number = request.GET.get('page')
    usages = paginator.get_page(page_number)
    
    context = {
        'coupon': coupon,
        'usages': usages,
        'usage_count': usage_history.count(),
        'remaining_uses': (coupon.max_uses - coupon.current_uses) if coupon.max_uses else 'Unlimited',
    }
    
    return render(request, 'coupon_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_coupon(request, coupon_id):
    """Admin view to edit an existing coupon"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            coupon.code = request.POST.get('code', '').strip().upper()
            coupon.name = request.POST.get('name', '').strip()
            coupon.description = request.POST.get('description', '').strip()
            
            # Update discount settings
            coupon.discount_type = request.POST.get('discount_type', 'percentage')
            coupon.discount_value = Decimal(request.POST.get('discount_value', '0'))
            
            # Update usage limitations
            max_uses = request.POST.get('max_uses', '').strip()
            coupon.max_uses = int(max_uses) if max_uses else None
            coupon.max_uses_per_user = int(request.POST.get('max_uses_per_user', '1'))
            
            # Update amount limitations
            min_order = request.POST.get('minimum_order_amount', '').strip()
            coupon.minimum_order_amount = Decimal(min_order) if min_order else None
            
            max_discount = request.POST.get('maximum_discount_amount', '').strip()
            coupon.maximum_discount_amount = Decimal(max_discount) if max_discount else None
            
            # Update date limitations
            valid_from_str = request.POST.get('valid_from')
            valid_until_str = request.POST.get('valid_until')
            
            if valid_from_str:
                coupon.valid_from = timezone.datetime.fromisoformat(valid_from_str.replace('T', ' ')).replace(tzinfo=timezone.get_current_timezone())
            if valid_until_str:
                coupon.valid_until = timezone.datetime.fromisoformat(valid_until_str.replace('T', ' ')).replace(tzinfo=timezone.get_current_timezone())
            
            # Update user limitations
            coupon.new_users_only = 'new_users_only' in request.POST
            
            # Update status
            coupon.status = request.POST.get('status', 'active')
            
            # Validate coupon data
            if coupon.discount_type == 'percentage' and (coupon.discount_value < 0 or coupon.discount_value > 100):
                messages.error(request, 'Percentage discount must be between 0 and 100.')
                return redirect('edit_coupon', coupon_id=coupon_id)
            
            if coupon.discount_type == 'fixed' and coupon.discount_value < 0:
                messages.error(request, 'Fixed discount amount cannot be negative.')
                return redirect('edit_coupon', coupon_id=coupon_id)
            
            if coupon.valid_from >= coupon.valid_until:
                messages.error(request, 'Valid from date must be before valid until date.')
                return redirect('edit_coupon', coupon_id=coupon_id)
            
            if Coupon.objects.filter(code=coupon.code).exclude(id=coupon.id).exists():
                messages.error(request, 'A coupon with this code already exists.')
                return redirect('edit_coupon', coupon_id=coupon_id)
            
            coupon.save()
            
            # Handle allowed users (many-to-many field)
            allowed_user_ids = request.POST.getlist('allowed_users')
            if allowed_user_ids:
                coupon.allowed_users.set(User.objects.filter(id__in=allowed_user_ids))
            else:
                coupon.allowed_users.clear()
            
            # Handle applicable charts (many-to-many field)
            applicable_chart_ids = request.POST.getlist('applicable_charts')
            if applicable_chart_ids:
                coupon.applicable_charts.set(chart.objects.filter(id__in=applicable_chart_ids))
            else:
                coupon.applicable_charts.clear()
            
            messages.success(request, f'Coupon "{coupon.code}" has been updated successfully.')
            return redirect('admin_coupons')
            
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return redirect('edit_coupon', coupon_id=coupon_id)
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
            return redirect('edit_coupon', coupon_id=coupon_id)
    
    # GET request - show the edit form
    all_users = User.objects.all().order_by('username')
    all_charts = chart.objects.all().order_by('title')
    
    context = {
        'coupon': coupon,
        'all_users': all_users,
        'all_charts': all_charts,
        'discount_type_choices': Coupon.DISCOUNT_TYPE_CHOICES,
        'status_choices': Coupon.COUPON_STATUS_CHOICES,
    }
    
    return render(request, 'edit_coupon.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_coupon_status(request, coupon_id):
    """Admin view to toggle coupon status between active and inactive"""
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        
        try:
            # Toggle between active and inactive only
            if coupon.status == 'active':
                coupon.status = 'inactive'
                action = 'deactivated'
            elif coupon.status == 'inactive':
                coupon.status = 'active' 
                action = 'activated'
            else:
                # If expired, allow reactivation only if still within valid dates
                now = timezone.now()
                if now <= coupon.valid_until:
                    coupon.status = 'active'
                    action = 'activated'
                else:
                    messages.error(request, 'Cannot activate an expired coupon. Please update the expiry date first.')
                    return JsonResponse({'success': False, 'message': 'Cannot activate expired coupon'})
            
            coupon.save()
            messages.success(request, f'Coupon "{coupon.code}" has been {action} successfully.')
            
            return JsonResponse({
                'success': True, 
                'new_status': coupon.status,
                'message': f'Coupon {action} successfully'            })
            
        except Exception as e:
            messages.error(request, f'Error updating coupon status: {str(e)}')
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# @login_required
# @user_passes_test(lambda user: user.is_staff or user.groups.filter(name='Admin').exists())
# def edit_order(request, order_id):
#     """Edit a pending order"""
#     order = get_object_or_404(Order, id=order_id)
    
#     # Only allow editing of pending orders
#     if order.status != 'pending':
#         messages.error(request, 'Only pending orders can be edited.')
#         return redirect('admin_order_detail', order_id=order_id)
    
#     if request.method == 'POST':
#         # Get form data
#         user_id = request.POST.get('user')
#         chart_ids = request.POST.getlist('charts')
#         payment_method = request.POST.get('payment_method')
#         coupon_id = request.POST.get('coupon')
        
#         # Validate required fields
#         if not user_id or not chart_ids or not payment_method:
#             messages.error(request, 'Please fill in all required fields.')
#             return redirect('edit_order', order_id=order_id)
#         try:
#             # Get user and charts
#             user = User.objects.get(id=user_id)
#             charts = chart.objects.filter(id__in=chart_ids)
            
#             # Calculate amounts
#             subtotal = sum(Decimal(str(schart.price)) for schart in charts)
#             processing_fee = subtotal * Decimal('0.055')  # 5.5%
            
#             # Handle coupon
#             coupon = None
#             discount_amount = Decimal('0')
#             if coupon_id:
#                 coupon = Coupon.objects.get(id=coupon_id, status='active')
#                 if subtotal >= coupon.min_amount:
#                     if coupon.discount_type == 'percentage':
#                         discount_amount = (subtotal * coupon.discount_value) / 100
#                         if coupon.max_discount:
#                             discount_amount = min(discount_amount, coupon.max_discount)
#                     else:
#                         discount_amount = min(coupon.discount_value, subtotal)
            
#             total_amount = subtotal + processing_fee - discount_amount
            
#             # Update order
#             order.user = user
#             order.base_amount = subtotal
#             order.processing_fee = processing_fee
#             order.total_amount = total_amount
#             order.payment_method = payment_method
#             order.applied_coupon = coupon
#             order.discount_amount = discount_amount
#             order.save()
            
#             # Update order items
#             order.order_items.all().delete()
#             for schart in charts:
#                 OrderItem.objects.create(
#                     order=order,
#                     chart=schart,
#                     chart_title_at_purchase=schart.title,
#                     price_at_purchase=schart.price,
#                 )
            
#             messages.success(request, 'Order updated successfully.')
#             return redirect('admin_order_detail', order_id=order_id)
            
#         except Exception as e:
#             messages.error(request, f'Error updating order: {str(e)}')
    
#     # GET request
#     users = User.objects.all().order_by('username')
#     charts = chart.objects.all().order_by('title')
#     coupons = Coupon.objects.filter(status='active').order_by('code')
#     current_charts = [item.chart for item in order.order_items.all()]
    
#     context = {
#         'order': order,
#         'users': users,
#         'charts': charts,
#         'coupons': coupons,
#         'current_charts': current_charts,
#     }
    
#     return render(request, 'edit_order.html', context)


# @login_required
# @user_passes_test(lambda user: user.is_staff or user.groups.filter(name='Admin').exists())
# def resend_payment_instructions(request, order_id):
#     """Resend payment instructions email for an order"""
#     order = get_object_or_404(Order, id=order_id)
#     if request.method == 'POST':
#         try:
#             payment_notes = request.POST.get('payment_notes', '')
#             payment_method = order.payment_method
#             # Handle payment method specific actions
#             payment_link = None
#             if payment_method == 'razorpay':
#                 # Create Razorpay payment link
#                 payment_link = order.razorpay_payment_id
#             if payment_method == 'completed':
#                 # Send invoice for completed order
#                 if send_invoice_email(order):
#                     messages.success(request, f'Payment instructions email sent to {order.user.email}')
#             elif payment_method == 'razorpay':
#                 # Send payment link email
#                 if payment_link and send_payment_link_email(order, payment_link, payment_notes):
#                     messages.success(request, f'Payment instructions email sent to {order.user.email}')
#             elif payment_method == 'bank_transfer':
#                 # Send bank transfer instructions
#                 if send_bank_transfer_email(order, payment_notes):
#                     messages.success(request, f'Payment instructions email sent to {order.user.email}')            
#         except Exception as e:
#             messages.error(request, f'Error sending email: {str(e)}')
    
#     return redirect('admin_order_detail', order_id=order_id)

@require_GET
def view_orgchart_temp(request, chart_uuid):
    try:
        chart_obj = chart.objects.get(uuid=chart_uuid)
    except chart.DoesNotExist:
        context = {
        'chart_title': '',
        'chart_uuid': chart_uuid,
    }
        return render(request, 'orgcharts/orgchart-temp.html', context)
    context = {
        'chart_title': chart_obj.title,
        'chart_uuid': chart_obj.uuid,
    }
    return render(request, 'orgcharts/orgchart-temp.html', context)

@require_GET
def view_chart_by_filename(request, file_name):
    """Handle old chart URL format /charts/<filename>"""
    # Remove .html extension if present
    if file_name.endswith('.html'):
        file_name = file_name[:-5]
    
    # URL decode the filename
    import urllib.parse
    decoded_filename = urllib.parse.unquote(file_name)
    
    try:
        # Try to find chart by title first
        chart_obj = chart.objects.filter(title__iexact=decoded_filename).first()
        if not chart_obj:
            # Try partial match
            chart_obj = chart.objects.filter(title__icontains=decoded_filename.split('-')[0]).first()
        
        if chart_obj:
            # Redirect to new UUID-based URL
            return redirect('view_orgchart_temp', chart_uuid=chart_obj.uuid)
        else:
            # If no chart found, render with empty context
            context = {
                'chart_title': decoded_filename,
                'chart_uuid': '',
                'error_message': f'Chart "{decoded_filename}" not found'
            }
            return render(request, 'orgcharts/orgchart-temp.html', context)
            
    except Exception as e:
        # Fallback to error page
        context = {
            'chart_title': decoded_filename,
            'chart_uuid': '',
            'error_message': f'Error loading chart: {str(e)}'
        }
        return render(request, 'orgcharts/orgchart-temp.html', context)

def is_superadmin(user):
        return hasattr(user, 'userprofile') and getattr(user.userprofile, 'is_superadmin', False)

@login_required
def view_chart_preview(request, chart_id):
    """
    View function for the 'ORG CHART' button in marketplace.
    Shows a preview of the organizational chart.
    """
    try:
        chart_instance = get_object_or_404(chart, pk=chart_id)
        
        # Check if user has access or chart is public in marketplace
        user_has_access = False
        if request.user.is_staff and request.user.groups.filter(name='Admin').exists():
            user_has_access = True
        elif hasattr(request.user, 'userprofile') and request.user.userprofile.is_superadmin:
            user_has_access = True
        elif chart_instance.allowed_users.filter(id=request.user.id).exists():
            user_has_access = True
        else:
            # For marketplace preview, allow limited preview
            user_has_access = True
        
        if user_has_access:
            # Redirect to the chart viewing page
            return redirect('view_orgchart_temp', chart_uuid=chart_instance.uuid)
        else:
            messages.error(request, "You don't have permission to view this chart.")
            return redirect('marketplace_dash')
            
    except Exception as e:
        messages.error(request, f"Error accessing chart: {str(e)}")
        return redirect('marketplace_dash')

def view_chart_blurred_preview(request, chart_id):
    """
    View function for the 'ORG CHART' button in marketplace.
    Shows a blurred/limited preview of the organizational chart with restricted functionality.
    
    IMPORTANT: This view is PUBLIC and accessible without login.
    Anyone can access preview org charts regardless of authentication status.
    """
    try:
        chart_instance = get_object_or_404(chart, pk=chart_id)
        
        # Log access for debugging (can be removed in production)
        user_status = "authenticated" if request.user.is_authenticated else "anonymous"
        print(f"Preview access by {user_status} user for chart ID: {chart_id}")
        
        # For preview mode, we don't need the actual data file
        # The template will use the original chart data but apply blurring
        context = {
            'chart_title': chart_instance.title,
            'chart_uuid': chart_instance.uuid,
            'chart_data': None,  # Let the template handle data loading
            'chart': chart_instance,
            'total_employees': chart_instance.personCount,
            'is_preview_mode': True,
            'has_preview_version': chart_instance.has_preview_version,
            'user_can_purchase': True,  # Always allow purchase redirect
            'is_authenticated': request.user.is_authenticated,  # Pass auth status for UI
            'user': request.user if request.user.is_authenticated else None,
            'access_type': 'Public Preview - No Login Required',
        }
        
        return render(request, 'orgcharts/orgchart-blurred-preview.html', context)
        
    except Exception as e:
        # If there's any error, provide a minimal context
        # Still accessible to anonymous users
        print(f"Error in preview for chart {chart_id}: {str(e)}")
        context = {
            'chart_title': 'Organization Chart Preview',
            'chart_uuid': 'preview-demo',
            'chart_data': None,
            'chart': None,
            'total_employees': 52,
            'is_preview_mode': True,
            'has_preview_version': False,
            'user_can_purchase': True,
            'is_authenticated': request.user.is_authenticated,
            'user': request.user if request.user.is_authenticated else None,
            'access_type': 'Public Preview - No Login Required',
        }
        return render(request, 'orgcharts/orgchart-blurred-preview.html', context)

@login_required  
def download_chart_sample(request, chart_id):
    """
    View function for the 'GET SAMPLE' button in marketplace.
    Downloads a sample/preview version of the chart data.
    """
    try:
        chart_instance = get_object_or_404(chart, pk=chart_id)
        
        # Create sample CSV with limited data (first 10 rows)
        file_path = os.path.join(settings.MEDIA_ROOT, "csv_files", f"{chart_instance.title}.csv")
        
        if os.path.exists(file_path):
            import csv
            import io
            
            # Read original CSV and create sample
            sample_data = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader, None)  # Get headers
                if headers:
                    sample_data.append(headers)
                    
                    # Add first 10 data rows
                    for i, row in enumerate(reader):
                        if i < 10:  # Limit to first 10 rows for sample
                            sample_data.append(row)
                        else:
                            break
            
            # Create CSV response
            output = io.StringIO()
            writer = csv.writer(output)
            for row in sample_data:
                writer.writerow(row)
            
            response = HttpResponse(
                output.getvalue().encode('utf-8'),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{chart_instance.title}_sample.csv"'
            
            # Add success message
            messages.success(request, f"Sample data for '{chart_instance.title}' downloaded successfully!")
            
            return response
        else:
            messages.error(request, "Sample data not available for this chart.")
            return redirect('marketplace_dash')
            
    except Exception as e:
        messages.error(request, f"Error downloading sample: {str(e)}")
        return redirect('marketplace_dash')

@csrf_exempt
def request_sample_ajax(request):
    """
    Handle AJAX request for sample request form submission.
    """
    if request.method == 'POST':
        try:
            import json
            from .models import SampleRequest
            
            data = json.loads(request.body)
            
            email = data.get('email', '').strip()
            requirements = data.get('requirements', '').strip()
            chart_id = data.get('chart_id')
            chart_title = data.get('chart_title', '')
            
            # Basic validation
            if not email or not requirements:
                return JsonResponse({
                    'success': False,
                    'message': 'Email and requirements are required.'
                })
            
            # Get chart instance
            try:
                chart_instance = chart.objects.get(pk=chart_id)
            except chart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Chart not found.'
                })
            
            # Get user if authenticated
            current_user = request.user if request.user.is_authenticated else None
            
            # Save the sample request to database
            sample_request = SampleRequest.objects.create(
                email=email,
                requirements=requirements,
                chart=chart_instance,
                chart_title=chart_title,
                user=current_user,
                status='pending'
            )
            
            # Log the request for debugging
            print(f"Sample request created with ID: {sample_request.id}")
            print(f"Chart: {chart_title} (ID: {chart_id})")
            print(f"Email: {email}")
            print(f"Requirements: {requirements}")
            
            # Optional: Send email notification to admin here
            # You can implement email notification logic if needed
            
            return JsonResponse({
                'success': True,
                'message': 'Sample request submitted successfully! We will review your request and contact you shortly.',
                'request_id': sample_request.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing request: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })