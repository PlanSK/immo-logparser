from typing import Any

from django.views.generic import TemplateView

from dzllogparser.services.ftp import get_ftp_data

class IndexView(TemplateView):
    template_name = 'dzllogparser/index.html'
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        get_ftp_data()
        return context
