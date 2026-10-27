# Continuidad — real_time_kpi_monitor

Estado: WIP; pausa preventiva para respetar el umbral de 8 % restante. Última consulta: 10 % disponible en 5h, 41 % semanal. Próxima restauración: 2026-10-27 01:41:27 America/Santiago.
Checkout: C:/Users/gzola/Documents/ChatGPT/Correcciones de proyetos/real_time_kpi_monitor
Rama: codex/kpi-industrial-portfolio. Base ec282f3df5816b527e674b648d7218e65689b403.
No se ha hecho push, PR, merge ni despliegue. No iniciar otros repositorios.

Implementado: dominio OEE, almacenamiento, API, CLI, dashboard, reportes/frescura, MQTT con ACK después del commit, sesiones persistentes, configuración Docker/CI, lock uv + requirements con hashes, licencia y documentación.
Verificado: 61 tests, 90 % cobertura Python, Ruff aprobado. Broker TCP real con reenvíos/reconexión/pendientes. Navegador desktop/mobile, cinco escenarios, alertas, descarga y pérdida/recuperación de API. Ver docs/VALIDATION.md.
Entorno canónico: .venv/Scripts/python.exe (uv, Python 3.12.14).
Entornos de ensayo: ../work/kpi-venv, ../work/kpi-wheel-check; wheel previo en ../work/kpi-dist.

Pendientes: revisión final, video breve (capturas reales scene-01..04 en docs/evidence), prueba del healthcheck MQTT y Docker/CI remoto, reconstrucción del paquete final, commit/push/PR revisable y resultado final. docs/VALIDATION.md debe actualizarse tras comprobaciones reales. Docker no instalado localmente. gh funciona al permitir red (sin red produce falso error de autenticación).

Atención: no sobrescribir código con staging antiguo. La fuente vigente es este checkout. Staging auxiliar en C:/Users/gzola/Documents/Codex/2026-10-26/v/work/kpi-edit/files se usó porque el heartbeat tiene permisos de escritura distintos; sus Python pueden diferir en orden de imports tras Ruff. sync_sources.py copia todo staging. Preferir editar directamente mediante exec autorizado o sincronizar solo archivos nuevos/revisados.

MQTT tests: AnonymousAuthPlugin allow_anonymous=False + username integration-test permite persistencia en aMQTT; no es prueba de autenticación. 8 tests MQTT pasaron. Healthcheck opcional MQTT_READY_FILE se añadió después y la suite completa de 61 pasó; falta prueba del archivo de estado vía contenedor. Python API alertas se refrescan al consultar reporte/snapshot, no worker independiente.

Servidor local de revisión: puerto 8765, var/browser-demo.db. Ver ../work/kpi-server.pid y proceso que escucha antes de operar; el launcher puede ser padre del proceso real. Será detenido para la pausa. Export UI comprobado en C:/Users/gzola/Downloads/oee-healthy.json. Capturas también en C:/Users/gzola/Documents/Codex/2026-10-26/v/outputs/kpi-evidence.

Reanudar: consultar cuota, si cualquiera <=8 % no implementar. Leer este archivo y ../work/KPI_PROGRESS.md, verificar status/HEAD. Continuar los pendientes, reconsultar cuota en hitos. Mantener respaldos Git bundle + ZIP. Eliminar heartbeat cuando todo esté entregado.
