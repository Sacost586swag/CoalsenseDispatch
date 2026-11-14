# Trazabilidad: requisito → tarea → prueba

Generado a partir de los `requirements.md` y `tasks.md` de cada spec. La auditoría `tools/audit/audit_traceability.py` (tarea T-00-006) lo regenera y falla si un requisito queda sin tarea o sin prueba. La spec 08 es de la fase 2 y no tiene tareas del MVP.

## Resumen

| Spec | Requisitos | Con tarea | Tareas |
| --- | --- | --- | --- |
| 00-fundaciones | 34 | 34 | 17 |
| 01-capa-de-entrada | 157 | 157 | 57 |
| 02-orquestador-y-agentes | 65 | 65 | 28 |
| 03-ciclo-de-control | 45 | 45 | 17 |
| 04-espacio-de-trabajo | 39 | 39 | 16 |
| 05-seguridad-y-bienestar | 38 | 38 | 13 |
| 06-cuidador-y-perfiles | 33 | 33 | 12 |
| 07-privacidad-y-datos | 41 | 41 | 15 |
| 08-mercado-b2b (fase 2) | 30 | 0 | 0 |
| 09-despliegue | 36 | 36 | 15 |
| **Total** | **518** | **488** | **190** |

Requisitos del MVP sin tarea: **0**. Tareas sin prueba: **0**.

## 00-fundaciones

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-00-001 | integration | T-00-001 | `tools/audit/tests/test_clean_checkout.py` |
| REQ-00-002 | integration | T-00-002 | `tools/audit/tests/test_ci_config.py` |
| REQ-00-003 | audit | T-00-004, T-00-005 | `tools/audit/tests/test_audit_imports.py`<br>`tools/audit/tests/test_audit_secrets.py` |
| REQ-00-004 | audit | T-00-003 | `tools/audit/tests/test_audit_licenses.py` |
| REQ-00-005 | audit | T-00-006 | `tools/audit/tests/test_audit_traceability.py` |
| REQ-00-006 | audit | T-00-001 | `tools/audit/tests/test_clean_checkout.py` |
| REQ-00-007 | unit | T-00-007 | `packages/common-py/tests/test_config_errors_ids.py`<br>`packages/common-ts/tests/common.test.ts` |
| REQ-00-008 | audit | T-00-005 | `tools/audit/tests/test_audit_secrets.py` |
| REQ-00-009 | unit, manual | T-00-007 | `packages/common-py/tests/test_config_errors_ids.py`<br>`packages/common-ts/tests/common.test.ts` |
| REQ-00-010 | security | T-00-008 | `packages/common-py/tests/test_logging_scrub.py` |
| REQ-00-011 | audit | T-00-009 | `tools/audit/tests/test_audit_copy.py` |
| REQ-00-012 | unit | T-00-007 | `packages/common-py/tests/test_config_errors_ids.py`<br>`packages/common-ts/tests/common.test.ts` |
| REQ-00-020 | e2e, a11y | T-00-010, T-00-012 | `apps/orchestrator/tests/auth/test_codes_pairing.py`<br>`apps/web/tests/e2e/auth.spec.ts` |
| REQ-00-021 | e2e | T-00-010, T-00-012 | `apps/orchestrator/tests/auth/test_codes_pairing.py`<br>`apps/web/tests/e2e/auth.spec.ts` |
| REQ-00-022 | integration | T-00-011 | `apps/orchestrator/tests/auth/test_sessions_roles.py` |
| REQ-00-023 | e2e | T-00-011 | `apps/orchestrator/tests/auth/test_sessions_roles.py` |
| REQ-00-024 | security | T-00-011 | `apps/orchestrator/tests/auth/test_sessions_roles.py` |
| REQ-00-025 | security | T-00-010 | `apps/orchestrator/tests/auth/test_codes_pairing.py` |
| REQ-00-026 | security | T-00-010 | `apps/orchestrator/tests/auth/test_codes_pairing.py` |
| REQ-00-027 | integration | T-00-010 | `apps/orchestrator/tests/auth/test_codes_pairing.py` |
| REQ-00-040 | unit | T-00-013 | `packages/ui/tests/tokens.test.ts` |
| REQ-00-041 | a11y | T-00-014 | `packages/ui/tests/components.test.tsx` |
| REQ-00-042 | a11y | T-00-014 | `packages/ui/tests/components.test.tsx` |
| REQ-00-043 | a11y | T-00-014 | `packages/ui/tests/components.test.tsx` |
| REQ-00-044 | a11y | T-00-015 | `packages/ui/tests/state-approval-stopbar.test.tsx` |
| REQ-00-045 | a11y | T-00-013 | `packages/ui/tests/tokens.test.ts` |
| REQ-00-046 | a11y | T-00-015 | `packages/ui/tests/state-approval-stopbar.test.tsx` |
| REQ-00-047 | integration | T-00-016 | `packages/ui/tests/nav-registry.test.tsx` |
| REQ-00-048 | a11y | T-00-014 | `packages/ui/tests/components.test.tsx` |
| REQ-00-049 | a11y | T-00-017 | `packages/ui/tests/a11y-ci.test.ts` |
| REQ-00-050 | a11y | T-00-015 | `packages/ui/tests/state-approval-stopbar.test.tsx` |
| REQ-00-060 | a11y | T-00-013 | `packages/ui/tests/tokens.test.ts` |
| REQ-00-061 | perf | T-00-002 | `tools/audit/tests/test_ci_config.py` |
| REQ-00-062 | integration | T-00-017 | `packages/ui/tests/a11y-ci.test.ts` |

