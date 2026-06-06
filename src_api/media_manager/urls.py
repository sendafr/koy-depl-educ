from django.urls import path
from . import views

urlpatterns = [
    # MediaUpload endpoints
    path('media_uploads/', views.media_upload_list_create, name='media_upload_list_create'),
    path('media_uploads/<int:pk>/', views.media_upload_detail, name='media_upload_detail'),

    # MediaFile endpoints
    path('media_file/', views.media_file_list_create, name='media_file_list_create'),
    path('media_file/<int:pk>/', views.media_file_detail, name='media_file_detail'),

    # Category endpoints
    path('media_category/', views.media_category_list_create, name='media_category_list_create'),
    path('media_category/<int:pk>/', views.media_category_detail, name='media_category_detail'),

    # Tag endpoints
    path('media_tag/', views.media_tag_list_create, name='media_tag_list_create'),
    path('media_tag/<int:pk>/', views.media_tag_detail, name='media_tag_detail'),

    # Download endpoints
    path('media_download/', views.media_download_list_create, name='media_download_list_create'),
    path('media_download/<int:pk>/', views.media_download_detail, name='media_download_detail'),
    path('serve_media_file/<path:file_path>', views.serve_media_file, name='serve_media_file'),
]