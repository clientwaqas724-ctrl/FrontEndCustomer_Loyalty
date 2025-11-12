from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import force_bytes
from django.shortcuts import render, redirect,reverse
from django.contrib import messages
import requests
import json
import base64
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, Alignment
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from django.core.paginator import Paginator
from datetime import datetime, time
import pytz
############################################################################################################################################################
##########################################################################################################################################################
def index(request):
    context = {
        'active_merchants': 24,  # You can get these from your models
        'active_coupons': 156,
        'running_promotions': 42,
        'merchant_outlets': 89,
    }
    return render(request, 'My_Home/index.html', context)
############################################################################################################################################################
##########################################################################################################################################################
# New view for rendering registration template and handling form submission
def register_page(request):
    context = {}
    if request.method == 'POST':
        # Collect form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        role = request.POST.get('role', 'admin')  # Default to admin for registration page
        tc = bool(request.POST.get('tc', False))
        
        # Handle profile image
        profile_image = ""
        profile_image_file = request.FILES.get('profile_image')
        
        if profile_image_file:
            # Validate file type
            valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if profile_image_file.content_type not in valid_types:
                messages.error(request, "Please select a valid image file (JPEG, JPG, PNG, GIF)")
                return render(request, 'My_Home/User/register.html', context)
            
            # Validate file size (max 5MB)
            if profile_image_file.size > 5 * 1024 * 1024:
                messages.error(request, "Image size must be less than 5MB")
                return render(request, 'My_Home/User/register.html', context)
            
            # Convert image to base64
            try:
                image_data = profile_image_file.read()
                profile_image = base64.b64encode(image_data).decode('utf-8')
            except Exception as e:
                messages.error(request, f"Error processing image: {str(e)}")
                return render(request, 'My_Home/User/register.html', context)
        
        # Basic validation
        errors = []
        
        if not name or len(name) < 2:
            errors.append("Please enter a valid name (at least 2 characters)")
        
        if not email or '@' not in email:
            errors.append("Please enter a valid email address")
        
        if not phone:
            errors.append("Please enter a phone number")
        
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not role:
            errors.append("Please select a role")
        
        if not tc:
            errors.append("You must agree to the terms and conditions")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            # Preserve form data
            context.update({
                'name': name,
                'email': email,
                'phone': phone,
                'role': role,
            })
            return render(request, 'My_Home/User/register.html', context)
        
        # Prepare data for API
        data = {
            "email": email,
            "name": name,
            "tc": tc,
            "password": password,
            "password2": confirm_password,
            "role": role,
            "phone": phone,
            "profile_image": profile_image
        }
        
        # Make API request
        api_url = "https://http-127-0-0-1-8000-vst6.onrender.com/api/user/register/"
        
        try:
            response = requests.post(
                api_url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            debug_info = f"HTTP Status: {response.status_code}\n"
            debug_info += f"Request Data: {json.dumps(data, indent=2)}\n"
            debug_info += f"Response: {response.text}\n"
            
            if response.status_code in [200, 201]:
                messages.success(request, "Admin account created successfully!")
                # Optionally redirect to login page after success
                # return redirect('login')
            else:
                response_data = response.json()
                error_message = "An error occurred while creating the account."
                
                # Extract specific error messages from API response
                if 'email' in response_data:
                    error_message = response_data['email'][0] if isinstance(response_data['email'], list) else response_data['email']
                elif 'detail' in response_data:
                    error_message = response_data['detail']
                elif 'non_field_errors' in response_data:
                    error_message = response_data['non_field_errors'][0] if isinstance(response_data['non_field_errors'], list) else response_data['non_field_errors']
                elif 'password' in response_data:
                    error_message = response_data['password'][0] if isinstance(response_data['password'], list) else response_data['password']
                elif 'phone' in response_data:
                    error_message = response_data['phone'][0] if isinstance(response_data['phone'], list) else response_data['phone']
                
                messages.error(request, error_message)
                context['debug_info'] = debug_info
                
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Connection error: {str(e)}")
    
    return render(request, 'My_Home/User/register.html', context)
#############################################################################################################################################################
MERCHANTS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/merchants/'
PROMOTIONS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/promotions/'
COUPONS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/coupons/'
OUTLETS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/outlets/'
USER_PROFILE_API = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/update/'
##########################################################################################################################################################
def admin_dashboard(request):
    """
    Admin dashboard view that fetches user profile and real-time data from APIs
    """
    # Check login session
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect(f'{reverse("login")}?next={request.path}')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # --- Fetch User Profile ---
    user_profile = request.session.get('user_profile')
    if not user_profile:
        try:
            resp = requests.get(USER_PROFILE_API, headers=headers)
            if resp.status_code == 200:
                user_profile = resp.json()
                request.session['user_profile'] = user_profile
            else:
                user_profile = {}
        except Exception as e:
            messages.error(request, f'Error fetching profile: {e}')
            user_profile = {}

    # --- Fetch Merchants ---
    merchants = []
    try:
        resp = requests.get(MERCHANTS_API_URL, headers=headers)
        if resp.status_code == 200:
            merchants = resp.json()
    except Exception as e:
        messages.error(request, f'Error fetching merchants: {e}')

    # --- Fetch Promotions ---
    promotions = []
    try:
        resp = requests.get(PROMOTIONS_API_URL, headers=headers)
        if resp.status_code == 200:
            promotions = resp.json()
    except Exception as e:
        messages.error(request, f'Error fetching promotions: {e}')

    # --- Fetch Coupons ---
    coupons = []
    try:
        resp = requests.get(COUPONS_API_URL, headers=headers)
        if resp.status_code == 200:
            coupons = resp.json()
    except Exception as e:
        messages.error(request, f'Error fetching coupons: {e}')

    # --- Fetch Outlets ---
    outlets = []
    try:
        resp = requests.get(OUTLETS_API_URL, headers=headers)
        if resp.status_code == 200:
            outlets = resp.json()
    except Exception as e:
        messages.error(request, f'Error fetching outlets: {e}')

    # --- Totals ---
    total_merchants = len(merchants)
    total_promotions = len(promotions)
    total_coupons = len(coupons)
    total_outlets = len(outlets)

    # --- Chart Data (Example Trend) ---
    performance_data = {
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "merchants": [max(1, total_merchants - 5), max(1, total_merchants - 3), total_merchants],
        "coupons": [max(1, total_coupons - 2), total_coupons - 1 if total_coupons > 1 else 1, total_coupons],
        "promotions": [max(1, total_promotions - 2), total_promotions - 1 if total_promotions > 1 else 1, total_promotions],
    }

    context = {
        'user_profile': user_profile or {},
        'title': 'Admin Dashboard',
        'merchants': merchants,
        'total_merchants': total_merchants,
        'total_coupons': total_coupons,
        'total_outlets': total_outlets,
        'total_promotions': total_promotions,
        'performance_data': performance_data,
    }
    return render(request, 'My_Admin/My_Admin.html', context)
#############################################################################################################################################################
##########################################################################################################################################################
def login_page(request):
    """
    Login view that uses the API for authentication
    """
    context = {}
    
    # Handle redirect after login
    next_url = request.GET.get('next', '')
    if next_url:
        context['next'] = next_url
    
    if request.method == 'POST':
        # Collect form data
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember_me = bool(request.POST.get('remember', False))
        next_url = request.POST.get('next', '')
        
        # Basic validation
        errors = []
        if not email or '@' not in email:
            errors.append("Please enter a valid email address")
        if not password:
            errors.append("Please enter your password")
        if errors:
            for error in errors:
                messages.error(request, error)
            # Preserve form data
            context.update({
                'email': email,
                'next': next_url
            })
            return render(request, 'My_Home/User/login.html', context)

        # Prepare data for API
        data = {
            "email": email,
            "password": password,
        }
        # Make API request to login endpoint
        api_url = "https://http-127-0-0-1-8000-vst6.onrender.com/api/user/login/"
        try:
            response = requests.post(
                api_url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Store tokens and user data in session
                request.session['access_token'] = response_data['token']['access']
                request.session['refresh_token'] = response_data['token']['refresh']
                request.session['user_data'] = response_data['user']
                
                # Set session expiry based on remember me
                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks
                else:
                    request.session.set_expiry(3600)  # 1 hour
                
                messages.success(request, response_data.get('message', 'Login successful!'))
                
                # Redirect based on user role or next parameter
                user_role = response_data['user']['role']
                
                # If there's a next parameter, redirect there
                if next_url:
                    return redirect(next_url)
                
                # Otherwise, redirect based on role
                return redirect_user_by_role(request, user_role)
                
            else:
                response_data = response.json()
                error_message = "Invalid email or password. Please try again."
                
                # Extract specific error messages from API response
                if 'non_field_errors' in response_data:
                    error_message = response_data['non_field_errors'][0] if isinstance(response_data['non_field_errors'], list) else response_data['non_field_errors']
                elif 'email' in response_data:
                    error_message = response_data['email'][0] if isinstance(response_data['email'], list) else response_data['email']
                elif 'password' in response_data:
                    error_message = response_data['password'][0] if isinstance(response_data['password'], list) else response_data['password']
                elif 'detail' in response_data:
                    error_message = response_data['detail']
                
                messages.error(request, error_message)
                context.update({
                    'email': email,  # Preserve email
                    'next': next_url
                })
                
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Connection error: {str(e)}")
            context.update({
                'email': email,  # Preserve email
                'next': next_url
            })
    
    return render(request, 'My_Home/User/login.html', context)
#############################################################################################################################################################
##########################################################################################################################################################
def redirect_user_by_role(request, role):
    """Redirect user based on their role after login"""
    role_redirects = {
        'admin': 'admin_dashboard',
        # Add other roles as needed
    }
    redirect_view = role_redirects.get(role, 'admin_dashboard')
    return redirect(redirect_view)
#############################################################################################################################################################
##########################################################################################################################################################
def logout_view(request):
    """
    Logout view that clears session
    """
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')
#############################################################################################################################################################
##########################################################################################################################################################
# Base API URLs
MERCHANTS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/merchants/'
USER_PROFILES_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/'
OUTLETS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/outlets/'
#############################################################################################################################################################
##########################################################################################################################################################
# Base API URLs
MERCHANTS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/merchants/'
USER_PROFILES_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/'
##########################################################################################################################################################
##########################################################################################################################################################
def get_current_user_from_api(request):
    """
    Helper function to fetch current user from profile API with authentication
    """
    try:
        access_token = request.session.get('access_token')
        if not access_token:
            return None
            
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get current user profile
        response = requests.get(USER_PROFILES_API_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
            
    except requests.RequestException:
        return None
#############################################################################################################################################################
##########################################################################################################################################################
def add_merchant(request):
    """
    Add a new merchant.
    - Shows all outlets.
    - No outlet check before creating merchant (removed validation).
    """
    user_profile = request.session.get('user_profile')
    if not user_profile:
        user_profile = get_current_user_from_api(request)
        if user_profile:
            request.session['user_profile'] = user_profile

    users = [user_profile] if user_profile else []
    outlets = []
    token = request.session.get('access_token')

    # ------------------------------------------------------------
    # Fetch outlets from API
    # ------------------------------------------------------------
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            outlet_resp = requests.get(OUTLETS_API_URL, headers=headers)
            if outlet_resp.status_code == 200:
                outlets = outlet_resp.json()
            else:
                messages.warning(request, f"Failed to load outlets (HTTP {outlet_resp.status_code})")
        except requests.RequestException as e:
            messages.error(request, f"Error fetching outlets: {str(e)}")

    # ------------------------------------------------------------
    # Handle POST (create merchant directly)
    # ------------------------------------------------------------
    if request.method == 'POST':
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        merchant_data = {
            'user': request.POST.get('user'),
            'company_name': request.POST.get('company_name'),
            'logo_url': request.POST.get('logo_url'),
            'status': request.POST.get('status'),
            'outlet': request.POST.get('outlet')
        }

        # Basic validation only
        if not merchant_data['user'] or not merchant_data['outlet']:
            messages.error(request, "Please select both a user and an outlet.")
            return redirect('add_merchant')

        try:
            # ✅ Directly create merchant (no outlet or user check)
            create_resp = requests.post(MERCHANTS_API_URL, json=merchant_data, headers=headers)

            if create_resp.status_code == 201:
                messages.success(request, "✅ Merchant created successfully and outlet assigned.")
                return redirect('merchant_list')
            else:
                try:
                    err_data = create_resp.json()
                    messages.error(request, f"Failed to create merchant: {err_data}")
                except Exception:
                    messages.error(request, f"Failed to create merchant (HTTP {create_resp.status_code})")

        except requests.RequestException as e:
            messages.error(request, f"Error communicating with API: {str(e)}")

    # ------------------------------------------------------------
    # Render page
    # ------------------------------------------------------------
    context = {
        'users': users,
        'outlets': outlets,
        'user_profile': user_profile or {}
    }
    return render(request, 'My_Admin/My_Marcant/add_merchant.html', context)

#############################################################################################################################################################
##########################################################################################################################################################
def get_users_from_api():
    """
    Helper function to fetch all users (if available)
    This might need a different API endpoint
    """
    try:
        # You'll need to implement this based on your API
        # This is just a placeholder - adjust according to your actual API
        response = requests.get('https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/')  # Adjust URL
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []
#############################################################################################################################################################
##########################################################################################################################################################
def merchant_list(request):
    """
    View to display all merchants
    """
    try:
        # Get current user profile for top bar
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
        
        # Fetch merchants from API
        response = requests.get(MERCHANTS_API_URL)
        merchants = []
        
        if response.status_code == 200:
            merchants_data = response.json()
            
            # Handle both list and single object responses
            if isinstance(merchants_data, list):
                merchants = merchants_data
            else:
                # If API returns a single object, wrap it in a list
                merchants = [merchants_data] if merchants_data else []
            
            # Debug: Print merchants data to console
            print("Merchants data received:", merchants)
            
        else:
            messages.error(request, f'Failed to load merchants from API. Status: {response.status_code}')
            print(f"API Error: {response.status_code} - {response.text}")
            
        context = {
            'merchants': merchants,
            'user_profile': user_profile or {}
        }
        return render(request, 'My_Admin/My_Marcant/merchant_list.html', context)
        
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        context = {
            'merchants': [],
            'user_profile': get_current_user_from_api(request) or {}
        }
        return render(request, 'My_Admin/My_Marcant/merchant_list.html', context)
#############################################################################################################################################################
##########################################################################################################################################################
def update_merchant(request, merchant_id):
    """
    View to update a merchant's details
    """
    try:
        # Get current user profile for top bar
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
            return redirect('login')

        # Fetch existing merchant data
        merchant_url = f"{MERCHANTS_API_URL}{merchant_id}/"
        response = requests.get(merchant_url)
        
        if response.status_code != 200:
            messages.error(request, f'Merchant not found. Status: {response.status_code}')
            return redirect('merchant_list')
        
        merchant_data = response.json()

        if request.method == 'POST':
            # Prepare update data
            update_data = {
                'user': merchant_data.get('user'),  # Keep original user
                'company_name': request.POST.get('company_name'),
                'logo_url': request.POST.get('logo_url'),
                'status': request.POST.get('status')
            }

            # Send PUT request to update merchant
            update_response = requests.put(merchant_url, json=update_data)
            
            if update_response.status_code == 200:
                messages.success(request, 'Merchant updated successfully!')
                return redirect('merchant_list')
            else:
                messages.error(request, f'Failed to update merchant. Status: {update_response.status_code}')
                print(f"Update Error: {update_response.status_code} - {update_response.text}")

        context = {
            'merchant': merchant_data,
            'user_profile': user_profile or {}
        }
        return render(request, 'My_Admin/My_Marcant/merchant_form.html', context)
        
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return redirect('merchant_list')
#############################################################################################################################################################
##########################################################################################################################################################
def delete_merchant(request, merchant_id):
    """
    Individual view to delete a merchant with confirmation page
    """
    try:
        # Get current user profile
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
            return redirect('login')

        # Fetch merchant details for confirmation page
        merchant_url = f"{MERCHANTS_API_URL}{merchant_id}/"
        response = requests.get(merchant_url)
        
        if response.status_code != 200:
            messages.error(request, f'Merchant not found. Status: {response.status_code}')
            return redirect('merchant_list')
        
        merchant_data = response.json()

        if request.method == 'POST':
            # Send DELETE request to API
            headers = {
                'Content-Type': 'application/json',
            }
            
            delete_response = requests.delete(merchant_url, headers=headers)
            
            print(f"DELETE Request to: {merchant_url}")
            print(f"DELETE Response Status: {delete_response.status_code}")
            print(f"DELETE Response Text: {delete_response.text}")
            
            if delete_response.status_code in [200, 204]:  # 200 OK or 204 No Content
                messages.success(request, f'Merchant "{merchant_data.get("company_name", "Unknown")}" deleted successfully!')
                print("Merchant deleted successfully")
                return redirect('merchant_list')
            elif delete_response.status_code == 404:
                messages.error(request, 'Merchant not found. It may have been already deleted.')
                print("Merchant not found")
                return redirect('merchant_list')
            else:
                messages.error(request, f'Failed to delete merchant. Status: {delete_response.status_code}')
                print(f"Delete Error: {delete_response.status_code} - {delete_response.text}")
                return redirect('merchant_list')

        # If GET request, show confirmation page
        context = {
            'merchant': merchant_data,
            'user_profile': user_profile or {}
        }
        return render(request, 'My_Admin/My_Marcant/merchant_confirm_delete.html', context)
        
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        print(f"Request Exception: {str(e)}")
        return redirect('merchant_list')
#############################################################################################################################################################
##########################################################################################################################################################
def get_api_headers(request):
    """Helper function to get API headers with authentication"""
    access_token = request.session.get('access_token')
    headers = {
        'Content-Type': 'application/json'
    }
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    return headers

##########################################################################################################################################################
##########################################################################################################################################################
def add_outlet(request):
    """Add a new outlet"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page.')
        return redirect('login')

    malaysian_states = [
        'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan',
        'Melaka', 'Negeri Sembilan', 'Pahang', 'Penang', 'Perak',
        'Perlis', 'Putrajaya', 'Sabah', 'Sarawak', 'Selangor', 'Terengganu'
    ]

    headers = get_api_headers(request)

    if request.method == 'POST':
        # Collect form fields
        outlet_data = {
            'merchant': request.POST.get('merchant'),
            'name': request.POST.get('name'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'state': request.POST.get('state'),
            'country': request.POST.get('country'),
            'postal_code': request.POST.get('postal_code'),
            'latitude': request.POST.get('latitude'),
            'longitude': request.POST.get('longitude'),
            'contact_number': request.POST.get('contact_number'),
            'email': request.POST.get('email'),
        }

        image_url = request.POST.get('outlet_image_url')
        image_file = request.FILES.get('outlet_image')

        # ✅ Removed frontend validation for "one outlet per merchant"
        # (This logic is now handled by backend)

        # Prepare data for submission
        files = {}
        data = {k: v for k, v in outlet_data.items() if v}

        if image_file:
            files['outlet_image'] = image_file
        elif image_url:
            data['outlet_image_url'] = image_url

        try:
            # POST request to API
            if files:
                post_response = requests.post(OUTLETS_API_URL, headers=headers, data=data, files=files)
            else:
                headers['Content-Type'] = 'application/json'
                post_response = requests.post(OUTLETS_API_URL, headers=headers, data=json.dumps(data))

            # Handle response
            if post_response.status_code in [200, 201]:
                messages.success(request, 'Outlet created successfully!')
                return redirect('outlet_list')

            # Check Content-Type to safely parse JSON
            content_type = post_response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    error_data = post_response.json()
                    error_message = 'Failed to create outlet. '
                    if 'detail' in error_data:
                        error_message += str(error_data['detail'])
                    else:
                        for field, errors in error_data.items():
                            if isinstance(errors, list):
                                error_message += f"{field}: {', '.join(errors)}; "
                            else:
                                error_message += f"{field}: {errors}; "
                    messages.error(request, error_message)
                except ValueError:
                    messages.error(request, f"Failed to create outlet. Invalid JSON response: {post_response.text[:300]}")
            else:
                messages.error(request, f"Failed to create outlet. Unexpected response type: {post_response.text[:300]}")

            return redirect('add_outlet')

        except requests.RequestException as e:
            messages.error(request, f"API connection error: {str(e)}")
            return redirect('add_outlet')
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('add_outlet')

    # --- GET method: fetch merchants ---
    try:
        merchant_response = requests.get(MERCHANTS_API_URL, headers=headers)
        merchants_data = merchant_response.json() if merchant_response.status_code == 200 else []
        merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
    except Exception:
        merchants = []
        messages.error(request, 'Error fetching merchant list.')

    context = {
        'user_profile': user_profile,
        'merchants': merchants,
        'malaysian_states': malaysian_states,
        'access_token': request.session.get('access_token'),
        'OUTLETS_API_URL': OUTLETS_API_URL
    }

    return render(request, 'My_Admin/My_Outlets/add_outlet.html', context)
##########################################################################################################################################################
##########################################################################################################################################################
def outlet_list(request):
    """View to display list of outlets in both card and table view"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    # Get view type and search query
    view_type = request.GET.get('view', 'card')  # Default to card view
    search_query = request.GET.get('search', '')
    
    # Fetch outlets from API
    headers = get_api_headers(request)
    params = {}
    if search_query:
        params['search'] = search_query
    
    try:
        response = requests.get(OUTLETS_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            outlets_data = response.json()
            
            # Handle pagination if API returns paginated results
            if 'results' in outlets_data:
                raw_outlets = outlets_data['results']
            else:
                raw_outlets = outlets_data
            
            # Process outlets to include all required fields and default timing
            processed_outlets = []
            for outlet in raw_outlets:
                # Get current Malaysia time for default timing
                malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
                current_time = datetime.now(malaysia_tz)
                
                processed_outlet = {
                    'id': outlet.get('id'),
                    'name': outlet.get('name'),
                    'merchant_name': get_merchant_name(outlet),
                    'address': outlet.get('address'),
                    'city': outlet.get('city'),
                    'state': outlet.get('state'),
                    'country': outlet.get('country'),
                    'postal_code': outlet.get('postal_code'),
                    'latitude': outlet.get('latitude'),
                    'longitude': outlet.get('longitude'),
                    'contact_number': outlet.get('contact_number'),
                    'email': outlet.get('email'),
                    'outlet_image': outlet.get('outlet_image'),
                    'outlet_image_url': outlet.get('outlet_image_url'),
                    'created_at': outlet.get('created_at'),
                    'updated_at': outlet.get('updated_at'),
                    # Default timing (current day)
                    'opening_time': time(9, 0).strftime('%I:%M %p'),  # 9:00 AM
                    'closing_time': time(21, 0).strftime('%I:%M %p'), # 9:00 PM
                    'current_day': current_time.strftime('%A'),
                    'is_open': True  # Default to open
                }
                processed_outlets.append(processed_outlet)
            
            # Paginate results
            paginator = Paginator(processed_outlets, 12 if view_type == 'card' else 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'user_profile': user_profile,
                'outlets': page_obj,
                'view_type': view_type,
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            }
            return render(request, 'My_Admin/My_Outlets/outlet_list.html', context)
        else:
            messages.error(request, f'Failed to fetch outlets from API: {response.status_code}')
            return render(request, 'My_Admin/My_Outlets/outlet_list.html', {
                'user_profile': user_profile,
                'outlets': [],
                'view_type': view_type,
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            })
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return render(request, 'My_Admin/My_Outlets/outlet_list.html', {
            'user_profile': user_profile,
            'outlets': [],
            'view_type': view_type,
            'search_query': search_query,
            'access_token': request.session.get('access_token')
        })
###################################################################################################################################################################
def get_merchant_name(outlet):
    """Extract merchant name from various possible field structures"""
    merchant = outlet.get('merchant', {})
    if isinstance(merchant, dict):
        return merchant.get('company_name') or merchant.get('name') or merchant.get('username') or merchant.get('email')
    return str(merchant)
##########################################################################################################################################################
##########################################################################################################################################################
def edit_outlet(request, outlet_id):
    """Edit an existing outlet"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page.')
        return redirect('login')

    malaysian_states = [
        'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan',
        'Melaka', 'Negeri Sembilan', 'Pahang', 'Penang', 'Perak',
        'Perlis', 'Putrajaya', 'Sabah', 'Sarawak', 'Selangor', 'Terengganu'
    ]

    headers = get_api_headers(request)

    try:
        # Fetch existing outlet data
        outlet_response = requests.get(f"{OUTLETS_API_URL}{outlet_id}/", headers=headers)
        if outlet_response.status_code != 200:
            messages.error(request, 'Failed to fetch outlet data.')
            return redirect('outlet_list')
        outlet = outlet_response.json()
    except Exception as e:
        messages.error(request, f"Error fetching outlet: {str(e)}")
        return redirect('outlet_list')

    if request.method == 'POST':
        # Collect form fields
        outlet_data = {
            'merchant': request.POST.get('merchant'),
            'name': request.POST.get('name'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'state': request.POST.get('state'),
            'country': request.POST.get('country'),
            'postal_code': request.POST.get('postal_code'),
            'latitude': request.POST.get('latitude'),
            'longitude': request.POST.get('longitude'),
            'contact_number': request.POST.get('contact_number'),
            'email': request.POST.get('email'),
        }

        image_url = request.POST.get('outlet_image_url')
        image_file = request.FILES.get('outlet_image')

        # Prepare data and files
        files = {}
        data = {k: v for k, v in outlet_data.items() if v}

        if image_file:
            files['outlet_image'] = image_file
        elif image_url:
            data['outlet_image_url'] = image_url

        try:
            # Send PUT request
            if files:
                put_response = requests.put(f"{OUTLETS_API_URL}{outlet_id}/", headers=headers, data=data, files=files)
            else:
                headers['Content-Type'] = 'application/json'
                put_response = requests.put(f"{OUTLETS_API_URL}{outlet_id}/", headers=headers, data=json.dumps(data))

            # Handle response
            if put_response.status_code in [200, 201]:
                messages.success(request, 'Outlet updated successfully!')
                return redirect('outlet_list')

            # Parse JSON errors
            content_type = put_response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    error_data = put_response.json()
                    error_message = 'Failed to update outlet. '
                    if 'detail' in error_data:
                        error_message += str(error_data['detail'])
                    else:
                        for field, errors in error_data.items():
                            if isinstance(errors, list):
                                error_message += f"{field}: {', '.join(errors)}; "
                            else:
                                error_message += f"{field}: {errors}; "
                    messages.error(request, error_message)
                except ValueError:
                    messages.error(request, f"Failed to update outlet. Invalid JSON response: {put_response.text[:300]}")
            else:
                messages.error(request, f"Failed to update outlet. Unexpected response type: {put_response.text[:300]}")

            return redirect('edit_outlet', outlet_id=outlet_id)

        except requests.RequestException as e:
            messages.error(request, f"API connection error: {str(e)}")
            return redirect('edit_outlet', outlet_id=outlet_id)
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('edit_outlet', outlet_id=outlet_id)

    # --- GET method: fetch merchants ---
    try:
        merchant_response = requests.get(MERCHANTS_API_URL, headers=headers)
        merchants_data = merchant_response.json() if merchant_response.status_code == 200 else []
        merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
    except Exception:
        merchants = []
        messages.error(request, 'Error fetching merchant list.')

    context = {
        'user_profile': user_profile,
        'outlet': outlet,
        'merchants': merchants,
        'malaysian_states': malaysian_states,
        'access_token': request.session.get('access_token'),
        'OUTLETS_API_URL': OUTLETS_API_URL
    }

    return render(request, 'My_Admin/My_Outlets/edit_outlet.html', context)
##########################################################################################################################################################
def delete_outlet(request, outlet_id):
    """
    Individual view to delete an outlet with confirmation page
    """
    try:
        # Get current user profile
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
            return redirect('login')

        # Fetch outlet details for confirmation page
        outlet_url = f"{OUTLETS_API_URL}{outlet_id}/"
        headers = get_api_headers(request)
        
        response = requests.get(outlet_url, headers=headers)
        
        if response.status_code != 200:
            messages.error(request, f'Outlet not found. Status: {response.status_code}')
            return redirect('outlet_list')
        
        outlet_data = response.json()

        if request.method == 'POST':
            print(f"Processing POST request to delete outlet: {outlet_id}")
            
            # Send DELETE request to API
            delete_response = requests.delete(outlet_url, headers=headers)
            
            print(f"DELETE Request to: {outlet_url}")
            print(f"DELETE Response Status: {delete_response.status_code}")
            print(f"DELETE Response Headers: {delete_response.headers}")
            
            if delete_response.status_code in [200, 204]:  # 200 OK or 204 No Content
                messages.success(request, f'Outlet "{outlet_data.get("name", "Unknown")}" deleted successfully!')
                print("Outlet deleted successfully")
                return redirect('outlet_list')
            elif delete_response.status_code == 404:
                messages.error(request, 'Outlet not found. It may have been already deleted.')
                print("Outlet not found")
                return redirect('outlet_list')
            else:
                # Try to get more detailed error information
                try:
                    error_detail = delete_response.json()
                    error_message = f'Failed to delete outlet. Error: {error_detail}'
                except:
                    error_message = f'Failed to delete outlet. Status: {delete_response.status_code}'
                
                messages.error(request, error_message)
                print(f"Delete Error: {delete_response.status_code} - {delete_response.text}")
                return redirect('outlet_list')

        # If GET request, show confirmation page
        print(f"Showing confirmation page for outlet: {outlet_id}")
        context = {
            'outlet': outlet_data,
            'user_profile': user_profile or {}
        }
        # Use the correct template path
        return render(request, 'My_Admin/My_Outlets/outlet_confirm_delete.html', context)
        
    except requests.RequestException as e:
        error_msg = f'Error connecting to API: {str(e)}'
        messages.error(request, error_msg)
        print(f"Request Exception: {str(e)}")
        return redirect('outlet_list')
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        messages.error(request, error_msg)
        print(f"Unexpected Exception: {str(e)}")
        return redirect('outlet_list')
##########################################################################################################################################################
##########################################################################################################################################################
COUPONS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/coupons/'
##########################################################################################################################################################
##########################################################################################################################################################
def coupon_list(request):
    """View to display list of coupons"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Fetch coupons from API
    headers = get_api_headers(request)
    params = {}
    if search_query:
        params['search'] = search_query
    
    try:
        response = requests.get(COUPONS_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            coupons_data = response.json()
            
            # Handle pagination if API returns paginated results
            if 'results' in coupons_data:
                raw_coupons = coupons_data['results']
            else:
                raw_coupons = coupons_data
            
            # Process coupons to ensure consistent field names
            processed_coupons = []
            for coupon in raw_coupons:
                processed_coupon = {
                    'id': coupon.get('id'),
                    'title': coupon.get('title'),
                    'merchant': coupon.get('merchant'),
                    'merchant_name': get_merchant_name(coupon),
                    'description': coupon.get('description'),
                    'points_required': coupon.get('points_required'),
                    'expiry_date': coupon.get('expiry_date'),
                    'status': coupon.get('status'),
                    'created_at': coupon.get('created_at') or coupon.get('created')
                }
                processed_coupons.append(processed_coupon)
            
            # Paginate results (10 per page)
            paginator = Paginator(processed_coupons, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'user_profile': user_profile,
                'coupons': page_obj,
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            }
            return render(request, 'My_Admin/My_Coupon/View_Coupon.html', context)
        else:
            messages.error(request, f'Failed to fetch coupons from API: {response.status_code}')
            return render(request, 'My_Admin/My_Coupon/View_Coupon.html', {
                'user_profile': user_profile,
                'coupons': [],
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            })
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return render(request, 'My_Admin/My_Coupon/View_Coupon.html', {
            'user_profile': user_profile,
            'coupons': [],
            'search_query': search_query,
            'access_token': request.session.get('access_token')
        })

def add_coupon(request):
    """View to add a new coupon"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    # Handle POST request - traditional form submission
    if request.method == 'POST':
        # Get form data
        coupon_data = {
            'merchant': request.POST.get('merchant'),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'points_required': request.POST.get('points_required'),
            'expiry_date': request.POST.get('expiry_date'),
            'status': request.POST.get('status')
        }
        
        # Send to API
        headers = get_api_headers(request)
        try:
            response = requests.post(COUPONS_API_URL, headers=headers, data=json.dumps(coupon_data))
            
            if response.status_code == 201:
                messages.success(request, 'Coupon created successfully!')
                return redirect('coupon_list')
            else:
                error_data = response.json()
                error_message = 'Failed to create coupon. '
                if 'detail' in error_data:
                    error_message += error_data['detail']
                else:
                    # Collect field errors
                    field_errors = []
                    for field, errors in error_data.items():
                        field_errors.append(f"{field}: {', '.join(errors)}")
                    error_message += '; '.join(field_errors)
                
                messages.error(request, error_message)
        except requests.RequestException as e:
            messages.error(request, f'Error connecting to API: {str(e)}')
    
    # Fetch merchants for dropdown (for both GET and POST with errors)
    headers = get_api_headers(request)
    try:
        merchants_response = requests.get(MERCHANTS_API_URL, headers=headers)
        if merchants_response.status_code == 200:
            merchants_data = merchants_response.json()
            merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
        else:
            merchants = []
            messages.error(request, 'Failed to fetch merchants from API')
    except requests.RequestException:
        merchants = []
        messages.error(request, 'Error connecting to merchants API')
    
    context = {
        'user_profile': user_profile,
        'merchants': merchants,
        'access_token': request.session.get('access_token')
    }
    
    return render(request, 'My_Admin/My_Coupon/Add_Coupon.html', context)

def edit_coupon(request, coupon_id):
    """View to edit an existing coupon"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    headers = get_api_headers(request)
    
    # Handle POST request - traditional form submission
    if request.method == 'POST':
        # Get form data
        coupon_data = {
            'merchant': request.POST.get('merchant'),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'points_required': request.POST.get('points_required'),
            'expiry_date': request.POST.get('expiry_date'),
            'status': request.POST.get('status')
        }
        
        # Send PUT request to API
        try:
            response = requests.put(
                f'{COUPONS_API_URL}{coupon_id}/', 
                headers=headers, 
                data=json.dumps(coupon_data)
            )
            
            if response.status_code == 200:
                messages.success(request, 'Coupon updated successfully!')
                return redirect('coupon_list')
            else:
                error_data = response.json()
                error_message = 'Failed to update coupon. '
                if 'detail' in error_data:
                    error_message += error_data['detail']
                else:
                    # Collect field errors
                    field_errors = []
                    for field, errors in error_data.items():
                        field_errors.append(f"{field}: {', '.join(errors)}")
                    error_message += '; '.join(field_errors)
                
                messages.error(request, error_message)
        except requests.RequestException as e:
            messages.error(request, f'Error connecting to API: {str(e)}')
    
    try:
        # Fetch coupon data
        coupon_response = requests.get(f'{COUPONS_API_URL}{coupon_id}/', headers=headers)
        if coupon_response.status_code != 200:
            messages.error(request, 'Failed to fetch coupon data')
            return redirect('coupon_list')
        
        coupon = coupon_response.json()
        
        # Fetch merchants for dropdown
        merchants_response = requests.get(MERCHANTS_API_URL, headers=headers)
        merchants_data = merchants_response.json() if merchants_response.status_code == 200 else []
        merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
        
        context = {
            'user_profile': user_profile,
            'coupon': coupon,
            'merchants': merchants,
            'access_token': request.session.get('access_token')
        }
        return render(request, 'My_Admin/My_Coupon/Edit_Coupon.html', context)
        
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return redirect('coupon_list')

def delete_coupon(request, coupon_id):
    """View to delete a coupon with confirmation page"""
    try:
        # Get current user profile
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
            return redirect('login')

        # Fetch coupon details for confirmation page
        coupon_url = f"{COUPONS_API_URL}{coupon_id}/"
        headers = get_api_headers(request)
        
        response = requests.get(coupon_url, headers=headers)
        
        if response.status_code != 200:
            messages.error(request, f'Coupon not found. Status: {response.status_code}')
            return redirect('coupon_list')
        
        coupon_data = response.json()

        if request.method == 'POST':
            print(f"Processing POST request to delete coupon: {coupon_id}")
            
            # Send DELETE request to API
            delete_response = requests.delete(coupon_url, headers=headers)
            
            print(f"DELETE Request to: {coupon_url}")
            print(f"DELETE Response Status: {delete_response.status_code}")
            
            if delete_response.status_code in [200, 204]:  # 200 OK or 204 No Content
                messages.success(request, f'Coupon "{coupon_data.get("title", "Unknown")}" deleted successfully!')
                print("Coupon deleted successfully")
                return redirect('coupon_list')
            elif delete_response.status_code == 404:
                messages.error(request, 'Coupon not found. It may have been already deleted.')
                print("Coupon not found")
                return redirect('coupon_list')
            else:
                # Try to get more detailed error information
                try:
                    error_detail = delete_response.json()
                    error_message = f'Failed to delete coupon. Error: {error_detail}'
                except:
                    error_message = f'Failed to delete coupon. Status: {delete_response.status_code}'
                
                messages.error(request, error_message)
                print(f"Delete Error: {delete_response.status_code} - {delete_response.text}")
                return redirect('coupon_list')

        # If GET request, show confirmation page
        print(f"Showing confirmation page for coupon: {coupon_id}")
        context = {
            'coupon': coupon_data,
            'user_profile': user_profile or {}
        }
        return render(request, 'My_Admin/My_Coupon/Delete_Confirm.html', context)
        
    except requests.RequestException as e:
        error_msg = f'Error connecting to API: {str(e)}'
        messages.error(request, error_msg)
        print(f"Request Exception: {str(e)}")
        return redirect('coupon_list')
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        messages.error(request, error_msg)
        print(f"Unexpected Exception: {str(e)}")
        return redirect('coupon_list')
##########################################################################################################################################################
##########################################################################################################################################################
# Add these constants and views to your views.py
PROMOTIONS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/merchants/promotions/'

def promotion_list(request):
    """View to display list of promotions"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Fetch promotions from API
    headers = get_api_headers(request)
    params = {}
    if search_query:
        params['search'] = search_query
    
    try:
        response = requests.get(PROMOTIONS_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            promotions_data = response.json()
            
            # Handle pagination if API returns paginated results
            if 'results' in promotions_data:
                raw_promotions = promotions_data['results']
            else:
                raw_promotions = promotions_data
            
            # Process promotions to ensure consistent field names
            processed_promotions = []
            for promotion in raw_promotions:
                processed_promotion = {
                    'id': promotion.get('id'),
                    'title': promotion.get('title'),
                    'merchant_name': get_merchant_name(promotion),
                    'description': promotion.get('description'),
                    'image_url': promotion.get('image_url'),
                    'start_date': promotion.get('start_date'),
                    'end_date': promotion.get('end_date'),
                    'created_at': promotion.get('created_at') or promotion.get('created')
                }
                processed_promotions.append(processed_promotion)
            
            # Paginate results (10 per page)
            paginator = Paginator(processed_promotions, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'user_profile': user_profile,
                'promotions': page_obj,
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            }
            return render(request, 'My_Admin/My_Promotion/View_Promotion.html', context)
        else:
            messages.error(request, f'Failed to fetch promotions from API: {response.status_code}')
            return render(request, 'My_Admin/My_Promotion/View_Promotion.html', {
                'user_profile': user_profile,
                'promotions': [],
                'search_query': search_query,
                'access_token': request.session.get('access_token')
            })
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return render(request, 'My_Admin/My_Promotion/View_Promotion.html', {
            'user_profile': user_profile,
            'promotions': [],
            'search_query': search_query,
            'access_token': request.session.get('access_token')
        })

def add_promotion(request):
    """View to add a new promotion"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    # Handle POST request - traditional form submission
    if request.method == 'POST':
        # Get form data
        promotion_data = {
            'merchant': request.POST.get('merchant'),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'image_url': request.POST.get('image_url') or None,
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date')
        }
        
        # Send to API
        headers = get_api_headers(request)
        try:
            response = requests.post(PROMOTIONS_API_URL, headers=headers, data=json.dumps(promotion_data))
            
            if response.status_code == 201:
                messages.success(request, 'Promotion created successfully!')
                return redirect('promotion_list')
            else:
                error_data = response.json()
                error_message = 'Failed to create promotion. '
                if 'detail' in error_data:
                    error_message += error_data['detail']
                else:
                    # Collect field errors
                    field_errors = []
                    for field, errors in error_data.items():
                        field_errors.append(f"{field}: {', '.join(errors)}")
                    error_message += '; '.join(field_errors)
                
                messages.error(request, error_message)
        except requests.RequestException as e:
            messages.error(request, f'Error connecting to API: {str(e)}')
    
    # Fetch merchants for dropdown (for both GET and POST with errors)
    headers = get_api_headers(request)
    try:
        merchants_response = requests.get(MERCHANTS_API_URL, headers=headers)
        if merchants_response.status_code == 200:
            merchants_data = merchants_response.json()
            merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
        else:
            merchants = []
            messages.error(request, 'Failed to fetch merchants from API')
    except requests.RequestException:
        merchants = []
        messages.error(request, 'Error connecting to merchants API')
    
    context = {
        'user_profile': user_profile,
        'merchants': merchants,
        'access_token': request.session.get('access_token')
    }
    
    return render(request, 'My_Admin/My_Promotion/Add_Promotion.html', context)

def edit_promotion(request, promotion_id):
    """View to edit an existing promotion"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    headers = get_api_headers(request)
    
    # Handle POST request - traditional form submission
    if request.method == 'POST':
        # Get form data
        promotion_data = {
            'merchant': request.POST.get('merchant'),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'image_url': request.POST.get('image_url') or None,
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date')
        }
        
        # Send PUT request to API
        try:
            response = requests.put(
                f'{PROMOTIONS_API_URL}{promotion_id}/', 
                headers=headers, 
                data=json.dumps(promotion_data)
            )
            
            if response.status_code == 200:
                messages.success(request, 'Promotion updated successfully!')
                return redirect('promotion_list')
            else:
                error_data = response.json()
                error_message = 'Failed to update promotion. '
                if 'detail' in error_data:
                    error_message += error_data['detail']
                else:
                    # Collect field errors
                    field_errors = []
                    for field, errors in error_data.items():
                        field_errors.append(f"{field}: {', '.join(errors)}")
                    error_message += '; '.join(field_errors)
                
                messages.error(request, error_message)
        except requests.RequestException as e:
            messages.error(request, f'Error connecting to API: {str(e)}')
    
    try:
        # Fetch promotion data
        promotion_response = requests.get(f'{PROMOTIONS_API_URL}{promotion_id}/', headers=headers)
        if promotion_response.status_code != 200:
            messages.error(request, 'Failed to fetch promotion data')
            return redirect('promotion_list')
        
        promotion = promotion_response.json()
        
        # Fetch merchants for dropdown
        merchants_response = requests.get(MERCHANTS_API_URL, headers=headers)
        merchants_data = merchants_response.json() if merchants_response.status_code == 200 else []
        merchants = merchants_data.get('results', merchants_data) if isinstance(merchants_data, dict) else merchants_data
        
        context = {
            'user_profile': user_profile,
            'promotion': promotion,
            'merchants': merchants,
            'access_token': request.session.get('access_token')
        }
        return render(request, 'My_Admin/My_Promotion/Edit_Promotion.html', context)
        
    except requests.RequestException as e:
        messages.error(request, f'Error connecting to API: {str(e)}')
        return redirect('promotion_list')

def delete_promotion(request, promotion_id):
    """
    Individual view to delete a promotion with confirmation page
    """
    try:
        # Get current user profile
        user_profile = get_current_user_from_api(request)
        if not user_profile:
            messages.error(request, 'Please login to access this page')
            return redirect('login')

        # Fetch promotion details for confirmation page
        promotion_url = f"{PROMOTIONS_API_URL}{promotion_id}/"
        headers = get_api_headers(request)
        
        response = requests.get(promotion_url, headers=headers)
        
        if response.status_code != 200:
            messages.error(request, f'Promotion not found. Status: {response.status_code}')
            return redirect('promotion_list')
        
        promotion_data = response.json()

        if request.method == 'POST':
            print(f"Processing POST request to delete promotion: {promotion_id}")
            
            # Send DELETE request to API
            delete_response = requests.delete(promotion_url, headers=headers)
            
            print(f"DELETE Request to: {promotion_url}")
            print(f"DELETE Response Status: {delete_response.status_code}")
            print(f"DELETE Response Headers: {delete_response.headers}")
            
            if delete_response.status_code in [200, 204]:  # 200 OK or 204 No Content
                messages.success(request, f'Promotion "{promotion_data.get("title", "Unknown")}" deleted successfully!')
                print("Promotion deleted successfully")
                return redirect('promotion_list')
            elif delete_response.status_code == 404:
                messages.error(request, 'Promotion not found. It may have been already deleted.')
                print("Promotion not found")
                return redirect('promotion_list')
            else:
                # Try to get more detailed error information
                try:
                    error_detail = delete_response.json()
                    error_message = f'Failed to delete promotion. Error: {error_detail}'
                except:
                    error_message = f'Failed to delete promotion. Status: {delete_response.status_code}'
                
                messages.error(request, error_message)
                print(f"Delete Error: {delete_response.status_code} - {delete_response.text}")
                return redirect('promotion_list')

        # If GET request, show confirmation page
        print(f"Showing confirmation page for promotion: {promotion_id}")
        context = {
            'promotion': promotion_data,
            'user_profile': user_profile or {}
        }
        return render(request, 'My_Admin/My_Promotion/Promotion_confirm_delete.html', context)
        
    except requests.RequestException as e:
        error_msg = f'Error connecting to API: {str(e)}'
        messages.error(request, error_msg)
        print(f"Request Exception: {str(e)}")
        return redirect('promotion_list')
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        messages.error(request, error_msg)
        print(f"Unexpected Exception: {str(e)}")
        return redirect('promotion_list')
##########################################################################################################################################################
##########################################################################################################################################################
# API URLs
TRANSACTIONS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/loyalty/transactions/'
CUSTOMERS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/update/'
#######################################################################################################################################################
# def get_customers_with_role(request, role='customer'):
#     """Get users with specific role"""
#     headers = get_api_headers(request)
#     try:
#         response = requests.get(CUSTOMERS_API_URL, headers=headers)
#         if response.status_code == 200:
#             users_data = response.json()
#             # Filter users by role
#             customers = []
#             for user in users_data:
#                 if user.get('role') == role:
#                     customers.append(user)
#             return customers
#         return []
#     except requests.RequestException:
#         return []
#########################################################################################
def get_customers_with_role(request, role='customer'):
    """Get users with specific role"""
    headers = get_api_headers(request)
    try:
        response = requests.get(CUSTOMERS_API_URL, headers=headers)
        if response.status_code == 200:
            users_data = response.json()
            
            # Handle different response formats
            users_list = []
            
            if isinstance(users_data, dict):
                if 'results' in users_data:
                    users_list = users_data['results']
                elif 'data' in users_data:
                    users_list = users_data['data']
                elif 'users' in users_data:
                    users_list = users_data['users']
                else:
                    # Check if the dict itself represents a user
                    if 'id' in users_data or 'email' in users_data:
                        users_list = [users_data]
                    else:
                        users_list = []
            elif isinstance(users_data, list):
                users_list = users_data
            else:
                users_list = []
            
            # Filter users by role
            customers = []
            for user in users_list:
                if isinstance(user, dict) and user.get('role') == role:
                    customers.append(user)
            
            print(f"Found {len(customers)} customers with role '{role}'")  # Debug
            return customers
        else:
            print(f"API returned status {response.status_code}")  # Debug
            return []
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error in get_customers_with_role: {str(e)}")  # Debug
        return []
#######################################################################################################################################################
#######################################################################################################################################################
# Update your API URL to use the new search endpoint
USER_SEARCH_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/role-search/'
CUSTOMERS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/role-search/'
USER_REGISTER_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/register/'
USER_UPDATE_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/update/'
# List Customers
#################################################################################################
# List customers
def customer_list(request):
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    search_query = request.GET.get('search', '')
    headers = get_api_headers(request)
    
    try:
        params = {'role': 'customer'}
        if search_query:
            params['search'] = search_query
        
        response = requests.get(CUSTOMERS_API_URL, headers=headers, params=params)
        customers = []
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                customers = data.get('users') or data.get('results') or data.get('data') or []
            elif isinstance(data, list):
                customers = data
        else:
            messages.error(request, f'API Error: {response.status_code}')
        
        # Process customers for template
        processed_customers = []
        for customer in customers:
            processed_customers.append({
                'id': customer.get('id', 'N/A'),
                'name': customer.get('name', 'N/A'),
                'email': customer.get('email', 'N/A'),
                'phone': customer.get('phone', 'N/A'),
                'profile_image': customer.get('profile_image', ''),
                'role': customer.get('role', 'customer'),
                'created_at': customer.get('created_at', 'N/A'),
                'updated_at': customer.get('updated_at', 'N/A')
            })
        
        paginator = Paginator(processed_customers, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'My_Admin/My_Customer/customer_list.html', {
            'user_profile': user_profile,
            'customers': page_obj,
            'search_query': search_query
        })
        
    except requests.RequestException as e:
        messages.error(request, f'Network error: {str(e)}')
    except json.JSONDecodeError:
        messages.error(request, 'Invalid JSON response from API.')
    
    return render(request, 'My_Admin/My_Customer/customer_list.html', {
        'user_profile': user_profile,
        'customers': [],
        'search_query': search_query
    })

#################################################################################################
# Add customer
def add_customer(request):
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    if request.method == 'POST':
        customer_data = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'profile_image': request.POST.get('profile_image', ''),
            'role': 'customer',
            'password': request.POST.get('password'),
            'password2': request.POST.get('password2'),
            'tc': request.POST.get('tc') == 'on'
        }
        
        headers = get_api_headers(request)
        try:
            response = requests.post(USER_REGISTER_API_URL, headers=headers, data=json.dumps(customer_data))
            if response.status_code == 201:
                messages.success(request, 'Customer created successfully!')
                return redirect('customer_list')
            else:
                error_data = response.json()
                messages.error(request, json.dumps(error_data))
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'My_Admin/My_Customer/add_customer.html', {
        'user_profile': user_profile
    })
###############################################################################################
# Update your API URLs
USER_SEARCH_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/role-search/'
CUSTOMERS_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/role-search/'
USER_REGISTER_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/register/'
USER_UPDATE_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/update/'
USER_PROFILE_API_URL = 'https://http-127-0-0-1-8000-vst6.onrender.com/api/user/profile/'  # Add this
#################################################################################################
def update_customer(request, customer_id):
    """View to update an existing customer."""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')

    headers = get_api_headers(request)
    customer_data = {}

    # Fetch customer details
    try:
        params = {'role': 'customer', 'user_id': customer_id}
        response = requests.get(CUSTOMERS_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            # Normalize API response to single customer object
            if isinstance(data, dict):
                if 'users' in data and data['users']:
                    customer_data = data['users'][0]
                elif 'results' in data and data['results']:
                    customer_data = data['results'][0]
                elif 'data' in data and data['data']:
                    customer_data = data['data'][0]
                else:
                    customer_data = data
            elif isinstance(data, list) and data:
                customer_data = data[0]
            else:
                messages.error(request, "Customer not found")
                return redirect('customer_list')
        else:
            messages.error(request, f"Failed to fetch customer details: {response.status_code}")
            return redirect('customer_list')

    except requests.RequestException as e:
        messages.error(request, f"Error connecting to API: {str(e)}")
        return redirect('customer_list')

    if request.method == 'POST':
        # Collect updated data from form
        updated_data = {
            'id': str(customer_id),
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'profile_image': request.POST.get('profile_image') or customer_data.get('profile_image', ''),
            'role': 'customer',
            'tc': request.POST.get('tc') == 'on',
        }

        # Optional password update
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password and password2 and password == password2:
            updated_data['password'] = password
            updated_data['password2'] = password2

        try:
            response = requests.put(
                USER_UPDATE_API_URL,
                headers=headers,
                data=json.dumps(updated_data)
            )

            if response.status_code in [200, 201]:
                messages.success(request, 'Customer updated successfully!')
                return redirect('customer_list')
            else:
                try:
                    error_data = response.json()
                    error_message = ''
                    for field, errors in error_data.items():
                        if isinstance(errors, list):
                            error_message += f"{field}: {', '.join(errors)}; "
                        else:
                            error_message += f"{field}: {errors}; "
                    messages.error(request, f"Failed to update: {error_message}")
                except json.JSONDecodeError:
                    messages.error(request, f"API Error: {response.status_code} - {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Error connecting to API: {str(e)}")

    context = {
        'user_profile': user_profile,
        'customer': customer_data
    }
    return render(request, 'My_Admin/My_Customer/update_customer.html', context)
#######################################################################################################################################################
############################################################################################################################################################
def setting_list(request):
    """View to display list of customers using the new role-search API"""
    user_profile = get_current_user_from_api(request)
    if not user_profile:
        messages.error(request, 'Please login to access this page')
        return redirect('login')
    
    search_query = request.GET.get('search', '')
    headers = get_api_headers(request)
    
    try:
        # Build query parameters for the API
        params = {
            'role': 'admin'  # Always filter by customer role
        }
        
        # Add search parameter if provided
        if search_query:
            params['search'] = search_query
        
        print(f"Fetching from API: {USER_SEARCH_API_URL} with params: {params}")  # Debug
        
        response = requests.get(USER_SEARCH_API_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            api_response = response.json()
            print(f"API Response: {api_response}")  # Debug
            
            # Extract users from the API response
            customers = []
            
            if isinstance(api_response, dict):
                # The new API returns { 'count': X, 'users': [...] }
                if 'users' in api_response:
                    customers = api_response['users']
                elif 'results' in api_response:
                    customers = api_response['results']
                elif 'data' in api_response:
                    customers = api_response['data']
                else:
                    # If it's a single user object
                    if any(key in api_response for key in ['id', 'email', 'name']):
                        customers = [api_response]
            elif isinstance(api_response, list):
                customers = api_response
            
            print(f"Found {len(customers)} customers")  # Debug
            
            # Process customers for template with default values
            processed_customers = []
            for customer in customers:
                processed_customer = {
                    'id': customer.get('id', 'N/A'),
                    'name': customer.get('name', 'N/A'),
                    'email': customer.get('email', 'N/A'),
                    'phone': customer.get('phone', 'N/A'),
                    'city': customer.get('city', 'N/A'),
                    'country': customer.get('country', 'N/A'),
                    'role': customer.get('role', 'customer'),
                    'address': customer.get('address', 'N/A'),
                    'state': customer.get('state', 'N/A'),
                    'date_of_birth': customer.get('date_of_birth', 'N/A'),
                    'profile_image': customer.get('profile_image', ''),
                    'created_at': customer.get('created_at', 'N/A'),
                    'updated_at': customer.get('updated_at', 'N/A')
                }
                processed_customers.append(processed_customer)
            
            # Paginate results
            paginator = Paginator(processed_customers, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'user_profile': user_profile,
                'customers': page_obj,
                'search_query': search_query
            }
            return render(request, 'My_Admin/My_Customer/setting_list.html', context)
        else:
            error_msg = f'API returned status {response.status_code}: {response.text}'
            messages.error(request, error_msg)
            print(f"API Error: {error_msg}")  # Debug
            
    except requests.RequestException as e:
        error_msg = f'Network error: {str(e)}'
        messages.error(request, error_msg)
        print(f"Request Exception: {error_msg}")  # Debug
    except json.JSONDecodeError as e:
        error_msg = f'Invalid JSON response: {str(e)}'
        messages.error(request, error_msg)
        print(f"JSON Decode Error: {error_msg}")  # Debug
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        messages.error(request, error_msg)
        print(f"Unexpected Error: {error_msg}")  # Debug
    
    # Return empty page if failed
    return render(request, 'My_Admin/My_Customer/setting_list.html', {
        'user_profile': user_profile,
        'customers': [],
        'search_query': search_query
    })
#######################################################################################################################################################
############################################################################################################################################################
def get_api_data(url, access_token, params=None):
    """Helper function to fetch data from API with authentication"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"API Error for {url}: {e}")
        return None

def post_api_data(url, access_token, data):
    """Helper function to post data to API"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=data)
        return response
    except requests.RequestException as e:
        print(f"API POST Error for {url}: {e}")
        return None

def put_api_data(url, access_token, data):
    """Helper function to update data via API"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.put(url, headers=headers, json=data)
        return response
    except requests.RequestException as e:
        print(f"API PUT Error for {url}: {e}")
        return None

def delete_api_data(url, access_token):
    """Helper function to delete data via API"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.delete(url, headers=headers)
        return response
    except requests.RequestException as e:
        print(f"API DELETE Error for {url}: {e}")
        return None

def get_current_user_from_api(request):
    """Helper function to fetch current user from profile API"""
    try:
        access_token = request.session.get('access_token')
        if not access_token:
            return None
        return get_api_data(USER_PROFILES_API_URL, access_token)
    except Exception as e:
        print(f"User API Error: {e}")
        return None

##################################################################################################################
def merchant_report(request):
    response = requests.get(MERCHANTS_API_URL)
    merchants = response.json() if response.status_code == 200 else []
    return render(request, 'My_Admin/report/merchant_report.html', {'merchants': merchants})

def promotion_report(request):
    response = requests.get(PROMOTIONS_API_URL)
    promotions = response.json() if response.status_code == 200 else []
    return render(request, 'My_Admin/report/promotion_report.html', {'promotions': promotions})

def outlet_report(request):
    response = requests.get(OUTLETS_API_URL)
    outlets = response.json() if response.status_code == 200 else []
    return render(request, 'My_Admin/report/outlets_report.html', {'outlets': outlets})
def export_merchants_pdf(request):
    response = requests.get(MERCHANTS_API_URL)
    data = response.json() if response.status_code == 200 else []

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    style = getSampleStyleSheet()['Normal']

    table_data = [['ID', 'Company', 'Status', 'Created']]
    for m in data:
        table_data.append([m['id'], m['company_name'], m['status'], m['created_at'][:10]])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(Paragraph("Merchant Report", style))
    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="merchants.pdf"'
    return response
def export_merchants_excel(request):
    response = requests.get(MERCHANTS_API_URL)
    data = response.json() if response.status_code == 200 else []
    df = pd.DataFrame(data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Merchants')
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="merchants.xlsx"'
    return response
####################################################################################################
# 📄 Export PDF
def export_promotions_pdf(request):
    response = requests.get(PROMOTIONS_API_URL)
    promotions = response.json() if response.status_code == 200 else []

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Promotions Report")

    pdf.drawString(200, 750, "Promotions Report")
    y = 720
    for promo in promotions:
        pdf.drawString(50, y, f"Title: {promo.get('title', '')}")
        pdf.drawString(250, y, f"Merchant: {promo.get('merchant', '')}")
        y -= 20
        pdf.drawString(70, y, f"Desc: {promo.get('description', '')[:50]}")
        y -= 30
        if y < 100:
            pdf.showPage()
            y = 750

    pdf.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


# 📊 Export Excel
def export_promotions_excel(request):
    response = requests.get(PROMOTIONS_API_URL)
    promotions = response.json() if response.status_code == 200 else []

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Promotions"

    headers = ["ID", "Title", "Description", "Merchant", "Start Date", "End Date"]
    sheet.append(headers)

    for p in promotions:
        sheet.append([
            p.get('id', ''),
            p.get('title', ''),
            p.get('description', ''),
            p.get('merchant', ''),
            p.get('start_date', ''),
            p.get('end_date', ''),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=promotions_report.xlsx'
    workbook.save(response)
    return response
################################################################################################################################
def export_outlets_pdf(request):
    from .models import Outlet  # import your Outlet model
    outlets = Outlet.objects.all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Outlets Report")

    p.setFont("Helvetica", 12)
    y = height - 100
    for outlet in outlets:
        p.drawString(100, y, f"Name: {outlet.name} | Address: {outlet.address if hasattr(outlet, 'address') else 'N/A'}")
        y -= 20
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = height - 50

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
#######################################################################################################################################################
############################################################################################################################################################
def forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()
        print("📧 EMAIL FROM FORM:", email)
        
        if not email:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "My_Home/User/forget_password.html")

        api_url = "https://http-127-0-0-1-8000-vst6.onrender.com/api/user/forgot-password/"
        payload = {"email": email}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                res_data = response.json()
                messages.success(request, res_data.get("message", "Password reset link sent successfully!"))
                
                # Store in session for the reset page
                request.session['reset_uid'] = res_data.get("uid")
                request.session['reset_token'] = res_data.get("token")
                request.session['reset_email'] = email
                
                return redirect("update_password")
            else:
                error_data = response.json()
                error_msg = error_data.get('email', [error_data.get('message', 'Failed to send reset link.')])[0]
                messages.error(request, error_msg)
                
        except requests.exceptions.ConnectionError:
            messages.error(request, "Cannot connect to server. Please try again later.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, "My_Home/User/forget_password.html")

def update_password(request):
    # Get data from session or request
    uid = request.session.get('reset_uid') or request.POST.get("uid")
    token = request.session.get('reset_token') or request.POST.get("token")
    email = request.session.get('reset_email', '')
    
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not all([uid, token, new_password, confirm_password]):
            messages.error(request, "Missing required fields.")
            return render(request, "My_Home/User/update_password.html", {
                "uid": uid,
                "token": token,
                "email": email
            })

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "My_Home/User/update_password.html", {
                "uid": uid,
                "token": token,
                "email": email
            })

        api_url = "https://http-127-0-0-1-8000-vst6.onrender.com/user/reset-password/"
        payload = {
            "uid": uid,
            "token": token,
            "new_password": new_password,
            "confirm_password": confirm_password
        }

        try:
            response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                res_data = response.json()
                messages.success(request, res_data.get("message", "Password updated successfully!"))
                
                # Clear session data
                if 'reset_uid' in request.session:
                    del request.session['reset_uid']
                if 'reset_token' in request.session:
                    del request.session['reset_token']
                if 'reset_email' in request.session:
                    del request.session['reset_email']
                    
                return redirect("login")
            else:
                error_data = response.json()
                error_msg = error_data.get('message', 'Password reset failed. Please try again.')
                if 'uid' in error_data:
                    error_msg = error_data['uid'][0]
                elif 'token' in error_data:
                    error_msg = error_data['token'][0]
                elif 'password' in error_data:
                    error_msg = error_data['password'][0]
                    
                messages.error(request, error_msg)

        except requests.exceptions.ConnectionError:
            messages.error(request, "Cannot connect to server. Please try again later.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, "My_Home/User/update_password.html", {
        "uid": uid,
        "token": token,
        "email": email
    })