"""
:Created: 12 March 2016
:Author: Lucas Connors

"""

import math

from django.conf import settings
from django.db import models
from django.utils import timezone
from pinax.stripe.models import Charge

from campaign.managers import InvestmentManager


class Project(models.Model):

    artist = models.ForeignKey("artist.Artist", on_delete=models.CASCADE)
    reason = models.CharField(
        max_length=40,
        help_text="The reason why the artist is raising money, in a few words",
    )

    def __str__(self):
        return "{artist} project {reason}".format(
            artist=str(self.artist), reason=self.reason
        )

    def active(self):
        return (
            self.campaign_set.filter(start_datetime__lte=timezone.now())
            .exclude(end_datetime__lte=timezone.now())
            .exists()
        )

    def total_num_shares(self):
        total_num_shares = 0
        for campaign in self.campaign_set.all():
            total_num_shares += campaign.num_shares()
        return total_num_shares

    def total_fans_percentage(self):
        return self.campaign_set.all().aggregate(
            fans_percentage=models.Sum("fans_percentage")
        )["fans_percentage"]

    def total_artist_percentage(self):
        fans_percentage = self.total_fans_percentage()
        if fans_percentage:
            return 100 - fans_percentage

    def artist_percentage(self):
        percentage_breakdowns = (
            self.artistpercentagebreakdown_set.annotate(
                name=models.F("displays_publicly_as")
            )
            .values("name")
            .annotate(percentage=models.Sum("percentage"))
            .order_by("-percentage")
        )
        if not percentage_breakdowns:
            percentage_breakdowns = [
                {"name": self.artist.name, "percentage": self.total_artist_percentage()}
            ]
        return percentage_breakdowns

    def generated_revenue(self):
        return (
            self.revenuereport_set.all().aggregate(gr=models.Sum("amount"))["gr"] or 0
        )

    def generated_revenue_fans(self):
        return float(self.generated_revenue()) * (
            float(self.total_fans_percentage()) / 100
        )

    def project_investors(self, investors=None):
        investors = investors or {}
        for campaign in self.campaign_set.all():
            investors = campaign.campaign_investors(investors=investors)

        # Calculate percentage ownership for each investor (if project is active)
        if self.active():
            for investor_id, investor in investors.items():
                percentage = (
                    float(investor["num_shares"]) / self.total_num_shares()
                ) * self.total_fans_percentage()
                investors[investor_id]["percentage"] = percentage

        return investors


