import re

from coalsense_common.i18n_es import es

# Un UTF-8 leído como cp1252/latin-1 deja "Ã³", "Â" o "â€" en lugar de la letra acentuada.
MOJIBAKE = re.compile("[ÃÂ]|â€|�")


def test_catalog_values_are_not_mojibake() -> None:
    broken = [key for key, value in es.items() if MOJIBAKE.search(value)]
    assert broken == []


def test_accented_auth_messages_are_real_utf8() -> None:
    assert es["auth.code.invalid.message"] == "Ese código no coincide."
    assert es["auth.next.checkCode"] == "Revisa el código e inténtalo de nuevo."
    assert es["auth.tls.required.message"] == "Esta conexión no es segura."
