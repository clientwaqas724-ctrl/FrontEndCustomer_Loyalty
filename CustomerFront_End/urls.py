from django.contrib import admin
from django.urls import path
from My_App import views
urlpatterns = [
    path('admin/', admin.site.urls),
######################################################################################################################
    path('', views.index, name='index'),
    path('register/', views.register_page, name='register'),
    ########################################################################################
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    ########################################################################################
    #Merchant management URLs
    path('merchants/', views.merchant_list, name='merchant_list'),
    path('merchants/add/', views.add_merchant, name='add_merchant'),
    path('merchants/update/<uuid:merchant_id>/', views.update_merchant, name='update_merchant'),
    path('merchants/delete/<uuid:merchant_id>/', views.delete_merchant, name='delete_merchant'),
    ########################################################################################
    #Outlets management URLs
    path('outlets/', views.outlet_list, name='outlet_list'),
    path('outlets/add/', views.add_outlet, name='add_outlet'),
    path('outlets/edit/<uuid:outlet_id>/', views.edit_outlet, name='edit_outlet'),
    path('delete_outlet/<str:outlet_id>/', views.delete_outlet, name='delete_outlet'),
    ################################################################################################
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.add_coupon, name='add_coupon'),
    path('coupons/edit/<uuid:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('coupons/delete/<uuid:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    ################################################################################################
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/add/', views.add_promotion, name='add_promotion'),
    path('promotions/edit/<uuid:promotion_id>/', views.edit_promotion, name='edit_promotion'),
    path('promotions/delete/<uuid:promotion_id>/', views.delete_promotion, name='delete_promotion'),
    ###################################################################################################
    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/update/<uuid:customer_id>/', views.update_customer, name='update_customer'),
    ###################################################################################################
    # Transaction URLs
    path('setting_list/',views.setting_list,name='setting_list'),
    ###############################################################################
      # 📊 Report Pages
    path('reports/merchants/', views.merchant_report, name='merchant_report'),
    path('reports/promotions/', views.promotion_report, name='promotion_report'),
    path('reports/outlets/', views.outlet_report, name='outlet_report'),
    # 📄 PDF Export URLs
    path('reports/merchants/pdf/', views.export_merchants_pdf, name='export_merchants_pdf'),
    # 📊 Excel Export URLs
    path('reports/merchants/excel/', views.export_merchants_excel, name='export_merchants_excel'),
    path('reports/promotions/pdf/', views.export_promotions_pdf, name='export_promotions_pdf'),
    path('reports/promotions/excel/', views.export_promotions_excel, name='export_promotions_excel'),
####################################################################################################################
    path('forget-password/', views.forget_password, name='forget_password'),
    path('update-password/', views.update_password, name='update_password'),


]

