from TravelMateServer.API.serializers import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import generics, filters
from .models import UserProfile, Trip, Invitation, City, Rate, Application, Language, Interest
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from datetime import datetime
from django.db.models import Q, Count, StdDev, Avg, Sum, Case, When, IntegerField, Value
from django.utils.datastructures import MultiValueDictKeyError
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from collections import namedtuple
from django.contrib.auth.hashers import make_password


def get_user_by_token(request):
    key = request.data.get('token', '')
    tk = get_object_or_404(Token, key=key)
    user = tk.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Sets user to no Premium if it's been 1 year since the user paid
    if user_profile.isPremium:
        today = datetime.today().date()
        datePremium = user_profile.datePremium
        diff = today - datePremium
        if diff.days >= 365:
            user_profile.isPremium = False
            user_profile.save()

    return user_profile



class GetUserView(APIView):
    def post(self, request):
        user_profile = get_user_by_token(request)

        return Response(UserProfileSerializer(user_profile, many=False).data)


class GetUserByIdView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id', '')
        user_profile = UserProfile.objects.get(pk=user_id)

        return Response(UserProfileSerializer(user_profile, many=False).data)


def refreshUserAverageRating(votedUserProfile):
    userRatings = Rate.objects.filter(voted=votedUserProfile)
    sumRatings = 0
    numRatings = 0
    for r in userRatings:
        sumRatings += r.value
        numRatings = numRatings + 1
    avgUserRating = sumRatings / numRatings
    votedUserProfile.avarageRate = avgUserRating
    votedUserProfile.numRate = numRatings
    votedUserProfile.save()


