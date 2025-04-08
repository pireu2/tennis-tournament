import random
from abc import ABC, abstractmethod
from apps.matches.models import Match

class MatchGenerationStrategy(ABC):
    @abstractmethod
    def generate_matches(self, tournament, players):
        pass

class SingleEliminationStrategy(MatchGenerationStrategy):
    def generate_matches(self, tournament, players):
        players_list = list(players)
        random.shuffle(players_list)

        import math
        player_count = len(players_list)
        rounds_needed = math.ceil(math.log2(player_count))

        first_round_matches = 2 ** rounds_needed - player_count

        matches = []
        round_number = 1
        match_idx = 0

        while match_idx < first_round_matches:
            player1 = players_list[match_idx * 2]
            player2 = players_list[match_idx * 2 + 1]

            match = Match.objects.create(
                tournament=tournament,
                player1=player1,
                player2=player2,
                round_number=round_number,
                status='SCHEDULED'
            )
            matches.append(match)
            match_idx += 1

        remaining_players = players_list[match_idx * 2:]
        for player in remaining_players:
            pass

        return matches

class RoundRobinStrategy(MatchGenerationStrategy):
    def generate_matches(self, tournament, players):
        players_list = list(players)
        matches = []

        for i, player1 in enumerate(players_list):
            for player2 in players_list[i+1:]:
                match = Match.objects.create(
                    tournament=tournament,
                    player1=player1,
                    player2=player2,
                    round_number=1,  
                    status='SCHEDULED'
                )
                matches.append(match)

        return matches

class MatchGeneratorContext:
    def __init__(self, strategy=None):
        self.strategy = strategy or SingleEliminationStrategy()

    def set_strategy(self, strategy):
        self.strategy = strategy

    def generate_tournament_matches(self, tournament, players):
        return self.strategy.generate_matches(tournament, players)