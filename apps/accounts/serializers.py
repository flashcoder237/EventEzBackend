from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OrganizerProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class OrganizerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerProfile
        fields = ['description', 'logo', 'website', 'verified_status', 'rating', 'event_count']
        read_only_fields = ['verified_status', 'rating', 'event_count']

class UserSerializer(serializers.ModelSerializer):
    organizer_profile = OrganizerProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 
                  'role', 'organizer_type', 'company_name', 'registration_number', 
                  'is_verified', 'billing_address', 'organizer_profile']
        read_only_fields = ['id', 'email', 'role', 'is_verified']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone_number', 
                  'password', 'confirm_password']
    
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            role='user'
        )
        return user

class OrganizerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    organizer_type = serializers.ChoiceField(choices=User.TYPE_CHOICES)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone_number', 
                  'password', 'confirm_password', 'organizer_type', 
                  'company_name', 'registration_number']
    
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        
        # Valider les informations d'organisation si le type est 'organization'
        if data['organizer_type'] == 'organization':
            if not data.get('company_name'):
                raise serializers.ValidationError("Le nom de l'entreprise est requis pour les organisateurs de type organisation")
            if not data.get('registration_number'):
                raise serializers.ValidationError("Le numéro d'enregistrement est requis pour les organisateurs de type organisation")
        
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            role='organizer',
            organizer_type=validated_data.get('organizer_type'),
            company_name=validated_data.get('company_name', ''),
            registration_number=validated_data.get('registration_number', '')
        )
        
        # Créer un profil organisateur
        OrganizerProfile.objects.create(user=user)
        
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Ajouter des informations supplémentaires au token
        token['email'] = user.email
        token['username'] = user.username
        token['role'] = user.role
        
        return token

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data