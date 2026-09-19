from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    vector_top_k: int = 5
    graph_top_k: int = 5
    max_context_chars: int = 16000
    max_question_chars: int = 2000
    max_answer_chars: int = 6000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
