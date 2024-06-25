import logging
import time
from typing import NoReturn, Optional

from whatsapp_chatbot_python import GreenAPIBotError, Bot


class PatchedBot(Bot):
    def run_forever(self) -> Optional[NoReturn]:
        self.api.session.headers["Connection"] = "keep-alive"

        self.logger.log(
            logging.INFO, "Started receiving incoming notifications."
        )

        while True:
            try:
                response = self.api.receiving.receiveNotification()

                if not response.data:
                    continue
                response = response.data

                self.router.route_event(response["body"])

                self.api.receiving.deleteNotification(response["receiptId"])
            except KeyboardInterrupt:
                break
            except Exception as error:
                if self.raise_errors:
                    raise GreenAPIBotError(error)

                error_code = "500. Data: Internal server error"
                if str(error).count(error_code):
                    time.sleep(7.0)
                    continue

                self.logger.log(logging.ERROR, error)

                time.sleep(5.0)

                continue

        self.api.session.headers["Connection"] = "close"

        self.logger.log(
            logging.INFO, "Stopped receiving incoming notifications."
        )
