"""
Worker Entrypoint — Inicializa o worker RQ customizado e os imports de jobs para registro.
"""

import os
import sys
import threading
import time

import httpx
from redis import Redis
from rq import Queue, Worker

# Configurar logging estruturado
from packages.shared.logging import get_logger

logger = get_logger("worker.main")

KEEP_ALIVE_URL = "https://mktplace-worker.onrender.com/"
KEEP_ALIVE_INTERVAL_SECONDS = 240
KEEP_ALIVE_TIMEOUT_SECONDS = 10

# Garantir que o path inclua a raiz para encontrar "apps" e "packages"
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Para registrar as funções no worker, precisam ser importadas
try:
    from apps.worker.jobs import (
        import_job,
        resolve_job,
        generate_job,
        publish_job,
        discovery_job
    )
    logger.info("Jobs importados para registro no Worker RQ.")
except ImportError as e:
    logger.warning(f"Alguns handlers ainda não existem (normal durante build iterativa): {e}")


def ping_keep_alive(*, url: str, timeout_seconds: int) -> None:
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        client.get(url)


def keep_alive_loop(
    *,
    interval_seconds: int = KEEP_ALIVE_INTERVAL_SECONDS,
    url: str = KEEP_ALIVE_URL,
    timeout_seconds: int = KEEP_ALIVE_TIMEOUT_SECONDS,
    sleep_fn=time.sleep,
    ping_fn=ping_keep_alive,
) -> None:
    while True:
        sleep_fn(interval_seconds)
        try:
            ping_fn(url=url, timeout_seconds=timeout_seconds)
            logger.info(f"Keep-alive enviado para {url}")
        except Exception as exc:
            logger.warning(f"Falha no keep-alive do worker para {url}: {exc}")


def start_keep_alive_thread() -> None:
    thread = threading.Thread(
        target=keep_alive_loop,
        kwargs={
            "interval_seconds": KEEP_ALIVE_INTERVAL_SECONDS,
            "url": KEEP_ALIVE_URL,
            "timeout_seconds": KEEP_ALIVE_TIMEOUT_SECONDS,
        },
        daemon=True,
        name="render-worker-keep-alive",
    )
    thread.start()
    logger.info(f"Thread de keep-alive iniciada para {KEEP_ALIVE_URL}")


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    start_keep_alive_thread()

    logger.info(f"Conectando ao Redis em {redis_url}...")
    redis_conn = Redis.from_url(redis_url)

    queues = ["default", "high", "low"]
    
    logger.info(f"Iniciando Worker RQ escutando nas filas: {queues}")
    
    worker_queues = [Queue(name, connection=redis_conn) for name in queues]
    worker = Worker(worker_queues, connection=redis_conn)
    worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()
