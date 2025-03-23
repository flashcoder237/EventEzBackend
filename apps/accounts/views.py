from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .models import OrganizerProfile
from .serializers import (
    UserSerializer, 
    OrganizerProfileSerializer, 
    UserRegistrationSerializer,
    OrganizerRegistrationSerializer,
    CustomTokenObtainPairSerializer
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom view for refreshing tokens.
    """
    pass

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class OrganizerRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = OrganizerRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def become_organizer(self, request):
        user = request.user
        
        # Vérifier si l'utilisateur a déjà un profil d'organisateur
        if hasattr(user, 'organizer_profile'):
            return Response({'detail': 'Vous êtes déjà un organisateur.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le rôle de l'utilisateur
        user.role = 'organizer'
        user.save()
        
        # Créer un profil d'organisateur
        organizer_data = request.data.get('organizer_data', {})
        organizer_serializer = OrganizerProfileSerializer(data=organizer_data)
        if organizer_serializer.is_valid():
            organizer_serializer.save(user=user)
            
            # Retourner les informations mises à jour de l'utilisateur
            user_serializer = self.get_serializer(user)
            return Response(user_serializer.data)
        
        return Response(organizer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)