from django.urls import path
from .views import update_step_order
from .views import (
    ProceduraListView, ProceduraDetailView, ProceduraCreateView, ProceduraUpdateView, ProceduraDeleteView,
    StepListView, StepDetailView, StepCreateView, StepUpdateView, StepDeleteView
)

urlpatterns = [
    # CRUD per Procedura
    path('', ProceduraListView.as_view(), name='procedura-list'),
    path('procedura/<int:pk>/', ProceduraDetailView.as_view(), name='procedura-detail'),
    path('procedura/create/', ProceduraCreateView.as_view(), name='procedura-create'),
    path('procedura/<int:pk>/update/', ProceduraUpdateView.as_view(), name='procedura-update'),
    path('procedura/<int:pk>/delete/', ProceduraDeleteView.as_view(), name='procedura-delete'),

    # CRUD per Step
    path('step/', StepListView.as_view(), name='step-list'),
    path('step/<int:pk>/', StepDetailView.as_view(), name='step-detail'),
    path('procedura/<int:procedura_id>/step/create/', StepCreateView.as_view(), name='step-create'),  # Modifica qui
    path('step/<int:pk>/update/', StepUpdateView.as_view(), name='step-update'),
    path('step/<int:pk>/delete/', StepDeleteView.as_view(), name='step-delete'),

    #API
    path('api/steps/update_order/', update_step_order, name='update-step-order'),
]
