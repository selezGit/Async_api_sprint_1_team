import os
from logging import config as logging_config

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv('PROJECT_NAME', 'movies')

# Настройки Redis cluster
# для кластера достаточно указания имени имени ноды,
# можно указать одну или сразу все
REDIS_HOST = os.getenv('REDIS_HOST', ["redis://redis-node-0",
                                      "redis://redis-node-1",
                                      "redis://redis-node-2",
                                      "redis://redis-node-3",
                                      "redis://redis-node-4",
                                      "redis://redis-node-5",
                                      ])


# Настройки Elasticsearch
ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'elasticsearch')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
