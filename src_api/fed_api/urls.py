# src_api/fed_api/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404
import os
from django.conf import settings

# Uncomment these if you are using DRF ViewSets
#from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
#from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #JWT Token endpoints (Uncomment if using SimpleJWT)
    #path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- API Routes ---
    
    # Content & Sections
    path('api/content/', include('content.urls')),
    path('api/section/', include('section.urls')),
    path('api/quiz/', include('quiz.urls')),
    path('api/question/', include('question.urls')),
    
    # Comparison & Case Studies
    path('api/comparison/', include('comparison.urls')),
    path('api/', include('caseStudy.urls')), 
    # Fixed path to match namespace convention
    
    # Benefits & Drawbacks
    path('api/benefits/', include('benefits.urls')),
    path('api/drawbacks/', include('drawbacks.urls')),
    
    # --- Authentication & Users ---
    # Ensure 'users' has a unique namespace if defined in its urls.py
    path('api/', include('users.urls')),
    path('api/auth/', include('users.urls')),
    
    # --- Media Management ---
    path('api/', include('media_manager.urls')),
    path('api/', include('media_external_manager.urls')),
]

#Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Serve Single Page App index for root and unknown routes
def spa_index(request):
    index_path = os.path.join(settings.STATIC_ROOT, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')
    raise Http404("index.html not found")

urlpatterns += [
    path('', spa_index),
]