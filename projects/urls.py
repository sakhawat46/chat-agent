from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # path("admin/", admin.site.urls),

    # # Users
    # path('api/', include('apps.users.urls')),

    # # Agents
    # path('api/', include('apps.agents.urls')),

    # # Chat
    # path('api/', include('apps.voice.urls')),
    
    # # Dashboard
    # path('api/', include('apps.dashboard.urls')),

    # # Embeds
    # path('api/', include('apps.embeds.urls')),
    
]




# config/urls.py
from django.shortcuts import render

def test_page(request):
    return render(request, "test.html")

urlpatterns += [ path("test/", test_page) ]
