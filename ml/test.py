from . import api_key
from .ChatClient import GeminiFlash

if api_key is None:
    error_message = (
        "API-ключ не установлен. Пожалуйста, установите переменную LLM_API_KEY в вашей среде. "
        "Для этого создайте файл .env в корне проекта и добавьте в конец строку вида "
        "LLM_API_KEY=<api_key> (API-ключ указывается без кавычек)."
    )
    raise ValueError(error_message)

llm = GeminiFlash(api_key)

completion = llm.create_completion(llm.make_user_promt('Как поживаешь?'))

print(completion)