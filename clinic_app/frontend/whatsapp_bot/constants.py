from clinic_app.frontend.whatsapp_bot.green_api import PatchedBot
from clinic_app.shared.config import get_config

cfg = get_config()["whatsapp_bot"]
id_instance = cfg["id_instance"]
token_instance = cfg["token_instance"]


bot = PatchedBot(id_instance=str(id_instance), api_token_instance=token_instance)
