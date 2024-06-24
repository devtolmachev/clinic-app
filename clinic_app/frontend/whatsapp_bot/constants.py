from clinic_app.shared.config import get_config
from whatsapp_chatbot_python import GreenAPIBot

cfg = get_config()["whatsapp_bot"]
id_instance = cfg["id_instance"]
token_instance = cfg["token_instance"]


bot = GreenAPIBot(id_instance=str(id_instance), api_token_instance=token_instance)
