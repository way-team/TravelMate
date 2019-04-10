from TravelMateServer.API.serializers import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics, filters
from .models import UserProfile, Trip, Invitation, City, Rate, Application, Language
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from datetime import datetime
from django.db.models import Q, Count, StdDev, Avg, Sum
from django.utils.datastructures import MultiValueDictKeyError
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie


def get_user_by_token(request):
    key = request.data.get('token', '')
    tk = get_object_or_404(Token, key=key)
    user = tk.user
    user_profile = UserProfile.objects.get(user=user)

    return user_profile


class GetUserView(APIView):
    def post(self, request):
        userProfile = get_user_by_token(request)

        return Response(UserProfileSerializer(userProfile, many=False).data)


class RateUser(APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        userId = request.data.get('userId', '')
        user = User.objects.get(id=userId).userProfile
        refreshUserAverageRating(user)
        avgRating = user.avarageRate

        return Response(UserProfileSerializer(userProfile, many=False).data)


    def post(self, request):
        """
        POST method
        """

        #Comment the following line and remove the comment from one after that to test with Postman
        username = request.user.username
        #username = request.data.get('username', '')
        voterUser = User.objects.get(username=username)
        voterUserProfile = UserProfile.objects.get(user=voterUser) #Voter User

        votedUsername = request.data.get('voted', '')
        votedUser = User.objects.get(username=votedUsername)
        votedUserProfile = UserProfile.objects.get(user=votedUser) #Voted User

        value = request.data.get('rating', '0') #Value of the rating

        #Checks if the users are friends
        areFriends = False
        friends, pending = get_friends_or_pending(voterUserProfile)
        for f in friends:
            if (f==votedUserProfile):
                areFriends = True
                break

        oldRating = Rate.objects.filter(voter=voterUserProfile, voted=votedUserProfile).first()
        print("Value=", oldRating)

        if(areFriends):
            if oldRating is None:
                rate = Rate(voter=voterUserProfile, voted=votedUserProfile, value=value)
                rate.save()
            else:
                oldRating.delete()
                rate = Rate(voter=voterUserProfile, voted=votedUserProfile, value=value)
                rate.save()
        else:
            raise ValueError("You can not rate this user")

        refreshUserAverageRating(votedUserProfile)
        return Response(UserProfileSerializer(votedUserProfile, many=False).data)
    
def refreshUserAverageRating(votedUserProfile):
    userRatings = Rate.objects.filter(voted=votedUserProfile)
    print(userRatings)
    sumRatings = 0
    numRatings = 0
    for r in userRatings:
        sumRatings += r.value
        print(str(sumRatings))
        numRatings = numRatings + 1
        print(str(numRatings))
    avgUserRating = sumRatings / numRatings
    votedUserProfile.avarageRate = avgUserRating
    votedUserProfile.numRate = numRatings
    votedUserProfile.save()
    print(votedUserProfile.avarageRate)


class UserList(APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request, *args, **kwargs):
        """
        Get the user by his username
        """
        username = kwargs.get('username')
        userProfile = User.objects.get(username=username).userprofile
        return Response(UserProfileSerializer(userProfile, many=False).data)


def get_friends_or_pending(user):
    """
    Method to get the list of an user's friends or pending friends
    """
    friends = []
    pending = []

    sended_invitations = Invitation.objects.filter(sender=user, status="A")
    if sended_invitations:
        for i in sended_invitations:
            friends.append(i.receiver)

    received_invitations = Invitation.objects.filter(receiver=user, status="A")
    if received_invitations:
        for j in received_invitations:
            friends.append(j.sender)

    pending_invitations = Invitation.objects.filter(receiver=user, status="P")
    if pending_invitations:
        for k in pending_invitations:
            pending.append(k.sender)

    return (friends, pending)


class GetFriendsView(APIView):
    """
    Method to get the friends of the logged user
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        friends, pending = get_friends_or_pending(user)

        return Response(UserProfileSerializer(friends, many=True).data)


class GetPendingView(APIView):
    """
    Method to get the pending friends of the logged user
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        friends, pending = get_friends_or_pending(user)

        return Response(UserProfileSerializer(pending, many=True).data)


class DiscoverPeopleView(APIView):
    """
    Method to get the people who have the same interests as you in order to discover people
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        friends, pending = get_friends_or_pending(user)

        discover_people = []
        interests = user.interests.all()

        # First, we obtain the people with the same interests
        #for interest in interests:
        aux = UserProfile.objects.filter(interests__in=interests)
        for person in aux:
            if not person in discover_people:
                discover_people.append(person)

        # After, we obtain the people without the same interests
        # and append them at the end of the discover list
        all_users = list(UserProfile.objects.all())
        for person in discover_people:
            all_users.remove(person)
        for person in all_users:
            discover_people.append(person)

        # Finally, we remove from the discover list the people
        # who are our friends or pending friends
        for person in friends:
            discover_people.remove(person)
        for person in pending:
            discover_people.remove(person)
        discover_people.remove(user)

        return Response(UserProfileSerializer(discover_people, many=True).data)


class MyTripsList(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(
            user__user=self.request.user).order_by('-startDate')


class AvailableTripsList(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        today = datetime.today()
        return Trip.objects.filter(
            Q(status=True) & Q(startDate__gte=today) & Q(
                tripType='PUBLIC')).exclude(
                    user__user=self.request.user).order_by('-startDate')


class AvailableTripsSearch(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        today = datetime.today()
        return Trip.objects.filter(
            Q(status=True) & Q(startDate__gte=today) & Q(
                tripType='PUBLIC')).exclude(
                    user__user=self.request.user).order_by('-startDate')

    queryset = get_queryset
    serializer_class = TripSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('title', 'description')


class ListCities(APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):

        cities = City.objects.all()
        return Response(CitySerializer(cities, many=True).data)


class CreateTrip(APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):

        #GET TRIP DATA
        #Comment the following line and remove the comment from one after that to test with Postman
        username = request.user.username
        #username= request.data.get('username','')
        user = User.objects.get(username=username).userprofile
        title = request.data.get('title', '')
        description = request.data.get('description', '')
        startDate = request.data.get('start_date', '')
        endDate = request.data.get('end_date', '')
        tripType = request.data.get('trip_type', '')

        #GET CITY DATA
        cityId = request.data.get('city')

        #GET CITY
        city = City.objects.get(pk=cityId)
        image_name = city.country.name + '.jpg'

        try:
            userImage = request.data['file']
            trip = Trip(
                user=user,
                title=title,
                description=description,
                startDate=startDate,
                endDate=endDate,
                tripType=tripType,
                image=image_name,
                userImage=userImage)

            trip.save()

        except MultiValueDictKeyError:
            trip = Trip(
                user=user,
                title=title,
                description=description,
                startDate=startDate,
                endDate=endDate,
                tripType=tripType,
                image=image_name)

            trip.save()
        finally:
            #GET CITY AND ADD TRIP
            city = City.objects.get(pk=cityId)
            city.trips.add(trip)

            return Response(TripSerializer(trip, many=False).data)


class GetTripView(APIView):
    """
    Method to get a trip by its ID
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request, *args, **kwargs):
        """
        GET method
        """
        trip_id = kwargs.get("trip_id", "")
        trip = Trip.objects.get(pk=trip_id)

        return Response(TripSerializer(trip, many=False).data)


