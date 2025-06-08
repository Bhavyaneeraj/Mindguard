from django.urls import path
from . import views

urlpatterns = [
    path('',views.home_page,name='home_page'),
    path('api/track/', views.track_url, name='track_url'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/sentiment-score/', views.sentiment_score_view, name='sentiment_score'),
    path('sentiment-dashboard/', views.sentiment_dashboard, name='sentiment_dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reset-alerts/', views.reset_alerts, name='reset_alerts'),
    path('stop-alerts/', views.stop_alerts, name='stop_alerts'),
    path('sentiment_visual/', views.sentiment_visual, name='sentiment_visual'), 
    path('insights/', views.insights_page, name='insights_page')
]
