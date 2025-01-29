# class_catch_app/views.py

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Class, Subscription, EnrollmentHistory
from .serializers import ClassSerializer, SubscriptionSerializer, EnrollmentHistorySerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from .filters import ClassFilter
# for CAS
from rest_framework.authtoken.models import Token
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings


class ClassViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Class.objects.all().order_by('class_code', 'course_number')
    serializer_class = ClassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ClassFilter
    filterset_fields = [
        'term',
        'class_code',
        'course_number',
        'distrib',
        'instructor',
        'world_culture',
        'period',
        # if we also store 'lang_req' in the model, add here
    ]
    search_fields = ['title', 'instructor', 'class_code', 'course_number']

    @action(detail=True, methods=['get'])
    def enrollment_history(self, request, pk=None):
        class_instance = self.get_object()
        history = class_instance.enrollment_history.order_by('timestamp')
        serializer = EnrollmentHistorySerializer(history, many=True)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    CRUD viewset:
    - POST /api/subscriptions/ to create (subscribe)
    - GET /api/subscriptions/ to list the user's subscriptions
    - DELETE /api/subscriptions/<pk>/ to unsubscribe
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return subscriptions only for this logged-in user
        return Subscription.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # grab the "subscribed_class_id" from request
        class_id = request.data.get('subscribed_class_id')
        if not class_id:
            return Response({"detail": "subscribed_class_id is required."}, status=400)

        # validate that class_id is a real Class record
        class_obj = get_object_or_404(Class, pk=class_id)

        # check if already subscribed
        if Subscription.objects.filter(user=request.user, subscribed_class=class_obj).exists():
            return Response({"detail": "You are already subscribed to this class."}, status=400)

        # build data for serializer
        data_for_serializer = {
            "user": request.user.id,  # or you can store user=...
            "email": request.data.get('email') or request.user.email,
            "subscribed_class_id": class_id,
        }

        # create subscription
        serializer = self.get_serializer(data=data_for_serializer)
        serializer.is_valid(raise_exception=True)
        sub_instance = serializer.save()

        # return final serialized data
        return Response(self.get_serializer(sub_instance).data, status=201)


class UserSubscriptionsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('created_at')


class EnrollmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentHistorySerializer

    def get_queryset(self):
        class_id = self.kwargs.get('class_id')
        return EnrollmentHistory.objects.filter(class_obj_id=class_id).order_by('timestamp')

# register Django user model
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user with username, email, and password.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password or not email:
        return Response(
            {"detail": "Username, email, and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # check if user already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {"detail": "Username already taken."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # create user
    user = User.objects.create_user(
        username=username, email=email, password=password)
    return Response(
        {"detail": "User created successfully."},
        status=status.HTTP_201_CREATED
    )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    """
    Get the authenticated user's details.
    """
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })

@login_required
def cas_callback_view(request):
    """
    CAS calls back here after a successful login. 
    By now, request.user should be a valid Django user 
    (auto-created if CAS_AUTO_CREATE_USER=True).
    """
    user = request.user

    # get or create a DRF token for this user
    token, _ = Token.objects.get_or_create(user=user)

    # build a redirect URL back to Next.js with the token
    frontend_url = "http://localhost:3000/profile" # DEBUG REPLACE WITH ACTUAL URL
    redirect_url = f"{frontend_url}?token={token.key}"

    # redirect the browser to Next.js with ?token=...
    return redirect(redirect_url)