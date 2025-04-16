from os import stat
from django.urls import path,re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from Auth_System import settings
from .views import AuthView
from .views import TaskView
# from .matc import match_missing_person
from .match_fields import match_with_unidentified_person
from .match_fields import match_with_unidentified_body

schema_view = get_schema_view(
    openapi.Info(
        title="Task Management API",
        default_version="v1",
        description="API documentation for authentication and task management",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("auth/", AuthView.as_view(), name="auth"),
    path("auth/<str:action>/", AuthView.as_view(), name="auth-action"),
    path("auth/reset-password/<slug:token>/", AuthView.as_view(), name="reset-password"),
    path("tasks/", TaskView.as_view(), name="task-list-create"),
    path("tasks/<int:task_id>/", TaskView.as_view(), name="task-detail"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('match-person/<int:missing_person_id>/unidentified_person/',match_with_unidentified_person,name='match_with_unidentified_person'),
    path('match-person/<int:missing_person_id>/unidentified_body/',match_with_unidentified_body,name='match_with_unidentified_body'),

]
# if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
