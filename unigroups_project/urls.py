from django.contrib import admin
from django.urls    import path, include
from django.http    import JsonResponse

def health(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/', health),
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    path('api/auth/',          include('users.urls')),
    path('api/groups/',        include('groups.urls')),
    path('api/chat/',          include('chat.urls')),
    path('api/notifications/', include('notifications.urls')),
=======
    path('api/auth/',   include('users.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/chat/',   include('chat.urls')),
>>>>>>> 63a7da21ebd8ec983cf9ca698be62c4cc76c5803
]
