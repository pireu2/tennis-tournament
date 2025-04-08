import os
import django
import random
import datetime
from django.utils import timezone

# Set up Django - change this line to match your project's settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Try to find the correct settings module if the above fails
if not os.path.exists(os.path.join(os.path.dirname(__file__), 'config')):
    # Try with the project name directly
    project_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    os.environ['DJANGO_SETTINGS_MODULE'] = f'{project_name}.settings'

try:
    django.setup()
    print("Django successfully set up.")
except ImportError as e:
    print(f"Failed to set up Django: {e}")
    print("\nTry setting the correct settings module path manually:")
    print("1. Look at the root directory of your project")
    print("2. Find the settings.py file - it's probably in a subdirectory")
    print("3. Update line 9 with the correct module path")
    print("   For example: 'myproject.settings' or 'config.settings'")
    exit(1)

# Import models after Django setup
from apps.accounts.models import User, TennisPlayer, Referee
from apps.tournaments.models import Tournament
from apps.matches.models import Match, MatchScore
from django.db import transaction

# Password for all test users
TEST_PASSWORD = 'password123'

@transaction.atomic
def create_users():
    # Create admin users
    admin_data = [
        {'username': 'superadmin', 'first_name': 'Super', 'last_name': 'Admin', 'email': 'superadmin@example.com', 'is_superuser': True},
        {'username': 'admin1', 'first_name': 'John', 'last_name': 'Smith', 'email': 'admin1@example.com'},
        {'username': 'admin2', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'admin2@example.com'},
    ]
    
    admin_users = []
    for data in admin_data:
        is_superuser = data.pop('is_superuser', False)
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                **data,
                password=TEST_PASSWORD,
                is_staff=True,
                is_superuser=is_superuser,
                user_type='ADMIN'
            )
            admin_users.append(user)
            print(f"Created admin user: {user.username}")
        else:
            user = User.objects.get(username=data['username'])
            user.user_type = 'ADMIN'
            user.save()
            admin_users.append(user)
            print(f"Updated existing user: {user.username}")
    
    # Create player users
    player_data = [
        {'username': 'roger', 'first_name': 'Roger', 'last_name': 'Federer', 'email': 'roger@example.com', 'ranking': 2, 'dob': '1981-08-08', 'gender': 'M'},
        {'username': 'rafael', 'first_name': 'Rafael', 'last_name': 'Nadal', 'email': 'rafael@example.com', 'ranking': 3, 'dob': '1986-06-03', 'gender': 'M'},
        {'username': 'novak', 'first_name': 'Novak', 'last_name': 'Djokovic', 'email': 'novak@example.com', 'ranking': 1, 'dob': '1987-05-22', 'gender': 'M'},
        {'username': 'andy', 'first_name': 'Andy', 'last_name': 'Murray', 'email': 'andy@example.com', 'ranking': 45, 'dob': '1987-05-15', 'gender': 'M'},
        {'username': 'serena', 'first_name': 'Serena', 'last_name': 'Williams', 'email': 'serena@example.com', 'ranking': 8, 'dob': '1981-09-26', 'gender': 'F'},
        {'username': 'venus', 'first_name': 'Venus', 'last_name': 'Williams', 'email': 'venus@example.com', 'ranking': 80, 'dob': '1980-06-17', 'gender': 'F'},
        {'username': 'maria', 'first_name': 'Maria', 'last_name': 'Sharapova', 'email': 'maria@example.com', 'ranking': 318, 'dob': '1987-04-19', 'gender': 'F'},
        {'username': 'simona', 'first_name': 'Simona', 'last_name': 'Halep', 'email': 'simona@example.com', 'ranking': 20, 'dob': '1991-09-27', 'gender': 'F'},
        {'username': 'stan', 'first_name': 'Stan', 'last_name': 'Wawrinka', 'email': 'stan@example.com', 'ranking': 30, 'dob': '1985-03-28', 'gender': 'M'},
        {'username': 'dominic', 'first_name': 'Dominic', 'last_name': 'Thiem', 'email': 'dominic@example.com', 'ranking': 15, 'dob': '1993-09-03', 'gender': 'M'},
        {'username': 'ash', 'first_name': 'Ashleigh', 'last_name': 'Barty', 'email': 'ash@example.com', 'ranking': 1, 'dob': '1996-04-24', 'gender': 'F'},
        {'username': 'naomi', 'first_name': 'Naomi', 'last_name': 'Osaka', 'email': 'naomi@example.com', 'ranking': 10, 'dob': '1997-10-16', 'gender': 'F'},
        {'username': 'alex', 'first_name': 'Alexander', 'last_name': 'Zverev', 'email': 'alex@example.com', 'ranking': 7, 'dob': '1997-04-20', 'gender': 'M'},
        {'username': 'stefanos', 'first_name': 'Stefanos', 'last_name': 'Tsitsipas', 'email': 'stefanos@example.com', 'ranking': 5, 'dob': '1998-08-12', 'gender': 'M'},
        {'username': 'coco', 'first_name': 'Coco', 'last_name': 'Gauff', 'email': 'coco@example.com', 'ranking': 15, 'dob': '2004-03-13', 'gender': 'F'},
        {'username': 'john', 'first_name': 'John', 'last_name': 'Isner', 'email': 'john@example.com', 'ranking': 22, 'dob': '1985-04-26', 'gender': 'M'},
    ]
    
    player_users = []
    for data in player_data:
        ranking = data.pop('ranking')
        dob_str = data.pop('dob')
        gender = data.pop('gender')
        
        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                **data,
                password=TEST_PASSWORD,
                user_type='PLAYER'
            )
            
            # Create or update player profile
            player, created = TennisPlayer.objects.update_or_create(
                user=user,
                defaults={
                    'ranking': ranking,
                    'date_of_birth': dob,
                    'gender': gender
                }
            )
            
            player_users.append(user)
            print(f"Created player: {user.username} with ranking {ranking}")
        else:
            user = User.objects.get(username=data['username'])
            user.user_type = 'PLAYER'
            user.save()
            
            # Create or update player profile
            player, created = TennisPlayer.objects.update_or_create(
                user=user,
                defaults={
                    'ranking': ranking,
                    'date_of_birth': dob,
                    'gender': gender
                }
            )
            
            player_users.append(user)
            print(f"Updated existing player: {user.username}")
    
    # Create referee users
    referee_data = [
        {'username': 'referee1', 'first_name': 'Carlos', 'last_name': 'Ramos', 'email': 'referee1@example.com', 'level': 'GOLD'},
        {'username': 'referee2', 'first_name': 'Alison', 'last_name': 'Hughes', 'email': 'referee2@example.com', 'level': 'SILVER'},
        {'username': 'referee3', 'first_name': 'James', 'last_name': 'Keothavong', 'email': 'referee3@example.com', 'level': 'PLATINUM'},
        {'username': 'referee4', 'first_name': 'Eva', 'last_name': 'Asderaki', 'email': 'referee4@example.com', 'level': 'GOLD'},
    ]
    
    referee_users = []
    for data in referee_data:
        level = data.pop('level')
        
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                **data,
                password=TEST_PASSWORD,
                user_type='REFEREE'
            )
            
            # Create or update referee profile
            referee, created = Referee.objects.update_or_create(
                user=user,
                defaults={
                    'certification_level': level
                }
            )
            
            referee_users.append(user)
            print(f"Created referee: {user.username} with level {level}")
        else:
            user = User.objects.get(username=data['username'])
            user.user_type = 'REFEREE'
            user.save()
            
            # Create or update referee profile
            referee, created = Referee.objects.update_or_create(
                user=user,
                defaults={
                    'certification_level': level
                }
            )
            
            referee_users.append(user)
            print(f"Updated existing referee: {user.username}")
            
    return {
        'admins': admin_users,
        'players': player_users,
        'referees': [user.referee for user in referee_users]  # Return Referee objects, not User objects
    }

