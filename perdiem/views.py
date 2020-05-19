"""
:Created: 11 May 2016
:Author: Lucas Connors

"""

from django.core.exceptions import ImproperlyConfigured
from django.forms import formset_factory
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.views.generic import TemplateView


class Http405(Exception):
    pass


class FormsetView(TemplateView):
    def get_success_url(self):
        try:
            return self.success_url
        except AttributeError:
            raise ImproperlyConfigured(
                "FormsetView requires either a definition of 'success_url' or implementation of 'get_success_url()'"
            )

    def get_form_class(self):
        try:
            return self.form_class
        except AttributeError:
            raise ImproperlyConfigured(
                "FormsetView requires either a definition of 'form_class' or implementation of 'get_form_class()'"
            )

    def get_formset_factory_kwargs(self):
        return {}

    def get_initial(self):
        return []

    def get_context_data(self, **kwargs):
        view_formset = formset_factory(
            self.get_form_class(), **self.get_formset_factory_kwargs()
        )

        if self.request.method == "GET":
            formset = view_formset(initial=self.get_initial())
        elif self.request.method == "POST":
            formset = view_formset(self.request.POST, initial=self.get_initial())
        else:
            raise Http405

        context = {"formset": formset}
        return context

    def formset_valid(self, formset):
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http405:
            return HttpResponseNotAllowed(["GET", "POST"])

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        formset = context["formset"]
        if formset.is_valid():
            return self.formset_valid(formset)

        return self.render_to_response(context)


class ConstituentFormView:

    provide_user = False
    includes_files = False

    def __init__(self, request):
        self.request = request

    def get_initial(self):
        return {}

    def form_valid(self):
        pass


class MultipleFormView(TemplateView):

    constituent_form_views = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["forms_with_errors"] = []
        for form_name, form_view_class in self.constituent_form_views.items():
            form_view = form_view_class(self.request)
            form_context_name = f"{form_name}_form"
            if form_context_name not in context:
                form_args = []
                form_kwargs = {"initial": form_view.get_initial()}
                if form_view.provide_user:
                    form_args.append(self.request.user)
                context[form_context_name] = form_view.form_class(
                    *form_args, **form_kwargs
                )
            elif context[form_context_name].errors:
                context["forms_with_errors"].append(form_name)

        return context

    def post(self, request, *args, **kwargs):
        try:
            form_name = request.POST["action"]
            form_view_class = self.constituent_form_views[form_name]
        except KeyError:
            return HttpResponseBadRequest("Form action unrecognized or unspecified.")

        form_view = form_view_class(request)
        form_args = [request.POST]
        if form_view.provide_user:
            form_args = [request.user] + form_args
        if form_view.includes_files:
            form_args.append(request.FILES)
        form = form_view.form_class(*form_args)
        if form.is_valid():
            form_view.form_valid(form)
        else:
            form_context_name = f"{form_name}_form"
            kwargs.update({form_context_name: form})
        return self.render_to_response(self.get_context_data(**kwargs))
