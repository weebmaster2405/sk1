from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve as static_serve
import os
from pathlib import Path


urlpatterns = [
    path('', views.landing, name='landing'),  # Public landing page
    path('dashboard/', views.home, name='home'),  # Authenticated dashboard
    path('signup', views.signup, name='signup'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('signin', views.signin, name='signin'),
    path('signout', views.signout, name='signout'),
    path('reset-password/', views.password_reset_request, name='password_reset'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('org/create', views.createorgchart, name='createorgchart'),
    path('org/list', views.listorgchart, name='listorgchart'),
    path('myaccount', views.myaccount, name='myaccount'),
    path("upload_csv/", views.upload_csv, name="upload_csv"),
    path('charts/<str:file_name>', views.view_chart_by_filename, name='view_chart_by_filename'),
    path('api/request/chart/', views.serve_file, name='serve_file'), #for access managmeent
    path('delete/<int:pk>/', views.delete_file, name='delete_file'),
    path('org/manage', views.manage_access, name='manage_access'),
    path('org/access', views.view_access, name='view_access'),
    path('upload_image', views.upload_image, name='upload_image'),
    path('delete_images', views.delete_images, name='delete_images'),
    path('export_image_urls', views.export_image_urls, name='export_image_urls'),
    path('download-all-csv', views.download_all_csv, name='download_all_csv'),
    path('download-source/<int:chart_id>/', views.download_source, name='download_source'),
    path('profile', views.view_profile, name='view_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('org/request', views.request_orgchart, name='request_orgchart'),
    path('client/details/add', views.client_details, name='client_details'),
    path('client/details/show', views.client_details_show, name='client_details_show'),
    path('lead/<int:lead_id>/update', views.update_lead_status, name='update_lead_status'),
    path('lead/<int:lead_id>/delete', views.delete_lead, name='delete_lead'),
    path('client/lead/assign', views.assign_client_to_user, name='assign_client_to_user'),
    path('user/operations', views.user_operations, name='user_operations'),
    path('user/filter', views.filter_users_by_group, name='filter_users_by_group'), 
    path('marketplace', views.marketplace_dash, name='marketplace_dash'),
    path('marketplace/config', views.admin_marketplace, name='admin_marketplace'),
    path('marketplace/settings/update/', views.update_marketplace_settings, name='update_marketplace_settings'),
    
    # Marketplace Action URLs
    path('view-chart/<int:chart_id>/', views.view_chart_preview, name='view_chart_preview'),
    path('preview-chart/<int:chart_id>/', views.view_chart_blurred_preview, name='view_chart_blurred_preview'),
    path('chart/<int:chart_id>/preview/', views.view_chart_blurred_preview, name='chart_preview_public'),
    path('download-sample/<int:chart_id>/', views.download_chart_sample, name='download_chart_sample'),
    path('request-sample/', views.request_sample_ajax, name='request_sample_ajax'),
    path('check-login/', views.check_login, name='check_login'),
    path('payment/create/<int:chart_id>/', views.create_payment, name='create_payment'),
    path('update-chart-details/<int:chart_id>/', views.update_chart, name='update-chart'),
    path('payment/execute/', views.execute_payment, name='execute_payment'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/payment/execute/', views.execute_cart_payment, name='execute_cart_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    
    path('org/view/<uuid:chart_uuid>/', views.view_orgchart_temp, name='view_orgchart_temp'),
    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/mini/', views.mini_cart, name='mini_cart'),
    path('cart/add/<int:chart_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:chart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/execute-payment/', views.execute_cart_payment, name='execute_cart_payment'),
    path('cart/success/', views.cart_success, name='cart_success'),
    
    # Debug URLs
    path('test-razorpay/', views.test_razorpay_connection, name='test_razorpay_connection'),
    
    # Order Management URLs
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/pdf/', views.generate_order_pdf, name='generate_order_pdf'),
    path('orders/<int:order_id>/email-invoice/', views.email_order_invoice, name='email_order_invoice'),
    path('orders/<int:order_id>/update-payment/', views.manual_payment_update, name='manual_payment_update'),
    path('orders/create-manual/', views.create_manual_order_dashboard, name='create_manual_order_dashboard'),
    path('payment-dashboard/', views.admin_payment_dashboard, name='admin_payment_dashboard'),
    
    # Webhook URLs
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    path('user/profile/', views.profile, name='profile'),
    
    # Coupon Management URLs
    path('coupons/', views.admin_coupons, name='admin_coupons'),
    path('coupons/create/', views.create_coupon, name='create_coupon'),
    path('coupons/<int:coupon_id>/', views.coupon_detail, name='coupon_detail'),
    path('coupons/<int:coupon_id>/edit/', views.edit_coupon, name='edit_coupon'),
    path('coupons/<int:coupon_id>/toggle/', views.toggle_coupon_status, name='toggle_coupon_status'),
    path('coupons/validate/', views.validate_coupon_ajax, name='validate_coupon_ajax'),
    path('coupons/apply/', views.apply_coupon_ajax, name='apply_coupon_ajax'),
    path('coupons/remove/', views.remove_coupon_ajax, name='remove_coupon_ajax'),
    path('coupons/validate-manual-order/', views.validate_manual_order_coupon_ajax, name='validate_manual_order_coupon_ajax'),
    path('api/test/request/chart/', views.serve_file_testing, name='serve_file_testing'),
    
    # Media files
    re_path(r'^media/img/(?P<path>.*)$', static_serve, {
        'document_root': os.path.join(settings.MEDIA_ROOT, 'img'),
    }),
]



