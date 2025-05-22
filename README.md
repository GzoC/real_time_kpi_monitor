# Sistema Automatizado de Monitoreo de Calidad y KPI de Producción Industrial en Tiempo Real

## Descripción
Este proyecto implementa una **plataforma completa** para el monitoreo en tiempo real de indicadores clave de desempeño (KPIs) y calidad en procesos industriales. Captura datos desde sensores (PLC, MES), los procesa automáticamente, calcula métricas como OEE, tasa de rechazo y MTBF/MTTR, y los presenta en un dashboard interactivo. Además, envía alertas cuando los KPIs exceden umbrales definidos.

> Combina tu experiencia en automatización industrial con habilidades de Data Analytics; diseñado para que un agente IA en VS Code pueda desarrollarlo paso a paso.

---

## Tabla de contenidos
1. [Tecnologías y Herramientas](#tecnologías-y-herramientas)
2. [Arquitectura de alto nivel](#arquitectura-de-alto-nivel)
3. [Requisitos Previos](#requisitos-previos)
4. [Estructura del Repositorio](#estructura-del-repositorio)
5. [Entorno de Desarrollo en VS Code](#entorno-de-desarrollo-en-vs-code)
6. [Instalación y Configuración](#instalación-y-configuración)
7. [Ejecución del Proyecto](#ejecución-del-proyecto)
8. [Fases y Workflow Git](#fases-y-workflow-git)
9. [Testing](#testing)
10. [CI/CD con GitHub Actions](#ci-cd-con-github-actions)
11. [Contribución](#contribución)
12. [Licencia](#licencia)

---

## Tecnologías y Herramientas
- **Lenguaje:** Python 3.11
- **Base de datos:** TimescaleDB (PostgreSQL con extensión time-series)
- **Broker de mensajes:** Kafka o Redpanda
- **Orquestación ETL:** Apache Airflow (o Prefect)
- **Visualización:** Power BI o Tableau (DirectQuery)
- **Framework web:** FastAPI (servicio de alertas)
- **Contenedores:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Control de versiones:** Git
- **Documentación:** MkDocs + Material for MkDocs

---

## Arquitectura de alto nivel
```plaintext
 PLCs ──▶ [Ingestor MQTT/OPC UA] ──▶ [Kafka/Redpanda] ──▶ [TimescaleDB]
                                                  │
                                                  ├─▶ [Airflow DAGs] ──▶ [ETL / limpieza]
                                                  ├─▶ [KPI Engine (Python)]
                                                  └─▶ [Alert Service (FastAPI)]

                                                  ▼
                                           [Power BI / Tableau]
```  

---

## Requisitos Previos
- Docker y Docker Compose instalados
- VS Code con extensión Remote - Containers (opcional)
- Git instalado y configurado (usuario y correo)
- Cuenta de GitHub (para repositorio y Actions)
- Power BI Desktop o Tableau Public para visualizar dashboards

---

## Estructura del Repositorio
```
real-time-kpi-monitor/
├── .github/
│   └── workflows/          # Definición de CI/CD
├── docs/                   # MkDocs: documentación del proyecto
├── src/
│   ├── ingestor.py         # Captura datos MQTT/OPC UA → Kafka
│   ├── etl.py              # Tareas de limpieza y carga a DB
│   ├── kpi_engine.py       # Cálculo de KPIs (OEE, MTBF, etc.)
│   ├── alert_service.py    # Servicio FastAPI para alertas
│   └── config.py           # Parámetros y variables de entorno
├── tests/                  # Pruebas unitarias e integración
│   ├── test_ingestor.py
│   ├── test_etl.py
│   ├── test_kpi_engine.py
│   └── test_alert_service.py
├── airflow/                # Carpeta para DAGs y configuración Airflow
│   └── dags/
├── docker-compose.yml      # Definición de servicios Docker
├── Dockerfile              # Imagen para servicios Python
├── .env.template           # Variables de entorno de ejemplo
├── mkdocs.yml              # Configuración MkDocs
├── README.md               # Este archivo
└── .devcontainer.json      # Configuración de contenedor VS Code
```

---

## Entorno de Desarrollo en VS Code
1. Abre el proyecto en VS Code.
2. Instala la extensión **Remote - Containers**.
3. Abre la paleta (`Ctrl+Shift+P`) y ejecuta `Remote-Containers: Reopen in Container`.
4. VS Code creará un contenedor con Python 3.11 y todas las dependencias definidas en `Dockerfile` y `devcontainer.json`.

> El agente IA podrá usar este contenedor para ejecutar tareas, instalar dependencias y ejecutar comandos sin salir de VS Code.

---

## Instalación y Configuración
1. Clona el repositorio:
   ```bash
   git clone https://github.com/GzoC/real-time-kpi-monitor.git
   cd real-time-kpi-monitor
   ```
2. Copia y ajusta variables de entorno:
   ```bash
   cp .env.template .env
   # Edita .env con credenciales y parámetros de tu entorno
   ```
3. Inicia servicios Docker:
   ```bash
   docker-compose up -d
   ```
4. Verifica que los contenedores estén corriendo:
   ```bash
   docker-compose ps
   ```
5. Inicializa Airflow (si aplica):
   ```bash
   docker exec -it airflow_webserver airflow db init
   docker exec -it airflow_webserver airflow users create --username admin --role Admin --firstname Nombre --lastname Apellido --email admin@example.com
   ```

---

## Ejecución del Proyecto
- **Ingestor:**
  ```bash
  docker exec -it kpi_app python -m src.ingestor
  ```
- **ETL y KPI Engine via Airflow:** abre UI en `http://localhost:8080`, activa y ejecuta DAG `kpi_pipeline`.
- **Alert Service:**
  ```bash
  docker exec -it kpi_app uvicorn src.alert_service:app --host 0.0.0.0 --port 8000
  ```
- **Dashboard:**
  1. Abre Power BI Desktop.
  2. Conecta mediante DirectQuery apuntando a tu TimescaleDB.
  3. Carga el archivo `dashboard/powerbi/report.pbit`.

---

## Fases y Workflow Git
1. **Ramas**: `main` (estable), `dev` (desarrollo), `feature/<nombre>` (cada nueva funcionalidad).
2. **Commits atómicos**: 1 cambio por commit, mensaje claro (`feat:`, `fix:`, `docs:`, etc.).
3. **Pull Requests**: de `feature/...` a `dev`, con revisión de código y tests.
4. **Merge a main**: desde `dev` vía GitHub Flow cuando `dev` esté estable.
5. **Etiquetas**: `v1.0.0`, `v1.1.0`, etc., para releases.

---

## Testing
- Ejecuta todas las pruebas localmente antes de cada PR:
  ```bash
  docker exec -it kpi_app pytest --maxfail=1 --disable-warnings -q
  ```
- Ubicación de tests: carpeta `tests/`.
- Cobertura mínima: 80% en unitarias para módulos clave (`ingestor.py`, `kpi_engine.py`).

---

## CI/CD con GitHub Actions
- Archivo principal: `.github/workflows/ci.yml`.
- Workflow incluye:
  1. Build de imagen Docker.
  2. Ejecución de `pytest`.
  3. Linter (flake8).
  4. Despliegue a entorno de testing (opcional).
  5. Publicación de documentación con MkDocs en GitHub Pages.
  6. Tagging automático en `main`.

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
Este proyecto está bajo la licencia MIT. Revisa el archivo [LICENSE](LICENSE) para más detalles.

---

> **Autor:** Gonzalo Cisterna Salinas (`GzoC`)  
> **Contacto:** cisternasalinasg@gmail.com
