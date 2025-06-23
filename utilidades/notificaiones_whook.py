import requests
import json

class WebhookNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, message):
        """
        Sends a notification to the webhook URL.

        :param message: The message to send as a string.
        :return: Response object from the POST request.
        """
        headers = {'Content-Type': 'application/json'}
        payload = {"text": message}

        try:
            response = requests.post(self.webhook_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification: {e}")
            return None