class EditTripView(APIView):
    """
    Method to edit a trip by its ID
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        trip_id = request.data.get("trip_id", "")
        title = request.data.get("title", "")
        description = request.data.get("description", "")
        start_date = request.data.get("start_date", "")
        end_date = request.data.get("end_date", "")
        trip_type = request.data.get("trip_type", "")

        city_id = request.data.get("city", "")

        city = City.objects.get(pk=city_id)
        image_name = city.country.name + '.jpg'

        stored_trip = Trip.objects.get(pk=trip_id)
        stored_creator = stored_trip.user
        if stored_creator != user:
            raise ValueError("You are not the creator of this trip")

        stored_cities = stored_trip.cities.all()

        try:
            user_image = request.data['file']
            trip = Trip(
                id=trip_id,
                user=user,
                title=title,
                description=description,
                startDate=start_date,
                endDate=end_date,
                tripType=trip_type,
                image=image_name,
                userImage=user_image)
            trip.save()

        except MultiValueDictKeyError:
            trip = Trip(
                id=trip_id,
                user=user,
                title=title,
                description=description,
                startDate=start_date,
                endDate=end_date,
                tripType=trip_type,
                image=image_name)
            trip.save()

        finally:
            if not city in stored_cities:
                city.trips.add(stored_trip)

        return Response(TripSerializer(stored_trip, many=False).data)

class DashboardData(APIView):
    """
    Method to apply to a trip specified by its ID
    """
    permission_classes = (IsAdminUser, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        stats = {}
        numberOfTrips = Trip.objects.all().count()
        stats['numberOfTrips']= numberOfTrips
        stats['numberOfTripsJanuary']=Trip.objects.filter(Q(startDate__month='01')|Q(endDate__month='01')).count()
        stats['numberOfTripsFebruary']=Trip.objects.filter(Q(startDate__month='02')|Q(endDate__month='02')).count()
        stats['numberOfTripsMarch']=Trip.objects.filter(Q(startDate__month='03')|Q(endDate__month='03')).count()
        stats['numberOfTripsApril']=Trip.objects.filter(Q(startDate__month='04')|Q(endDate__month='04')).count()
        stats['numberOfTripsMay']=Trip.objects.filter(Q(startDate__month='05')|Q(endDate__month='05')).count()
        stats['numberOfTripsJune']=Trip.objects.filter(Q(startDate__month='06')|Q(endDate__month='06')).count()
        stats['numberOfTripsJuly']=Trip.objects.filter(Q(startDate__month='07')|Q(endDate__month='07')).count()
        stats['numberOfTripsAugust']=Trip.objects.filter(Q(startDate__month='08')|Q(endDate__month='08')).count()
        stats['numberOfTripsSeptember']=Trip.objects.filter(Q(startDate__month='09')|Q(endDate__month='09')).count()
        stats['numberOfTripsOctober']=Trip.objects.filter(Q(startDate__month='10')|Q(endDate__month='10')).count()
        stats['numberOfTripsNovember']=Trip.objects.filter(Q(startDate__month='11')|Q(endDate__month='11')).count()
        stats['numberOfTripsDecember']=Trip.objects.filter(Q(startDate__month='12')|Q(endDate__month='12')).count()
        
        numberOfPublicTrips = Trip.objects.filter(tripType='PUBLIC').count()
        numberOfPrivateTrips = Trip.objects.filter(tripType='PRIVATE').count()
        stats['numberOfPublicTrips']=numberOfPublicTrips
        stats['numberOfPrivateTrips']=numberOfPrivateTrips
        if(numberOfPublicTrips!=0):
            stats['ratioOfPrivateTrips'] = numberOfPrivateTrips/numberOfPublicTrips
        else:
            stats['ratioOfPrivateTrips'] = 0
        stats['percentagePrivateTrips'] = numberOfPrivateTrips/numberOfTrips
        stats['percentagePublicTrips'] = numberOfPublicTrips/numberOfTrips


        numberOfUsers = UserProfile.objects.all().count()
        stats['numberOfUsers']= numberOfUsers
        
        stats['percentageMen']=UserProfile.objects.filter(gender='M').count()/numberOfUsers
        stats['percentageWomen']=UserProfile.objects.filter(gender='F').count()/numberOfUsers
        stats['percentageNonBinary']=UserProfile.objects.filter(gender='N').count()/numberOfUsers


        numberOfPremiumUsers = UserProfile.objects.filter(isPremium=True).count()
        numberOfNonPremiumUsers = UserProfile.objects.filter(isPremium=False).count()
        stats['numberOfPremiumUsers']= numberOfPremiumUsers
        stats['numberOfNonPremiumUsers']= numberOfNonPremiumUsers
        stats['percentagePremiumUsers']= numberOfPremiumUsers/numberOfUsers
        
        activeUsers=UserProfile.objects.filter(status='Active').count()
        deletedUsers=UserProfile.objects.filter(status='Deleted').count()

        if(deletedUsers!=0):
            stats['activeUsersRatio']= activeUsers/deletedUsers
        else:
            stats['activeUsersRatio']= 0

        if(numberOfNonPremiumUsers!=0):
            stats['premiumUsersRatio']= numberOfPremiumUsers/numberOfNonPremiumUsers
        else:
            stats['premiumUsersRatio']= 0

        stats['avgTripsPerUser']= numberOfTrips/numberOfUsers

        numberOfApps = Application.objects.all().count()
        stats['avgAppsPerTrip']= numberOfApps/numberOfTrips

        numberOfLanguages = Language.objects.all().count()
        stats['avgLanguagesPerUser']=numberOfLanguages/numberOfUsers
        #stats['stDevLanguagesPerUser']=


        stats['avgRatingPerUser']=UserProfile.objects.aggregate(Avg('avarageRate'))['avarageRate__avg']
        #stats['stDevRatingPerUser']=
        stats['top5AppsTrips']= TripSerializer(Trip.objects.annotate(apps=Count('applications')).order_by('-apps')[:5], many=True).data
        stats['top5NumberOfCitiesTrips']=TripSerializer(Trip.objects.annotate(cities_count=Count('cities')).order_by('-cities_count')[:5], many=True).data
        stats['top5NumberOfTripsCities']=CitySerializer(City.objects.annotate(trips_count=Count('trips')).order_by('-trips_count')[:5], many=True).data
        stats['top5MostCommonInterests']=InterestSerializer(Interest.objects.annotate(users_count=Count('users')).order_by('-users_count')[:5], many=True).data



        return JsonResponse(stats)

class ApplyTripView(APIView):
    """
    Method to apply to a trip specified by its ID
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        trip_id = request.data.get("trip_id", "")
        trip = Trip.objects.get(pk=trip_id)

        try:
            query = Application.objects.filter(trip=trip).get(applicant=user)
        except Application.DoesNotExist:
            query = None

        if query is None:
            application = Application(applicant=user, trip=trip, status="P")
            application.save()
        else:
            raise ValueError("You have already applied to this trip")

        return Response(TripSerializer(trip, many=False).data)

class SetUserToPremium(APIView):
    """
    Makes a user Premium
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        usernamepaid = request.user.username

        userpaid = User.objects.get(username=usernamepaid)
        userprofilepaid = UserProfile.objects.get(user=userpaid)
        userprofilepaid.isPremium = True;
        userprofilepaid.save()

        return Response(UserProfileSerializer(userprofilepaid, many=False).data)

@csrf_exempt
def message_list(request, sender=None, receiver=None):
    """
    List all required messages, or create a new message.
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    if request.method == 'GET':
        messagesSend = Message.objects.filter(
            sender_id=sender, receiver_id=receiver)
        messagesReceives = Message.objects.filter(
            sender_id=receiver, receiver_id=sender)

        allmessages = messagesSend | messagesReceives
        messages = allmessages.order_by('timestamp')

        serializer = MessageSerializer(
            messages, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        data = request.POST
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
