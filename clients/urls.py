from django.urls import path
from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Authentication
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    # Products
    path("products/", views.products, name="products"),
    path("products/<str:pid>/", views.product_detail, name="product_detail"),
]