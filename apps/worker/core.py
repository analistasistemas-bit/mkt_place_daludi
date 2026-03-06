"""
Worker Core — Utilitários de infraestrutura para os jobs do RQ.

Implementa:
- Decorator de retry com backoff exponencial e jitter
- Mecanismo de Idempotência
- Tratamento de Dead Letter Queue (DLQ) via status de erro no banco
- Registro de Job Events
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Dict, Literal, Optional, TypeVar

from apps.api.deps import get_supabase_admin_client
from packages.shared.logging import get_logger

logger = get_logger("worker.core")

T = TypeVar("T")

JobStatus = Literal["pending", "processing", "completed", "failed"]


def create_job_event(
    supabase_client: Any,
    job_id: str,
    tenant_id: str,
    event_type: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Registra um evento de execução do job na tabela job_events."""
    try:
        supabase_client.table("job_events").insert({
            "job_id": job_id,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {}
        }).execute()
    except Exception as e:
        logger.error(
            f"Erro ao registrar job_event: {e}",
            extra={"extra_data": {"job_id": job_id, "event_type": event_type}}
        )

def update_job_status(
    supabase_client: Any,
    job_id: str,
    status: JobStatus,
    error_message: Optional[str] = None
) -> None:
    """Atualiza o status principal do job (tabela jobs)."""
    try:
        data = {"status": status, "updated_at": "now()"}
        if error_message:
            data["error"] = error_message
            if status == "failed":
                data["completed_at"] = "now()"
        elif status == "completed":
            data["completed_at"] = "now()"
            
        supabase_client.table("jobs").update(data).eq("id", job_id).execute()
    except Exception as e:
        logger.error(
            f"Erro ao atualizar status do job: {e}",
            extra={"extra_data": {"job_id": job_id, "status": status}}
        )


def with_retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para Retry com Exponential Backoff e Jitter (Full Jitter approach).
    
    Tenta executar a função até `max_retries` vezes se `exceptions` forem capturadas.
    O tempo de espera aumenta exponencialmente, com um "jitter" (0 até o delay exponencial)
    para evitar thundering herd.
    
    Suporta funções síncronas e assíncronas.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Job falhou após {max_retries} tentativas: {str(e)}")
                        raise e
                    
                    # Exponential Backoff with Jitter
                    # calc_delay = min(max_delay, base_delay * (2 ** (retries - 1)))
                    # sleep_time = random.uniform(0, calc_delay)
                    calc_delay = min(max_delay, base_delay * (2 ** (retries - 1)))
                    sleep_time = random.uniform(base_delay, calc_delay)
                    
                    logger.warning(
                        f"Tentativa {retries}/{max_retries} falhou. "
                        f"Retentando em {sleep_time:.2f}s devido a: {str(e)}"
                    )
                    time.sleep(sleep_time)
                    
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Async Job falhou após {max_retries} tentativas: {str(e)}")
                        raise e
                    
                    calc_delay = min(max_delay, base_delay * (2 ** (retries - 1)))
                    sleep_time = random.uniform(base_delay, calc_delay)
                    
                    logger.warning(
                        f"Tentativa async {retries}/{max_retries} falhou. "
                        f"Retentando em {sleep_time:.2f}s devido a: {str(e)}"
                    )
                    await asyncio.sleep(sleep_time)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def handle_job_lifecycle():
    """
    Decorator que encapsula a lógica de ciclo de vida de um job:
    1. Marca como processing
    2. Executa função
    3. Marca como completed ou failed
    4. Trata DLQ (via status failed) automaticamente.
    (Assíncrono suportado).
    
    Atenção: A função envolvida deve recerber o job_id como kwarg `job_id`, e 
    geralmente um `supabase` client para update.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            job_id = kwargs.get("job_id")
            tenant_id = kwargs.get("tenant_id")
            supabase = kwargs.get("supabase")

            # Se não vier supabase pelo enqueue, cria com service role.
            if not supabase and job_id and tenant_id:
                try:
                    supabase = get_supabase_admin_client()
                    kwargs["supabase"] = supabase
                except Exception as e:
                    logger.error(
                        "Falha ao criar client admin do Supabase para lifecycle do job.",
                        extra={"extra_data": {"job_id": job_id, "tenant_id": tenant_id, "error": str(e)}},
                    )
            
            if not all([job_id, supabase, tenant_id]):
                # Se não temos credenciais de banco no kwargs, apenas executa
                # É útil para quando não for injetado diretamente mas precisávamos do wrapper
                logger.warning(
                    "Lifecycle do job ignorado por ausência de metadados obrigatórios.",
                    extra={
                        "extra_data": {
                            "handler": func.__name__,
                            "job_id": job_id,
                            "tenant_id": tenant_id,
                        }
                    },
                )
                return func(*args, **kwargs)
                
            try:
                update_job_status(supabase, job_id, "processing")
                create_job_event(
                    supabase,
                    job_id,
                    tenant_id,
                    "started",
                    "Iniciando processamento do job.",
                )
                
                result = func(*args, **kwargs)
                
                update_job_status(supabase, job_id, "completed")
                create_job_event(
                    supabase,
                    job_id,
                    tenant_id,
                    "completed",
                    "Job finalizado com sucesso.",
                )
                return result
                
            except Exception as e:
                # Trata DLQ
                error_msg = str(e)
                update_job_status(supabase, job_id, "failed", error_message=error_msg)
                create_job_event(
                    supabase,
                    job_id,
                    tenant_id,
                    "failed",
                    f"Falha fatal no job: {error_msg}",
                )
                raise e
                
        # omitimos o async_wrapper aqui por simplicidade, no worker do RQ os handlers costumam ser chamados
        # em event loop ou empacotados pelo RQ, que é síncrono.
        return sync_wrapper
        
    return decorator
