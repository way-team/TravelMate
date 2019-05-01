"""TravelMateServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.contacts, name='contacts')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='contacts')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path
from django.conf.urls import url
from rest_framework import routers
from TravelMateServer.API import views
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('login/', obtain_auth_token),
    path('getUserByToken/', views.GetUserView.as_view(),  name='get_user'),
    path('getUserById/', views.GetUserByIdView.as_view(),  name='get_user_by_id'),
    url('^users/(?P<username>.+)/$', views.UserList.as_view()),
    path('rate/', views.RateUser.as_view(), name='rate_user'),
    path('trips/', views.AvailableTripsList.as_view(), name='available_trips_list'),
    path('trips/myTrips/', views.MyTripsList.as_view(), name='my_trips_list'),
    path('trips/search/', views.AvailableTripsSearch.as_view(), name='available_trips_search'),
    path('list-cities/', views.ListCities.as_view(), name='list_cities'),
    path('createTrip/', views.CreateTrip.as_view(), name='create_trip'),
    path('getFriends/', views.GetFriendsView.as_view(), name='get_friends'),
    path('getPending/', views.GetPendingView.as_view(), name='get_pending' ),
    path('getPendingInvitations/', views.GetPendingInvitationsView.as_view()),
    path('sendInvitation/', views.SendInvitation.as_view(), name='send_invitation'),
    path('acceptFriend/', views.AcceptFriend.as_view(), name='accept_friend'),
    path('rejectFriend/', views.RejectFriend.as_view(), name='reject_friend'),
    path('removeFriend/', views.RemoveFriend.as_view()),
    path('getDiscoverPeople/', views.DiscoverPeopleView.as_view()),
    url('^getTrip/(?P<trip_id>.+)/$', views.GetTripView.as_view()),
    path('editTrip/', views.EditTripView.as_view()),
    path('applyTrip/', views.ApplyTripView.as_view(), name='apply_trip'),
    path('acceptApplication/', views.AcceptApplicationView.as_view(), name='accept_application'),
    path('rejectApplication/', views.RejectApplicationView.as_view(), name='reject_application'),
    path('dashboard/', views.DashboardData.as_view(), name='dashboard'),
    path(
        'messages/<int:sender>/<int:receiver>/',
        views.message_list,
        name='message-detail'),
    path('messages/', views.message_list, name='message-list'),
    path('paid/', views.SetUserToPremium.as_view(), name='set_user_to_premium'),
    path('register/', views.RegisterUser.as_view(), name='register_user'),
    path('list-languages/', views.ListLanguages.as_view(), name='list_languages' ),
    path('list-interests/', views.ListInterest.as_view(), name='list_interest'),
    path('backend-wakeup/',views.backendWakeUp, name='backend-wakeup'),
] + static(
    settings.STATIC_URL, document_root=settings.STATICFILES_STORAGE)