class RateUser(APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        userId = request.data.get('userId', '')
        user = User.objects.get(id=userId).userProfile
        refreshUserAverageRating(user)
        avgRating = user.avarageRate

        return Response(UserProfileSerializer(user, many=False).data)

    def post(self, request):
        """
        POST method
        """

        #Comment the following line and remove the comment from one after that to test with Postman
        username = request.user.username
        #username = request.data.get('username', '')
        voter0 = User.objects.get(username=username)
        voter = UserProfile.objects.get(user=voter0)

        votedusername = request.data.get('voted', '')
        voted0 = User.objects.get(username=votedusername)
        voteduser = UserProfile.objects.get(user=voted0)

        value = request.data.get('rating', '0')

        areFriends = False
        friends, pending, rejected = get_friends(voter, False)
        for f in friends:
            if f == voteduser:
                areFriends = True
                break

        oldRating = Rate.objects.filter(voter=voter, voted=voteduser).first()
        if areFriends:
            actualrating = int(voteduser.avarageRate)
            numTimes = int(voteduser.numRate)
            new = int(value)

            if oldRating:
                oldRating.delete()
                old = int(oldRating.value)
                voteduser.avarageRate = int(
                    (actualrating * numTimes + new - old) / (numTimes))

            else:
                voteduser.avarageRate = int(
                    (actualrating * numTimes + new) / (numTimes + 1))
                voteduser.numRate = numTimes + 1

            rate = Rate(voter=voter, voted=voteduser, value=value)
            voteduser.save()
            rate.save()
        else:
            raise ValueError("You can not rate this user")

        return Response(UserProfileSerializer(voteduser, many=False).data)


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


def get_friends(user, discover):
    """
    Method to get the list of an user's friends or pending friends
    """
    friends = []
    pending = []
    rejected = []

    sended_accepted = Invitation.objects.filter(sender=user, status="A")
    if sended_accepted:
        for i in sended_accepted:
            if i.receiver.status=='A':
                friends.append(i.receiver)

    received_accepted = Invitation.objects.filter(receiver=user, status="A")
    if received_accepted:
        for j in received_accepted:
            if j.sender.status=='A':
                friends.append(j.sender)

    sended_rejected = Invitation.objects.filter(sender=user, status="R")
    if sended_rejected:
        for i in sended_rejected:
            if i.receiver.status=='A':
                rejected.append(i.receiver)

    received_rejected = Invitation.objects.filter(receiver=user, status="R")
    if received_rejected:
        for j in received_rejected:
            if j.sender.status=='A':
                rejected.append(j.sender)

    received_pending = Invitation.objects.filter(receiver=user, status="P")
    if received_pending:
        for i in received_pending:
            if i.sender.status=='A':
                pending.append(i.sender)

    if discover:
        sended_pending = Invitation.objects.filter(sender=user, status="P")
        if sended_pending:
            for j in sended_pending:
                    pending.append(j.receiver)


    return (friends, pending, rejected)

def get_deleted_users():
    """
    Method to get the list of all deleted users
    """
    users = []

    users_deleted = UserProfile.objects.filter(status="D")
    for i in users_deleted:
        users.append(i)

    return users

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

        friends, pending, rejected = get_friends(user, False)

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

        friends, pending, rejected = get_friends(user, False)

        return Response(UserProfileSerializer(pending, many=True).data)

class GetPendingInvitationsView(APIView):
    """
    Method to get the user's invitations not accepted
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        pendingI=[]

        user = get_user_by_token(request)

        pendingInvitations = get_pendingInvitations(user, False)
        if pendingInvitations:
            for i in pendingInvitations:
                    pendingI.append(i.receiver)

        return Response(UserProfileSerializer(pendingI, many=True).data)



def get_pendingInvitations(user, discover):
    """
    Method to get the list of an user's invitations not accepted
    """

    pendingInvitations = []

    pendingInvitations = Invitation.objects.filter(sender=user, status="P")

    return pendingInvitations


class SendInvitation(APIView):
    """
    Method to send a friend invitation to other user
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        sender = get_user_by_token(request)

        receivername = request.data.get("username", "")
        receiver = User.objects.get(username=receivername).userprofile

        allinvitations = Invitation.objects.all()

        control = None

        for invitation in allinvitations:
            if invitation.sender == receiver and invitation.receiver == sender and invitation.status == "P":
                control = "A"
                break
            elif invitation.sender == sender and invitation.receiver == receiver and invitation.status == "P":
                control = "B"
                break
            elif invitation.sender == receiver and invitation.receiver == sender and invitation.status == "R":
                control = "C"
                break
            elif invitation.sender == sender and invitation.receiver == receiver and invitation.status == "R":
                control = "D"
                break
            elif invitation.sender == receiver and invitation.receiver == sender and invitation.status == "A":
                control = "E"
                break
            elif invitation.sender == sender and invitation.receiver == receiver and invitation.status == "A":
                control = "F"
                break
            elif sender == receiver:
                control = "G"
                break

        if control == "A":
            raise ValueError(
                "This person has sent you a friend request before")
        elif control == "B":
            raise ValueError(
                "You already sent a friend request to this person before")
        elif control == "C":
            raise ValueError("You already rejected this person")
        elif control == "D":
            raise ValueError("This person has rejected you")
        elif control == "E":
            raise ValueError("You are already friends")
        elif control == "F":
            raise ValueError("You are already friends")
        elif control == "G":
            raise ValueError("You can't be your own friend")
        elif control == None:
            newinvitation = Invitation(
                sender=sender, receiver=receiver, status="P")
            newinvitation.save()

        return Response(InvitationSerializer(newinvitation, many=False).data)


class AcceptFriend(APIView):
    """
    Method to accept an invitation to be a friend of the logged user
    """

    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        sendername = request.data.get("sendername", "")
        sender = User.objects.get(username=sendername).userprofile

        try:
            invitation = Invitation.objects.filter(
                sender=sender, status="P").get(receiver=user)
        except Invitation.DoesNotExist:
            invitation = None

        if invitation is not None:
            invitation.status = "A"
            invitation.save()
        else:
            raise ValueError(
                "There is no pending invitation for that two users")

        return Response(InvitationSerializer(invitation, many=False).data)


class RejectFriend(APIView):
    """
    Method to decline an invitation to be a friend of the logged user
    """

    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        sendername = request.data.get("sendername", "")
        sender = User.objects.get(username=sendername).userprofile

        try:
            invitation = Invitation.objects.filter(
                sender=sender, status="P").get(receiver=user)
        except Invitation.DoesNotExist:
            invitation = None

        if invitation is not None:
            invitation.status = "R"
            invitation.save()
        else:
            raise ValueError(
                "There is no pending invitation for that two users")

        return Response(InvitationSerializer(invitation, many=False).data)


class RemoveFriend(APIView):
    """
    Method to remove a friend of the logged user
    """

    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        sendername = request.data.get("sendername", "")
        sender = User.objects.get(username=sendername).userprofile

        try:
            invitation = Invitation.objects.get(Q(sender=sender, receiver=user, status="A") | Q(sender=user, receiver=sender, status="A"))
        except Invitation.DoesNotExist:
            invitation = None

        if invitation is not None:
            invitation.status = "R"
            invitation.save()
        else:
            raise ValueError("No relation between these two users")

        return Response(InvitationSerializer(invitation, many=False).data)

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
        friends, pending, rejected = get_friends(user, True)
        limit = int(request.data.get("limit",""))
        offset = int(request.data.get("offset",""))
        discover_people = []
        interests = user.interests.all()

        # First, we obtain the people with the same interests
        #for interest in interests:
        ranking = []
        for interest in interests:
            l = []
            l.append(interest)
            aux = UserProfile.objects.filter(interests__in=l)
            for person in aux:
                ranking.append(person)
        import collections
        ranking = collections.Counter(ranking).most_common()
        discover_people = [i[0] for i in ranking]
        discover_people = set(discover_people)

        # After, we obtain the people without the same interests
        # and append them at the end of the discover list
        all_users = list(UserProfile.objects.all())
        for person in discover_people:
            all_users.remove(person)
        for person in all_users:
            discover_people.add(person)

        # Finally, we remove from the discover list the people
        # who are our friends or pending friends
        for person in friends:
            discover_people.discard(person)
        for person in pending:
            discover_people.discard(person)
        for person in rejected:
            discover_people.discard(person)
        # who are the deleted users and remove them
        deleted_users = get_deleted_users()
        for person in deleted_users:
            discover_people.discard(person)

        discover_people.discard(user)
        discover_people = list(discover_people)
        return Response(UserProfileSerializer(discover_people[limit:limit+offset], many=True).data)


class MyTripsList(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(
            user__user=self.request.user).order_by('-startDate')


class AvailableTripsList(generics.ListAPIView):
    ''' Gets trips available (Application not rejected) '''
    
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        today = datetime.today()
        user_profile = UserProfile.objects.get(user=self.request.user)

        myRejectedApplications = Application.objects.filter(applicant_id = user_profile.id, status='R')
        myRejectedAppTripsIds = Trip.objects.filter(applications__in=myRejectedApplications).values_list('id', flat=True)
        premiumUsers = UserProfile.objects.filter(isPremium=1).values_list('id', flat=True)

        return Trip.objects.annotate(isPremiumUser=Case(When(user_id__in=premiumUsers, then=Value(1)),default=Value(0),output_field=IntegerField())).filter(
            Q(status=True) & Q(startDate__gte=today) & Q(
                tripType='PUBLIC')).exclude(
                    user__user=self.request.user).exclude(id__in=myRejectedAppTripsIds).order_by('-isPremiumUser')


class AvailableTripsSearch(generics.ListAPIView):
    ''' Search trips available (Application not rejected) '''

    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    serializer_class = TripSerializer

    def get_queryset(self):
        today = datetime.today()
        user_profile = UserProfile.objects.get(user=self.request.user)

        myRejectedApplications = Application.objects.filter(applicant_id = user_profile.id, status='R')
        myRejectedAppTripsIds = Trip.objects.filter(applications__in=myRejectedApplications).values_list('id', flat=True)
        premiumUsers = UserProfile.objects.filter(isPremium=1).values_list('id', flat=True)

        return Trip.objects.annotate(isPremiumUser=Case(When(user_id__in=premiumUsers, then=Value(1)),default=Value(0),output_field=IntegerField())).filter(
            Q(status=True) & Q(startDate__gte=today) & Q(
                tripType='PUBLIC')).exclude(
                    user__user=self.request.user).exclude(id__in=myRejectedAppTripsIds).order_by('-isPremiumUser')

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


class ListLanguages(APIView):
    def get(self, request):

        languages = Language.objects.all()
        return Response(LanguageSerializer(languages, many=True).data)


class ListInterest(APIView):
    def get(self, request):

        interests = Interest.objects.all()
        return Response(InterestNameSerializer(interests, many=True).data)


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
        price = request.data.get('price', '0')
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
                price=price,
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
                price=price,
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


FullTrip = namedtuple('FullTrip', ('trip', 'applicationsList', 'pendingsList', 'rejectedList'))


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
        try:
            trip = Trip.objects.get(pk=trip_id)
            applications = Application.objects.filter(trip=trip, status="A")
            pendings = Application.objects.filter(trip=trip, status="P")
            rejected = Application.objects.filter(trip=trip, status="R")

            full_trip = FullTrip(
                trip=trip,
                applicationsList=applications,
                pendingsList=pendings,
                rejectedList=rejected,
            )
            return Response(FullTripSerializer(full_trip, many=False).data)
        except Trip.DoesNotExist:
            raise ValueError("The trip does not exist")


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
        data = request.data
        trip = Trip.objects.get(pk=request.data["tripId"])

        stored_creator = trip.user
        user = get_user_by_token(request)
        if stored_creator != user:
            raise ValueError("You are not the creator of this trip")

        if request.data["startDate"] > request.data["endDate"]:
            raise ValueError("The start date must be before that the end date")

        if request.data["tripType"] == "PUBLIC":
            raise ValueError("This trip is public, so it can't be edited ")

        serializer = TripSerializer(trip, data=data)
        if serializer.is_valid():
            serializer.save()
            try:
                new_city = City.objects.get(pk=request.data["city"])
                trip.city = new_city
            except City.DoesNotExist:
                raise ValueError("The city does not exist")
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


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
        stats['numberOfTrips'] = numberOfTrips
        stats['numberOfTripsJanuary'] = Trip.objects.filter(
            Q(startDate__month='01')).count()
        stats['numberOfTripsFebruary'] = Trip.objects.filter(
            Q(startDate__month='02')).count()
        stats['numberOfTripsMarch'] = Trip.objects.filter(
            Q(startDate__month='03')).count()
        stats['numberOfTripsApril'] = Trip.objects.filter(
            Q(startDate__month='04')).count()
        stats['numberOfTripsMay'] = Trip.objects.filter(
            Q(startDate__month='05')).count()
        stats['numberOfTripsJune'] = Trip.objects.filter(
            Q(startDate__month='06')).count()
        stats['numberOfTripsJuly'] = Trip.objects.filter(
            Q(startDate__month='07')).count()
        stats['numberOfTripsAugust'] = Trip.objects.filter(
            Q(startDate__month='08')).count()
        stats['numberOfTripsSeptember'] = Trip.objects.filter(
            Q(startDate__month='09')).count()
        stats['numberOfTripsOctober'] = Trip.objects.filter(
            Q(startDate__month='10')).count()
        stats['numberOfTripsNovember'] = Trip.objects.filter(
            Q(startDate__month='11')).count()
        stats['numberOfTripsDecember'] = Trip.objects.filter(
            Q(startDate__month='12')).count()

        numberOfPublicTrips = Trip.objects.filter(tripType='PUBLIC').count()
        numberOfPrivateTrips = Trip.objects.filter(tripType='PRIVATE').count()
        stats['numberOfPublicTrips'] = numberOfPublicTrips
        stats['numberOfPrivateTrips'] = numberOfPrivateTrips
        if (numberOfPublicTrips != 0):
            stats[
                'ratioOfPrivateTrips'] = numberOfPrivateTrips / numberOfPublicTrips
        else:
            stats['ratioOfPrivateTrips'] = 0
        stats['percentagePrivateTrips'] = numberOfPrivateTrips / numberOfTrips
        stats['percentagePublicTrips'] = numberOfPublicTrips / numberOfTrips

        numberOfUsers = UserProfile.objects.all().count()
        stats['numberOfUsers'] = numberOfUsers

        stats['numberMen'] = UserProfile.objects.filter(gender='M').count()
        stats['numberWomen'] = UserProfile.objects.filter(gender='F').count()
        stats['numberNonBinary'] = UserProfile.objects.filter(
            gender='N').count()

        stats['percentageMen'] = UserProfile.objects.filter(
            gender='M').count() / numberOfUsers
        stats['percentageWomen'] = UserProfile.objects.filter(
            gender='F').count() / numberOfUsers
        stats['percentageNonBinary'] = UserProfile.objects.filter(
            gender='N').count() / numberOfUsers

        numberOfPremiumUsers = UserProfile.objects.filter(
            isPremium=True).count()
        numberOfNonPremiumUsers = UserProfile.objects.filter(
            isPremium=False).count()
        stats['numberOfPremiumUsers'] = numberOfPremiumUsers
        stats['numberOfNonPremiumUsers'] = numberOfNonPremiumUsers
        stats['percentagePremiumUsers'] = numberOfPremiumUsers / numberOfUsers
        stats[
            'percentageNonPremiumUsers'] = numberOfNonPremiumUsers / numberOfUsers

        activeUsers = UserProfile.objects.filter(status='A').count()
        deletedUsers = UserProfile.objects.filter(status='D').count()

        if (deletedUsers != 0):
            stats['activeUsersRatio'] = activeUsers / deletedUsers
        else:
            stats['activeUsersRatio'] = 0

        stats['numberOfActiveUsers'] = activeUsers
        stats['numberOfDeletedUsers'] = deletedUsers
        stats['percentageActiveUsers'] = activeUsers / numberOfUsers
        stats['percentageDeletedUsers'] = deletedUsers / numberOfUsers

        if (numberOfNonPremiumUsers != 0):
            stats[
                'premiumUsersRatio'] = numberOfPremiumUsers / numberOfNonPremiumUsers
        else:
            stats['premiumUsersRatio'] = 0

        stats['avgTripsPerUser'] = numberOfTrips / numberOfUsers

        numberOfApps = Application.objects.all().count()
        stats['avgAppsPerTrip'] = numberOfApps / numberOfTrips

        numberOfLanguages = Language.objects.all().count()
        stats['avgLanguagesPerUser'] = numberOfLanguages / numberOfUsers
        #stats['stDevLanguagesPerUser']=

        stats['avgRatingPerUser'] = UserProfile.objects.aggregate(
            Avg('avarageRate'))['avarageRate__avg']
        #stats['stDevRatingPerUser']=
        stats['top5AppsTrips'] = TripSerializer(
            Trip.objects.annotate(
                apps=Count('applications')).order_by('-apps')[:5],
            many=True).data
        stats['top5NumberOfCitiesTrips'] = TripSerializer(
            Trip.objects.annotate(
                cities_count=Count('cities')).order_by('-cities_count')[:5],
            many=True).data
        stats['top5NumberOfTripsCities'] = CityReducedSerializer(
            City.objects.annotate(
                trips_count=Count('trips')).order_by('-trips_count')[:5],
            many=True).data
        stats['top5MostCommonInterests'] = InterestReducedSerializer(
            Interest.objects.annotate(
                users_count=Count('users')).order_by('-users_count')[:5],
            many=True).data

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


class AcceptApplicationView(APIView):
    """
    Method to accept an application to a trip specified by their IDs
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        aplication_id = request.data.get("application_id", "")

        try:
            application = Application.objects.get(pk=aplication_id)
            creator = application.trip.user
            if creator != user:
                raise ValueError(
                    "You are not the creator of the application's trip")
            if application.status != "P":
                raise ValueError(
                    "The application has just accepted or rejected")
            application.status = "A"
            application.save()
            return Response(TripSerializer(application.trip, many=False).data)
        except Application.DoesNotExist:
            raise ValueError("The application does not exist")


class RejectApplicationView(APIView):
    """
    Method to reject an application to a trip specified by their IDs
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        """
        POST method
        """
        user = get_user_by_token(request)

        aplication_id = request.data.get("application_id", "")

        try:
            application = Application.objects.get(pk=aplication_id)
            creator = application.trip.user
            if creator != user:
                raise ValueError(
                    "You are not the creator of the application's trip")
            if application.status != "P":
                raise ValueError(
                    "The application has just accepted or rejected")
            application.status = "R"
            application.save()
            return Response(TripSerializer(application.trip, many=False).data)
        except Application.DoesNotExist:
            raise ValueError("The application does not exist")


class SetUserToPremium(APIView):
    """
    Makes a user Premium
    """
    permission_classes = (IsAuthenticated, )
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def post(self, request):
        usernamepaid = request.user.username

        userpaid = User.objects.get(username=usernamepaid)
        userprofilepaid = UserProfile.objects.get(user=userpaid)
        userprofilepaid.isPremium = True
        userprofilepaid.save()

        return Response(
            UserProfileSerializer(userprofilepaid, many=False).data)


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


class RegisterUser(APIView):
    def post(self, request):
        #username = request.user.username
        #password = make_password(request.user.password)
        username = request.data.get('username', '')
        password = make_password(request.data.get('password', ''))
        email = request.data.get('email', '')
        firstName = request.data.get('first_name', '')
        lastName = request.data.get('last_name', '')
        description = request.data.get('description', '')
        birthdate = request.data.get('birthdate', '')
        gender = request.data.get('gender', '')
        nationality = request.data.get('nationality', '')
        city = request.data.get('city', '')
        profesion = request.data.get('profesion', '')
        civilStatus = request.data.get('civilStatus', '')
        status = 'A'
        import json
        languages = json.loads(request.data.get('languages'))
        interests = json.loads(request.data.get('interests'))

        user = User(username=username, password=password)
        user.save()
        try:
            photo = request.data['photo']
            discoverPhoto = request.data['discoverPhoto']

            userProfile = UserProfile(
                user=user,
                email=email,
                first_name=firstName,
                last_name=lastName,
                description=description,
                birthdate=birthdate,
                gender=gender,
                nationality=nationality,
                city=city,
                status=status,
                profesion=profesion,
                civilStatus=civilStatus,
                photo=photo,
                discoverPhoto=discoverPhoto)

            userProfile.save()
            for i in languages:
                lang = Language.objects.get(name=i)
                userProfile.languages.add(lang)
            for i in interests:
                inter = Interest.objects.get(name=i)
                inter.users.add(userProfile)
        except:

            try:
                photo = request.data['photo']

                userProfile = UserProfile(
                    user=user,
                    email=email,
                    first_name=firstName,
                    last_name=lastName,
                    description=description,
                    birthdate=birthdate,
                    gender=gender,
                    nationality=nationality,
                    city=city,
                    status=status,
                    profesion=profesion,
                    civilStatus=civilStatus,
                    photo=photo)

                userProfile.save()
                for i in languages:
                    lang = Language.objects.get(name=i)
                    userProfile.languages.add(lang)
                for i in interests:
                    inter = Interest.objects.get(name=i)
                    inter.users.add(userProfile)
            
            except:
                try:
                    discoverPhoto = request.data['discoverPhoto']

                    userProfile = UserProfile(
                        user=user,
                        email=email,
                        first_name=firstName,
                        last_name=lastName,
                        description=description,
                        birthdate=birthdate,
                        gender=gender,
                        nationality=nationality,
                        city=city,
                        status=status,
                        profesion=profesion,
                        civilStatus=civilStatus,
                        discoverPhoto=discoverPhoto)

                    userProfile.save()
                    for i in languages:
                        lang = Language.objects.get(name=i)
                        userProfile.languages.add(lang)
                    for i in interests:
                        inter = Interest.objects.get(name=i)
                        inter.users.add(userProfile)
                except:
                    userProfile = UserProfile(
                        user=user,
                        email=email,
                        first_name=firstName,
                        last_name=lastName,
                        description=description,
                        birthdate=birthdate,
                        gender=gender,
                        nationality=nationality,
                        city=city,
                        status=status,
                        profesion=profesion,
                        civilStatus=civilStatus)
                    userProfile.save()
                    for i in languages:
                        lang = Language.objects.get(name=i)
                        userProfile.languages.add(lang)
                    for i in interests:
                        inter = Interest.objects.get(name=i)
                        inter.users.add(userProfile)
            

        finally:
            return JsonResponse({'message':'Sign up performed successfuly'}, status=201)


def backendWakeUp(request):
    return JsonResponse({'message':'Waking up backend'}, status=200)
