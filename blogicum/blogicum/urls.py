from django.contrib import admin
from django.urls import include, path

from blog import views as blog_views

urlpatterns = [
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
    path(
        'auth/registration/',
        blog_views.register,
        name='registration',
    ),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
