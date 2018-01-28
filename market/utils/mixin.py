from django.views.generic import View
from django.contrib.auth.decorators import login_required

class LoginRequiredView(View):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredView, cls).as_view()

        return login_required(view)


class LoginRequiredMixin(object):
    @classmethod

    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view()

        return login_required(view)