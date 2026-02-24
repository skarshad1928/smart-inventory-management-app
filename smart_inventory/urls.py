from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # All frontend routes handled by clients app
    path('', include('clients.urls')),
]
