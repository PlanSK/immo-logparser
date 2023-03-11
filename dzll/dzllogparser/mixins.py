class TitleMixin(object):
    title = None

    def get_title(self):
        return self.title

    def get_context_data(self, **kwargs):
        context= super(TitleMixin, self).get_context_data(**kwargs)
        context.update({
            'title': self.get_title()
        })
        return context