# Estado de implementación — pausa por cuota
Fecha: 2026-10-26. Estado: INCOMPLETO / WIP. No publicar como versión terminada.

## Autorización y límite
Implementar todas las recomendaciones de la auditoría para real_time_kpi_monitor, empezando solo por este proyecto. El usuario confirmó que al quedar <=8 % disponible se detiene la implementación, se respalda y se retoma tras restauración. Última consulta: ventana 5h 92 % usada / 8 % disponible; semanal 44 % usada / 56 % disponible. Restablecimiento indicado: 2026-10-26 19:29:57 America/Santiago.

## Ubicación
Checkout: C:/Users/gzola/Documents/ChatGPT/Correcciones de proyetos/real_time_kpi_monitor
Rama: codex/kpi-industrial-portfolio
Base: ec282f3df5816b527e674b648d7218e65689b403
Python de trabajo: ../work/kpi-venv/Scripts/python.exe
Respaldo: ../work/checkpoints/

## Implementado y verificado
- Nuevo paquete src/kpi_monitor y pyproject.toml.
- domain.py: contratos Pydantic, timestamps UTC conscientes, intervalos [start,end), turnos y descansos, conteos enteros y válidos.
- OEE basado en duraciones: sin datos -> null; calidad cero -> cero; rendimiento ideal ->100%; exceso de rendimiento se muestra y suprime OEE con error de configuración.
- No se extrapolan piezas en intervalos que cruzan límites planificados. Se detectan huecos y solapamientos.
- storage.py: SQLite WAL, transacciones atómicas, reenvíos idempotentes, conflictos explícitos, alertas sin duplicarse en cada consulta y reconocimiento persistente.
- simulation.py: escenarios sintéticos deterministas. Reference OEE68.4%, healthy98%, sensor_loss80% cobertura/OEE desconocido, zero_quality0%, no_data desconocido.
- api.py: factory FastAPI; turnos, eventos, reportes, alertas y modo demo explícito.
- 47 tests aprobados, ruff check aprobado y formato aplicado.
- Hay una advertencia externa de Starlette/httpx; revisar versiones compatibles al finalizar lock de dependencias.
- Código antiguo, pruebas basadas en cálculos incorrectos y residuos de ejecución retirados del árbol de trabajo. Se preservan en la base y en kpi-baseline.bundle.

## Pendiente obligatorio
1. Implementar cli.py (el entrypoint de pyproject todavía NO existe): demo, serve, importación JSONL, exportación/reportes y replay.
2. Dashboard local en static/: diseño profesional en español, responsive, accesible, métricas null explícitas, cobertura, períodos, eventos, alertas, estados de carga/error y escenarios. / devuelve503 mientras falten assets.
3. Adaptador MQTT usando paho-mqtt con el mismo contrato; TLS/auth configurables, rechazo visible, reconnect/QoS1/idempotencia. Simulador publica; pruebas reales con broker local amqtt (ya instalado).
4. Mejorar límites de volumen/consulta si corresponde; revisar semántica de freshness en datos externos y rango temporal. Evitar afirmar que snapshots históricos son telemetría de planta.
5. Dockerfile/Compose reales con API y broker opcional, sin Kafka/Airflow ni sleep infinity. Docker no está instalado en este equipo; probar donde haya runtime y declarar si queda sin ejecutar.
6. Dependencias runtime/dev bloqueadas y comprobación de instalación limpia/rueda; .env.example, LICENSE MIT consistente, .gitignore/.dockerignore.
7. CI GitHub Actions: lint, tests, MQTT, paquete y smoke de contenedores si viable.
8. README reescrito, docs de arquitectura/fórmulas/contrato/ejecución/limitaciones y migración de esquema. Los archivos README, Dockerfile, requirements y Compose originales siguen DESACTUALIZADOS.
9. Validación real de navegador desktop/móvil, estados de error y demo; capturas y video corto real, sin fabricar resultados.
10. Medición local reproducible si se publican cifras; no atribuir capacidad de producción.
11. Revisión final independiente mediante inspección propia (no se autorizó delegación), git diff --check y --cached, respaldo final y entrega revisable. No iniciar otro proyecto.
12. Al completar, desactivar la automatización de reanudación; identificar estado local/remoto y pruebas reales.

## Reanudar
Consultar cuotas antes de trabajar. Si cualquiera queda <=8 %, no implementar; conservar respaldo y esperar. Si la cuota se restableció, leer este archivo y ../work/KPI_PROGRESS.md, revisar git status y continuar exactamente desde aquí.
Comandos de comprobación: ../work/kpi-venv/Scripts/python.exe -m pytest -q; ../work/kpi-venv/Scripts/python.exe -m ruff check src/kpi_monitor tests
No hay despliegue, PR ni publicación remota de la implementación parcial.
