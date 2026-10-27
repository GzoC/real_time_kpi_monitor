FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 KPI_DB_PATH=/data/monitor.db
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home monitor \
    && mkdir /data && chown monitor:monitor /data
USER monitor
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3)"
ENTRYPOINT ["kpi-monitor"]
CMD ["demo", "--host", "0.0.0.0", "--port", "8000"]
