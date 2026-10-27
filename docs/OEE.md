# Criterio de cálculo

El motor usa el desglose A × P × Q de [Vorne / OEE.com](https://www.oee.com/calculating-oee/), con reglas de calidad de datos propias de esta implementación. No se afirma certificación ni conformidad con una norma industrial.

## Unidades y denominadores

- Tiempo planificado = duración del turno menos intervalos sin intención de producir.
- Disponibilidad = tiempo en marcha / tiempo planificado.
- Rendimiento = ciclo ideal en segundos por pieza × producción total / tiempo en marcha.
- Calidad = piezas buenas / producción total.
- OEE = disponibilidad × rendimiento × calidad.

Las paradas durante tiempo planificado penalizan disponibilidad. Un cambio de formato no se excluye automáticamente: si existía intención de producir, se representa como parada. `breaks` se reserva para tiempo sin intención de producción. La calidad se interpreta como piezas buenas a la primera; el gateway debe aplicar esa definición.

## Semántica temporal

Todos los intervalos son `[start, end)`: el fin no pertenece al intervalo. Las marcas incluyen zona horaria y se normalizan a UTC. No se cuentan muestras; se suman sus duraciones. Una muestra de 10 segundos y otra de 50 tienen pesos distintos.

Los conteos son incrementos dentro de cada intervalo, no contadores acumulativos del PLC. Si un evento cruza el inicio/fin del turno o un descanso, no se fraccionan piezas: ese evento queda fuera del agregado y aparece `interval_crosses_planned_boundary`. El gateway debe emitir intervalos alineados con esos límites.

Los reportes por ventanas siguen la misma regla. Un evento válido para el turno que cruce dos ventanas de diez minutos puede volver desconocidas esas ventanas; el total del turno conserva su cálculo. No se promedian porcentajes de ventanas para construir el OEE global.

## Ausencia, cero y configuración inválida

| Situación | Resultado |
|---|---|
| Sin eventos o huecos en el tiempo planificado | A/P/Q/OEE `null`; cobertura y conteos observados disponibles |
| Todos los eventos son paradas, cobertura completa | A = 0, P/Q indefinidos, OEE = 0; `no_production` |
| Hay marcha pero ninguna pieza, cobertura completa | P = 0, Q indefinido, OEE = 0 |
| Piezas producidas pero ninguna buena | Q = 0, OEE = 0 |
| Rendimiento > 100 % fuera de tolerancia numérica | P visible, OEE `null`; `invalid_configuration` |
| Datos completos y configuración válida | A/P/Q/OEE calculados |

Cobertura = duración de eventos válidos en tiempo planificado / tiempo planificado. No es disponibilidad: una máquina detenida con señal válida tiene cobertura completa.

Los cálculos usan segundos en punto flotante; las comparaciones de cobertura toleran 1 microsegundo y las de rendimiento 1e-9. Los conteos son enteros estrictos. Un resultado desconocido nunca se convierte en cero para dibujar la gráfica.

## Frescura y alertas

`metadata.event_age_seconds` compara la hora del servidor con el fin del evento más reciente del turno. En un turno externo en curso se muestra `stale=true` tras 120 segundos sin un intervalo reciente. Es un umbral de demostración, no una condición contractual de proceso. Fechas adelantadas más de 5 segundos muestran advertencia de reloj. Los históricos sintéticos nunca se anuncian como una señal de planta en vivo.

El OEE se calcula para el turno completo. Una parte futura todavía sin observar también cuenta como cobertura pendiente; la etiqueta “incompleta” no distingue por sí sola un hueco pasado de datos aún no esperados. La fase del turno y la antigüedad aportan ese contexto.

Las alertas son reglas de demostración: falta de cobertura, ciclo inválido u OEE < 85 % (crítica por debajo del 75 %). Se persisten por `(shift_id, code)`. Reconocer no elimina la condición; si se resuelve y reaparece, vuelve a requerir reconocimiento. Se actualizan al consultar reporte/snapshot: no existe un motor autónomo de notificaciones.
