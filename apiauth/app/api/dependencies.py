"""Dependency injection for FastAPI.

Provides dependency injection for use cases and adapters.
"""

from functools import lru_cache

from app.application.check_rate_limit import CheckRateLimitUseCase
from app.application.process_request import ProcessRequestUseCase
from app.application.validate_token import ValidateTokenUseCase
from app.infrastructure.postgres_adapter import PostgresAdapter
from app.infrastructure.redis_adapter import RedisAdapter


class Container:
    """Dependency injection container.

    Holds references to adapters and use cases.
    Lazily initializes connections.
    """

    def __init__(self):
        self._postgres: PostgresAdapter | None = None
        self._redis: RedisAdapter | None = None

    def get_postgres(self, connection_string: str) -> PostgresAdapter:
        """Get or create PostgreSQL adapter.

        Args:
            connection_string: PostgreSQL connection URL

        Returns:
            PostgresAdapter instance
        """
        if self._postgres is None:
            self._postgres = PostgresAdapter(connection_string)
        return self._postgres

    def get_redis(self, redis_url: str) -> RedisAdapter:
        """Get or create Redis adapter.

        Args:
            redis_url: Redis connection URL

        Returns:
            RedisAdapter instance
        """
        if self._redis is None:
            self._redis = RedisAdapter(redis_url)
        return self._redis

    def get_validate_token(self, connection_string: str, redis_url: str) -> ValidateTokenUseCase:
        """Get ValidateTokenUseCase with PostgreSQL + Redis dependencies."""
        postgres = self.get_postgres(connection_string)
        redis = self.get_redis(redis_url)
        return ValidateTokenUseCase(postgres, redis)

    def get_check_rate_limit(
        self, redis_url: str, window_seconds: int = 60
    ) -> CheckRateLimitUseCase:
        """Get CheckRateLimitUseCase with dependencies.

        Args:
            redis_url: Redis connection URL
            window_seconds: Rate limit window size

        Returns:
            CheckRateLimitUseCase instance
        """
        redis = self.get_redis(redis_url)
        return CheckRateLimitUseCase(redis, window_seconds)

    def get_process_request(
        self, connection_string: str, redis_url: str
    ) -> ProcessRequestUseCase:
        """Get ProcessRequestUseCase with dependencies.

        Args:
            connection_string: PostgreSQL connection URL
            redis_url: Redis connection URL

        Returns:
            ProcessRequestUseCase instance
        """
        validate_token = self.get_validate_token(connection_string, redis_url)
        check_rate_limit = self.get_check_rate_limit(redis_url)
        return ProcessRequestUseCase(validate_token, check_rate_limit)


container = Container()
