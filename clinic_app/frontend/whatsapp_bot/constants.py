from clinic_app.shared.config import get_config
from whatsapp_api_client_python import API

cfg = get_config()["whatsapp_bot"]
id_instance = cfg["id_instance"]
token_instance = cfg["token_instance"]


bot = API.GreenApi(idInstance=str(id_instance), apiTokenInstance=token_instance)
