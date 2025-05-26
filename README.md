# Sistema Automatizado de Monitoreo de Calidad y KPI de Producción Industrial en Tiempo Real

## Descripción
Este proyecto implementa una **plataforma** para el monitoreo de indicadores clave de desempeño (KPIs) y calidad en procesos industriales. Captura datos simulados de sensores, los procesa, calcula métricas como OEE, y los presenta a través de servicios. Además, cuenta con un sistema de alertas para cuando los KPIs exceden umbrales definidos.

El objetivo inicial era desarrollar un sistema completamente Dockerizado utilizando Kafka, TimescaleDB y Apache Airflow. Sin embargo, debido a limitaciones de espacio en disco en el entorno de desarrollo y pruebas proporcionado, no fue posible implementar ni verificar completamente esta arquitectura. Por ello, el proyecto fue adaptado para permitir una **verificación funcional de la lógica central de la aplicación en un modo de ejecución local**, utilizando SQLite como base de datos y archivos JSONL para el intercambio de datos (simulando el flujo a través de Kafka).

> Combina tu experiencia en automatización industrial con habilidades de Data Analytics; diseñado para que un agente IA en VS Code pueda desarrollarlo paso a paso.

---

## Tabla de contenidos
1. [Tecnologías y Herramientas](#tecnologías-y-herramientas)
2. [Arquitectura de alto nivel](#arquitectura-de-alto-nivel)
3. [Modo de Ejecución Local (Alternativo)](#modo-de-ejecución-local-alternativo)
4. [Requisitos Previos](#requisitos-previos)
5. [Estructura del Repositorio](#estructura-del-repositorio)
6. [Entorno de Desarrollo en VS Code](#entorno-de-desarrollo-en-vs-code)
7. [Instalación y Configuración](#instalación-y-configuración)
8. [Ejecución del Proyecto (Modo Local)](#ejecución-del-proyecto-modo-local)
9. [Fases y Workflow Git](#fases-y-workflow-git)
10. [Testing](#testing)
11. [CI/CD con GitHub Actions](#ci-cd-con-github-actions)
12. [Limitaciones del Entorno Actual](#limitaciones-del-entorno-actual)
13. [Contribución](#contribución)
14. [Licencia](#licencia)

---

## Tecnologías y Herramientas
- **Lenguaje:** Python 3.11
- **Base de datos (Local/Probada):** SQLite
- **Base de datos (Objetivo):** TimescaleDB (PostgreSQL con extensión time-series) - *No probado localmente debido a limitaciones.*
- **Broker de mensajes (Objetivo):** Kafka o Redpanda - *No probado localmente; simulado con archivos JSONL.*
- **Orquestación ETL (Objetivo):** Apache Airflow - *No implementado/probado localmente.*
- **Visualización (Objetivo):** Power BI o Tableau (DirectQuery)
- **Framework web:** FastAPI (servicio de alertas) - *Probado localmente.*
- **Contenedores (Preparado):** Docker, Docker Compose - *Configuración disponible para un entorno con más recursos.*
- **CI/CD:** GitHub Actions
- **Control de versiones:** Git
- **Documentación:** MkDocs + Material for MkDocs

---

## Arquitectura de alto nivel

**Arquitectura Objetivo (No implementada/probada completamente en el entorno actual):**
```plaintext
 PLCs ──▶ [Ingestor MQTT/OPC UA] ──▶ [Kafka/Redpanda] ──▶ [TimescaleDB]
                                                  │
                                                  ├─▶ [Airflow DAGs] ──▶ [ETL / limpieza]
                                                  ├─▶ [KPI Engine (Python)]
                                                  └─▶ [Alert Service (FastAPI)]

                                                  ▼
                                           [Power BI / Tableau]
```  
**Arquitectura Local Probada (Alternativa):**
```plaintext
 [Simulate_Sensors.py (output a JSONL file)] ──▶ [ETL.py (input from JSONL file)] ──▶ [SQLite Database]
                                                                                              │
                                                                                              ├─▶ [KPI Engine (Python, uses SQLite)]
                                                                                              └─▶ [Alert Service (FastAPI, uses SQLite)]
```

---

## Modo de Ejecución Local (Alternativo)
Debido a las limitaciones del entorno, se ha habilitado un modo de ejecución local que no depende de Kafka, TimescaleDB ni Airflow.
- **Base de datos:** SQLite (archivo local).
- **Intercambio de datos (simulando Kafka):** Archivos JSONL. El script de simulación de sensores escribe datos en un archivo, y el script ETL lee desde este archivo.
- **Variables de Entorno Clave para Modo Local:**
  - `DB_TYPE=sqlite`
  - `DATABASE_URL=sqlite:///./local_kpi_monitor.db` (o la ruta deseada para el archivo SQLite)
  - `SIMULATION_OUTPUT=file` (para que `simulate_sensors.py` escriba a un archivo)
  - `SIMULATION_OUTPUT_FILE=./sensor_data_simulation.jsonl` (ruta del archivo de datos de simulación)
  - `ETL_INPUT_SOURCE=file` (para que `etl.py` lea desde un archivo)
  - `ETL_INPUT_FILE=./sensor_data_simulation.jsonl` (ruta del archivo de entrada para ETL)
  - `SIMULATION_MAX_ITERATIONS=N` (opcional, para limitar el número de iteraciones del simulador)
  - `SIMULATION_INTERVAL_SECONDS=S` (opcional, intervalo entre simulaciones)

---

## Requisitos Previos
- Python 3.10 o superior.
- Git instalado y configurado.
- (Opcional para arquitectura objetivo) Docker y Docker Compose.
- (Opcional para arquitectura objetivo) Cuenta de GitHub (para repositorio y Actions).
- (Opcional para arquitectura objetivo) Power BI Desktop o Tableau Public para visualizar dashboards.

---

## Estructura del Repositorio
```
real-time-kpi-monitor/
├── .github/
│   └── workflows/          # Definición de CI/CD
├── docs/                   # (Opcional) MkDocs: documentación del proyecto
├── src/
│   ├── ingestor.py         # Captura datos (Kafka o modo archivo si se adapta)
│   ├── etl.py              # Tareas de limpieza y carga a DB (desde Kafka o archivo)
│   ├── processing/         # Lógica de cálculo de KPIs
│   │   └── kpi_engine.py
│   ├── alerts/             # Servicio FastAPI para alertas
│   │   └── alert_service.py
│   ├── db/                 # Módulos de base de datos (models, database)
│   └── config.py           # (Opcional) Parámetros y variables de entorno centralizadas
├── tests/                  # Pruebas unitarias e integración (adaptadas para SQLite)
│   ├── test_sensor_simulation_output.py
│   ├── test_etl.py
│   ├── test_kpi_engine.py
│   └── test_alert_service.py
├── scripts/                # Scripts utilitarios (init_db, simulate_sensors)
├── docker-compose.yml      # Definición de servicios Docker (para arquitectura objetivo simplificada)
├── Dockerfile              # Imagen para servicios Python (simplificada, sin Airflow)
├── .env.template           # Variables de entorno de ejemplo
├── requirements.txt        # Dependencias de Python
├── README.md               # Este archivo
└── .devcontainer.json      # (Opcional) Configuración de contenedor VS Code
```

---

## Entorno de Desarrollo en VS Code
(Se mantiene como referencia para la arquitectura objetivo)
1. Abre el proyecto en VS Code.
2. Instala la extensión **Remote - Containers**.
3. Abre la paleta (`Ctrl+Shift+P`) y ejecuta `Remote-Containers: Reopen in Container`.
4. VS Code creará un contenedor con Python y dependencias definidas en `Dockerfile` y `devcontainer.json`.

> El agente IA podrá usar este contenedor para ejecutar tareas, instalar dependencias y ejecutar comandos sin salir de VS Code.

---

## Instalación y Configuración

**Configuración Local (Recomendada para el entorno actual):**
1. Clona el repositorio:
   ```bash
   git clone https://github.com/GzoC/real-time-kpi-monitor.git
   cd real-time-kpi-monitor
   ```
2. Crea y activa un entorno virtual de Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Copia y ajusta variables de entorno para modo local (ver sección "Modo de Ejecución Local"):
   ```bash
   cp .env.template .env
   # Edita .env y asegúrate que las variables para modo local estén configuradas.
   # Ejemplo: DB_TYPE=sqlite, SIMULATION_OUTPUT=file, ETL_INPUT_SOURCE=file, etc.
   ```

**Configuración Docker (Para entornos con suficientes recursos):**
- Los archivos `Dockerfile` y `docker-compose.yml` están configurados para una versión simplificada del sistema (sin Airflow).
- **Nota:** En el entorno de desarrollo actual, la ejecución de `docker-compose up` falló debido a limitaciones de espacio en disco, incluso con esta configuración simplificada. Se proporcionan para uso en entornos con más recursos.
- Para intentar ejecutar con Docker:
  1. Asegúrate que Docker y Docker Compose estén instalados.
  2. Configura las variables en `.env` según sea necesario para los servicios Docker (e.g., `DB_HOST=timescaledb`, `KAFKA_BROKER=kafka:9092`).
  3. Ejecuta `docker-compose up -d --build`.

---

## Ejecución del Proyecto (Modo Local)
Asegúrate de tener las variables de entorno configuradas para el modo local (ver sección "Modo de Ejecución Local").

1.  **Establecer PYTHONPATH (si es necesario):**
    Dependiendo de tu IDE o cómo ejecutes los scripts, puede que necesites añadir el directorio raíz del proyecto al `PYTHONPATH` para que los módulos `src.*` se encuentren correctamente.
    ```bash
    export PYTHONPATH="${PYTHONPATH}:/ruta/completa/al/directorio/real-time-kpi-monitor"
    # O ejecútalo antes de cada comando: PYTHONPATH="${PYTHONPATH}:$(pwd)" python scripts/init_db.py
    ```

2.  **Inicializar la base de datos SQLite:**
    Este comando creará el archivo de base de datos SQLite (e.g., `./local_kpi_monitor.db`) y las tablas.
    ```bash
    python scripts/init_db.py
    ```

3.  **Ejecutar el Simulador de Sensores (salida a archivo):**
    Esto generará datos de ejemplo en un archivo JSONL. El número de iteraciones puede ser controlado con `SIMULATION_MAX_ITERATIONS`.
    ```bash
    python scripts/simulate_sensors.py
    ```

4.  **Ejecutar el Proceso ETL (entrada desde archivo):**
    Esto leerá los datos del archivo JSONL y los cargará en la base de datos SQLite.
    ```bash
    python src/etl.py
    ```

5.  **Ejecutar el Servicio de Alertas (FastAPI):**
    El servicio de alertas se puede ejecutar localmente. Utilizará la base de datos SQLite configurada.
    ```bash
    # Opción 1: Usando el ejecutable de uvicorn (si está en PATH o ~/.local/bin/uvicorn)
    uvicorn src.alerts.alert_service:app --host 0.0.0.0 --port 8000 --reload
    # Opción 2: Usando python -m uvicorn
    # python -m uvicorn src.alerts.alert_service:app --host 0.0.0.0 --port 8000 --reload
    ```
    Una vez iniciado, puedes acceder a la documentación interactiva de la API en `http://localhost:8000/docs`.

---

## Fases y Workflow Git
(Se mantiene la estructura original del workflow Git)
1. **Ramas**: `main` (estable), `dev` (desarrollo), `feature/<nombre>` (cada nueva funcionalidad).
2. **Commits atómicos**: 1 cambio por commit, mensaje claro (`feat:`, `fix:`, `docs:`, etc.).
3. **Pull Requests**: de `feature/...` a `dev`, con revisión de código y tests.
4. **Merge a main**: desde `dev` vía GitHub Flow cuando `dev` esté estable.
5. **Etiquetas**: `v1.0.0`, `v1.1.0`, etc., para releases.

---

## Testing
- Las pruebas automatizadas están configuradas para usar el entorno local con SQLite.
- Asegúrate de tener las dependencias de desarrollo instaladas (`pip install -r requirements.txt` debería cubrirlo si `pytest` está allí).
- Ejecuta todas las pruebas localmente:
  ```bash
  pytest -v
  ```
- Ubicación de tests: carpeta `tests/`.
- Cobertura mínima (objetivo original): 80% en unitarias para módulos clave (`ingestor.py`, `kpi_engine.py`). La cobertura actual puede variar.

---

## CI/CD con GitHub Actions
- Archivo principal: `.github/workflows/ci.yml`.
- Workflow incluye (o está planeado para incluir):
  1. Build de imagen Docker (actualmente podría fallar por tamaño si el runner de GH Actions tiene limitaciones similares).
  2. Ejecución de `pytest` (configurado para SQLite).
  3. Linter (flake8).
  4. Publicación de documentación con MkDocs en GitHub Pages (si `mkdocs.yml` y `docs/` están configurados).
  5. Tagging automático en `main`.

---

## Limitaciones del Entorno Actual
Debido a las restricciones de espacio en disco encontradas en el entorno de desarrollo y pruebas donde se gestó gran parte de este proyecto:
- **Arquitectura Completa no Verificada:** La integración completa con Kafka, TimescaleDB y Apache Airflow, tal como se diseñó en la arquitectura objetivo, no pudo ser implementada ni probada.
- **Pruebas de Rendimiento:** No se realizaron pruebas de rendimiento en un entorno distribuido o con grandes volúmenes de datos.
- **Modo Local como Alternativa:** Las funcionalidades principales (simulación de datos, ETL, cálculo de KPIs, servicio de alertas) han sido verificadas en un modo local utilizando archivos JSONL para el intercambio de datos y SQLite como base de datos.
- **Configuraciones Docker:** Los archivos `Dockerfile` y `docker-compose.yml` proporcionados en el repositorio reflejan una configuración simplificada (sin Airflow) que podría servir de base para un despliegue en un entorno con más recursos, pero que también falló en el entorno de desarrollo actual por falta de espacio.

---

## Contribución
1. Crea una rama a partir de `dev`:
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/nueva-funcionalidad
   ```
2. Desarrolla tu funcionalidad y añade tests.
3. Asegúrate de pasar `pytest` y que el linter no marque errores.
4. Haz PR a `dev` describiendo los cambios.

---

## Licencia
Este proyecto está bajo la licencia MIT. Revisa el archivo `LICENSE` (si existe) para más detalles.

---

> **Autor:** Gonzalo Cisterna Salinas (`GzoC`)  
> **Contacto:** cisternasalinasg@gmail.com
