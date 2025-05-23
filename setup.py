"""Setup file for the KPI Monitor package."""
from setuptools import setup, find_packages

setup(
    name="real_time_kpi_monitor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "paho-mqtt",
        "psycopg2-binary",
        "sqlalchemy",
        "python-dotenv",
        "loguru",
        "pytest",
        "httpx"
    ],
)
