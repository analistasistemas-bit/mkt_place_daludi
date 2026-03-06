"""
Logging estruturado JSON conforme CLAUDE.md.
Todo log deve incluir: tenant_id, job_id, service, level, message.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class StructuredJsonFormatter(logging.Formatter):
    """Formatter que gera logs em JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Campos contextuais (injetados via extra)
        for field in ("tenant_id", "job_id", "service", "user_id", "request_id"):
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = str(value)

        # Exceção
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        # Dados extras customizados
        extra_data = getattr(record, "extra_data", None)
        if extra_data and isinstance(extra_data, dict):
            log_data["data"] = extra_data

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(
    level: str = "INFO",
    service_name: str = "api",
) -> logging.Logger:
    """Configura logging estruturado JSON para o serviço."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)

    # Não propagar para o root logger
    logger.propagate = False

    return logger


def get_logger(
    service: str,
    tenant_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> logging.LoggerAdapter:
    """Retorna um LoggerAdapter com contexto (tenant_id, job_id, service)."""
    logger = logging.getLogger(service)

    if not logger.handlers:
        setup_logging(service_name=service)

    extra: dict[str, Any] = {"service": service}
    if tenant_id:
        extra["tenant_id"] = tenant_id
    if job_id:
        extra["job_id"] = job_id

    return logging.LoggerAdapter(logger, extra)
