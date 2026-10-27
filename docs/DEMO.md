# Recorrido para revisión técnica (2 minutos)

[Vista rápida: video de la aplicación ejecutada](evidence/walkthrough.mp4).

1. Ejecutar `uv run --no-sync kpi-monitor demo` y abrir `127.0.0.1:8000`.
2. Revisar el turno con parada: OEE **68,4 %**, A **80 %**, P **90 %**, Q **95 %**. Ver el descanso 08:30–08:40 separado de la parada 08:20–08:30.
3. Cambiar a **Pérdida de telemetría**: cobertura **80 %**, OEE desconocido. No se rellena el hueco con ceros ni con 100 %.
4. Reconocer la alerta y esperar la siguiente actualización. El reconocimiento persiste.
5. Cambiar a **Rechazo total**: calidad y OEE **0 %**. Volver a **Operación estable**: **98 %**, sin alerta activa.
6. Revisar la tabla de eventos y exportar el reporte JSON. Contrastar los conteos con las fórmulas del README.

Para una entrevista con más tiempo: reproducir el mismo turno por MQTT; enviarlo dos veces; comprobar que la cantidad de eventos y el OEE no cambian. Explicar el límite entre ACK del broker, transacción SQLite y entrega al consumidor. Mostrar el test de recuperación de una suscripción persistente y discutir sus límites operacionales.

## Qué afirmar y qué no inferir

El caso demuestra contratos de datos, instrumentación simulada, OEE, ingestión idempotente, visualización y pruebas de integración. No implica experiencia de puesta en marcha en una fábrica concreta, ahorros económicos medidos ni una disponibilidad operacional determinada. No hay PLC físico ni modelo de IA en este repositorio.
