"""
Worker Entrypoint — Inicializa o worker RQ customizado e os imports de jobs para registro.
"""

import os
import sys
import threading
import time
from typing import Any, Optional

import httpx
from redis import Redis
from rq import Queue, Worker

# Configurar logging estruturado
from packages.shared.logging import get_logger
from apps.api.deps import get_supabase_admin_client

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
    redis_conn: Optional[Redis] = None,
    supabase_client: Optional[Any] = None,
) -> None:
    while True:
        # 1. Keep-alive HTTP (para o Render)
        try:
            ping_fn(url=url, timeout_seconds=timeout_seconds)
            logger.info(f"Keep-alive HTTP enviado para {url}")
        except Exception as exc:
            logger.warning(f"Falha no keep-alive HTTP para {url}: {exc}")

        # 2. Keep-alive Redis (para o Upstash)
        if redis_conn:
            try:
                redis_conn.ping()
                logger.info("Keep-alive Redis PING enviado com sucesso para o Upstash.")
            except Exception as exc:
                logger.warning(f"Falha no keep-alive Redis para o Upstash: {exc}")

        # 3. Keep-alive Supabase (Postgres)
        if supabase_client:
            try:
                # Uma query simples para garantir tráfego no banco
                supabase_client.table("tenants").select("id").limit(1).execute()
                logger.info("Keep-alive Supabase (Postgres) enviado com sucesso.")
            except Exception as exc:
                logger.warning(f"Falha no keep-alive Supabase para o Postgres: {exc}")

        sleep_fn(interval_seconds)


def start_keep_alive_thread(
    redis_conn: Optional[Redis] = None, 
    supabase_client: Optional[Any] = None
) -> None:
    thread = threading.Thread(
        target=keep_alive_loop,
        kwargs={
            "interval_seconds": KEEP_ALIVE_INTERVAL_SECONDS,
            "url": KEEP_ALIVE_URL,
            "timeout_seconds": KEEP_ALIVE_TIMEOUT_SECONDS,
            "redis_conn": redis_conn,
            "supabase_client": supabase_client,
        },
        daemon=True,
        name="render-worker-keep-alive",
    )
    thread.start()
    status_msg = (
        f"Thread de keep-alive iniciada (HTTP: {KEEP_ALIVE_URL}, "
        f"Redis: {'Ativo' if redis_conn else 'Inativo'}, "
        f"Supabase: {'Ativo' if supabase_client else 'Inativo'})"
    )
    logger.info(status_msg)


def main():
    from packages.shared.config import get_settings
    settings = get_settings()
    redis_url = settings.redis_url
    
    logger.info(f"Conectando ao Redis em {redis_url}...")
    redis_conn = Redis.from_url(redis_url)

    # Obter client admin do Supabase para o heartbeat
    supabase_client = None
    try:
        supabase_client = get_supabase_admin_client()
        logger.info("Client Supabase Admin conectado para heartbeat.")
    except Exception as e:
        logger.warning(f"Não foi possível conectar ao Supabase para heartbeat: {e}")

    # Inicia a thread de monitoramento passando Redis e Supabase
    start_keep_alive_thread(redis_conn=redis_conn, supabase_client=supabase_client)

    queues = ["default", "high", "low"]
    
    logger.info(f"Iniciando Worker RQ escutando nas filas: {queues}")
    
    worker_queues = [Queue(name, connection=redis_conn) for name in queues]
    from rq import SimpleWorker
    worker_class_name = os.getenv("RQ_WORKER_CLASS", "Worker")
    worker_class = SimpleWorker if worker_class_name == "SimpleWorker" else Worker

    worker = worker_class(worker_queues, connection=redis_conn)
    worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()
