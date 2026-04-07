from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt
from .restapis import get_request, analyze_review_sentiments, post_review
from .populate import initiate
from .models import CarMake, CarModel
import json
import logging

logger = logging.getLogger(__name__)


def get_cars(request):
    count = CarMake.objects.count()

    if count == 0:
        initiate()

    car_models = CarModel.objects.select_related("car_make")

    cars = [
        {
            "CarModel": car.name,
            "CarMake": car.car_make.name
        }
        for car in car_models
    ]

    return JsonResponse({"CarModels": cars})


@csrf_exempt
def login_user(request):
    # Get username and password from request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']

    user = authenticate(username=username, password=password)

    response_data = {"userName": username}

    if user is not None:
        # Login user
        login(request, user)
        response_data = {
            "userName": username,
            "status": "Authenticated"
        }

    return JsonResponse(response_data)


def logout_request(request):
    logout(request)  # Terminate user session
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    data = json.loads(request.body)

    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']

    try:
        User.objects.get(username=username)
        return JsonResponse({
            "userName": username,
            "error": "Already Registered"
        })

    except Exception:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )

        login(request, user)

        return JsonResponse({
            "userName": username,
            "status": "Authenticated"
        })


# Update the `get_dealerships` view
def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state

    dealerships = get_request(endpoint)

    return JsonResponse({
        "status": 200,
        "dealers": dealerships
    })


def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint) or []

        for review_detail in reviews:
            try:
                sentiment_response = analyze_review_sentiments(
                    review_detail['review']
                )
                review_detail['sentiment'] = sentiment_response.get(
                    'sentiment', 'neutral'
                )
            except Exception:
                review_detail['sentiment'] = "neutral"

        return JsonResponse({
            "status": 200,
            "reviews": reviews
        })

    return JsonResponse({
        "status": 400,
        "message": "Bad Request"
    })


def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealership = get_request(endpoint)

        if isinstance(dealership, dict):
            dealership = [dealership]

        return JsonResponse({
            "status": 200,
            "dealer": dealership
        })

    return JsonResponse({
        "status": 400,
        "message": "Bad Request"
    })


def add_review(request):
    if not request.user.is_anonymous:
        data = json.loads(request.body)

        try:
            post_review(data)
            return JsonResponse({"status": 200})

        except Exception:
            return JsonResponse({
                "status": 401,
                "message": "Error in posting review"
            })

    return JsonResponse({
        "status": 403,
        "message": "Unauthorized"
    })
