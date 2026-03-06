"""
Configuração centralizada via pydantic-settings.
Todas as variáveis de ambiente do CLAUDE.md mapeadas aqui.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuração global do aplicativo carregada de variáveis de ambiente."""

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str = Field(..., description="URL do projeto Supabase")
    supabase_anon_key: str = Field(..., description="Anon key do Supabase")
    supabase_service_role_key: str = Field(
        ..., description="Service role key do Supabase"
    )

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="URL de conexão do Redis"
    )

    # ── Mercado Livre ─────────────────────────────────────────
    ml_client_id: Optional[str] = Field(
        default=None, description="Client ID do Mercado Livre"
    )
    ml_client_secret: Optional[str] = Field(
        default=None, description="Client Secret do Mercado Livre"
    )
    ml_redirect_uri: Optional[str] = Field(
        default=None, description="Redirect URI do Mercado Livre"
    )

    # ── LLM ───────────────────────────────────────────────────
    llm_provider: str = Field(
        default="stub", description="Provedor LLM: openai | anthropic | stub"
    )
    llm_api_key: Optional[str] = Field(default=None, description="API key do LLM")
    llm_model: str = Field(
        default="gpt-4o-mini", description="Modelo LLM a usar"
    )

    # ── Embeddings ────────────────────────────────────────────
    embeddings_provider: str = Field(
        default="stub", description="Provedor de embeddings: openai | stub"
    )
    embeddings_api_key: Optional[str] = Field(
        default=None, description="API key do provedor de embeddings"
    )

    # ── App ────────────────────────────────────────────────────
    api_secret_key: str = Field(
        default="dev-secret-key-change-me",
        description="Secret key para tokens JWT",
    )
    environment: str = Field(
        default="local", description="Ambiente: local | staging | production"
    )
    api_host: str = Field(default="0.0.0.0", description="Host da API")
    api_port: int = Field(default=8000, description="Porta da API")
    debug: bool = Field(default=True, description="Modo debug")

    # ── Worker ────────────────────────────────────────────────
    worker_concurrency: int = Field(
        default=4, description="Concorrência do worker RQ"
    )
    worker_queues: str = Field(
        default="default,high,low",
        description="Filas do RQ separadas por vírgula",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_local(self) -> bool:
        return self.environment == "local"

    @property
    def worker_queue_list(self) -> list[str]:
        return [q.strip() for q in self.worker_queues.split(",")]


def get_settings() -> Settings:
    """Factory para obter instância de Settings (cacheable)."""
    return Settings()
