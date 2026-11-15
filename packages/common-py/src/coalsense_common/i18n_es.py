"""Spec 00 base copy for message_es; kept in sync with the UI catalog by audit_copy."""

es: dict[str, str] = {
    "stop.label": "Alto",
    "undo.label": "Deshacer",
    "approval.approve.label": "Aprobar",
    "approval.reject.label": "Rechazar",
    "approval.defer.label": "Decidir después",
    "state.loading.label": "Cargando",
    "state.loading.message": "Se está cargando la información.",
    "state.empty.label": "Vacío",
    "state.empty.message": "No hay información para mostrar.",
    "state.error.label": "Error",
    "state.error.message": "No se pudo completar la acción.",
    "state.offline.label": "Sin conexión",
    "state.offline.message": "No hay conexión.",
    "state.calibrationFailed.label": "Calibración fallida",
    "state.calibrationFailed.message": "El equipo no pudo completar la calibración.",
    "state.modalityNotDetected.label": "Modalidad no detectada",
    "state.modalityNotDetected.message": "El equipo no detectó la modalidad de entrada.",
}
