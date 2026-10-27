# Migración y conservación del trabajo anterior

La versión anterior permanece en el historial Git, base `ec282f3df5816b527e674b648d7218e65689b403`. Esta reconstrucción cambia el modelo de datos y no reutiliza `local_kpi_monitor.db`.

| Antes | Ahora |
|---|---|
| Ausencia de lecturas podía devolver 100 % | Cobertura explícita y valores desconocidos `null` |
| Calidad cero se sustituía por uno | Cero y ausencia son casos distintos |
| Rendimiento limitado a 90 % | Fórmula de ciclo ideal; 100 % permitido, exceso diagnosticado |
| Disponibilidad basada en cantidad de muestras | Integración de duración de intervalos |
| Archivos `.new`, DB y datos de ejecución versionados | Fuente, pruebas y documentación; `var/` ignorado |
| Compose arrancaba `sleep infinity` | API/demo y worker MQTT ejecutables |
| Rutas Kafka/Airflow incompletas | Integración MQTT implementada y comprobable |

La nueva base usa `shifts`, `events`, `alerts` y `rejected_messages`. Las lecturas puntuales antiguas no contienen todos los tiempos, conteos y límites necesarios para reconstruir un OEE fiable. No se ofrece una conversión automática que invente esos datos.

Si necesitas conservar una base anterior, haz primero una copia fuera de `var/`. Selecciona una ruta nueva con `--db`. Para datos reales prepara intervalos mediante un adaptador que explicite conteos, paradas, pausas y ciclo ideal. El programa no elimina ni migra bases anteriores automáticamente.
