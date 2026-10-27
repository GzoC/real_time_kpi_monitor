# Contrato de datos v1

## Turno

```json
{
  "shift_id": "linea1-manana",
  "machine_id": "LINEA-01",
  "name": "Turno mañana",
  "start": "2026-01-15T08:00:00Z",
  "end": "2026-01-15T09:00:00Z",
  "ideal_cycle_seconds": 6,
  "breaks": [{"start": "2026-01-15T08:30:00Z", "end": "2026-01-15T08:40:00Z"}],
  "source": "external"
}
```

Configuración inmutable por `shift_id`. El mismo contenido se puede reenviar; cambiarlo devuelve conflicto. Para una corrección crea otro turno con ID distinto y documenta el motivo. Un turno dura como máximo 24 horas y tiene hasta 128 descansos disjuntos contenidos en él. El ciclo ideal debe ser positivo. `source` distingue `synthetic` de `external`; por defecto es `external`.

## Intervalo de producción

```json
{
  "event_id": "LINEA-01-20260115-080000",
  "machine_id": "LINEA-01",
  "start": "2026-01-15T08:00:00Z",
  "end": "2026-01-15T08:01:00Z",
  "state": "running",
  "total_count": 9,
  "good_count": 8
}
```

`state` admite `running` y `stopped`; una parada tiene cero piezas. Conteos enteros entre 0 y 2.147.483.647, con buenas ≤ total. No se admiten NaN, infinitos ni campos adicionales. Todos los timestamps necesitan zona horaria y `end > start`; máximo 24 horas por evento.

IDs: letras ASCII, números, guion y guion bajo. Hasta 80 caracteres para turno/máquina, 120 para evento. `event_id` es global en la base: incluye máquina/origen en la identidad. Duplicado idéntico → aceptado sin sumar; mismo ID con otro contenido o intervalos solapados de una máquina → conflicto. El orden de llegada puede ser distinto del orden temporal.

Se guardan eventos aunque el turno todavía no haya llegado. El reporte selecciona por máquina e intersección temporal, sin eliminar los demás registros. No hay edición destructiva de eventos ni retención automática.

## HTTP

| Método y ruta | Uso |
|---|---|
| `GET /api/health` | Almacenamiento accesible, modo demo, contador de rechazos MQTT |
| `GET /api/shifts?limit=100` | Hasta 500 turnos, los últimos insertados primero |
| `POST /api/shifts` | Un objeto turno |
| `POST /api/events` | Array de 1 a 1000 intervalos; transacción atómica |
| `GET /api/shifts/{id}/report` | Métricas y calidad del agregado |
| `GET /api/shifts/{id}/snapshot?minutes=10` | Turno, reporte, frescura, ventanas, alertas y últimos 120 eventos |
| `GET /api/shifts/{id}/events?limit=1000` | Últimos intervalos (máximo 5000) |
| `GET /api/alerts?shift_id={id}` | Condiciones activas/resueltas y reconocimiento |
| `POST /api/alerts/{id}/acknowledge` | Reconocer una condición sin borrar el historial |
| `GET /api/demo/scenarios` | Escenarios disponibles cuando la demo está habilitada |
| `POST /api/demo/{name}` | Carga sintética idempotente; 403 fuera del modo demo |

422 indica contrato inválido; 409 indica conflicto; 404 indica recurso ausente. Los reportes rechazan más de 50.000 intervalos con 413; no entregan un agregado truncado. El dashboard lista hasta 100 turnos y los eventos visibles pueden ser una muestra del reporte completo. Los límites de contrato no sustituyen un límite de tamaño de peticiones o rate limiting para una API expuesta a redes.

El JSON exportado por el dashboard contiene configuración, resultado y metadatos temporales. Para reproducir los datos completos usa la CLI/archivo de origen: la exportación del dashboard no es un respaldo de la base.