@transaction.atomic
def create_tournaments(users):
    today = timezone.now().date()
    
    tournament_data = [
        {
            'name': 'Wimbledon Open 2024',
            'location': 'London, UK',
            'description': 'The prestigious grass-court Grand Slam tournament.',
            'start_date': today - datetime.timedelta(days=90),  # 3 months ago
            'end_date': today - datetime.timedelta(days=77),    # 2.5 months ago
            'registration_deadline': today - datetime.timedelta(days=120),
            'max_participants': 32,
            'status': 'COMPLETED',
            'organizer': users['admins'][1],  # admin1
            'participants': users['players'][0:8]  # First 8 players (men's tournament)
        },
        {
            'name': 'Roland Garros 2024',
            'location': 'Paris, France',
            'description': 'The world\'s premier clay court tennis championship.',
            'start_date': today - datetime.timedelta(days=150),  # 5 months ago
            'end_date': today - datetime.timedelta(days=136),    # ~4.5 months ago
            'registration_deadline': today - datetime.timedelta(days=180),
            'max_participants': 32,
            'status': 'COMPLETED',
            'organizer': users['admins'][2],  # admin2
            'participants': users['players'][4:12]  # Players 5-12 (women's tournament)
        },
        {
            'name': 'Australian Open 2025',
            'location': 'Melbourne, Australia',
            'description': 'The first Grand Slam of the year.',
            'start_date': today + datetime.timedelta(days=90),  # 3 months in future
            'end_date': today + datetime.timedelta(days=104),   # ~3.5 months in future
            'registration_deadline': today + datetime.timedelta(days=60),
            'max_participants': 32,
            'status': 'REGISTRATION',
            'organizer': users['admins'][1],  # admin1
            'participants': users['players'][4:11]  # Players 5-11 (some women registered)
        },
        {
            'name': 'US Open 2024',
            'location': 'New York, USA',
            'description': 'The final Grand Slam tournament of the year.',
            'start_date': today - datetime.timedelta(days=10),  # 10 days ago
            'end_date': today + datetime.timedelta(days=2),     # 2 days in future
            'registration_deadline': today - datetime.timedelta(days=30),
            'max_participants': 32,
            'status': 'IN_PROGRESS',
            'organizer': users['admins'][2],  # admin2
            'participants': [users['players'][i] for i in [0, 1, 2, 9, 13, 8, 9, 15]]  # Mix of players
        },
        {
            'name': 'Madrid Open 2025',
            'location': 'Madrid, Spain',
            'description': 'Premier clay court tennis tournament.',
            'start_date': today + datetime.timedelta(days=230),  # ~7.5 months in future
            'end_date': today + datetime.timedelta(days=239),    # ~8 months in future
            'registration_deadline': today + datetime.timedelta(days=200),
            'max_participants': 16,
            'status': 'UPCOMING',
            'organizer': users['admins'][0],  # superadmin
            'participants': []  # No participants yet
        },
        {
            'name': 'Italian Open 2025',
            'location': 'Rome, Italy',
            'description': 'Important clay court tournament before the French Open.',
            'start_date': today + datetime.timedelta(days=250),  # ~8 months in future
            'end_date': today + datetime.timedelta(days=257),    # ~8.5 months in future
            'registration_deadline': today + datetime.timedelta(days=220),
            'max_participants': 16,
            'status': 'UPCOMING',
            'organizer': users['admins'][1],  # admin1
            'participants': []  # No participants yet
        }
    ]
    
    tournaments = []
    for data in tournament_data:
        participants = data.pop('participants')
        
        # Convert dates from strings to date objects
        data['start_date'] = data['start_date']
        data['end_date'] = data['end_date']
        data['registration_deadline'] = data['registration_deadline']
        
        tournament = Tournament.objects.create(**data)
        
        # Add participants
        for player in participants:
            tournament.participants.add(player)
        
        tournaments.append(tournament)
        print(f"Created tournament: {tournament.name} with {len(participants)} participants")
    
    return tournaments

