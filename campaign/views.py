"""
:Created: 29 May 2016
:Author: Lucas Connors

"""

from django.core.cache import cache
from django.db.models import Exists, OuterRef
from django.views.generic import TemplateView

from accounts.models import UserProfile
from campaign.models import Investment


class LeaderboardView(TemplateView):

    template_name = "leaderboard/leaderboard.html"

    @staticmethod
    def investor_context(investor):
        return {
            "name": investor.get_display_name(),
            "url": investor.public_profile_url(),
            "avatar_url": investor.avatar_url(),
            "amount": investor.get_total_earned(),
        }

    # TODO(lucas): Review to improve performance
    # Warning: top_earned_investors absolutely will not scale, the view is meant
    # to be run occasionally (once a day) and then have the whole page cached
    def calculate_leaderboard(self):
        user_profiles = UserProfile.objects.filter(invest_anonymously=False)
        investments = Investment.objects.filter_user_investments(user=OuterRef("pk"))
        investors = user_profiles.annotate(has_invested=Exists(investments)).filter(
            has_invested=True
        )

        # Top earned investors
        top_earned_investors = [
            self.investor_context(investor) for investor in investors
        ]
        top_earned_investors = list(
            filter(lambda context: context["amount"] > 0, top_earned_investors)
        )
        top_earned_investors = sorted(
            top_earned_investors, key=lambda context: context["amount"], reverse=True
        )[:20]
        return top_earned_investors

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leaderboard = cache.get_or_set("leaderboard", self.calculate_leaderboard)
        context["top_earned_investors"] = leaderboard
        return context
