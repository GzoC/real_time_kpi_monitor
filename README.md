# Sistema Automatizado de Monitoreo de Calidad y KPIs de Producción Industrial en Tiempo Real

---

## 📊 Visión General

Este proyecto implementa una solución completa para el monitoreo en tiempo real de indicadores clave de producción industrial (KPIs) y métricas de calidad, integrando tecnologías modernas de Data Analytics y automatización. Permite recopilar datos desde sensores o sistemas MES/ERP, procesarlos automáticamente, calcular KPIs relevantes y visualizarlos en dashboards interactivos, además de activar alertas automatizadas si algún valor crítico es detectado.

---

## 🎯 Objetivos del Proyecto

- **Captura de datos en tiempo real** desde fuentes industriales (sensores, PLC, archivos MES/ERP).
- **Procesamiento automático y cálculo de KPIs** de producción y calidad (OEE, tasa de rechazos, MTBF, etc.).
- **Visualización dinámica e interactiva** mediante dashboards en Power BI o Tableau.
- **Alertas automáticas** por correo/chat ante eventos críticos o anomalías.
- **Despliegue portable y reproducible** con Docker y buenas prácticas de DevOps.
- **Documentación clara y modular** para facilitar aprendizaje, mantenimiento y replicabilidad.

---

## 🏗️ Arquitectura del Sistema

```mermaid
flowchart LR
  A[Fuente de datos\n(Sensores, MES, CSV)] --> B[Ingesta\nde datos]
  B --> C[Base de datos\ntemporal\n(PostgreSQL/TimescaleDB)]
  C --> D[Procesamiento\nCálculo de KPIs]
  D --> E[Dashboard\n(Power BI/Tableau)]
  D --> F[Alertas\nAutomatizadas]
````

---

## ⚙️ Stack Tecnológico

* **Python 3.11+** (pandas, NumPy, SQLAlchemy)
* **PostgreSQL / TimescaleDB** (almacenamiento eficiente de series de tiempo)
* **MQTT / CSV** (fuentes de datos simuladas o reales)
* **Power BI / Tableau** (visualización de KPIs)
* **FastAPI** (servicio de alertas)
* **Docker y docker-compose** (entorno reproducible)
* **GitHub Actions** (automatización CI/CD)
* **MkDocs** (documentación profesional del proyecto)

---

## 🗂️ Estructura del Proyecto

```plaintext
real_time_kpi_monitor/
│
├── src/                  # Código fuente principal
│   ├── ingest/           # Ingesta de datos (MQTT/CSV)
│   ├── db/               # Conexión y manejo de la base de datos
│   ├── processing/       # Procesamiento y cálculo de KPIs
│   ├── alerts/           # Lógica de alertas automáticas
│   └── config.py         # Configuración global
├── notebooks/            # Notebooks de análisis y pruebas
├── data/                 # Datos de ejemplo (CSV)
├── dashboards/           # Dashboards Power BI/Tableau
├── tests/                # Pruebas automáticas
├── docker/               # Configuración avanzada de Docker
├── docs/                 # Documentación y recursos
├── .env.template         # Variables de entorno de ejemplo
├── requirements.txt      # Dependencias Python
├── docker-compose.yml    # Orquestador de servicios
├── README.md             # Este archivo
└── Makefile              # Comandos automatizados
```

---

## 🚀 Guía de Instalación y Ejecución (Paso a Paso)

1. **Clona el repositorio**

   ```bash
   git clone https://github.com/GzoC/real_time_kpi_monitor.git
   cd real_time_kpi_monitor
   ```

2. **Configura variables de entorno**

   * Copia `.env.template` como `.env` y ajusta los parámetros según tu entorno.

3. **Construye y levanta los servicios con Docker**

   ```bash
   docker-compose up --build
   ```

   Esto instala automáticamente PostgreSQL, TimescaleDB y servicios necesarios para el pipeline de datos.

4. **Carga datos de ejemplo (opcional para pruebas)**

   * Coloca archivos CSV en la carpeta `/data` o usa el simulador MQTT (se detalla en la documentación).

5. **Accede a los dashboards**

   * Abre el archivo Power BI o Tableau desde `/dashboards` y conecta a la base PostgreSQL definida.

6. **Verifica la ejecución de alertas**

   * Configura destinatarios en el archivo de configuración y revisa la bandeja de entrada o canal de chat.

7. **(Opcional) Ejecuta notebooks de prueba y análisis**

   * Los notebooks en `/notebooks` pueden ser abiertos en Jupyter para exploración adicional.

---

## 🔍 Buenas Prácticas y Recomendaciones

* Usa ramas (`main`, `dev`, `feature/tu-nueva-funcionalidad`) para mantener el control de versiones y facilitar colaboraciones.
* Documenta cada módulo en `docs/` y mantén el README actualizado.
* Automatiza pruebas y validaciones usando los scripts de `/tests`.
* Aplica principios de seguridad: nunca subas contraseñas o credenciales reales, usa siempre archivos `.env` para variables sensibles.
* Los comandos de Docker y los scripts en el Makefile facilitan la puesta en marcha del sistema en cualquier entorno.

---

## 🛡️ Licencia y Autoría

Proyecto creado por **Gonzalo Cisterna Salinas**
GitHub: [GzoC](https://github.com/GzoC)
Contacto: [cisternasalinasg@gmail.com](mailto:cisternasalinasg@gmail.com)
Licencia: MIT

---

## 📚 Recursos y Documentación Adicional

* Documentación extendida en `/docs` y [Wiki del repositorio](./docs).
* Ejemplos de dashboards en `/dashboards`.
* Scripts de ingestión y notebooks demostrativos en `/notebooks`.

---

**¿Dudas, sugerencias o mejoras?**
¡Tus aportes y preguntas son bienvenidos vía issues de GitHub o contacto directo!

```

---

¿Deseas agregar alguna sección especial antes de continuar con la **configuración del entorno**? Si no, avanzamos directo al setup técnico.
```
