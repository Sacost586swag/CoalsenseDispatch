"""Autenticación sin contraseña (T-00-010): código por correo y emparejamiento de dispositivo.

Puntos de extensión que llegan después (el orquestador no llama APIs directo, V-08):
- `CodeSender`: el envío real de correo entra por el gateway en H2; aquí solo la interfaz.
- `AuthRepository`: PostgreSQL llega con P-03/T-02-002; `migrations/0001_auth.sql` ya define
  el esquema y hoy hay una implementación en memoria.
- `EmailVault`: cifrado del correo (`email_ciphertext`), según la spec 07.
- `current_account` de `routes.create_app`: la sesión y la credencial del dispositivo son T-00-011.
"""
