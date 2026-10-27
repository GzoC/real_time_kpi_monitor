# Transporte MQTT y operación local

MQTT 3.1.1, QoS 1, biblioteca [Eclipse Paho](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html). Un mensaje contiene un objeto JSON UTF-8 del [contrato v1](DATA_CONTRACT.md):

- `kpi/v1/shifts`: turno completo.
- `kpi/v1/events`: un intervalo de producción.

El simulador publica sin `retain`. El consumidor tiene sesión persistente (`clean_session=false`) e identidad estable. Un nuevo proceso debe usar el mismo `MQTT_CLIENT_ID` para recuperar la sesión; dos consumidores simultáneos necesitan IDs distintos. La continuidad depende también de la configuración, cuotas y persistencia del broker.

## Configuración

| Variable | Predeterminado | Propósito |
|---|---|---|
| `KPI_DB_PATH` | `var/monitor.db` | Debe coincidir en API y consumidor |
| `MQTT_HOST` | `127.0.0.1` | Host del broker |
| `MQTT_PORT` | `1883` | Puerto explícito; usar el configurado para TLS |
| `MQTT_PREFIX` | `kpi/v1` | Prefijo concreto, sin comodines |
| `MQTT_CLIENT_ID` | `kpi-monitor-local` | Identidad persistente del consumidor |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | Sin definir | Credenciales opcionales |
| `MQTT_TLS` | `false` | `true` activa validación de certificado/hostname |
| `MQTT_CA_FILE` | Sin definir | CA propia opcional; exige TLS activado |
| `MQTT_READY_FILE` | Sin definir | Archivo de estado opcional para healthcheck del contenedor |

Ejemplo PowerShell para un broker TLS ya provisionado (sustituir los valores de ejemplo):

```powershell
$env:MQTT_HOST = 'broker.example.com'
$env:MQTT_PORT = '8883'
$env:MQTT_TLS = 'true'
$env:MQTT_USERNAME = 'monitor'
# Provisionar MQTT_PASSWORD por un mecanismo de secretos del entorno.
uv run --no-sync kpi-monitor mqtt-listen
```

La plantilla `.env.example` no contiene credenciales y no se carga automáticamente. El repositorio no desactiva la verificación TLS. No hay pruebas contra un broker industrial ni una infraestructura de certificados de planta.

## Confirmación y recuperación

1. El broker entrega el mensaje al consumidor.
2. Pydantic valida contrato; SQLite confirma el registro o reconoce un duplicado idéntico.
3. El consumidor envía ACK. Los reenvíos no vuelven a sumar producción.
4. Un mensaje inválido/conflictivo registra una categoría de rechazo y se confirma para evitar un bucle de mensajes irrecuperables. No se guarda el payload original.
5. Ante error de almacenamiento, no se confirma el mensaje: el worker termina con fallo y requiere reinicio tras reparar el almacenamiento. Compose puede reiniciarlo; el mismo ID permite al broker reentregar pendientes según sus garantías.

La reconexión de red usa espera progresiva de 1 a 30 segundos. `mqtt-replay` espera el ACK del **broker**, que no certifica persistencia en SQLite. Comprueba cobertura/eventos por API. MQTT QoS 1 permite duplicados; la idempotencia de aplicación evita el doble conteo. No se promete entrega exactamente una vez ni recuperación de eventos publicados antes de la primera suscripción.

## Broker incluido

Compose usa Mosquitto 2.0.22, volumen de persistencia y puerto host en loopback. El acceso anónimo es exclusivamente para la demo local. Para redes compartidas se requieren autenticación, ACL por equipo/tópico y TLS. No uses esta configuración como despliegue directo de planta.

La prueba Python usa aMQTT en TCP de loopback y una identidad de prueba. aMQTT no conserva sesiones anónimas desconectadas; por eso el caso de mensajes pendientes utiliza un username explícito. Esa identidad no constituye una prueba de autenticación.

## Límites

Payload máximo 64 KiB. Los intervalos inválidos no cambian métricas. No hay cola de errores con payload, rotación/retención automática, métricas del broker ni garantía de operación sin conexión indefinida. El contador de rechazos de `/api/health` corresponde solo al transporte MQTT; HTTP devuelve sus propios errores 4xx.

La salud HTTP comprueba acceso a almacenamiento, no la conexión del worker MQTT. Compose comprueba por separado que el consumidor haya recibido SUBACK antes de publicar con `up --wait`; el archivo de estado pasa a `not_ready` al desconectarse. La frescura mostrada en el dashboard se deriva de los timestamps de eventos, no de una luz de “conectado” al broker.
