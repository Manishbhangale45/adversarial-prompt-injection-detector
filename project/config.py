import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_PATH = os.path.join(BASE_DIR, "app.db")
    MODEL_PATH = os.path.join(BASE_DIR, "models", "prompt_detector.pkl")
    DATASET_PATH = os.path.join(BASE_DIR, "prompts_dataset.csv")
    LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    MAX_CONTENT_LENGTH = 16 * 1024