## 01-capa-de-entrada

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-01-001 | contract | T-01-001 | `packages/intents/tests/test_schema.py` |
| REQ-01-002 | contract | T-01-002 | `tools/audit/tests/test_schema_drift.py` |
| REQ-01-003 | unit | T-01-001 | `packages/intents/tests/test_schema.py` |
| REQ-01-004 | unit | T-01-003 | `apps/companion/tests/bus/test_core.py`<br>`test_dummy_adapter.py` |
| REQ-01-005 | unit | T-01-003 | `apps/companion/tests/bus/test_core.py`<br>`test_dummy_adapter.py` |
| REQ-01-006 | unit | T-01-003 | `apps/companion/tests/bus/test_core.py`<br>`test_dummy_adapter.py` |
| REQ-01-007 | security | T-01-004 | `apps/companion/tests/bus/test_auth.py` |
| REQ-01-008 | security | T-01-004 | `apps/companion/tests/bus/test_auth.py` |
| REQ-01-009 | contract | T-01-004 | `apps/companion/tests/bus/test_auth.py` |
| REQ-01-010 | contract | T-01-001, T-01-005 | `packages/intents/tests/test_schema.py`<br>`apps/companion/tests/bus/test_approval_guard.py` |
| REQ-01-011 | replay | T-01-005 | `apps/companion/tests/bus/test_approval_guard.py` |
| REQ-01-012 | security | T-01-004 | `apps/companion/tests/bus/test_auth.py` |
| REQ-01-013 | integration | T-01-006 | `apps/companion/tests/bus/test_audit_log.py` |
| REQ-01-014 | contract | T-01-003 | `apps/companion/tests/bus/test_core.py`<br>`test_dummy_adapter.py` |
| REQ-01-015 | replay | T-01-007 | `apps/companion/tests/replay/test_harness.py`<br>`test_audit_fixtures.py` |
| REQ-01-016 | unit | T-01-013 | `apps/companion/tests/profile/test_validate.py` |
| REQ-01-017 | unit | T-01-013 | `apps/companion/tests/profile/test_validate.py` |
| REQ-01-018 | integration | T-01-009 | `apps/companion/tests/bus/test_stop_guard.py` |
| REQ-01-019 | integration | T-01-009 | `apps/companion/tests/bus/test_stop_guard.py` |
| REQ-01-020 | replay | T-01-009 | `apps/companion/tests/bus/test_stop_guard.py` |
| REQ-01-021 | replay | T-01-021 | `apps/companion/tests/adapters/voice/test_control_words.py` |
| REQ-01-022 | unit | T-01-010 | `apps/companion/tests/actuator/test_undo.py` |
| REQ-01-023 | unit | T-01-010 | `apps/companion/tests/actuator/test_undo.py` |
| REQ-01-024 | unit | T-01-010 | `apps/companion/tests/actuator/test_undo.py` |
| REQ-01-025 | integration | T-01-012 | `apps/companion/tests/bus/test_help_route.py` |
| REQ-01-026 | integration | T-01-011 | `apps/companion/tests/bus/test_stop_state.py` |
| REQ-01-027 | security | T-01-020 | `apps/companion/tests/adapters/voice/test_modes.py` |
| REQ-01-028 | unit | T-01-018 | `apps/companion/tests/commands/test_loader.py` |
| REQ-01-029 | unit | T-01-018 | `apps/companion/tests/commands/test_loader.py` |
| REQ-01-030 | unit | T-01-019 | `apps/companion/tests/commands/test_base_coverage.py` |
| REQ-01-031 | replay | T-01-022 | `apps/companion/tests/adapters/voice/test_ambiguity.py` |
| REQ-01-032 | e2e | T-01-025 | `apps/web/tests/e2e/voice-help.spec.ts` |
| REQ-01-033 | replay | T-01-020 | `apps/companion/tests/adapters/voice/test_modes.py` |
| REQ-01-034 | e2e | T-01-025 | `apps/web/tests/e2e/voice-help.spec.ts` |
| REQ-01-035 | audit | T-01-019 | `apps/companion/tests/commands/test_base_coverage.py` |
| REQ-01-036 | unit | T-01-057 | `apps/companion/tests/commands/test_custom.py` |
| REQ-01-037 | replay | T-01-019 | `apps/companion/tests/commands/test_base_coverage.py` |
| REQ-01-038 | replay | T-01-023 | `apps/companion/tests/adapters/voice/test_dictation.py` |
| REQ-01-039 | replay | T-01-023 | `apps/companion/tests/adapters/voice/test_dictation.py` |
| REQ-01-040 | unit | T-01-023 | `apps/companion/tests/adapters/voice/test_dictation.py` |
| REQ-01-041 | integration | T-01-024 | `apps/companion/tests/adapters/voice/test_insert.py` |
| REQ-01-042 | security | T-01-023 | `apps/companion/tests/adapters/voice/test_dictation.py` |
| REQ-01-043 | integration | T-01-024 | `apps/companion/tests/adapters/voice/test_insert.py` |
| REQ-01-044 | security | T-01-027 | `apps/companion/tests/adapters/head_gesture/test_pipeline.py` |
| REQ-01-045 | replay | T-01-028 | `apps/companion/tests/adapters/head_gesture/test_pointer.py` |
| REQ-01-046 | replay | T-01-028 | `apps/companion/tests/adapters/head_gesture/test_pointer.py` |
| REQ-01-047 | replay | T-01-029 | `apps/companion/tests/adapters/head_gesture/test_gestures.py` |
| REQ-01-048 | unit | T-01-029 | `apps/companion/tests/adapters/head_gesture/test_gestures.py` |
| REQ-01-049 | unit | T-01-029 | `apps/companion/tests/adapters/head_gesture/test_gestures.py` |
| REQ-01-050 | replay | T-01-030 | `apps/companion/tests/adapters/head_gesture/test_presence.py` |
| REQ-01-051 | replay | T-01-030 | `apps/companion/tests/adapters/head_gesture/test_presence.py` |
| REQ-01-052 | replay | T-01-028 | `apps/companion/tests/adapters/head_gesture/test_pointer.py` |
| REQ-01-053 | replay | T-01-030 | `apps/companion/tests/adapters/head_gesture/test_presence.py` |
| REQ-01-054 | replay | T-01-030 | `apps/companion/tests/adapters/head_gesture/test_presence.py` |
| REQ-01-055 | e2e, security | T-01-031 | `apps/web/tests/e2e/vision-web.spec.ts` |
| REQ-01-056 | unit | T-01-032 | `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` |
| REQ-01-057 | unit | T-01-032 | `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` |
| REQ-01-058 | integration | T-01-032 | `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` |
| REQ-01-059 | security | T-01-032 | `apps/companion/tests/adapters/keyboard_mouse/test_adapter.py` |
| REQ-01-060 | integration | T-01-033 | `apps/companion/tests/actuator/test_actuator.py` |
| REQ-01-061 | e2e | T-01-034 | `apps/companion/tests/actuator/test_numbers.py` |
| REQ-01-062 | e2e | T-01-035 | `apps/companion/tests/actuator/test_grid_snapping.py` |
| REQ-01-063 | unit | T-01-035 | `apps/companion/tests/actuator/test_grid_snapping.py` |
| REQ-01-064 | e2e | T-01-035 | `apps/companion/tests/actuator/test_grid_snapping.py` |
| REQ-01-065 | integration | T-01-033 | `apps/companion/tests/actuator/test_actuator.py` |
| REQ-01-066 | e2e | T-01-036 | `apps/companion/tests/feedback/test_feedback.py` |
| REQ-01-067 | security | T-01-033 | `apps/companion/tests/actuator/test_actuator.py` |
| REQ-01-068 | e2e | T-01-033 | `apps/companion/tests/actuator/test_actuator.py` |
| REQ-01-069 | integration | T-01-037 | `apps/companion/tests/calibration/test_devices.py` |
| REQ-01-070 | e2e | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-071 | e2e | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-072 | replay | T-01-038 | `apps/companion/tests/calibration/test_thresholds.py` |
| REQ-01-073 | replay | T-01-039 | `apps/companion/tests/calibration/test_head_voice.py` |
| REQ-01-074 | replay | T-01-039 | `apps/companion/tests/calibration/test_head_voice.py` |
| REQ-01-075 | replay | T-01-038 | `apps/companion/tests/calibration/test_thresholds.py` |
| REQ-01-076 | e2e | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-077 | e2e | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-078 | unit, manual | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-079 | integration | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-080 | e2e | T-01-041 | `apps/companion/tests/calibration/test_drift.py` |
| REQ-01-081 | replay | T-01-041 | `apps/companion/tests/calibration/test_drift.py` |
| REQ-01-082 | security | T-01-038 | `apps/companion/tests/calibration/test_thresholds.py` |
| REQ-01-083 | contract | T-01-001, T-01-013 | `packages/intents/tests/test_schema.py`<br>`apps/companion/tests/profile/test_validate.py` |
| REQ-01-084 | unit | T-01-013 | `apps/companion/tests/profile/test_validate.py` |
| REQ-01-085 | security | T-01-014 | `apps/companion/tests/profile/test_store.py` |
| REQ-01-086 | security | T-01-016 | `apps/companion/tests/profile/test_proposals_egress.py` |
| REQ-01-087 | e2e | T-01-015 | `apps/companion/tests/profile/test_multi_export_erase.py` |
| REQ-01-088 | e2e | T-01-015 | `apps/companion/tests/profile/test_multi_export_erase.py` |
| REQ-01-089 | integration | T-01-016 | `apps/companion/tests/profile/test_proposals_egress.py` |
| REQ-01-090 | unit | T-01-016 | `apps/companion/tests/profile/test_proposals_egress.py` |
| REQ-01-091 | unit | T-01-014 | `apps/companion/tests/profile/test_store.py` |
| REQ-01-092 | e2e | T-01-017 | `apps/web/tests/e2e/profile-view.spec.ts` |
| REQ-01-093 | e2e | T-01-042 | `apps/companion/tests/privacy/test_indicators.py` |
| REQ-01-094 | integration | T-01-042 | `apps/companion/tests/privacy/test_indicators.py` |
| REQ-01-095 | security | T-01-043 | `apps/companion/tests/privacy/test_egress.py` |
| REQ-01-096 | e2e | T-01-026 | `apps/companion/tests/cloud/test_stt_cloud.py` |
| REQ-01-097 | security | T-01-043 | `apps/companion/tests/privacy/test_egress.py` |
| REQ-01-098 | audit | T-01-044 | `tools/audit/tests/test_audit_no_biometrics.py` |
| REQ-01-099 | e2e | T-01-037 | `apps/companion/tests/calibration/test_devices.py` |
| REQ-01-100 | audit | T-01-007, T-01-008 | `apps/companion/tests/replay/test_harness.py`<br>`test_audit_fixtures.py`<br>`apps/companion/tests/fixtures/test_fixtures_valid.py` |
| REQ-01-101 | replay | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-102 | e2e | T-01-051 | `apps/web/tests/e2e/gaze-dwell.spec.ts` |
| REQ-01-103 | unit | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-104 | replay | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-105 | replay | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-106 | replay | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-107 | audit | T-01-044, T-01-051 | `tools/audit/tests/test_audit_no_biometrics.py`<br>`apps/web/tests/e2e/gaze-dwell.spec.ts` |
| REQ-01-108 | contract | T-01-050 | `apps/companion/tests/adapters/gaze/test_dwell.py` |
| REQ-01-109 | unit | T-01-052 | `apps/companion/tests/adapters/switch_scan/test_scanner.py` |
| REQ-01-110 | e2e | T-01-053 | `apps/web/tests/e2e/scan.spec.ts` |
| REQ-01-111 | unit | T-01-052 | `apps/companion/tests/adapters/switch_scan/test_scanner.py` |
| REQ-01-112 | e2e | T-01-053 | `apps/web/tests/e2e/scan.spec.ts` |
| REQ-01-113 | a11y | T-01-053 | `apps/web/tests/e2e/scan.spec.ts` |
| REQ-01-114 | unit | T-01-052 | `apps/companion/tests/adapters/switch_scan/test_scanner.py` |
| REQ-01-115 | unit | T-01-052 | `apps/companion/tests/adapters/switch_scan/test_scanner.py` |
| REQ-01-116 | integration | T-01-052 | `apps/companion/tests/adapters/switch_scan/test_scanner.py` |
| REQ-01-117 | a11y | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-118 | a11y | T-01-046 | `apps/web/tests/e2e/stop-undo-bar.spec.ts` |
| REQ-01-119 | e2e | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-120 | e2e | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-121 | e2e | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-122 | e2e | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-123 | e2e | T-01-040 | `apps/web/tests/e2e/calibration.spec.ts` |
| REQ-01-124 | e2e | T-01-045 | `apps/web/tests/e2e/modalities-states.spec.ts` |
| REQ-01-125 | a11y | T-01-036 | `apps/companion/tests/feedback/test_feedback.py` |
| REQ-01-126 | integration | T-01-054 | `apps/companion/tests/integration/test_resilience_offline.py` |
| REQ-01-127 | integration | T-01-054 | `apps/companion/tests/integration/test_resilience_offline.py` |
| REQ-01-128 | integration | T-01-011 | `apps/companion/tests/bus/test_stop_state.py` |
| REQ-01-129 | integration | T-01-011 | `apps/companion/tests/bus/test_stop_state.py` |
| REQ-01-130 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-131 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-132 | e2e | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-133 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-134 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-135 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-136 | a11y | T-01-048 | `apps/web/tests/a11y/input-layer.spec.ts` |
| REQ-01-137 | perf | T-01-028, T-01-047 | `apps/companion/tests/adapters/head_gesture/test_pointer.py`<br>`apps/companion/tests/perf/test_budgets.py` |
| REQ-01-138 | perf | T-01-029, T-01-047 | `apps/companion/tests/adapters/head_gesture/test_gestures.py`<br>`apps/companion/tests/perf/test_budgets.py` |
| REQ-01-139 | perf | T-01-022, T-01-047 | `apps/companion/tests/adapters/voice/test_ambiguity.py`<br>`apps/companion/tests/perf/test_budgets.py` |
| REQ-01-140 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-141 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-142 | perf | T-01-021, T-01-047 | `apps/companion/tests/adapters/voice/test_control_words.py`<br>`apps/companion/tests/perf/test_budgets.py` |
| REQ-01-143 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-144 | perf | T-01-003, T-01-047 | `apps/companion/tests/bus/test_core.py`<br>`test_dummy_adapter.py`<br>`apps/companion/tests/perf/test_budgets.py` |
| REQ-01-145 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-146 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-147 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-148 | perf | T-01-047 | `apps/companion/tests/perf/test_budgets.py` |
| REQ-01-149 | audit | T-01-055 | `tools/audit/tests/test_audit_data_inventory.py` |
| REQ-01-150 | security | T-01-056 | `apps/companion/tests/uplink/test_tls.py` |
| REQ-01-151 | audit | T-01-044 | `tools/audit/tests/test_audit_no_biometrics.py` |
| REQ-01-152 | e2e | T-01-015 | `apps/companion/tests/profile/test_multi_export_erase.py` |
| REQ-01-153 | replay | T-01-008, T-01-049 | `apps/companion/tests/fixtures/test_fixtures_valid.py`<br>`apps/companion/tests/reliability/test_rest_stress.py` |
| REQ-01-154 | replay | T-01-021, T-01-049 | `apps/companion/tests/adapters/voice/test_control_words.py`<br>`apps/companion/tests/reliability/test_rest_stress.py` |
| REQ-01-155 | replay | T-01-005, T-01-049 | `apps/companion/tests/bus/test_approval_guard.py`<br>`apps/companion/tests/reliability/test_rest_stress.py` |
| REQ-01-156 | replay | T-01-039 | `apps/companion/tests/calibration/test_head_voice.py` |
| REQ-01-157 | replay | T-01-028 | `apps/companion/tests/adapters/head_gesture/test_pointer.py` |

