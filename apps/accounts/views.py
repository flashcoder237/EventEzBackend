from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .models import OrganizerProfile, PasswordResetToken
from .serializers import (
    UserSerializer, 
    OrganizerProfileSerializer, 
    UserRegistrationSerializer,
    OrganizerRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
import uuid
import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
    
    def get_permissions(self):
        """
        Actions spécifiques qui nécessitent ou non une authentification
        """
        if self.action in ['list', 'retrieve', 'organizers']:
            # Ces actions sont accessibles sans authentification
            return [permissions.AllowAny()]
        # Toutes les autres actions nécessitent une authentification
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """
        Permet de filtrer les utilisateurs selon le rôle d'admin ou non
        Pour les actions de lecture (list, retrieve), tous les utilisateurs sont accessibles
        """
        if self.action in ['list', 'retrieve']:
            # Pour les actions de lecture générale
            if 'role' in self.request.query_params:
                # Si un rôle spécifique est demandé
                return User.objects.filter(role=self.request.query_params.get('role'))
            return User.objects.all()
        
        # Pour les actions d'administration
        if self.request.user.is_staff:
            return User.objects.all()
        
        # Pour les autres actions, l'utilisateur ne voit que son propre profil
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Retourne le profil de l'utilisateur connecté
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def organizers(self, request):
        """
        Retourne tous les organisateurs (accessible sans authentification)
        """
        organizers = User.objects.filter(role='organizer')
        page = self.paginate_queryset(organizers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(organizers, many=True)
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

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Générer un token unique
                token = str(uuid.uuid4())
                
                # Définir la date d'expiration (24 heures)
                expires_at = timezone.now() + datetime.timedelta(hours=24)
                
                # Supprimer les anciens tokens pour cet utilisateur
                PasswordResetToken.objects.filter(user=user).delete()
                
                # Créer un nouveau token
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Construire l'URL de réinitialisation (à adapter selon votre frontend)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
                
                # Préparer l'email
                context = {
                    'user': user,
                    'reset_url': reset_url,
                    'expires_at': expires_at
                }
                html_message = render_to_string('accounts/password_reset_email.html', context)
                plain_message = strip_tags(html_message)
                
                # Envoyer l'email
                send_mail(
                    subject='Réinitialisation de votre mot de passe Eventez',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return Response({
                    'detail': 'Instructions de réinitialisation envoyées par email.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Pour des raisons de sécurité, ne pas révéler si l'email existe ou non
                return Response({
                    'detail': 'Instructions de réinitialisation envoyées par email si l\'adresse existe.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                # Vérifier si le token existe et est valide
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid():
                    return Response({
                        'detail': 'Le lien de réinitialisation a expiré.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mettre à jour le mot de passe
                user = reset_token.user
                user.password = make_password(password)
                user.save()
                
                # Supprimer le token utilisé
                reset_token.delete()
                
                return Response({
                    'detail': 'Mot de passe réinitialisé avec succès.'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'detail': 'Token de réinitialisation invalide.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetValidateTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid():
                return Response({
                    'valid': False,
                    'detail': 'Le lien de réinitialisation a expiré.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'valid': True,
                'detail': 'Token valide.'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'valid': False,
                'detail': 'Token de réinitialisation invalide.'
            }, status=status.HTTP_400_BAD_REQUEST)