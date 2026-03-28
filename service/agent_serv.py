from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from config import GEMINI_API_KEY
from database.repo import TripRepo, UserRepo, NoteRepo
from sqlalchemy.orm import Session


class AgentService:
    """Сервис для работы с ИИ агентом Gemini."""

    def __init__(self, session: Session):
        self.session = session
        self.trip_repo = TripRepo(session)
        self.user_repo = UserRepo(session)
        self.note_repo = NoteRepo(session)

        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_user_dossier(self, user_id: int) -> str:
        """Генерация ИИ досье пользователя на основе его поездок."""
        trips = self.trip_repo.get_by_user_id(user_id)
        user = self.user_repo.get_by_id(user_id)

        username = user.username if user else "неизвестно"

        if not trips:
            return "У пользователя пока нет поездок."

        # Формируем контекст из поездок
        trips_context = "\n".join(
            f"- {trip.title}: {trip.description or 'без описания'}"
            for trip in trips
        )

        prompt = f"""
Имя пользователя: {username}

Поездки пользователя:
{trips_context}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",

                config=types.GenerateContentConfig(
                    system_instruction="Ты — персональный ассистент, который по данным о пользователе "
                        "(имя пользователя и список его поездок) формулирует на русском "
                        "дружелюбное, понятное и правдивое описание этого человека и его путешествий, "
                        "не придумывая отсутствующие факты и не упоминая технические детали БД или моделей. "
                        "Обращайся к пользователю по имени (username). "
                        "Если у пользователя пока нет поездок, скажи об этом дружелюбно и предложи создать первую поездку. "
                        "Не пиши приветствие в начале. "
                        "Не используй HTML теги в ответе."
                ),
                contents=prompt
            )
            
            # Очистка ответа от HTML тегов
            text = response.text
            if text.startswith("<!DOCTYPE") or text.startswith("<html"):
                return "⚠️ Ошибка при генерации досье. Попробуйте позже."
            
            # Удаляем HTML теги если есть
            import re
            text = re.sub(r'<[^>]+>', '', text)
            
            return text
        except genai_errors.ClientError as e:
            if e.code == 429:
                return "⚠️ Лимит запросов к ИИ исчерпан. Попробуйте позже."
            return f"⚠️ Ошибка ИИ: {e}"
        except Exception as e:
            return f"⚠️ Произошла ошибка при генерации досье: {e}"

    def generate_note_text(self, prompt: str) -> str:
        """Генерация текста заметки на основе короткого промпта пользователя."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",

                config=types.GenerateContentConfig(
                    system_instruction="Ты — помощник для создания заметок о поездках. "
                        "Пользователь вводит короткий текст или идею, а ты расширяешь её в полноценную заметку на русском языке. "
                        "Пиши кратко, информативно и дружелюбно. Не добавляй приветствий или заключений. "
                        "Просто текст заметки, который можно сохранить."
                ),
                contents=f"Создай заметку для поездки на основе: {prompt}"
            )
            return response.text
        except genai_errors.ClientError as e:
            if e.code == 429:
                return "⚠️ Лимит запросов к ИИ исчерпан. Попробуйте позже."
            return f"⚠️ Ошибка ИИ: {e}"
        except Exception as e:
            return f"⚠️ Произошла ошибка при генерации заметки: {e}"

    def generate_trip_description(self, trip_id: int) -> tuple[str | None, str | None]:
        """
        Генерация описания и эмбеддинга поездки на основе всех заметок.
        
        :return: кортеж (описание, эмбеддинг в формате JSON-строки) или (None, None) при ошибке
        """
        notes = self.note_repo.get_by_trip_id(trip_id)
        print(f"🔍 Генерация описания для поездки {trip_id}, заметок: {len(notes)}")

        if not notes:
            print(f"⚠️ Нет заметок для поездки {trip_id}")
            return None, None

        # Формируем контекст из заметок
        notes_context = "\n".join(
            f"- {note.text}"
            for note in notes
        )

        prompt = f"""
Заметки о поездке:
{notes_context}
"""

        try:
            # Генерируем описание
            print(f"🤖 Отправка запроса к ИИ для генерации описания...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",

                config=types.GenerateContentConfig(
                    system_instruction="Ты — помощник для создания описаний поездок. "
                        "На основе заметок пользователя создай краткое, информативное и дружелюбное описание поездки на русском языке. "
                        "Не добавляй приветствий или заключений. Только описание поездки."
                ),
                contents=prompt
            )
            description = response.text
            print(f"✅ Получено описание: {description[:50]}...")

            # Генерируем эмбеддинг
            print(f"🔢 Генерация эмбеддинга...")
            try:
                # Используем правильный формат имени модели для v1beta API
                embedding_response = self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=description
                )
                embedding = embedding_response.embeddings[0].values
                print(f"✅ Получен эмбеддинг: {len(embedding)} элементов")
            except Exception as emb_error:
                print(f"⚠️ Не удалось сгенерировать эмбеддинг: {emb_error}")
                print(f"💡 Сохраняем только описание...")
                embedding = None
            
            # Преобразуем в JSON-строку
            import json
            embedding_json = json.dumps(embedding) if embedding else None

            return description, embedding_json

        except genai_errors.ClientError as e:
            print(f"❌ Ошибка ИИ при генерации описания: {e}")
            if e.code == 429:
                return None, None  # Тихо игнорируем при лимите
            return None, None
        except Exception as e:
            print(f"❌ Произошла ошибка при генерации описания: {e}")
            return None, None

    def chat_with_ai(self, user_message: str) -> str:
        """
        Чат с ИИ - ответ на произвольный вопрос пользователя.
        
        :return: ответ ИИ или сообщение об ошибке
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",

                config=types.GenerateContentConfig(
                    system_instruction="Ты — дружелюбный и полезный ИИ-ассистент для путешественников. "
                        "Отвечай на вопросы пользователей на русском языке кратко, информативно и дружелюбно. "
                        "Помогай с советами о поездках, маршрутах, упаковке вещей и всем, что связано с путешествиями."
                ),
                contents=user_message
            )
            return response.text
        except genai_errors.ClientError as e:
            if e.code == 429:
                return "⚠️ Лимит запросов к ИИ исчерпан. Попробуйте позже."
            return f"⚠️ Ошибка ИИ: {e}"
        except Exception as e:
            return f"⚠️ Произошла ошибка: {e}"
    