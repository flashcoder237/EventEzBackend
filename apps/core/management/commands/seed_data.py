# seeders.py
import os
import random
import datetime
import json
import uuid
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.base import ContentFile

# Importation des modèles
from apps.accounts.models import User, OrganizerProfile
from apps.events.models import Event, EventCategory, EventTag, EventImage, CustomFormField
from apps.registrations.models import Registration, TicketType, TicketPurchase, Discount
from apps.payments.models import Payment, Refund, Invoice
from apps.feedback.models import EventFeedback, EventFlag, EventValidation
from apps.notifications.models import Notification, NotificationTemplate

User = get_user_model()

class Command(BaseCommand):
    help = 'Génère des données de test pour l\'application Eventez'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Génération des données de test pour Eventez...'))
        
        try:
            with transaction.atomic():
                # Nettoyer les données existantes
                self.clean_data()
                
                # Générer les données dans l'ordre des dépendances
                self.create_users()
                self.create_event_categories_and_tags()
                self.create_events()
                self.create_registrations()
                self.create_payments()
                self.create_feedback()
                self.create_notifications()
                
                self.stdout.write(self.style.SUCCESS('Données de test générées avec succès !'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la génération des données: {str(e)}'))
    
    def clean_data(self):
        """Nettoyer les données existantes, sauf les superutilisateurs"""
        self.stdout.write(self.style.WARNING('Nettoyage des données existantes...'))
        
        # Conserver les superutilisateurs
        superusers = User.objects.filter(is_superuser=True)
        superuser_ids = list(superusers.values_list('id', flat=True))
        
        # Supprimer toutes les données sauf les superutilisateurs
        Notification.objects.all().delete()
        EventFeedback.objects.all().delete()
        EventFlag.objects.all().delete()
        EventValidation.objects.all().delete()
        Refund.objects.all().delete()
        Invoice.objects.all().delete()
        Payment.objects.all().delete()
        TicketPurchase.objects.all().delete()
        Registration.objects.all().delete()
        Discount.objects.all().delete()
        TicketType.objects.all().delete()
        CustomFormField.objects.all().delete()
        Event.objects.all().delete()
        EventImage.objects.all().delete()
        EventTag.objects.all().delete()
        EventCategory.objects.all().delete()
        
        # Supprimer les utilisateurs sauf les superutilisateurs
        User.objects.exclude(id__in=superuser_ids).delete()
        
        self.stdout.write(self.style.SUCCESS('Nettoyage terminé !'))
    
    def create_users(self):
        """Création d'utilisateurs de test"""
        self.stdout.write(self.style.WARNING('Création des utilisateurs...'))
        
        # Utilisateurs standards
        standard_users = []
        for i in range(1, 21):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password123',
                first_name=random.choice(['Jean', 'Marie', 'Paul', 'Sophie', 'Luc', 'Anne', 'Michel', 'Julie']),
                last_name=random.choice(['Dupont', 'Martin', 'Dubois', 'Bernard', 'Petit', 'Leroy', 'Moreau', 'Simon']),
                phone_number=f'+23767{random.randint(1000000, 9999999)}',
                role='user',
                is_active=True,
                is_verified=True
            )
            standard_users.append(user)
        
        # Organisateurs individuels
        individual_organizers = []
        for i in range(1, 6):
            user = User.objects.create_user(
                username=f'organizer{i}',
                email=f'organizer{i}@example.com',
                password='password123',
                first_name=random.choice(['Thomas', 'Camille', 'Antoine', 'Emilie', 'Nicolas']),
                last_name=random.choice(['Lefevre', 'Girard', 'Morel', 'Fournier', 'Lambert']),
                phone_number=f'+23768{random.randint(1000000, 9999999)}',
                role='organizer',
                organizer_type='individual',
                is_active=True,
                is_verified=True
            )
            organizer_profile = OrganizerProfile.objects.create(
                user=user,
                description=f"Organisateur d'événements spécialisé dans {random.choice(['les concerts', 'les conférences', 'les séminaires', 'les ateliers', 'les événements sportifs'])}.",
                verified_status=True,
                rating=round(random.uniform(3.5, 5.0), 1)
            )
            individual_organizers.append(user)
        
        # Organisations
        organization_names = [
            'Afrik Events', 'Douala Conference Center', 'Yaoundé Festival', 
            'Cameroon Tech Hub', 'Kribi Beach Party'
        ]
        
        organization_organizers = []
        for i in range(5):
            company_name = organization_names[i]
            user = User.objects.create_user(
                username=f'org_{company_name.lower().replace(" ", "_")}',
                email=f'contact@{company_name.lower().replace(" ", "")}.cm',
                password='password123',
                first_name='Admin',
                last_name=company_name,
                phone_number=f'+23769{random.randint(1000000, 9999999)}',
                role='organizer',
                organizer_type='organization',
                company_name=company_name,
                registration_number=f'REG-{random.randint(10000, 99999)}',
                is_active=True,
                is_verified=True
            )
            organizer_profile = OrganizerProfile.objects.create(
                user=user,
                description=f"{company_name} est une entreprise spécialisée dans l'organisation d'événements au Cameroun.",
                verified_status=True,
                rating=round(random.uniform(4.0, 5.0), 1),
                event_count=random.randint(5, 20)
            )
            organization_organizers.append(user)
        
        # Créer un admin pour les tests
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@eventez.cm',
            password='admin123',
            first_name='Admin',
            last_name='Eventez',
            phone_number='+237670000000',
            role='admin',
            is_staff=True,
            is_active=True,
            is_verified=True
        )
        
        self.users = standard_users
        self.individual_organizers = individual_organizers
        self.organization_organizers = organization_organizers
        self.stdout.write(self.style.SUCCESS(f'Créé {len(standard_users)} utilisateurs standards, {len(individual_organizers)} organisateurs individuels et {len(organization_organizers)} organisations !'))
    
    def create_event_categories_and_tags(self):
        """Création des catégories et tags d'événements"""
        self.stdout.write(self.style.WARNING('Création des catégories et tags...'))
        
        # Catégories
        categories = [
            {'name': 'Concerts', 'description': 'Événements musicaux et spectacles'},
            {'name': 'Conférences', 'description': 'Conférences professionnelles et académiques'},
            {'name': 'Séminaires', 'description': 'Sessions de formation et ateliers'},
            {'name': 'Sports', 'description': 'Compétitions et événements sportifs'},
            {'name': 'Expositions', 'description': 'Expositions d\'art et de culture'},
            {'name': 'Gastronomie', 'description': 'Festivals culinaires et dégustations'},
            {'name': 'Technologie', 'description': 'Meetups, hackathons et événements tech'},
            {'name': 'Affaires', 'description': 'Réunions d\'affaires et networking'},
        ]
        
        # Créer les catégories
        category_objects = []
        for cat in categories:
            category = EventCategory.objects.create(
                name=cat['name'],
                description=cat['description']
            )
            category_objects.append(category)
        
        # Tags
        tags = [
            'Musique', 'Business', 'Formation', 'Technologie', 'Développement', 
            'Networking', 'Art', 'Culture', 'Gastronomie', 'Sport', 'Santé', 
            'Education', 'Mode', 'Design', 'Sciences', 'Politique', 'Gratuit', 
            'VIP', 'Famille', 'En ligne', 'Hybride', 'Weekend', 'Soirée', 'Débutants'
        ]
        
        # Créer les tags
        tag_objects = []
        for tag_name in tags:
            tag = EventTag.objects.create(name=tag_name)
            tag_objects.append(tag)
        
        self.categories = category_objects
        self.tags = tag_objects
        self.stdout.write(self.style.SUCCESS(f'Créé {len(category_objects)} catégories et {len(tag_objects)} tags !'))
    
    def create_events(self):
        """Création des événements de test"""
        self.stdout.write(self.style.WARNING('Création des événements...'))
        
        # Villes camerounaises
        cities = ['Douala', 'Yaoundé', 'Bafoussam', 'Garoua', 'Bamenda', 'Maroua', 'Limbé', 'Kribi', 'Buea', 'Ngaoundéré']
        
        # Créer une diversité d'événements
        events = []
        
        # Événements futurs avec billetterie
        for i in range(1, 16):
            # Dates futures (entre aujourd'hui et 90 jours dans le futur)
            start_date = timezone.now() + datetime.timedelta(days=random.randint(7, 90))
            end_date = start_date + datetime.timedelta(hours=random.randint(2, 12))
            registration_deadline = start_date - datetime.timedelta(days=random.randint(1, 5))
            
            organizer = random.choice(self.individual_organizers + self.organization_organizers)
            category = random.choice(self.categories)
            
            # Créer l'événement
            event = Event.objects.create(
                title=f"{random.choice(['Grand', 'Super', 'Méga', 'Festival', 'Expo'])} {category.name} {random.choice(cities)}",
                slug=f"event-{i}-{uuid.uuid4().hex[:8]}",
                description=f"Cet événement est l'occasion de découvrir les meilleurs {category.name.lower()} du Cameroun. Ne manquez pas cet événement unique en son genre !",
                short_description=f"Découvrez les meilleurs {category.name.lower()} du Cameroun",
                organizer=organizer,
                category=category,
                event_type='billetterie',
                start_date=start_date,
                end_date=end_date,
                registration_deadline=registration_deadline,
                location_name=f"{category.name} Arena",
                location_address=f"{random.randint(1, 100)} Avenue Principale",
                location_city=random.choice(cities),
                location_country="Cameroun",
                status=random.choice(['draft', 'published', 'validated', 'validated', 'validated']),  # Plus de chance d'être validé
                is_featured=random.choice([True, False, False, False]),  # 25% de chance d'être mis en avant
                view_count=random.randint(50, 1000),
                registration_count=0  # Sera mis à jour plus tard
            )
            
            # Ajouter des tags aléatoires
            for _ in range(random.randint(2, 5)):
                event.tags.add(random.choice(self.tags))
            
            events.append(event)
            
            # Créer des types de billets pour chaque événement
            self.create_ticket_types(event)
        
        # Événements futurs avec formulaire d'inscription
        for i in range(1, 11):
            # Dates futures (entre aujourd'hui et 90 jours dans le futur)
            start_date = timezone.now() + datetime.timedelta(days=random.randint(7, 90))
            end_date = start_date + datetime.timedelta(hours=random.randint(2, 12))
            registration_deadline = start_date - datetime.timedelta(days=random.randint(1, 5))
            
            organizer = random.choice(self.individual_organizers + self.organization_organizers)
            category = random.choice([cat for cat in self.categories if cat.name in ['Conférences', 'Séminaires', 'Technologie', 'Affaires']])
            
            # Créer l'événement
            event = Event.objects.create(
                title=f"{random.choice(['Workshop', 'Séminaire', 'Conférence', 'Formation', 'Meetup'])} sur {random.choice(['le développement web', 'le marketing digital', 'l\'entrepreneuriat', 'la finance', 'l\'intelligence artificielle'])}",
                slug=f"event-form-{i}-{uuid.uuid4().hex[:8]}",
                description="Participez à cet événement de formation professionnelle pour acquérir de nouvelles compétences et développer votre réseau. Cet événement est limité en places, inscrivez-vous dès maintenant !",
                short_description="Formation professionnelle pour acquérir de nouvelles compétences",
                organizer=organizer,
                category=category,
                event_type='inscription',
                start_date=start_date,
                end_date=end_date,
                registration_deadline=registration_deadline,
                location_name=f"{organizer.company_name if organizer.organizer_type == 'organization' else 'Centre de formation'} - Salle {random.randint(1, 20)}",
                location_address=f"{random.randint(1, 100)} Rue des Formations",
                location_city=random.choice(cities),
                location_country="Cameroun",
                status=random.choice(['draft', 'published', 'validated', 'validated']),
                is_featured=random.choice([True, False, False, False]),
                view_count=random.randint(20, 500),
                registration_count=0,
                form_storage_usage=random.uniform(0.1, 2.0),
                form_active_days=random.randint(1, 30)
            )
            
            # Ajouter des tags aléatoires
            for _ in range(random.randint(2, 5)):
                event.tags.add(random.choice(self.tags))
            
            events.append(event)
            
            # Créer des champs de formulaire pour chaque événement d'inscription
            self.create_form_fields(event)
        
        # Événements passés (pour les statistiques et l'historique)
        for i in range(1, 8):
            # Dates passées (entre 90 jours dans le passé et aujourd'hui)
            end_date = timezone.now() - datetime.timedelta(days=random.randint(1, 90))
            start_date = end_date - datetime.timedelta(hours=random.randint(2, 12))
            registration_deadline = start_date - datetime.timedelta(days=random.randint(1, 5))
            
            organizer = random.choice(self.individual_organizers + self.organization_organizers)
            category = random.choice(self.categories)
            event_type = random.choice(['billetterie', 'inscription'])
            
            # Créer l'événement
            event = Event.objects.create(
                title=f"[PASSÉ] {random.choice(['Événement', 'Festival', 'Rencontre', 'Soirée'])} {category.name} {random.choice(cities)}",
                slug=f"past-event-{i}-{uuid.uuid4().hex[:8]}",
                description="Cet événement est déjà passé. Merci à tous les participants pour leur présence !",
                short_description="Événement passé",
                organizer=organizer,
                category=category,
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                registration_deadline=registration_deadline,
                location_name=f"Salle {random.randint(1, 50)}",
                location_address=f"{random.randint(1, 100)} Boulevard Principal",
                location_city=random.choice(cities),
                location_country="Cameroun",
                status='completed',
                is_featured=False,
                view_count=random.randint(100, 2000),
                registration_count=random.randint(10, 200),
                form_storage_usage=random.uniform(0.1, 5.0) if event_type == 'inscription' else 0,
                form_active_days=random.randint(10, 60) if event_type == 'inscription' else 0
            )
            
            # Ajouter des tags aléatoires
            for _ in range(random.randint(2, 5)):
                event.tags.add(random.choice(self.tags))
            
            events.append(event)
            
            # Créer des types de billets ou des champs de formulaire selon le type d'événement
            if event_type == 'billetterie':
                self.create_ticket_types(event)
            else:
                self.create_form_fields(event)
        
        self.events = events
        self.stdout.write(self.style.SUCCESS(f'Créé {len(events)} événements !'))
    
    def create_ticket_types(self, event):
        """Création des types de billets pour un événement"""
        # Types de billets standards
        ticket_types = [
            {'name': 'Standard', 'price': random.randint(5000, 15000), 'quantity': random.randint(50, 200)},
            {'name': 'VIP', 'price': random.randint(20000, 50000), 'quantity': random.randint(10, 50)},
        ]
        
        # Ajouter des types de billets aléatoires supplémentaires
        extras = [
            {'name': 'Early Bird', 'price': random.randint(3000, 10000), 'quantity': random.randint(20, 100)},
            {'name': 'Groupe (5 personnes)', 'price': random.randint(20000, 60000), 'quantity': random.randint(5, 20)},
            {'name': 'Premium', 'price': random.randint(30000, 80000), 'quantity': random.randint(5, 30)},
        ]
        
        if random.choice([True, False]):
            ticket_types.append(random.choice(extras))
        
        # Dates de début et fin de vente
        now = timezone.now()
        sales_start = now if event.status == 'validated' else event.start_date - datetime.timedelta(days=random.randint(30, 60))
        sales_end = event.registration_deadline or event.start_date - datetime.timedelta(days=1)
        
        # Créer les types de billets
        created_types = []
        for ticket in ticket_types:
            ticket_type = TicketType.objects.create(
                event=event,
                name=ticket['name'],
                description=f"Billet {ticket['name']} pour {event.title}",
                price=ticket['price'],
                quantity_total=ticket['quantity'],
                quantity_sold=0,  # Sera mis à jour lors des inscriptions
                sales_start=sales_start,
                sales_end=sales_end,
                is_visible=True,
                max_per_order=min(10, ticket['quantity']),
                min_per_order=1
            )
            created_types.append(ticket_type)
        
        # Ajouter des codes promo pour certains événements
        if random.choice([True, False, False]):  # 33% de chance
            discount = Discount.objects.create(
                event=event,
                code=f"PROMO{random.randint(10, 99)}",
                discount_type=random.choice(['percentage', 'fixed']),
                value=random.randint(5, 30) if random.choice(['percentage', 'fixed']) == 'percentage' else random.randint(1000, 5000),
                valid_from=now,
                valid_until=event.start_date,
                max_uses=random.randint(10, 100),
                times_used=0
            )
            
            # Appliquer la réduction à certains types de billets
            for ticket_type in created_types:
                if random.choice([True, False]):
                    discount.applicable_ticket_types.add(ticket_type)
    
    def create_form_fields(self, event):
        """Création des champs de formulaire pour un événement d'inscription"""
        # Champs standards
        fields = [
            {'label': 'Nom complet', 'field_type': 'text', 'required': True, 'order': 1},
            {'label': 'Email', 'field_type': 'email', 'required': True, 'order': 2},
            {'label': 'Téléphone', 'field_type': 'phone', 'required': True, 'order': 3},
            {'label': 'Entreprise / Organisation', 'field_type': 'text', 'required': False, 'order': 4},
        ]
        
        # Champs spécifiques selon la catégorie
        if event.category.name == 'Conférences' or event.category.name == 'Séminaires':
            fields.extend([
                {'label': 'Profession', 'field_type': 'text', 'required': True, 'order': 5},
                {'label': 'Avez-vous des attentes particulières ?', 'field_type': 'textarea', 'required': False, 'order': 6},
                {'label': 'Comment avez-vous entendu parler de cet événement ?', 'field_type': 'select', 
                 'options': 'Réseaux sociaux,Site web,Bouche à oreille,Email,Autre', 'required': False, 'order': 7},
            ])
        
        elif event.category.name == 'Technologie':
            fields.extend([
                {'label': 'Niveau de compétence', 'field_type': 'select', 
                 'options': 'Débutant,Intermédiaire,Avancé,Expert', 'required': True, 'order': 5},
                {'label': 'Technologies maîtrisées', 'field_type': 'checkbox', 
                 'options': 'HTML/CSS,JavaScript,Python,PHP,Java,SQL,React,Angular,Vue.js,Node.js,Django,Laravel', 'required': False, 'order': 6},
                {'label': 'Avez-vous un ordinateur portable ?', 'field_type': 'radio', 
                 'options': 'Oui,Non', 'required': True, 'order': 7},
            ])
        
        elif event.category.name == 'Affaires':
            fields.extend([
                {'label': 'Secteur d\'activité', 'field_type': 'text', 'required': True, 'order': 5},
                {'label': 'Fonction', 'field_type': 'text', 'required': True, 'order': 6},
                {'label': 'Objectifs de participation', 'field_type': 'checkbox', 
                 'options': 'Networking,Recherche de partenaires,Investissement,Formation,Autre', 'required': True, 'order': 7},
            ])
        
        # Créer les champs
        for field in fields:
            CustomFormField.objects.create(
                event=event,
                label=field['label'],
                field_type=field['field_type'],
                required=field['required'],
                placeholder=f"Entrez votre {field['label'].lower()}" if field['field_type'] in ['text', 'email', 'phone'] else "",
                help_text=f"Ce champ est {'obligatoire' if field['required'] else 'optionnel'}" if random.choice([True, False]) else "",
                options=field.get('options', ""),
                order=field['order']
            )
    
    def create_registrations(self):
        """Création des inscriptions aux événements"""
        self.stdout.write(self.style.WARNING('Création des inscriptions...'))
        
        registrations = []
        
        # Inscriptions pour les événements avec billetterie
        billetterie_events = [event for event in self.events if event.event_type == 'billetterie' and event.status in ['validated', 'completed']]
        
        for event in billetterie_events:
            # Nombre d'inscriptions pour cet événement
            num_registrations = random.randint(5, 30)
            
            for _ in range(num_registrations):
                user = random.choice(self.users)
                
                # Créer l'inscription
                registration = Registration.objects.create(
                    event=event,
                    user=user,
                    registration_type='billetterie',
                    status=random.choice(['confirmed', 'confirmed', 'confirmed', 'pending']),  # 75% de chance d'être confirmé
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
                    confirmed_at=timezone.now() - datetime.timedelta(days=random.randint(1, 15)) if random.choice([True, True, True, False]) else None,
                    reference_code=f"EVT{random.randint(10000, 99999)}"
                )
                
                # Si l'inscription est confirmée, mettre à jour le statut
                if registration.status == 'confirmed' and not registration.confirmed_at:
                    registration.confirmed_at = timezone.now() - datetime.timedelta(days=random.randint(1, 15))
                    registration.save()
                
                # Créer des achats de billets
                ticket_types = TicketType.objects.filter(event=event)
                if ticket_types.exists():
                    # Choisir un type de billet aléatoire
                    ticket_type = random.choice(ticket_types)
                    quantity = random.randint(1, min(5, ticket_type.max_per_order))
                    
                    # Vérifier si un code promo est disponible
                    discount = None
                    discount_amount = 0
                    
                    discounts = Discount.objects.filter(event=event, applicable_ticket_types=ticket_type)
                    if discounts.exists() and random.choice([True, False, False]):  # 33% de chance
                        discount = random.choice(discounts)
                        
                        # Calculer la remise
                        if discount.discount_type == 'percentage':
                            discount_amount = (ticket_type.price * discount.value / 100) * quantity
                        else:  # fixed
                            discount_amount = min(discount.value * quantity, ticket_type.price * quantity)
                        
                        # Incrémenter le compteur d'utilisation
                        discount.times_used += 1
                        discount.save()
                    
                    # Calculer le prix total
                    unit_price = ticket_type.price
                    total_price = (unit_price * quantity) - discount_amount
                    
                    # Créer l'achat de billets
                    ticket_purchase = TicketPurchase.objects.create(
                        registration=registration,
                        ticket_type=ticket_type,
                        quantity=quantity,
                        unit_price=unit_price,
                        discount_code=discount,
                        discount_amount=discount_amount,
                        total_price=total_price,
                        is_checked_in=random.choice([True, False]) if event.status == 'completed' else False,
                        checked_in_at=event.end_date - datetime.timedelta(hours=random.randint(1, 3)) if event.status == 'completed' and random.choice([True, False]) else None
                    )
                    
                    # Mettre à jour le nombre de billets vendus
                    ticket_type.quantity_sold += quantity
                    ticket_type.save()
                    
                registrations.append(registration)
        
        # Inscriptions pour les événements avec formulaire
        form_events = [event for event in self.events if event.event_type == 'inscription' and event.status in ['validated', 'completed']]
        
        for event in form_events:
            # Nombre d'inscriptions pour cet événement
            num_registrations = random.randint(5, 20)
            
            for _ in range(num_registrations):
                user = random.choice(self.users)
                
                # Créer des données de formulaire
                form_data = {}
                
                # Récupérer les champs du formulaire
                form_fields = CustomFormField.objects.filter(event=event)
                
                for field in form_fields:
                    if field.field_type == 'text':
                        if field.label == 'Nom complet':
                            form_data[field.label] = f"{user.first_name} {user.last_name}"
                        elif field.label == 'Entreprise / Organisation':
                            form_data[field.label] = random.choice(['Acme Inc', 'Tech Solutions', 'Global Services', 'Local Business', ''])
                        elif field.label == 'Profession':
                            form_data[field.label] = random.choice(['Développeur', 'Designer', 'Manager', 'Entrepreneur', 'Consultant', 'Étudiant'])
                        elif field.label == 'Secteur d\'activité':
                            form_data[field.label] = random.choice(['Technologie', 'Finance', 'Éducation', 'Santé', 'Commerce', 'Transport'])
                        elif field.label == 'Fonction':
                            form_data[field.label] = random.choice(['Directeur', 'Responsable', 'Chargé de projet', 'Analyste', 'Consultant'])
                        else:
                            form_data[field.label] = f"Valeur pour {field.label}"
                    
                    elif field.field_type == 'email':
                        form_data[field.label] = user.email
                    
                    elif field.field_type == 'phone':
                        form_data[field.label] = user.phone_number
                    
                    elif field.field_type == 'textarea':
                        form_data[field.label] = random.choice([
                            "Je souhaite approfondir mes connaissances dans ce domaine.",
                            "J'espère rencontrer des personnes partageant les mêmes intérêts.",
                            "Je suis intéressé par les opportunités de networking.",
                            "Je veux découvrir les dernières tendances du secteur.",
                            ""
                        ])
                    
                    elif field.field_type == 'select':
                        options = field.options.split(',')
                        form_data[field.label] = random.choice(options)
                    
                    elif field.field_type == 'checkbox':
                        options = field.options.split(',')
                        selected = random.sample(options, random.randint(1, min(3, len(options))))
                        form_data[field.label] = selected
                    
                    elif field.field_type == 'radio':
                        options = field.options.split(',')
                        form_data[field.label] = random.choice(options)
                
                # Calculer la taille des données du formulaire (approximative)
                form_data_size = len(json.dumps(form_data)) / (1024 * 1024)  # Taille en MB
                
                # Créer l'inscription
                registration = Registration.objects.create(
                    event=event,
                    user=user,
                    registration_type='inscription',
                    status=random.choice(['confirmed', 'confirmed', 'confirmed', 'pending']),
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
                    confirmed_at=timezone.now() - datetime.timedelta(days=random.randint(1, 15)) if random.choice([True, True, True, False]) else None,
                    reference_code=f"FORM{random.randint(10000, 99999)}",
                    form_data=form_data,
                    form_data_size=form_data_size
                )
                
                registrations.append(registration)
        
        # Mettre à jour le nombre d'inscriptions pour chaque événement
        for event in self.events:
            event_registrations = Registration.objects.filter(event=event).count()
            event.registration_count = event_registrations
            event.save()
        
        self.registrations = registrations
        self.stdout.write(self.style.SUCCESS(f'Créé {len(registrations)} inscriptions !'))
    
    def create_payments(self):
        """Création des paiements et factures"""
        self.stdout.write(self.style.WARNING('Création des paiements...'))
        
        payments = []
        
        # Paiements pour les inscriptions confirmées
        confirmed_registrations = [reg for reg in self.registrations if reg.status == 'confirmed']
        
        for registration in confirmed_registrations:
            # Pour les événements avec billetterie
            if registration.registration_type == 'billetterie':
                # Récupérer les achats de billets
                ticket_purchases = TicketPurchase.objects.filter(registration=registration)
                
                if ticket_purchases.exists():
                    # Calculer le montant total
                    total_amount = sum(purchase.total_price for purchase in ticket_purchases)
                    
                    # Créer le paiement
                    payment = Payment.objects.create(
                        registration=registration,
                        user=registration.user,
                        amount=total_amount,
                        currency='XAF',
                        payment_method=random.choice(['mtn_money', 'orange_money', 'credit_card']),
                        status='completed',
                        transaction_id=f"TX-{uuid.uuid4().hex[:10].upper()}",
                        payment_date=registration.confirmed_at or timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
                        billing_name=f"{registration.user.first_name} {registration.user.last_name}",
                        billing_email=registration.user.email,
                        billing_phone=registration.user.phone_number,
                        billing_address=f"{random.randint(1, 100)} Rue {random.choice(['Principale', 'des Fleurs', 'du Marché', 'de la Paix'])}, {registration.event.location_city}",
                        is_usage_based=False
                    )
                    
                    # Créer une facture
                    invoice = Invoice.objects.create(
                        payment=payment,
                        generated_at=payment.payment_date,
                        due_date=None  # Payé immédiatement
                    )
                    
                    payments.append(payment)
            
            # Pour les événements avec formulaire
            else:
                # 75% des inscriptions ont un paiement
                if random.random() < 0.75:
                    # Calculer les frais basés sur l'usage
                    storage_amount = registration.form_data_size or random.uniform(0.1, 2.0)
                    duration_days = random.randint(1, 30)
                    
                    storage_fee = storage_amount * 50  # 50 XAF par MB
                    duration_fee = duration_days * 50  # 50 XAF par jour
                    total_fee = storage_fee + duration_fee
                    
                    # Créer le paiement
                    payment = Payment.objects.create(
                        registration=registration,
                        user=registration.user,
                        amount=total_fee,
                        currency='XAF',
                        payment_method=random.choice(['mtn_money', 'orange_money', 'bank_transfer']),
                        status='completed',
                        transaction_id=f"TX-FORM-{uuid.uuid4().hex[:10].upper()}",
                        payment_date=registration.confirmed_at or timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
                        billing_name=f"{registration.user.first_name} {registration.user.last_name}",
                        billing_email=registration.user.email,
                        billing_phone=registration.user.phone_number,
                        billing_address=f"{random.randint(1, 100)} Rue {random.choice(['Principale', 'des Fleurs', 'du Marché', 'de la Paix'])}, {registration.event.location_city}",
                        is_usage_based=True,
                        storage_amount=storage_amount,
                        duration_days=duration_days
                    )
                    
                    # Créer une facture
                    invoice = Invoice.objects.create(
                        payment=payment,
                        generated_at=payment.payment_date,
                        due_date=None,  # Payé immédiatement
                        billing_period_start=registration.created_at,
                        billing_period_end=registration.created_at + datetime.timedelta(days=duration_days)
                    )
                    
                    payments.append(payment)
        
        # Créer quelques remboursements
        for _ in range(3):
            if payments:
                payment = random.choice(payments)
                
                # Montant du remboursement (partiel ou total)
                refund_amount = payment.amount if random.choice([True, False]) else payment.amount / 2
                
                # Créer le remboursement
                refund = Refund.objects.create(
                    payment=payment,
                    amount=refund_amount,
                    reason=random.choice([
                        "Annulation de l'événement",
                        "Indisponibilité du participant",
                        "Erreur de paiement",
                        "Demande du client"
                    ]),
                    status=random.choice(['completed', 'processing', 'requested']),
                    requested_at=timezone.now() - datetime.timedelta(days=random.randint(1, 10)),
                    processed_at=timezone.now() - datetime.timedelta(days=random.randint(0, 5)) if random.choice([True, False]) else None,
                    transaction_id=f"REF-{uuid.uuid4().hex[:8].upper()}" if random.choice([True, False]) else ""
                )
                
                # Si le remboursement est traité, mettre à jour le statut du paiement
                if refund.status == 'completed':
                    payment.status = 'refunded'
                    payment.save()
        
        self.payments = payments
        self.stdout.write(self.style.SUCCESS(f'Créé {len(payments)} paiements et quelques remboursements !'))
    
    def create_feedback(self):
        """Création des retours et feedbacks"""
        self.stdout.write(self.style.WARNING('Création des feedbacks...'))
        
        feedbacks = []
        validations = []
        flags = []
        
        # Commentaires pour les événements passés ou en cours
        events_with_feedback = [event for event in self.events if event.status in ['validated', 'completed']]
        
        for event in events_with_feedback:
            # Nombre de commentaires
            num_feedbacks = random.randint(3, 15)
            
            for _ in range(num_feedbacks):
                user = random.choice(self.users)
                
                # Éviter les doublons
                if EventFeedback.objects.filter(event=event, user=user).exists():
                    continue
                
                # Créer le feedback
                feedback = EventFeedback.objects.create(
                    event=event,
                    user=user,
                    rating=random.randint(3, 5),  # La plupart des notes sont bonnes
                    comment=random.choice([
                        "Excellent événement, très bien organisé !",
                        "J'ai beaucoup appris lors de cet événement.",
                        "Ambiance conviviale et contenu intéressant.",
                        "Organisation impeccable, je recommande !",
                        "Contenu de qualité, intervenant passionnant.",
                        "Bon rapport qualité-prix, à refaire !",
                        "Une expérience enrichissante et agréable.",
                        "",
                    ]),
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 30)),
                    is_approved=True,
                    is_featured=random.choice([True, False, False, False])  # 25% de chance d'être mis en avant
                )
                
                feedbacks.append(feedback)
        
        # Validations pour les événements actifs
        active_events = [event for event in self.events if event.status == 'validated']
        
        for event in active_events:
            # Nombre de validations
            num_validations = random.randint(5, 20)
            
            for _ in range(num_validations):
                user = random.choice(self.users)
                
                # Éviter les doublons
                if EventValidation.objects.filter(event=event, user=user).exists():
                    continue
                
                # Créer la validation
                validation = EventValidation.objects.create(
                    event=event,
                    user=user,
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 15)),
                    notes="" if random.choice([True, False, False]) else random.choice([
                        "Événement qui semble très intéressant !",
                        "J'ai hâte de participer à cet événement.",
                        "Organisateur sérieux, je recommande.",
                    ])
                )
                
                validations.append(validation)
        
        # Signalements pour quelques événements au hasard
        for _ in range(5):
            event = random.choice(self.events)
            user = random.choice(self.users)
            
            # Éviter les doublons
            if EventFlag.objects.filter(event=event, user=user).exists():
                continue
            
            # Créer le signalement
            flag = EventFlag.objects.create(
                event=event,
                user=user,
                reason=random.choice(['inappropriate', 'misleading', 'scam', 'duplicate', 'other']),
                description=random.choice([
                    "Informations incorrectes sur l'événement.",
                    "Le lieu semble suspect.",
                    "Prix excessif par rapport à la prestation.",
                    "Cet événement existe déjà sous un autre nom.",
                    "",
                ]),
                created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 20)),
                is_resolved=random.choice([True, False]),
                resolved_at=timezone.now() - datetime.timedelta(days=random.randint(1, 5)) if random.choice([True, False]) else None
            )
            
            flags.append(flag)
        
        self.stdout.write(self.style.SUCCESS(f'Créé {len(feedbacks)} commentaires, {len(validations)} validations et {len(flags)} signalements !'))
    
    def create_notifications(self):
        """Création des modèles de notification et notifications"""
        self.stdout.write(self.style.WARNING('Création des notifications...'))
        
        # Créer des modèles de notification
        templates = [
            {
                'name': 'Confirmation d\'inscription',
                'notification_type': 'registration_confirmation',
                'email_subject': 'Confirmation de votre inscription à {event_title}',
                'email_body': 'Bonjour {user_name},\n\nVotre inscription à l\'événement {event_title} a été confirmée.\n\nRéférence: {reference_code}\nDate: {event_date}\nLieu: {event_location}\n\nMerci de votre confiance,\nL\'équipe Eventez',
                'sms_body': 'Confirmation: Votre inscription à {event_title} est confirmée. Ref: {reference_code}',
                'in_app_title': 'Inscription confirmée',
                'in_app_body': 'Votre inscription à {event_title} a été confirmée.',
            },
            {
                'name': 'Confirmation de paiement',
                'notification_type': 'payment_confirmation',
                'email_subject': 'Confirmation de paiement pour {event_title}',
                'email_body': 'Bonjour {user_name},\n\nVotre paiement de {amount} {currency} pour l\'événement {event_title} a été reçu.\n\nTransaction: {transaction_id}\nDate: {payment_date}\n\nVotre facture est disponible dans votre espace personnel.\n\nMerci,\nL\'équipe Eventez',
                'sms_body': 'Paiement reçu: {amount} {currency} pour {event_title}. Merci!',
                'in_app_title': 'Paiement confirmé',
                'in_app_body': 'Votre paiement de {amount} {currency} pour {event_title} a été traité avec succès.',
            },
            {
                'name': 'Rappel d\'événement',
                'notification_type': 'event_reminder',
                'email_subject': 'Rappel: {event_title} commence demain',
                'email_body': 'Bonjour {user_name},\n\nNous vous rappelons que l\'événement {event_title} auquel vous êtes inscrit commence demain.\n\nDate: {event_date}\nLieu: {event_location}\nRéférence: {reference_code}\n\nNous avons hâte de vous y retrouver!\n\nL\'équipe Eventez',
                'sms_body': 'Rappel: {event_title} commence demain! Lieu: {event_location}',
                'in_app_title': 'Événement imminent',
                'in_app_body': '{event_title} commence demain. N\'oubliez pas votre inscription!',
            },
            {
                'name': 'Mise à jour d\'événement',
                'notification_type': 'event_update',
                'email_subject': 'Mise à jour importante: {event_title}',
                'email_body': 'Bonjour {user_name},\n\nNous vous informons d\'une mise à jour concernant l\'événement {event_title} auquel vous êtes inscrit.\n\n{update_message}\n\nPour plus d\'informations, veuillez consulter la page de l\'événement.\n\nMerci de votre compréhension,\nL\'équipe Eventez',
                'sms_body': 'Mise à jour: {event_title} - {update_message}',
                'in_app_title': 'Mise à jour d\'événement',
                'in_app_body': 'L\'événement {event_title} a été mis à jour: {update_message}',
            },
            {
                'name': 'Facturation usage',
                'notification_type': 'usage_billing_update',
                'email_subject': 'Mise à jour de facturation pour {event_title}',
                'email_body': 'Bonjour {user_name},\n\nVoici une mise à jour de votre facturation basée sur l\'usage pour l\'événement {event_title}.\n\nJours actifs: {active_days}\nStockage utilisé: {storage_usage}\nCoût estimé: {estimated_cost}\n\nVous pouvez consulter ces informations dans votre espace organisateur.\n\nMerci,\nL\'équipe Eventez',
                'in_app_title': 'Mise à jour facturation',
                'in_app_body': 'Facturation événement {event_title}: {active_days} jours, {storage_usage}, coût estimé: {estimated_cost}',
            },
        ]
        
        for template_data in templates:
            NotificationTemplate.objects.create(**template_data)
        
        # Créer des notifications pour les utilisateurs
        notifications = []
        
        # Notifications de confirmation d'inscription
        for registration in random.sample(self.registrations, min(20, len(self.registrations))):
            notification = Notification.objects.create(
                user=registration.user,
                title=f"Inscription confirmée: {registration.event.title}",
                message=f"Votre inscription à l'événement {registration.event.title} a été confirmée.",
                notification_type='registration_confirmation',
                related_object_id=str(registration.id),
                related_object_type='registration',
                channel='in_app',
                is_read=random.choice([True, False]),
                is_sent=True,
                created_at=registration.created_at + datetime.timedelta(minutes=random.randint(5, 60)),
                sent_at=registration.created_at + datetime.timedelta(minutes=random.randint(5, 60)),
                read_at=registration.created_at + datetime.timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None,
                extra_data={
                    'event_title': registration.event.title,
                    'reference_code': registration.reference_code,
                    'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                    'event_date': registration.event.start_date.strftime('%d/%m/%Y à %H:%M'),
                    'event_location': registration.event.location_address
                }
            )
            
            notifications.append(notification)
        
        # Notifications de rappel d'événement
        for event in [e for e in self.events if e.status == 'validated' and e.start_date > timezone.now()]:
            registrations = Registration.objects.filter(event=event, status='confirmed')
            
            for registration in registrations[:3]:  # Limiter à 3 par événement
                notification = Notification.objects.create(
                    user=registration.user,
                    title=f"Rappel: {event.title}",
                    message=f"L'événement {event.title} approche! N'oubliez pas votre inscription.",
                    notification_type='event_reminder',
                    related_object_id=str(event.id),
                    related_object_type='event',
                    channel='in_app',
                    is_read=random.choice([True, False]),
                    is_sent=True,
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(1, 5)),
                    sent_at=timezone.now() - datetime.timedelta(days=random.randint(1, 5)),
                    read_at=timezone.now() - datetime.timedelta(hours=random.randint(1, 12)) if random.choice([True, False]) else None,
                    extra_data={
                        'event_title': event.title,
                        'user_name': f"{registration.user.first_name} {registration.user.last_name}",
                        'event_date': event.start_date.strftime('%d/%m/%Y à %H:%M'),
                        'event_location': event.location_address,
                        'reference_code': registration.reference_code
                    }
                )
                
                notifications.append(notification)
        
        self.stdout.write(self.style.SUCCESS(f'Créé {len(templates)} modèles de notification et {len(notifications)} notifications !'))