@transaction.atomic
def create_matches_and_scores(tournaments, users):
    # Wimbledon (completed tournament)
    create_completed_tournament_matches(
        tournament=tournaments[0],
        players=users['players'][0:8],
        referees=users['referees'],
        base_date=tournaments[0].start_date
    )
    
    # Roland Garros (completed tournament)
    create_completed_tournament_matches(
        tournament=tournaments[1],
        players=users['players'][4:12],
        referees=users['referees'],
        base_date=tournaments[1].start_date
    )
    
    # US Open (in progress)
    create_in_progress_tournament_matches(
        tournament=tournaments[3],
        players=[users['players'][i] for i in [0, 1, 2, 9, 13, 8, 9, 15]],
        referees=users['referees'],
        base_date=tournaments[3].start_date
    )
    
    print("Created matches and scores for all tournaments")
# Update this function
def create_completed_tournament_matches(tournament, players, referees, base_date):
    # Create Round 1 matches (quarterfinals)
    round1_matches = []
    for i in range(0, len(players), 2):
        if i+1 < len(players):
            # Use referee.user to get the User object for the match
            referee_obj = random.choice(referees)
            
            match = Match.objects.create(
                tournament=tournament,
                player1=players[i],
                player2=players[i+1],
                referee=referee_obj,  # Pass the Referee object directly
                round_number=1,
                court_number=i//2 + 1,
                scheduled_time=datetime.datetime.combine(
                    base_date + datetime.timedelta(days=random.randint(0, 3)),
                    datetime.time(hour=10 + 2*(i//2))
                ),
                status='COMPLETED'
            )
            round1_matches.append(match)
            
            # Create score (rest of code unchanged)
            player1_wins = random.choice([True, False])
            
            if player1_wins:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=6, player2_set1=random.randint(0, 4),
                    player1_set2=random.randint(4, 7), player2_set2=random.randint(0, 5),
                    player1_set3=6, player2_set3=random.randint(0, 4),
                    winner=match.player1
                )
            else:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=random.randint(0, 4), player2_set1=6,
                    player1_set2=random.randint(0, 5), player2_set2=random.randint(5, 7),
                    player1_set3=random.randint(0, 4), player2_set3=6,
                    winner=match.player2
                )
    
    # Create Round 2 matches (semifinals)
    round2_matches = []
    winners = []
    for i in range(0, len(round1_matches), 2):
        if i+1 < len(round1_matches):
            match1_winner = round1_matches[i].score.winner
            match2_winner = round1_matches[i+1].score.winner
            
            referee_obj = random.choice(referees)
            
            match = Match.objects.create(
                tournament=tournament,
                player1=match1_winner,
                player2=match2_winner,
                referee=referee_obj,  # Pass the Referee object directly
                round_number=2,
                court_number=i//2 + 1,
                scheduled_time=datetime.datetime.combine(
                    base_date + datetime.timedelta(days=random.randint(7, 10)),
                    datetime.time(hour=12 + 3*(i//2))
                ),
                status='COMPLETED'
            )
            round2_matches.append(match)
            
            # Create score
            player1_wins = random.choice([True, False])
            
            if player1_wins:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=6, player2_set1=random.randint(2, 4),
                    player1_set2=7, player2_set2=random.randint(5, 6),
                    player1_set3=6, player2_set3=random.randint(2, 4),
                    winner=match.player1
                )
                winners.append(match.player1)
            else:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=random.randint(2, 4), player2_set1=6,
                    player1_set2=random.randint(4, 6), player2_set2=7,
                    player1_set3=random.randint(2, 4), player2_set3=6,
                    winner=match.player2
                )
                winners.append(match.player2)
    
    # Create final match
    if len(winners) >= 2:
        referee_obj = random.choice(referees)
        
        final_match = Match.objects.create(
            tournament=tournament,
            player1=winners[0],
            player2=winners[1],
            referee=referee_obj,  # Pass the Referee object directly
            round_number=3,
            court_number=1,
            scheduled_time=datetime.datetime.combine(
                base_date + datetime.timedelta(days=random.randint(14, 16)),
                datetime.time(hour=14)
            ),
            status='COMPLETED'
        )
        
        # Create final score - more exciting 5-set match
        player1_wins = random.choice([True, False])
        
        if player1_wins:
            score = MatchScore.objects.create(
                match=final_match,
                player1_set1=6, player2_set1=random.randint(2, 4),
                player1_set2=4, player2_set2=6,
                player1_set3=7, player2_set3=6,
                player1_set4=random.randint(3, 5), player2_set4=7,
                player1_set5=6, player2_set5=4,
                winner=final_match.player1
            )
        else:
            score = MatchScore.objects.create(
                match=final_match,
                player1_set1=random.randint(2, 4), player2_set1=6,
                player1_set2=6, player2_set2=4,
                player1_set3=6, player2_set3=7,
                player1_set4=7, player2_set4=random.randint(3, 5),
                player1_set5=4, player2_set5=6,
                winner=final_match.player2
            )