class Campaign(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        help_text="The amount of money the artist wishes to raise"
    )
    value_per_share = models.PositiveIntegerField(
        default=1,
        help_text="The value (in dollars) per share the artist wishes to sell",
    )
    start_datetime = models.DateTimeField(
        db_index=True,
        default=timezone.now,
        help_text="When the campaign will start accepting investors",
    )
    end_datetime = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        help_text="When the campaign ends and will no longer accept investors (no end date if blank)",
    )
    use_of_funds = models.TextField(
        null=True, blank=True, help_text="A description of how the funds will be used"
    )
    fans_percentage = models.PositiveSmallIntegerField(
        help_text="The percentage of revenue that goes back to the fans (a value from 0-100)"
    )

    @staticmethod
    def funded_rounding(n):
        if n < 99:
            return int(math.ceil(n))
        return int(math.floor(n))

    def __str__(self):
        return "{artist}: ${amount} {reason}".format(
            artist=str(self.project.artist),
            amount=self.amount,
            reason=self.project.reason,
        )

    def value_per_share_cents(self):
        return self.value_per_share * 100

    def total(self, num_shares):
        subtotal = num_shares * self.value_per_share
        total = (
            subtotal * (1 + settings.PERDIEM_PERCENTAGE + settings.STRIPE_PERCENTAGE)
            + settings.STRIPE_FLAT_FEE
        )
        return math.ceil(total * 100.0) / 100.0

    def num_shares(self):
        return self.amount / self.value_per_share

    def total_shares_purchased(self):
        return (
            self.investment_set.filter(
                charge__paid=True, charge__refunded=False
            ).aggregate(total_shares=models.Sum("num_shares"))["total_shares"]
            or 0
        )

    def num_shares_remaining(self):
        return self.num_shares() - self.total_shares_purchased()

    def default_num_shares(self):
        default_num = math.ceil(settings.DEFAULT_MIN_PURCHASE / self.value_per_share)
        return min(default_num, self.num_shares_remaining())

    def amount_raised(self):
        return self.total_shares_purchased() * self.value_per_share

    def percentage_funded(self):
        try:
            percentage = (float(self.amount_raised()) / self.amount) * 100
        except ZeroDivisionError:
            return 100
        return self.funded_rounding(percentage)

    def percentage_per_share(self):
        return float(self.fans_percentage) / float(self.num_shares())

    def percentage_roi(self, percentage):
        return self.amount * (percentage / self.fans_percentage)

    def valuation(self):
        return self.percentage_roi(100)

    def open(self):
        started = self.start_datetime is None or self.start_datetime < timezone.now()
        ended = self.end_datetime and self.end_datetime < timezone.now()
        return started and not ended and self.amount_raised() < self.amount

    def campaign_investors(self, investors=None):
        investors = investors or {}
        investments = self.investment_set.filter(
            charge__paid=True, charge__refunded=False
        ).select_related("charge", "charge__customer", "charge__customer__user")

        for investment in investments:
            investor = investment.investor()
            if investor.id not in investors:
                investors[investor.id] = {
                    "name": investor.userprofile.get_display_name(),
                    "avatar_url": investor.userprofile.display_avatar_url(),
                    "public_profile_url": investor.userprofile.public_profile_url(),
                    "num_shares": 0,
                    "total_investment": 0,
                }
            investors[investor.id]["num_shares"] += investment.num_shares
            investors[investor.id]["total_investment"] += (
                investment.num_shares * investment.campaign.value_per_share
            )

        return investors


class ArtistPercentageBreakdown(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    artist_admin = models.ForeignKey(
        "artist.ArtistAdmin", on_delete=models.SET_NULL, null=True, blank=True
    )
    displays_publicly_as = models.CharField(
        max_length=30, help_text="The name shown on the artist's detail page"
    )
    percentage = models.FloatField(
        help_text="The percentage of revenue that goes back to this group/individual (a value from 0-100)"
    )

    def __str__(self):
        return "{project}: {displays_publicly_as} - {percentage}%".format(
            project=str(self.project),
            displays_publicly_as=self.displays_publicly_as,
            percentage=self.percentage,
        )


class Expense(models.Model):

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    expense = models.CharField(
        max_length=30,
        help_text="A description of one of the expenses for the artist (eg. Studio cost)",
    )

    class Meta:
        unique_together = ("campaign", "expense")

    def __str__(self):
        return "{campaign} ({expense})".format(
            campaign=str(self.campaign), expense=self.expense
        )


class Investment(models.Model):

    charge = models.OneToOneField(Charge, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    transaction_datetime = models.DateTimeField(db_index=True, auto_now_add=True)
    num_shares = models.PositiveSmallIntegerField(
        default=1, help_text="The number of shares an investor made in a transaction"
    )

    objects = InvestmentManager()

    def __str__(self):
        return "{num_shares} shares in {campaign} to {investor}".format(
            num_shares=self.num_shares,
            campaign=str(self.campaign),
            investor=str(self.investor()),
        )

    def investor(self):
        return self.charge.customer.user

    def generated_revenue(self):
        relevant_revenue_reports = RevenueReport.objects.filter(
            project=self.campaign.project,
            reported_datetime__gt=self.transaction_datetime,
        )
        total_relevant_revenue = (
            relevant_revenue_reports.aggregate(total_revenue=models.Sum("amount"))[
                "total_revenue"
            ]
            or 0
        )

        percentage_ownership = float(self.num_shares) / self.campaign.num_shares()
        investor_ownership = percentage_ownership * (
            float(self.campaign.fans_percentage) / 100
        )
        return investor_ownership * float(total_relevant_revenue)


class RevenueReport(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        help_text="The amount of revenue generated (in dollars) being reported (since last report)",
    )
    reported_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "${amount} for {project}".format(
            amount=self.amount, project=str(self.project)
        )
