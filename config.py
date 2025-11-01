import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Bot token
    BOT_TOKEN = os.getenv('BOT_TOKEN', '8045456928:AAGWY-ehDy1cRMeVO8orNJ1egO6VEAwU6qY')

    # OpenRouter API
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY',
                                   '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')
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    # Admin ID lari
    ADMIN_IDS = [5842512278]

    # Available AI Models
    AI_MODELS = {
        "openai/gpt-3.5-turbo": "🤖 GPT-3.5 Turbo",
        "openai/gpt-4": "🚀 GPT-4",
        "anthropic/claude-3-haiku:beta": "⚡ Claude 3 Haiku",
        "google/gemini-pro": "💎 Gemini Pro",
        "meta-llama/llama-3-70b-instruct": "🦙 Llama 3 70B",
        "mistralai/mistral-7b-instruct": "🌪️ Mistral 7B"
    }

    # Model settings
    MODEL_SETTINGS = {
        "openai/gpt-3.5-turbo": {"max_tokens": 2000},
        "openai/gpt-4": {"max_tokens": 2000},
        "anthropic/claude-3-haiku:beta": {"max_tokens": 2000},
        "google/gemini-pro": {"max_tokens": 2000},
        "meta-llama/llama-3-70b-instruct": {"max_tokens": 2000},
        "mistralai/mistral-7b-instruct": {"max_tokens": 2000}
    }

    # Free user limits
    FREE_DAILY_LIMIT = 20
    FREE_MONTHLY_LIMIT = 200
    FREE_MODELS = ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku:beta"]

    # Premium user limits
    PREMIUM_DAILY_LIMIT = 1000
    PREMIUM_MONTHLY_LIMIT = 30000
    PREMIUM_MODELS = list(AI_MODELS.keys())

    # Unlimited user limits (adminlar uchun)
    UNLIMITED_DAILY_LIMIT = 99999
    UNLIMITED_MONTHLY_LIMIT = 999999

    # Payment settings
    PAYMENT_AMOUNTS = {
        "1oy": 50000,
        "3oy": 120000,
        "6oy": 200000,
        "12oy": 350000
    }

    DEFAULT_MODEL = "openai/gpt-3.5-turbo"

    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2