# Also update this function
def create_in_progress_tournament_matches(tournament, players, referees, base_date):
    # Create Round 1 matches (all completed)
    round1_matches = []
    for i in range(0, len(players), 2):
        if i+1 < len(players):
            referee_obj = random.choice(referees)
            
            match = Match.objects.create(
                tournament=tournament,
                player1=players[i],
                player2=players[i+1],
                referee=referee_obj,  # Pass the Referee object directly
                round_number=1,
                court_number=i//2 + 1,
                scheduled_time=datetime.datetime.combine(
                    base_date + datetime.timedelta(days=random.randint(0, 3)),
                    datetime.time(hour=10 + 2*(i//2))
                ),
                status='COMPLETED'
            )
            round1_matches.append(match)
            
            # Create score
            player1_wins = random.choice([True, False])
            
            if player1_wins:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=6, player2_set1=random.randint(0, 4),
                    player1_set2=random.randint(6, 7), player2_set2=random.randint(2, 5),
                    player1_set3=6, player2_set3=random.randint(0, 4),
                    winner=match.player1
                )
            else:
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=random.randint(0, 4), player2_set1=6,
                    player1_set2=random.randint(2, 5), player2_set2=random.randint(6, 7),
                    player1_set3=random.randint(0, 4), player2_set3=6,
                    winner=match.player2
                )
    
    # Create Round 2 matches (semifinals) - one in progress, one scheduled
    round2_matches = []
    winners = []
    
    for i in range(0, len(round1_matches), 2):
        if i+1 < len(round1_matches):
            match1_winner = round1_matches[i].score.winner
            match2_winner = round1_matches[i+1].score.winner
            referee_obj = random.choice(referees)
            
            # First semifinal in progress
            if i == 0:
                match = Match.objects.create(
                    tournament=tournament,
                    player1=match1_winner,
                    player2=match2_winner,
                    referee=referee_obj,  # Pass the Referee object directly
                    round_number=2,
                    court_number=i//2 + 1,
                    scheduled_time=datetime.datetime.combine(
                        base_date + datetime.timedelta(days=random.randint(7, 8)),
                        datetime.time(hour=12)
                    ),
                    status='IN_PROGRESS'
                )
                
                # Partial score (match in progress)
                score = MatchScore.objects.create(
                    match=match,
                    player1_set1=6, player2_set1=3,
                    player1_set2=3, player2_set2=6,
                    player1_set3=random.randint(5, 6), player2_set3=random.randint(3, 5)
                )
            else:
                # Second semifinal scheduled
                match = Match.objects.create(
                    tournament=tournament,
                    player1=match1_winner,
                    player2=match2_winner,
                    referee=referee_obj,  # Pass the Referee object directly
                    round_number=2,
                    court_number=i//2 + 1,
                    scheduled_time=datetime.datetime.combine(
                        base_date + datetime.timedelta(days=random.randint(7, 8)),
                        datetime.time(hour=15)
                    ),
                    status='SCHEDULED'
                )
            
            round2_matches.append(match)

def run():
    print("Starting database population...")
    
    # Clear existing data
    print("Clearing existing data...")
    MatchScore.objects.all().delete()
    Match.objects.all().delete()
    Tournament.objects.all().delete()
    
    # Create users
    print("Creating users...")
    users = create_users()
    
    # Create tournaments
    print("Creating tournaments...")
    tournaments = create_tournaments(users)
    
    # Create matches and scores
    print("Creating matches and scores...")
    create_matches_and_scores(tournaments, users)
    
    print("Database population complete!")

if __name__ == '__main__':
    run()