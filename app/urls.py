from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view, register_view, logout_view
from management_profile.views import ListProfileView, ProfileDetailView, ProfileQrCodeView, NewProfileView, ProfileDeleteView, ProfileUpdateView, ImportProfilesView, download_profiles_qr_code_view, download_profile_qr_code_view, AdvanceSearchProfileView
from eventos.views import NewEventView, ListEventView, DetailEventView, UpdateEventView, DeleteEventView, analisar_nota_fiscal, carregar_dispendios, scanner_evento, registrar_presenca, listar_presencas_evento, exportar_presencas_csv, AdvanceSearchEventView, HomeEventView, NewDispendioView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    # Rotas necessárias para reset de senha.
    # --------------------------------------------------
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    # --------------------------------------------------
    path('new_profile/', NewProfileView.as_view(), name='new_profile'),
    path('list_profile/', ListProfileView.as_view(), name='list_profile'),
    path('delete_profile/<int:pk>/', ProfileDeleteView.as_view(), name='delete_profile'),
    path('update_profile/<int:pk>/', ProfileUpdateView.as_view(), name='update_profile'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<int:pk>/qrcode', ProfileQrCodeView.as_view(), name='profile_qrcode'),
    path('import_profiles/', ImportProfilesView.as_view(), name='import_profiles'),
    path('profiles/pdf/', download_profiles_qr_code_view, name='profiles_pdf'),
    path('profile/<int:pk>/qrcode/profile_pdf', download_profile_qr_code_view, name= 'profile_pdf'),
    path('advance_search_profile/', AdvanceSearchProfileView, name='advance_search_profile'),
    # --------------------EVENTOS----------------------------
    path('new_event/', NewEventView.as_view(), name='new_event'),
    path('list_event/', ListEventView.as_view(), name='list_event'),
    path('advance_search_event/', AdvanceSearchEventView, name='advance_search_event'),
    path('detail_event/<int:pk>/', DetailEventView.as_view(), name='detail_event'),
    path('update_event/<int:pk>/', UpdateEventView.as_view(), name='update_event'),
    path('delete_event/<int:pk>/', DeleteEventView.as_view(), name='delete_event'),
    path('', HomeEventView.as_view(), name='home'),
    path('dispendios/<int:pk>/', NewDispendioView.as_view(), name='new_dispendio'),
    path('dispendios/',NewDispendioView.as_view(),name='dispendios'),
    path('dispendios/carregar/<int:evento_id>/',carregar_dispendios,name='carregar_dispendios'),
    path('dispendios/analisar-nota/', analisar_nota_fiscal, name='analisar_nota_fiscal'),
    # ------------------------------------------------
    path('evento/<int:evento_id>/scanner/', scanner_evento, name='scanner_evento'),
    path('evento/<int:evento_id>/registrar-presenca/', registrar_presenca, name='registrar_presenca'),
    path('evento/<int:evento_id>/presencas/', listar_presencas_evento, name='listar_presencas_evento'),
    path('evento/<int:evento_id>/presencas/csv/', exportar_presencas_csv, name='exportar_presencas_csv'),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