## 02-orquestador-y-agentes

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-02-001 | integration | T-02-015 | `apps/orchestrator/tests/agents/test_planner.py` |
| REQ-02-002 | unit | T-02-015 | `apps/orchestrator/tests/agents/test_planner.py` |
| REQ-02-003 | unit | T-02-009 | `apps/orchestrator/tests/agents/test_router.py` |
| REQ-02-004 | integration | T-02-009 | `apps/orchestrator/tests/agents/test_router.py` |
| REQ-02-005 | security | T-02-008 | `apps/orchestrator/tests/agents/test_prompt_builder.py` |
| REQ-02-006 | security | T-02-008 | `apps/orchestrator/tests/agents/test_prompt_builder.py` |
| REQ-02-007 | unit | T-02-009 | `apps/orchestrator/tests/agents/test_router.py` |
| REQ-02-008 | audit | T-02-017 | `tools/audit/tests/test_gateway_boundaries.py` |
| REQ-02-010 | unit | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-011 | unit | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-012 | security, audit | T-02-002 | `apps/orchestrator/tests/persistence/test_rls.py` |
| REQ-02-013 | integration | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-014 | integration | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-015 | integration | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-016 | unit | T-02-016 | `apps/orchestrator/tests/agents/test_agents.py` |
| REQ-02-020 | audit | T-02-007, T-02-017 | `apps/orchestrator/tests/gateway/test_executor.py`<br>`tools/audit/tests/test_gateway_boundaries.py` |
| REQ-02-021 | contract | T-02-006 | `apps/orchestrator/tests/gateway/test_manifest.py` |
| REQ-02-022 | unit | T-02-006 | `apps/orchestrator/tests/gateway/test_manifest.py` |
| REQ-02-023 | security | T-02-007 | `apps/orchestrator/tests/gateway/test_executor.py` |
| REQ-02-024 | integration | T-02-007 | `apps/orchestrator/tests/gateway/test_executor.py` |
| REQ-02-025 | audit | T-02-021 | `apps/orchestrator/tests/gateway/test_n8n.py` |
| REQ-02-026 | e2e | T-02-022 | `apps/orchestrator/tests/gateway/test_mcp_enablement.py` |
| REQ-02-027 | unit | T-02-022 | `apps/orchestrator/tests/gateway/test_mcp_enablement.py` |
| REQ-02-028 | security | T-02-023 | `apps/orchestrator/tests/gateway/test_mcp_security.py` |
| REQ-02-029 | security | T-02-023 | `apps/orchestrator/tests/gateway/test_mcp_security.py` |
| REQ-02-030 | audit | T-02-022 | `apps/orchestrator/tests/gateway/test_mcp_enablement.py` |
| REQ-02-031 | e2e | T-02-022 | `apps/orchestrator/tests/gateway/test_mcp_enablement.py` |
| REQ-02-032 | integration | T-02-007 | `apps/orchestrator/tests/gateway/test_executor.py` |
| REQ-02-040 | unit | T-02-010 | `apps/orchestrator/tests/policy/test_engine.py` |
| REQ-02-041 | unit | T-02-010 | `apps/orchestrator/tests/policy/test_engine.py` |
| REQ-02-042 | unit | T-02-011 | `apps/orchestrator/tests/policy/test_grant.py` |
| REQ-02-043 | unit | T-02-011 | `apps/orchestrator/tests/policy/test_grant.py` |
| REQ-02-044 | unit | T-02-011 | `apps/orchestrator/tests/policy/test_grant.py` |
| REQ-02-045 | security | T-02-012 | `apps/orchestrator/tests/policy/test_origin.py` |
| REQ-02-046 | security | T-02-012 | `apps/orchestrator/tests/policy/test_origin.py` |
| REQ-02-047 | unit | T-02-013 | `apps/orchestrator/tests/policy/test_autonomy.py` |
| REQ-02-048 | unit | T-02-013 | `apps/orchestrator/tests/policy/test_autonomy.py` |
| REQ-02-049 | security | T-02-010 | `apps/orchestrator/tests/policy/test_engine.py` |
| REQ-02-050 | integration | T-02-014 | `apps/orchestrator/tests/policy/test_hold.py` |
| REQ-02-051 | integration | T-02-020 | `apps/orchestrator/tests/policy/test_stop_gate.py` |
| REQ-02-052 | integration | T-02-010 | `apps/orchestrator/tests/policy/test_engine.py` |
| REQ-02-053 | security | T-02-003 | `apps/orchestrator/tests/audit/test_chain.py` |
| REQ-02-060 | integration | T-02-018 | `apps/orchestrator/tests/agents/test_halt.py` |
| REQ-02-061 | perf | T-02-018 | `apps/orchestrator/tests/agents/test_halt.py` |
| REQ-02-062 | unit | T-02-019 | `apps/orchestrator/tests/gateway/test_undo.py` |
| REQ-02-063 | integration | T-02-018 | `apps/orchestrator/tests/agents/test_halt.py` |
| REQ-02-064 | unit | T-02-019 | `apps/orchestrator/tests/gateway/test_undo.py` |
| REQ-02-070 | e2e | T-02-025 | `apps/orchestrator/tests/memory/test_memory.py` |
| REQ-02-071 | security | T-02-025 | `apps/orchestrator/tests/memory/test_memory.py` |
| REQ-02-072 | security | T-02-002 | `apps/orchestrator/tests/persistence/test_rls.py` |
| REQ-02-073 | security | T-02-025 | `apps/orchestrator/tests/memory/test_memory.py` |
| REQ-02-080 | unit | T-02-003 | `apps/orchestrator/tests/audit/test_chain.py` |
| REQ-02-081 | e2e | T-02-005 | `apps/web/tests/e2e/audit-log.spec.ts` |
| REQ-02-082 | security | T-02-004 | `apps/orchestrator/tests/audit/test_merge_read.py` |
| REQ-02-083 | security | T-02-004 | `apps/orchestrator/tests/audit/test_merge_read.py` |
| REQ-02-084 | integration | T-02-004 | `apps/orchestrator/tests/audit/test_merge_read.py` |
| REQ-02-090 | e2e | T-02-026 | `apps/orchestrator/tests/api/test_degraded.py` |
| REQ-02-091 | contract | T-02-001 | `apps/orchestrator/tests/api/test_api_base.py` |
| REQ-02-092 | unit | T-02-001 | `apps/orchestrator/tests/api/test_api_base.py` |
| REQ-02-093 | security | T-02-027 | `apps/orchestrator/tests/observability/test_metrics.py` |
| REQ-02-094 | perf | T-02-028 | `apps/orchestrator/tests/perf/test_latency.py` |
| REQ-02-095 | perf | T-02-028 | `apps/orchestrator/tests/perf/test_latency.py` |
| REQ-02-096 | security | T-02-001 | `apps/orchestrator/tests/api/test_api_base.py` |
| REQ-02-097 | security | T-02-024 | `apps/orchestrator/tests/security/test_prompt_injection.py` |
| REQ-02-098 | integration | T-02-027 | `apps/orchestrator/tests/observability/test_metrics.py` |

