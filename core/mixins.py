class SoloMieiMixin:
    """Per le viste di dettaglio/modifica/eliminazione: l'utente raggiunge
    solo gli oggetti di cui è proprietario. Gli altri danno 404."""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)
