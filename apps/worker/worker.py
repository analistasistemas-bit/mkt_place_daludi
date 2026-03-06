"""
Worker Entrypoint — Inicializa o worker RQ customizado e os imports de jobs para registro.
"""

import os
import sys
from redis import Redis
from rq import Worker, Queue, Connection

# Configurar logging estruturado
from packages.shared.logging import get_logger

logger = get_logger("worker.main")

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


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    logger.info(f"Conectando ao Redis em {redis_url}...")
    redis_conn = Redis.from_url(redis_url)

    queues = ["default", "high", "low"]
    
    logger.info(f"Iniciando Worker RQ escutando nas filas: {queues}")
    
    with Connection(redis_conn):
        worker = Worker(map(Queue, queues))
        worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()
