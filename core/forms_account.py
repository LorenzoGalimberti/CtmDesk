from django.contrib.auth.forms import PasswordChangeForm


class CambioPasswordForm(PasswordChangeForm):
    """Cambio password con etichette in italiano e stile Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        etichette = {
            'old_password': 'Password attuale',
            'new_password1': 'Nuova password',
            'new_password2': 'Conferma nuova password',
        }
        for nome, etichetta in etichette.items():
            self.fields[nome].label = etichetta
            self.fields[nome].widget.attrs.update({'class': 'form-control'})
