from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404

from .serializers import (
    SignupSerializer, LoginSerializer, UserSerializer, PaymentCardSerializer,
    ChefSerializer, ConsumerSerializer
)
from .models import PaymentCard, Chef, Consumer
from .permissions import UserProfilePermission

User = get_user_model()


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_type = request.data.get('user_type')
        
        # Return appropriate serializer based on user type
        if user_type == 'chef':
            chef = Chef.objects.get(user=user)
            data = ChefSerializer(chef).data
        else:
            consumer = Consumer.objects.get(user=user)
            data = ConsumerSerializer(consumer).data
        
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        
        # Return user type specific data
        user_type = user.get_user_type()
        user_data = UserSerializer(user).data
        
        response_data = {
            'token': token.key,
            'user': user_data,
        }
        
        if user_type == 'chef':
            chef = Chef.objects.get(user=user)
            response_data['profile'] = ChefSerializer(chef).data
        elif user_type == 'consumer':
            consumer = Consumer.objects.get(user=user)
            response_data['profile'] = ConsumerSerializer(consumer).data
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # delete token for the user
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out'}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If that email exists, a reset token will be sent.'}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # For development we return token in response. In production, email this link.
        return Response({'uid': uid, 'token': token}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not all([uid, token, new_password]):
            return Response({'detail': 'uid, token and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid_int = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_int)
        except Exception:
            return Response({'detail': 'Invalid uid'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)


class PaymentCardCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCardSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        card = serializer.save()
        return Response({'card': serializer.data}, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    """
    View to retrieve user profiles with access controls:
    - Consumer can read chef profiles
    - User can read their own profile
    - Chef can update their own profile
    - Consumer can update their own profile
    """
    permission_classes = [permissions.IsAuthenticated, UserProfilePermission]

    def get(self, request, user_id):
        # Get the user whose profile is being requested
        target_user = get_object_or_404(User, id=user_id)

        # Check the permission using the custom permission class
        if not self.permission_classes[1]().has_object_permission(request, self, target_user):
            return Response(
                {'detail': 'You do not have permission to view this profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # User can view their own profile or consumer can view chef profile
        user_type = target_user.get_user_type()
        if user_type == 'chef':
            chef = Chef.objects.get(user=target_user)
            serializer = ChefSerializer(chef)
        elif user_type == 'consumer':
            consumer = Consumer.objects.get(user=target_user)
            serializer = ConsumerSerializer(consumer)
        else:
            serializer = UserSerializer(target_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        # Only allow user to update their own profile
        target_user = get_object_or_404(User, id=user_id)

        if request.user.id != target_user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the user is a chef
        if hasattr(request.user, 'chef'):
            chef = get_object_or_404(Chef, user=target_user)
            serializer = ChefSerializer(chef, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is a consumer
        elif hasattr(request.user, 'consumer'):
            consumer = get_object_or_404(Consumer, user=target_user)
            serializer = ConsumerSerializer(consumer, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If user is neither chef nor consumer, return error
        return Response(
            {'detail': 'User profile type not recognized'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, user_id):
        # Only allow user to update their own profile
        target_user = get_object_or_404(User, id=user_id)

        if request.user.id != target_user.id:
            return Response(
                {'detail': 'You can only update your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the user is a chef
        if hasattr(request.user, 'chef'):
            chef = get_object_or_404(Chef, user=target_user)
            serializer = ChefSerializer(chef, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is a consumer
        elif hasattr(request.user, 'consumer'):
            consumer = get_object_or_404(Consumer, user=target_user)
            serializer = ConsumerSerializer(consumer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If user is neither chef nor consumer, return error
        return Response(
            {'detail': 'User profile type not recognized'},
            status=status.HTTP_400_BAD_REQUEST
        )
