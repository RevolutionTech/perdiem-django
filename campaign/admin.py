"""
:Created: 12 March 2016
:Author: Lucas Connors

"""

from django import forms
from django.contrib import admin
from pinax.stripe.models import (
    Account,
    BankAccount,
    Charge,
    Coupon,
    Customer,
    Event,
    EventProcessingException,
    Invoice,
    Plan,
    UserAccount,
)

from artist.models import ArtistAdmin
from campaign.models import (
    ArtistPercentageBreakdown,
    Campaign,
    Expense,
    Investment,
    Project,
    RevenueReport,
)

# Unregister Pinax Stripe models from admin
for pinax_stripe_model in [
    Account,
    BankAccount,
    Charge,
    Coupon,
    Customer,
    Event,
    EventProcessingException,
    Invoice,
    Plan,
    UserAccount,
]:
    admin.site.unregister(pinax_stripe_model)


class CampaignAdminForm(forms.ModelForm):

    fans_percentage = forms.IntegerField(
        min_value=0,
        max_value=100,
        help_text=Campaign._meta.get_field("fans_percentage").help_text,
    )

    class Meta:
        model = Campaign
        fields = (
            "project",
            "amount",
            "value_per_share",
            "start_datetime",
            "end_datetime",
            "use_of_funds",
            "fans_percentage",
        )

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime < start_datetime:
            raise forms.ValidationError("Campaign cannot end before it begins.")
        return cleaned_data


class ArtistPercentageBreakdownFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_artist_percentage = self.instance.total_artist_percentage()
        artist_percentage_so_far = 0
        num_forms = 0

        # Verify that the artist percentage adds up
        for form in self.forms:
            if "percentage" in form.cleaned_data and not form.cleaned_data["DELETE"]:
                num_forms += 1
                percentage = form.cleaned_data["percentage"]
                if percentage < 0 or percentage > 100:
                    raise forms.ValidationError("Percentages must be between 0-100.")
                artist_percentage_so_far += percentage

        if num_forms > 0 and artist_percentage_so_far != total_artist_percentage:
            raise forms.ValidationError(
                "Percentage breakdown does add up to total artist percentage of {total_artist_percentage}%.".format(
                    total_artist_percentage=total_artist_percentage
                )
            )


class ArtistPercentageBreakdownInline(admin.StackedInline):

    model = ArtistPercentageBreakdown
    extra = 1
    formset = ArtistPercentageBreakdownFormset

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Limit ArtistAdmins to the ArtistAdmins for the artist in this campaign
        formset.form.base_fields["artist_admin"].queryset = ArtistAdmin.objects.filter(
            artist=obj.artist
        )
        return formset


class ExpenseInline(admin.TabularInline):

    model = Expense


class ProjectAdmin(admin.ModelAdmin):
    def get_inline_instances(self, request, obj=None, **kwargs):
        inline_instances = []

        # Only show ArtistPercentageBreakdownInline in edit view
        # when the project has campaigns
        if obj and obj.campaign_set.exists():
            inline_instances.append(
                ArtistPercentageBreakdownInline(self.model, self.admin_site)
            )

        for inline in self.inlines:
            inline_instances.append(inline(self.model, self.admin_site))
        return inline_instances


class CampaignAdmin(admin.ModelAdmin):

    form = CampaignAdminForm
    raw_id_fields = ("project",)
    inlines = (ExpenseInline,)


class InvestmentAdmin(admin.ModelAdmin):

    list_display = ("id", "campaign", "investor", "transaction_datetime", "num_shares")
    readonly_fields = list(map(lambda f: f.name, Investment._meta.get_fields()))

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Project, ProjectAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(RevenueReport)
