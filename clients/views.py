import requests
from django.shortcuts import render, redirect
from django.http import Http404

BASE_URL = "https://smart-inventory-management-yos3.onrender.com/api"

PRODUCT_API_URL = f"{BASE_URL}/products"
REVIEW_API_URL = f"{BASE_URL}/reviews"
USER_API_URL = f"{BASE_URL}/users"


# ===============================
# HOME
# ===============================
def home(request):
    return render(request, "clients/home.html")


# ===============================
# REGISTER
# ===============================
def register_user(request):
    message = ""

    if request.method == "POST":
        try:
            response = requests.post(
                f"{USER_API_URL}/register",
                json={
                    "name": request.POST.get("name"),
                    "email": request.POST.get("email"),
                    "password": request.POST.get("password"),
                },
                timeout=10
            )

            data = response.json()

            if response.status_code in [200, 201]:
                message = "Registration successful. Please login."
            else:
                message = data.get("error", "Registration failed.")

        except Exception as e:
            message = f"Server error: {e}"

    return render(request, "clients/register.html", {"message": message})


# ===============================
# LOGIN
# ===============================
def login_user(request):
    message = ""

    if request.method == "POST":
        try:
            response = requests.post(
                f"{USER_API_URL}/login",
                json={
                    "email": request.POST.get("email"),
                    "password": request.POST.get("password"),
                },
                timeout=10
            )

            data = response.json()

            if response.status_code == 200:
                token = data.get("token")

                if token:
                    request.session["token"] = token
                    return redirect("products")
                else:
                    message = "Login failed. No token received."
            else:
                message = data.get("message", "Invalid credentials.")

        except Exception as e:
            message = f"Server error: {e}"

    return render(request, "clients/login.html", {"message": message})


# ===============================
# LOGOUT
# ===============================
def logout_user(request):
    request.session.flush()
    return redirect("home")


# ===============================
# PRODUCTS LIST
# ===============================
def products(request):
    page = request.GET.get("page", 1)

    try:
        response = requests.get(
            f"{PRODUCT_API_URL}?page={page}",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        product_list = data.get("products", [])
        cleaned_products = []

        for product in product_list:
            product["id"] = product.get("_id")
            cleaned_products.append(product)

        current_page = data.get("currentPage", 1)
        total_pages = data.get("totalPages", 1)

    except Exception:
        cleaned_products = []
        current_page = 1
        total_pages = 1

    return render(request, "clients/products.html", {
        "products": cleaned_products,
        "current_page": current_page,
        "total_pages": total_pages,
        "is_logged_in": bool(request.session.get("token"))
    })


# ===============================
# PRODUCT DETAIL + REVIEW
# ===============================
def product_detail(request, pid):

    review_message = ""
    error_message = ""
    reviews = []

    # -------------------------
    # Get Product
    # -------------------------
    try:
        product_response = requests.get(
            f"{PRODUCT_API_URL}/{pid}",
            timeout=10
        )
        product_response.raise_for_status()

        product = product_response.json()
        product["id"] = product.get("_id")

    except Exception:
        raise Http404("Product not found")

    # -------------------------
    # Get Reviews (IMPORTANT FIX)
    # -------------------------
    try:
        review_response = requests.get(
            f"{REVIEW_API_URL}/{pid}",
            timeout=10
        )

        if review_response.status_code == 200:
            reviews_data = review_response.json()

            # Ensure reviews is always a list
            if isinstance(reviews_data, list):
                reviews = reviews_data
            else:
                reviews = []

        else:
            reviews = []

    except Exception:
        reviews = []

    # -------------------------
    # Submit Review
    # -------------------------
    if request.method == "POST":

        token = request.session.get("token")

        if not token:
            error_message = "You must login to submit review."
        else:
            review_text = request.POST.get("review", "").strip()
            rating = request.POST.get("rating")

            if not review_text:
                error_message = "Review cannot be empty."

            elif len(review_text) > 150:
                error_message = "Review must be 150 characters or less."

            elif not rating:
                error_message = "Please select a rating."

            else:
                try:
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    post_response = requests.post(
                        REVIEW_API_URL,
                        json={
                            "product_id": pid,
                            "review_text": review_text,
                            "rating": int(rating)
                        },
                        headers=headers,
                        timeout=10
                    )

                    if post_response.status_code in [200, 201]:
                        review_message = "Review submitted successfully!"

                        # Refresh reviews after posting
                        refresh_response = requests.get(
                            f"{REVIEW_API_URL}/{pid}",
                            timeout=10
                        )

                        if refresh_response.status_code == 200:
                            refreshed_data = refresh_response.json()
                            if isinstance(refreshed_data, list):
                                reviews = refreshed_data

                    else:
                        error_message = post_response.json().get(
                            "error", "Failed to submit review."
                        )

                except Exception as e:
                    error_message = f"Error: {e}"

    return render(request, "clients/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "review_message": review_message,
        "error_message": error_message,
        "is_logged_in": bool(request.session.get("token"))
    })