## 03-ciclo-de-control

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-03-001 | e2e | T-03-002, T-03-003 | `apps/orchestrator/tests/tasks/test_api.py`<br>`apps/web/tests/e2e/choose-task.spec.ts` |
| REQ-03-002 | unit | T-03-001 | `apps/orchestrator/tests/tasks/test_state_machine.py` |
| REQ-03-003 | e2e | T-03-002, T-03-003 | `apps/orchestrator/tests/tasks/test_api.py`<br>`apps/web/tests/e2e/choose-task.spec.ts` |
| REQ-03-004 | unit | T-03-001 | `apps/orchestrator/tests/tasks/test_state_machine.py` |
| REQ-03-005 | e2e | T-03-001, T-03-004 | `apps/orchestrator/tests/tasks/test_state_machine.py`<br>`apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-006 | e2e | T-03-004 | `apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-007 | unit | T-03-001 | `apps/orchestrator/tests/tasks/test_state_machine.py` |
| REQ-03-008 | a11y | T-03-004 | `apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-010 | e2e | T-03-006 | `apps/web/tests/e2e/approval-card.spec.ts` |
| REQ-03-011 | a11y | T-03-006 | `apps/web/tests/e2e/approval-card.spec.ts` |
| REQ-03-012 | unit | T-03-005 | `apps/orchestrator/tests/tasks/test_approvals.py` |
| REQ-03-013 | integration | T-03-005 | `apps/orchestrator/tests/tasks/test_approvals.py` |
| REQ-03-014 | e2e | T-03-005 | `apps/orchestrator/tests/tasks/test_approvals.py` |
| REQ-03-015 | integration | T-03-005 | `apps/orchestrator/tests/tasks/test_approvals.py` |
| REQ-03-016 | e2e | T-03-007 | `apps/web/tests/e2e/hold-dispatch.spec.ts` |
| REQ-03-017 | integration | T-03-007 | `apps/web/tests/e2e/hold-dispatch.spec.ts` |
| REQ-03-018 | e2e | T-03-008 | `apps/web/tests/e2e/caregiver-notice.spec.ts` |
| REQ-03-019 | e2e | T-03-006 | `apps/web/tests/e2e/approval-card.spec.ts` |
| REQ-03-021 | e2e | T-03-010 | `apps/web/tests/e2e/autonomy-dial.spec.ts` |
| REQ-03-022 | unit | T-03-009 | `apps/orchestrator/tests/tasks/test_autonomy_settings.py` |
| REQ-03-023 | unit | T-03-009 | `apps/orchestrator/tests/tasks/test_autonomy_settings.py` |
| REQ-03-024 | e2e | T-03-009 | `apps/orchestrator/tests/tasks/test_autonomy_settings.py` |
| REQ-03-025 | e2e | T-03-010 | `apps/web/tests/e2e/autonomy-dial.spec.ts` |
| REQ-03-026 | unit | T-03-009 | `apps/orchestrator/tests/tasks/test_autonomy_settings.py` |
| REQ-03-030 | integration | T-03-011 | `apps/orchestrator/tests/achievements/test_achievements.py` |
| REQ-03-031 | a11y, manual | T-03-012 | `apps/web/tests/e2e/achievements.spec.ts` |
| REQ-03-032 | e2e | T-03-012 | `apps/web/tests/e2e/achievements.spec.ts` |
| REQ-03-033 | e2e | T-03-011 | `apps/orchestrator/tests/achievements/test_achievements.py` |
| REQ-03-034 | unit | T-03-013 | `apps/orchestrator/tests/tasks/test_next_task.py` |
| REQ-03-035 | e2e | T-03-013 | `apps/orchestrator/tests/tasks/test_next_task.py` |
| REQ-03-036 | security | T-03-014 | `apps/orchestrator/tests/achievements/test_metrics.py` |
| REQ-03-040 | e2e | T-03-015 | `apps/web/tests/e2e/first-task.spec.ts` |
| REQ-03-041 | e2e | T-03-015 | `apps/web/tests/e2e/first-task.spec.ts` |
| REQ-03-042 | e2e | T-03-015 | `apps/web/tests/e2e/first-task.spec.ts` |
| REQ-03-043 | e2e | T-03-015 | `apps/web/tests/e2e/first-task.spec.ts` |
| REQ-03-044 | e2e | T-03-015 | `apps/web/tests/e2e/first-task.spec.ts` |
| REQ-03-050 | e2e | T-03-004 | `apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-051 | e2e | T-03-003 | `apps/web/tests/e2e/choose-task.spec.ts` |
| REQ-03-052 | e2e | T-03-004 | `apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-053 | e2e | T-03-004 | `apps/web/tests/e2e/task-flow.spec.ts` |
| REQ-03-054 | a11y | T-03-016 | `apps/web/tests/a11y/control-cycle.spec.ts`<br>`tools/audit/tests/test_copy_control_cycle.py` |
| REQ-03-060 | a11y | T-03-016 | `apps/web/tests/a11y/control-cycle.spec.ts`<br>`tools/audit/tests/test_copy_control_cycle.py` |
| REQ-03-061 | a11y | T-03-006 | `apps/web/tests/e2e/approval-card.spec.ts` |
| REQ-03-062 | integration | T-03-017 | `apps/orchestrator/tests/tasks/test_recovery.py` |
| REQ-03-063 | audit | T-03-016 | `apps/web/tests/a11y/control-cycle.spec.ts`<br>`tools/audit/tests/test_copy_control_cycle.py` |

## 04-espacio-de-trabajo

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-04-001 | e2e | T-04-001, T-04-002 | `apps/orchestrator/tests/workspace/test_blocks_edit.py`<br>`apps/web/tests/e2e/block-editor.spec.ts` |
| REQ-04-002 | e2e | T-04-001 | `apps/orchestrator/tests/workspace/test_blocks_edit.py` |
| REQ-04-003 | e2e | T-04-001 | `apps/orchestrator/tests/workspace/test_blocks_edit.py` |
| REQ-04-004 | unit | T-04-003 | `apps/orchestrator/tests/workspace/test_versions.py` |
| REQ-04-005 | e2e | T-04-002 | `apps/web/tests/e2e/block-editor.spec.ts` |
| REQ-04-006 | a11y | T-04-001, T-04-002 | `apps/orchestrator/tests/workspace/test_blocks_edit.py`<br>`apps/web/tests/e2e/block-editor.spec.ts` |
| REQ-04-007 | integration | T-04-003 | `apps/orchestrator/tests/workspace/test_versions.py` |
| REQ-04-020 | e2e | T-04-004 | `apps/orchestrator/tests/workspace/test_email_agent.py` |
| REQ-04-021 | e2e | T-04-004 | `apps/orchestrator/tests/workspace/test_email_agent.py` |
| REQ-04-022 | security | T-04-005 | `apps/orchestrator/tests/workspace/test_connection.py` |
| REQ-04-023 | e2e | T-04-006 | `apps/orchestrator/tests/workspace/test_email_send.py` |
| REQ-04-024 | e2e | T-04-006 | `apps/orchestrator/tests/workspace/test_email_send.py` |
| REQ-04-025 | security | T-04-006 | `apps/orchestrator/tests/workspace/test_email_send.py` |
| REQ-04-026 | integration | T-04-006 | `apps/orchestrator/tests/workspace/test_email_send.py` |
| REQ-04-027 | e2e | T-04-006 | `apps/orchestrator/tests/workspace/test_email_send.py` |
| REQ-04-028 | e2e | T-04-005 | `apps/orchestrator/tests/workspace/test_connection.py` |
| REQ-04-030 | e2e | T-04-007 | `apps/orchestrator/tests/workspace/test_document_agent.py` |
| REQ-04-031 | e2e | T-04-007 | `apps/orchestrator/tests/workspace/test_document_agent.py` |
| REQ-04-032 | integration | T-04-008 | `apps/orchestrator/tests/workspace/test_doc_tools.py` |
| REQ-04-033 | unit | T-04-008 | `apps/orchestrator/tests/workspace/test_doc_tools.py` |
| REQ-04-034 | e2e | T-04-008 | `apps/orchestrator/tests/workspace/test_doc_tools.py` |
| REQ-04-035 | e2e | T-04-007 | `apps/orchestrator/tests/workspace/test_document_agent.py` |
| REQ-04-040 | e2e | T-04-009 | `apps/orchestrator/tests/workspace/test_social_agent.py` |
| REQ-04-041 | unit | T-04-009 | `apps/orchestrator/tests/workspace/test_social_agent.py` |
| REQ-04-042 | e2e | T-04-009 | `apps/orchestrator/tests/workspace/test_social_agent.py` |
| REQ-04-043 | integration | T-04-009 | `apps/orchestrator/tests/workspace/test_social_agent.py` |
| REQ-04-044 | e2e | T-04-010 | `apps/orchestrator/tests/workspace/test_social_extras.py` |
| REQ-04-045 | unit | T-04-010 | `apps/orchestrator/tests/workspace/test_social_extras.py` |
| REQ-04-046 | unit | T-04-010 | `apps/orchestrator/tests/workspace/test_social_extras.py` |
| REQ-04-050 | e2e | T-04-011 | `apps/web/tests/e2e/tool-catalog.spec.ts` |
| REQ-04-051 | e2e | T-04-011 | `apps/web/tests/e2e/tool-catalog.spec.ts` |
| REQ-04-052 | a11y | T-04-011 | `apps/web/tests/e2e/tool-catalog.spec.ts` |
| REQ-04-053 | unit | T-04-011 | `apps/web/tests/e2e/tool-catalog.spec.ts` |
| REQ-04-054 | e2e | T-04-012 | `apps/web/tests/e2e/workspace-states.spec.ts` |
| REQ-04-060 | a11y | T-04-013 | `apps/web/tests/a11y/workspace.spec.ts` |
| REQ-04-061 | perf | T-04-014 | `apps/orchestrator/tests/perf/test_first_draft.py` |
| REQ-04-062 | security | T-04-015 | `apps/orchestrator/tests/workspace/test_consent_encryption.py` |
| REQ-04-063 | security | T-04-015 | `apps/orchestrator/tests/workspace/test_consent_encryption.py` |
| REQ-04-064 | audit | T-04-016 | `tools/audit/tests/test_copy_workspace.py` |

## 05-seguridad-y-bienestar

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-05-001 | replay | T-05-002 | `packages/safety/python/tests/test_rules_corpus.py` |
| REQ-05-002 | security | T-05-003 | `apps/orchestrator/tests/safety/test_crisis_gate.py`<br>`tools/audit/tests/test_no_mood_inference.py` |
| REQ-05-003 | integration | T-05-004 | `packages/safety/python/tests/test_derivation.py` |
| REQ-05-004 | integration | T-05-004 | `packages/safety/python/tests/test_derivation.py` |
| REQ-05-005 | e2e | T-05-005 | `apps/web/tests/e2e/derivation.spec.ts` |
| REQ-05-006 | integration | T-05-004 | `packages/safety/python/tests/test_derivation.py` |
| REQ-05-007 | unit | T-05-004 | `packages/safety/python/tests/test_derivation.py` |
| REQ-05-008 | audit | T-05-006 | `packages/safety/python/tests/test_routes.py` |
| REQ-05-009 | e2e | T-05-006 | `packages/safety/python/tests/test_routes.py` |
| REQ-05-010 | e2e | T-05-007 | `apps/orchestrator/tests/safety/test_trusted_contact.py` |
| REQ-05-011 | unit | T-05-007 | `apps/orchestrator/tests/safety/test_trusted_contact.py` |
| REQ-05-012 | e2e | T-05-005 | `apps/web/tests/e2e/derivation.spec.ts` |
| REQ-05-013 | security | T-05-008 | `apps/orchestrator/tests/safety/test_events.py` |
| REQ-05-014 | e2e | T-05-007 | `apps/orchestrator/tests/safety/test_trusted_contact.py` |
| REQ-05-015 | audit | T-05-003 | `apps/orchestrator/tests/safety/test_crisis_gate.py`<br>`tools/audit/tests/test_no_mood_inference.py` |
| REQ-05-016 | audit | T-05-001 | `tools/audit/tests/test_audit_safety_review.py` |
| REQ-05-017 | replay | T-05-002 | `packages/safety/python/tests/test_rules_corpus.py` |
| REQ-05-020 | e2e | T-05-009 | `packages/safety/python/tests/test_advice_gate.py` |
| REQ-05-021 | security | T-05-010 | `packages/safety/python/tests/test_output_filter.py`<br>`tools/audit/tests/test_forbidden_words_ci.py` |
| REQ-05-022 | unit | T-05-010 | `packages/safety/python/tests/test_output_filter.py`<br>`tools/audit/tests/test_forbidden_words_ci.py` |
| REQ-05-023 | audit, manual | T-05-010 | `packages/safety/python/tests/test_output_filter.py`<br>`tools/audit/tests/test_forbidden_words_ci.py` |
| REQ-05-024 | audit | T-05-010 | `packages/safety/python/tests/test_output_filter.py`<br>`tools/audit/tests/test_forbidden_words_ci.py` |
| REQ-05-030 | e2e | T-05-012 | `apps/web/tests/e2e/consent.spec.ts` |
| REQ-05-031 | unit | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-032 | a11y | T-05-012 | `apps/web/tests/e2e/consent.spec.ts` |
| REQ-05-033 | e2e | T-05-012 | `apps/web/tests/e2e/consent.spec.ts` |
| REQ-05-034 | integration | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-035 | unit | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-036 | security | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-037 | unit | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-038 | unit | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-039 | security | T-05-011 | `apps/orchestrator/tests/consent/test_consent.py` |
| REQ-05-045 | e2e | T-05-005 | `apps/web/tests/e2e/derivation.spec.ts` |
| REQ-05-050 | perf | T-05-013 | `apps/web/tests/e2e/crisis-end-to-end.spec.ts`<br>`packages/safety/python/tests/test_derivation_perf.py` |
| REQ-05-051 | integration | T-05-004 | `packages/safety/python/tests/test_derivation.py` |
| REQ-05-052 | a11y | T-05-005 | `apps/web/tests/e2e/derivation.spec.ts` |
| REQ-05-053 | security | T-05-008 | `apps/orchestrator/tests/safety/test_events.py` |
| REQ-05-054 | e2e | T-05-013 | `apps/web/tests/e2e/crisis-end-to-end.spec.ts`<br>`packages/safety/python/tests/test_derivation_perf.py` |

## 06-cuidador-y-perfiles

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-06-001 | e2e | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-002 | security | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-003 | unit | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-004 | unit | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-005 | e2e | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-006 | security | T-06-002 | `apps/orchestrator/tests/caregivers/test_invitations.py` |
| REQ-06-010 | contract | T-06-001 | `apps/orchestrator/tests/caregivers/test_models_signing.py` |
| REQ-06-011 | security | T-06-003 | `apps/orchestrator/tests/caregivers/test_delegations.py` |
| REQ-06-012 | integration | T-06-004 | `apps/orchestrator/tests/caregivers/test_revocation.py` |
| REQ-06-013 | unit | T-06-003 | `apps/orchestrator/tests/caregivers/test_delegations.py` |
| REQ-06-014 | contract | T-06-003 | `apps/orchestrator/tests/caregivers/test_delegations.py` |
| REQ-06-015 | security | T-06-004 | `apps/orchestrator/tests/caregivers/test_revocation.py` |
| REQ-06-016 | e2e | T-06-003 | `apps/orchestrator/tests/caregivers/test_delegations.py` |
| REQ-06-017 | integration | T-06-005 | `apps/orchestrator/tests/caregivers/test_activity.py` |
| REQ-06-018 | security | T-06-005 | `apps/orchestrator/tests/caregivers/test_activity.py` |
| REQ-06-019 | e2e | T-06-007 | `apps/web/tests/e2e/my-caregivers.spec.ts` |
| REQ-06-030 | e2e | T-06-008 | `apps/web/tests/e2e/caregiver-panel.spec.ts` |
| REQ-06-031 | security | T-06-006 | `apps/orchestrator/tests/caregivers/test_scope_guard.py` |
| REQ-06-032 | e2e | T-06-006 | `apps/orchestrator/tests/caregivers/test_scope_guard.py` |
| REQ-06-033 | integration | T-06-009 | `apps/companion/tests/calibration/test_assisted.py` |
| REQ-06-034 | e2e | T-06-008 | `apps/web/tests/e2e/caregiver-panel.spec.ts` |
| REQ-06-035 | security | T-06-006 | `apps/orchestrator/tests/caregivers/test_scope_guard.py` |
| REQ-06-036 | unit | T-06-006 | `apps/orchestrator/tests/caregivers/test_scope_guard.py` |
| REQ-06-040 | e2e | T-06-010, T-06-011 | `apps/orchestrator/tests/caregivers/test_profile_versions.py`<br>`apps/web/tests/e2e/pending-profile-version.spec.ts` |
| REQ-06-041 | e2e | T-06-010, T-06-011 | `apps/orchestrator/tests/caregivers/test_profile_versions.py`<br>`apps/web/tests/e2e/pending-profile-version.spec.ts` |
| REQ-06-042 | unit | T-06-010 | `apps/orchestrator/tests/caregivers/test_profile_versions.py` |
| REQ-06-043 | unit | T-06-010 | `apps/orchestrator/tests/caregivers/test_profile_versions.py` |
| REQ-06-044 | e2e | T-06-010 | `apps/orchestrator/tests/caregivers/test_profile_versions.py` |
| REQ-06-050 | e2e | T-06-007, T-06-008 | `apps/web/tests/e2e/my-caregivers.spec.ts`<br>`apps/web/tests/e2e/caregiver-panel.spec.ts` |
| REQ-06-060 | a11y | T-06-012 | `apps/web/tests/a11y/caregivers.spec.ts`<br>`apps/orchestrator/tests/caregivers/test_encryption.py` |
| REQ-06-061 | perf | T-06-004 | `apps/orchestrator/tests/caregivers/test_revocation.py` |
| REQ-06-062 | security | T-06-001 | `apps/orchestrator/tests/caregivers/test_models_signing.py` |
| REQ-06-063 | security | T-06-012 | `apps/web/tests/a11y/caregivers.spec.ts`<br>`apps/orchestrator/tests/caregivers/test_encryption.py` |

## 07-privacidad-y-datos

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-07-001 | audit | T-07-001 | `tools/audit/tests/test_audit_data_inventory_full.py` |
| REQ-07-002 | audit | T-07-001 | `tools/audit/tests/test_audit_data_inventory_full.py` |
| REQ-07-003 | unit | T-07-001 | `tools/audit/tests/test_audit_data_inventory_full.py` |
| REQ-07-004 | unit | T-07-002 | `apps/orchestrator/tests/privacy/test_zero_retention.py` |
| REQ-07-005 | audit | T-07-001 | `tools/audit/tests/test_audit_data_inventory_full.py` |
| REQ-07-010 | security | T-07-006 | `apps/orchestrator/tests/privacy/test_tls_everywhere.py` |
| REQ-07-011 | security | T-07-003 | `apps/orchestrator/tests/privacy/test_crypto.py` |
| REQ-07-012 | security | T-07-003 | `apps/orchestrator/tests/privacy/test_crypto.py` |
| REQ-07-013 | security | T-07-005 | `apps/companion/tests/profile/test_local_encryption_audit.py` |
| REQ-07-014 | integration | T-07-004 | `apps/orchestrator/tests/privacy/test_key_audit.py` |
| REQ-07-015 | integration | T-07-003 | `apps/orchestrator/tests/privacy/test_crypto.py` |
| REQ-07-016 | audit | T-07-003 | `apps/orchestrator/tests/privacy/test_crypto.py` |
| REQ-07-020 | security | T-07-007 | `apps/orchestrator/tests/privacy/test_egress_layer.py` |
| REQ-07-021 | security | T-07-007 | `apps/orchestrator/tests/privacy/test_egress_layer.py` |
| REQ-07-022 | security | T-07-007 | `apps/orchestrator/tests/privacy/test_egress_layer.py` |
| REQ-07-023 | unit | T-07-008 | `apps/orchestrator/tests/privacy/test_third_parties.py` |
| REQ-07-024 | unit | T-07-008 | `apps/orchestrator/tests/privacy/test_third_parties.py` |
| REQ-07-025 | audit | T-07-008 | `apps/orchestrator/tests/privacy/test_third_parties.py` |
| REQ-07-030 | e2e | T-07-009, T-07-012 | `apps/orchestrator/tests/privacy/test_export.py`<br>`apps/web/tests/e2e/privacy.spec.ts` |
| REQ-07-031 | e2e | T-07-009 | `apps/orchestrator/tests/privacy/test_export.py` |
| REQ-07-032 | integration | T-07-009 | `apps/orchestrator/tests/privacy/test_export.py` |
| REQ-07-033 | e2e | T-07-010 | `apps/orchestrator/tests/privacy/test_erase.py` |
| REQ-07-034 | e2e | T-07-010 | `apps/orchestrator/tests/privacy/test_erase.py` |
| REQ-07-035 | integration | T-07-010 | `apps/orchestrator/tests/privacy/test_erase.py` |
| REQ-07-036 | integration | T-07-011 | `apps/orchestrator/tests/privacy/test_objection.py` |
| REQ-07-037 | a11y | T-07-012 | `apps/web/tests/e2e/privacy.spec.ts` |
| REQ-07-038 | security | T-07-011 | `apps/orchestrator/tests/privacy/test_objection.py` |
| REQ-07-045 | unit | T-07-013 | `apps/orchestrator/tests/privacy/test_retention.py` |
| REQ-07-046 | security | T-07-002 | `apps/orchestrator/tests/privacy/test_zero_retention.py` |
| REQ-07-047 | e2e | T-07-013 | `apps/orchestrator/tests/privacy/test_retention.py` |
| REQ-07-048 | unit | T-07-013 | `apps/orchestrator/tests/privacy/test_retention.py` |
| REQ-07-055 | security | T-07-014 | `apps/orchestrator/tests/privacy/test_operator_access.py` |
| REQ-07-056 | security | T-07-014 | `apps/orchestrator/tests/privacy/test_operator_access.py` |
| REQ-07-057 | security | T-07-014 | `apps/orchestrator/tests/privacy/test_operator_access.py` |
| REQ-07-058 | integration | T-07-014 | `apps/orchestrator/tests/privacy/test_operator_access.py` |
| REQ-07-065 | manual | T-07-015 | `apps/orchestrator/tests/privacy/test_incident_scope.py` |
| REQ-07-066 | integration | T-07-015 | `apps/orchestrator/tests/privacy/test_incident_scope.py` |
| REQ-07-070 | perf | T-07-009 | `apps/orchestrator/tests/privacy/test_export.py` |
| REQ-07-071 | perf | T-07-010 | `apps/orchestrator/tests/privacy/test_erase.py` |
| REQ-07-072 | a11y | T-07-012 | `apps/web/tests/e2e/privacy.spec.ts` |
| REQ-07-073 | integration | T-07-010 | `apps/orchestrator/tests/privacy/test_erase.py` |

## 08-mercado-b2b

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-08-001 | e2e | fase 2 | n/a |
| REQ-08-002 | security | fase 2 | n/a |
| REQ-08-003 | security | fase 2 | n/a |
| REQ-08-010 | e2e | fase 2 | n/a |
| REQ-08-011 | e2e | fase 2 | n/a |
| REQ-08-012 | e2e | fase 2 | n/a |
| REQ-08-013 | a11y | fase 2 | n/a |
| REQ-08-014 | unit | fase 2 | n/a |
| REQ-08-020 | e2e | fase 2 | n/a |
| REQ-08-021 | unit | fase 2 | n/a |
| REQ-08-022 | e2e | fase 2 | n/a |
| REQ-08-023 | e2e | fase 2 | n/a |
| REQ-08-024 | security | fase 2 | n/a |
| REQ-08-030 | security | fase 2 | n/a |
| REQ-08-031 | e2e | fase 2 | n/a |
| REQ-08-032 | integration | fase 2 | n/a |
| REQ-08-033 | audit | fase 2 | n/a |
| REQ-08-040 | integration | fase 2 | n/a |
| REQ-08-041 | audit | fase 2 | n/a |
| REQ-08-042 | integration | fase 2 | n/a |
| REQ-08-043 | e2e | fase 2 | n/a |
| REQ-08-044 | security | fase 2 | n/a |
| REQ-08-045 | a11y | fase 2 | n/a |
| REQ-08-050 | e2e | fase 2 | n/a |
| REQ-08-051 | unit | fase 2 | n/a |
| REQ-08-052 | security | fase 2 | n/a |
| REQ-08-053 | e2e | fase 2 | n/a |
| REQ-08-060 | a11y | fase 2 | n/a |
| REQ-08-061 | security | fase 2 | n/a |
| REQ-08-062 | integration | fase 2 | n/a |

## 09-despliegue

| Requisito | Prueba | Tareas | Archivos de prueba |
| --- | --- | --- | --- |
| REQ-09-001 | integration | T-09-001 | `apps/companion/tests/packaging/test_installer.py` |
| REQ-09-002 | security | T-09-001 | `apps/companion/tests/packaging/test_installer.py` |
| REQ-09-003 | integration | T-09-002 | `apps/companion/tests/packaging/test_models.py` |
| REQ-09-004 | e2e | T-09-003 | `apps/web/tests/e2e/install-wizard.spec.ts` |
| REQ-09-005 | e2e | T-09-004 | `apps/companion/tests/update/test_update.py` |
| REQ-09-006 | integration | T-09-004 | `apps/companion/tests/update/test_update.py` |
| REQ-09-007 | integration | T-09-005 | `apps/companion/tests/packaging/test_uninstall_autostart.py` |
| REQ-09-008 | e2e | T-09-005 | `apps/companion/tests/packaging/test_uninstall_autostart.py` |
| REQ-09-009 | security | T-09-006 | `tools/audit/tests/test_packaged_egress.py` |
| REQ-09-010 | security | T-09-007 | `apps/web/tests/e2e/pwa-security.spec.ts` |
| REQ-09-011 | security | T-09-007 | `apps/web/tests/e2e/pwa-security.spec.ts` |
| REQ-09-012 | e2e | T-09-007 | `apps/web/tests/e2e/pwa-security.spec.ts` |
| REQ-09-013 | e2e | T-09-007 | `apps/web/tests/e2e/pwa-security.spec.ts` |
| REQ-09-020 | integration | T-09-008 | `apps/orchestrator/tests/infra/test_compose.py` |
| REQ-09-021 | integration | T-09-008 | `apps/orchestrator/tests/infra/test_compose.py` |
| REQ-09-022 | security | T-09-008 | `apps/orchestrator/tests/infra/test_compose.py` |
| REQ-09-023 | integration | T-09-008 | `apps/orchestrator/tests/infra/test_compose.py` |
| REQ-09-024 | security | T-09-009 | `apps/orchestrator/tests/infra/test_mcp_isolation.py` |
| REQ-09-030 | audit | T-09-010 | `tools/audit/tests/test_audit_envs.py`<br>`apps/web/tests/e2e/test-env-banner.spec.ts` |
| REQ-09-031 | audit | T-09-010 | `tools/audit/tests/test_audit_envs.py`<br>`apps/web/tests/e2e/test-env-banner.spec.ts` |
| REQ-09-032 | audit | T-09-010 | `tools/audit/tests/test_audit_envs.py`<br>`apps/web/tests/e2e/test-env-banner.spec.ts` |
| REQ-09-033 | e2e | T-09-010 | `tools/audit/tests/test_audit_envs.py`<br>`apps/web/tests/e2e/test-env-banner.spec.ts` |
| REQ-09-034 | e2e | T-09-010 | `tools/audit/tests/test_audit_envs.py`<br>`apps/web/tests/e2e/test-env-banner.spec.ts` |
| REQ-09-040 | integration | T-09-011 | `tools/audit/tests/test_release_gate.py` |
| REQ-09-041 | audit | T-09-011 | `tools/audit/tests/test_release_gate.py` |
| REQ-09-042 | integration | T-09-011 | `tools/audit/tests/test_release_gate.py` |
| REQ-09-043 | unit | T-09-012 | `packages/common-py/tests/test_flags.py` |
| REQ-09-044 | audit | T-09-011 | `tools/audit/tests/test_release_gate.py` |
| REQ-09-050 | integration | T-09-013 | `apps/orchestrator/tests/infra/test_alerts.py` |
| REQ-09-051 | integration | T-09-014 | `apps/orchestrator/tests/infra/test_backup_restore.py` |
| REQ-09-052 | integration | T-09-013 | `apps/orchestrator/tests/infra/test_alerts.py` |
| REQ-09-053 | security | T-09-014 | `apps/orchestrator/tests/infra/test_backup_restore.py` |
| REQ-09-060 | perf | T-09-015 | `apps/companion/tests/perf/test_startup.py` |
| REQ-09-061 | perf | T-09-015 | `apps/companion/tests/perf/test_startup.py` |
| REQ-09-062 | integration | T-09-014 | `apps/orchestrator/tests/infra/test_backup_restore.py` |
| REQ-09-063 | a11y | T-09-003 | `apps/web/tests/e2e/install-wizard.spec.ts` |
