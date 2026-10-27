# Evidencia de validación

Validado el 27 de octubre de 2026. Código de backend y empaquetado comprobados en la [ejecución completa de CI](https://github.com/GzoC/real_time_kpi_monitor/actions/runs/40533990522), commit `d1276aa3432e837bf2b692f7dffb21771010a7bc`. Las comprobaciones de la revisión actual están en [PR #2 / checks](https://github.com/GzoC/real_time_kpi_monitor/pull/2/checks).

## Pruebas ejecutadas

| Comprobación | Entorno | Resultado |
|---|---|---|
| Dominio, almacenamiento, HTTP, CLI, MQTT | Windows / Python 3.12.14 | 61 pruebas aprobadas |
| La misma suite y Ruff | GitHub Actions / Linux / Python 3.11 y 3.13 | Ambas matrices aprobadas |
| Cobertura de líneas Python | CI / Python 3.13 | 90 %; 624 sentencias, 62 sin cubrir |
| Wheel y sdist | CI / Python 3.11 y 3.13 | Construidos; wheel instalado y ejecutado fuera del árbol fuente |
| Reporte desde wheel instalado | Entorno limpio de CI | 360 piezas, 342 buenas, OEE 0,684 |
| Docker Compose con API, Mosquitto y consumidor | GitHub Actions / Linux | Servicios saludables; dashboard HTTP accesible |
| Flujo MQTT → SQLite → API en contenedores | GitHub Actions / Linux | 50 intervalos recibidos; OEE 98 % |

La cobertura no mide el JavaScript ni demuestra aptitud industrial. Docker se ejecutó en CI: no está instalado en el equipo Windows de desarrollo. La CLI también se instaló y ejercitó localmente en un segundo entorno fuera del código fuente.

Las pruebas MQTT usan TCP real y comprueban publicación, commit SQLite, reenvíos sin doble conteo, rechazos, reconexión y recuperación de mensajes pendientes de una sesión persistente. También comprueban que el archivo de readiness cambia al suscribirse y desconectarse. El escenario local de broker usa identidad de prueba; no constituye una prueba de autenticación o TLS industrial.

## Comprobación real del navegador

- Escritorio de 1440 × 1000 y móvil de 390 × 844, sin desbordamiento horizontal de la página.
- Cinco escenarios: referencia 68,4 %, estable 98 %, pérdida de señal con OEE desconocido, calidad cero con OEE cero y ausencia total de datos.
- Reconocimiento de alertas persistente entre actualizaciones; exportación JSON descargada y revisada; foco por teclado entre los selectores.
- Interrupción deliberada del servidor: aviso visible, datos anteriores identificados como no actualizados y recuperación automática al reiniciar la API.
- Sin errores de consola en operación normal. Los errores de red durante la interrupción deliberada fueron esperados. No se afirma una auditoría completa de accesibilidad.

## Evidencia visual

- [Video del recorrido](evidence/walkthrough.mp4)
- [Dashboard de escritorio](evidence/dashboard-desktop.png)
- [Dashboard móvil con calidad cero](evidence/dashboard-mobile.png)
- [Pérdida de telemetría](evidence/sensor-loss.png)
- [Interrupción de la API](evidence/connection-lost.png)

El video se codificó a partir de 32 capturas del navegador durante un recorrido real de unos 15 segundos, conservando sus intervalos de captura. Muestra los cambios de escenario y no pretende medir latencia. Se verificó su decodificación completa. Las capturas no son mockups; los datos de producción mostrados sí son sintéticos y están etiquetados.

## Límites de la evidencia

No se han medido capacidad de producción, latencia industrial, alta disponibilidad, resistencia ante todos los fallos posibles ni interacción con un PLC físico. No hubo despliegue de planta. TLS y credenciales son opciones implementadas, sin validación contra infraestructura industrial. Los porcentajes de la demo son resultados de fixtures reproducibles, no resultados profesionales atribuidos al autor.
