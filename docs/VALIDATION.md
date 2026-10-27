# Evidencia de validación — entrega aún en preparación

Ejecución local: 26 de octubre de 2026, Windows, Python 3.12.14, entorno `uv sync --locked --extra dev`. Estado: **WIP; no publicar como versión terminada todavía**.

## Comprobado

- Ruff: análisis y formato aprobados en `src`, `tests` y `scripts`.
- Pytest: **61 pruebas aprobadas**, sin advertencias; cobertura de líneas Python **90 %** (624 sentencias, 63 sin cubrir). La cobertura no mide el JavaScript ni prueba aptitud industrial.
- MQTT: broker aMQTT TCP real en puerto efímero; publicación, transacción SQLite, reenvío idempotente, mensajes inválidos y conflictivos, reconexión y recuperación de 50 mensajes pendientes en una sesión persistente.
- Paquete: wheel y sdist construidos; wheel instalado con dependencias bloqueadas en un segundo entorno. La CLI, ejecutada fuera del árbol fuente, importó 50 eventos y calculó OEE 0,684. Esa construcción precede al último healthcheck MQTT y debe repetirse para el artefacto final.
- Navegador real: escritorio de 1440 × 1000 y móvil de 390 × 844; sin desbordamiento horizontal. Se verificaron los cinco escenarios, cero frente a ausencia, persistencia del reconocimiento de alerta, exportación JSON y foco por teclado entre selectores.
- Se detuvo el servidor de prueba: el dashboard mostró desconexión y avisó que retenía cifras de la última consulta correcta. Al reiniciar recuperó la actualización automáticamente.
- La consola no mostró errores en la operación normal; los errores de red durante la desconexión deliberada fueron esperados.

## Evidencia visual

- [Dashboard de escritorio](evidence/dashboard-desktop.png)
- [Dashboard móvil con calidad cero](evidence/dashboard-mobile.png)
- [Pérdida de telemetría](evidence/sensor-loss.png)
- [Interrupción de la API](evidence/connection-lost.png)

Las capturas provienen de la aplicación ejecutada. No son diseños simulados. Los datos de producción que muestran sí son sintéticos y están etiquetados en la interfaz.

## Pendientes antes de cerrar

- Revisión final de implementación y documentación; comprobar el healthcheck MQTT en contenedor.
- Ejecutar CI en GitHub, incluidas matrices Python 3.11/3.13 y Docker/Compose. Docker no está instalado localmente; no se ha ejecutado un contenedor en este equipo.
- Reconstruir y probar el paquete final; adjuntar video breve a partir de la demo real.
- Crear la entrega revisable en GitHub y registrar aquí las ejecuciones/SHAs finales.

No se han medido capacidad de producción, latencia industrial, alta disponibilidad ni interacción con un PLC físico. TLS y credenciales son opciones implementadas, aún sin prueba contra infraestructura industrial.
