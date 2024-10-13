import requests
import time, datetime
from openai import OpenAI
import urllib.request
import json


class WhatsAppProcess:
    def __init__(self):

        # параметры доступа к инстансу
        self.apiUrl = 'https://1103.api.green-api.com'
        self.mediaUrl = 'https://1103.media.green-api.com'
        self.idInstance = 'YOUR_ID_INSTANCE'
        self.apiTokenInstance = 'YOUR_API_TOKEN_INSTANCE'

    def set_settings(self):
        """Установка настроек инстанса, подробно в офф. документации green_api"""
        url = f"{self.apiUrl}/waInstance{self.idInstance}/setSettings/{self.apiTokenInstance}"

        payload = ("{\r\n\t\"webhookUrl\": \"\","
                   "\r\n\t\"delaySendMessagesMilliseconds\": 1000,"
                   "\r\n\t\"markIncomingMessagesReaded\": \"no\","
                   "\r\n\t\"outgoingWebhook\": \"no\","
                   "\r\n\t\"outgoingMessageWebhook\": \"yes\","
                   "\r\n\t\"stateWebhook\": \"yes\","
                   "\r\n\t\"incomingWebhook\": \"yes\","
                   "\r\n\t\"deviceWebhook\": \"no\","
                   "\r\n\t\"outgoingAPIMessageWebhook\": \"no\""
                   "\r\n}")

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print('set_settings: ', response.text.encode('utf8'))

    def get_settings(self):
        """Получение настроек инстанса"""
        url = f"{self.apiUrl}/waInstance{self.idInstance}/getSettings/{self.apiTokenInstance}"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text.encode('utf8'))

    def reboot(self):
        """Перезагрузка инстанса"""
        url = f"{self.apiUrl}/waInstance{self.idInstance}/reboot/{self.apiTokenInstance}"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text.encode('utf8'))

    def get_state_instance(self):
        """Получение состояние инстанса"""

        url = f"{self.apiUrl}/waInstance{self.idInstance}/getStateInstance/{self.apiTokenInstance}"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        state_instance = response.json().get("stateInstance")
        print('StateInstance: ', state_instance)
        return state_instance

    def receive_incoming_notifications(self):
        """Получение первого уведомления из очереди с последующим удалением из нее"""

        def receive_notification():
            """Получение первого уведомления из очереди"""
            global receipt_id, type_webhook, chat_id, response_receive_notification_json

            url = f"{self.apiUrl}/waInstance{self.idInstance}/receiveNotification/{self.apiTokenInstance}"

            # payload = {"{\r\n\t\"receiveTimeout\": 10,\r\n}"}
            payload = {}
            headers = {}

            response = requests.request("GET", url, headers=headers, data=payload)
            # Проверим, что ответ пришёл в формате JSON
            try:
                # Преобразуем ответ в JSON (словарь)
                response_receive_notification_json = response.json()
                # Получаем "receiptId"
                receipt_id = response_receive_notification_json.get("receiptId")
                # Получаем тип ChatId
                chat_id = (response_receive_notification_json
                           .get('body', {})
                           .get('senderData', {})
                           .get('chatId', None)
                           )
                # Получаем тип уведомления
                type_webhook = (response_receive_notification_json
                                .get('body', {})
                                .get('typeWebhook', None))
                if type_webhook:
                    print(type_webhook)
                else:
                    print("Ключ 'typeWebhook' не найден")

                print('receive_message: ', response_receive_notification_json)
                print('chat_id:', f'{chat_id}')

            except AttributeError as ae:
                # Если ответ не в формате JSON или произошла ошибка
                print(f"No notifications received: {ae}")
                receipt_id = 0
                chat_id, new_message = '', ''

        def delete_notification():
            """Удаление уведомления из очереди"""
            url = f"{self.apiUrl}/waInstance{self.idInstance}/deleteNotification/{self.apiTokenInstance}/{receipt_id}"

            payload = {}
            headers = {}

            response = requests.request("DELETE", url, headers=headers, json=payload)

            print('delete_message: ', response.text.encode('utf8'))
            print('receipt_id deleted: ', receipt_id)

        receive_notification()
        delete_notification()

    def clear_pull(self):
        """Почистить пул уведомлений"""
        WhatsAppProcess.receive_incoming_notifications(self)
        while receipt_id:
            WhatsAppProcess.receive_incoming_notifications(self)

    def send_message(self, bot_message):
        """Отправка сообщения"""
        url = f"{self.apiUrl}/waInstance{self.idInstance}/sendMessage/{self.apiTokenInstance}"

        payload = {
            "chatId": f"{chat_id}",
            "message": f"{bot_message}"
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload)

        print('send_message: ', response.text.encode('utf8'))

    def show_messages_queue(self):
        url = f"{self.apiUrl}/waInstance{self.idInstance}/showMessagesQueue/{self.apiTokenInstance}"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text.encode('utf8'))

    def get_chat_history(self):
        """Получение истории чата в виде списка словарей"""
        print('history chat id:', chat_id)
        url = f"{self.apiUrl}/waInstance{self.idInstance}/getChatHistory/{self.apiTokenInstance}"
        payload = {
            "chatId": f"{chat_id}",
            "count": 50  # Сколько сообщений входит в историю
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload)
        print('Chat history: ', response.text.encode('utf8'))

        # Обработка истории сообщений
        chat_memo = 20
        history_message_id = 1
        history_list, final_msg_list = [], []
        for json_obj in response.json():

            # Получим sender_name и message_type
            message_type = json_obj.get('type')
            if message_type == 'incoming':
                sender_name = json_obj.get('senderName')
            else:
                sender_name = 'bot'

            # Обработаем только текстовые сообщения (сообщения от bot почему-то считывает как extendedTextMessage,
            # поэтому добавляем его тоже)
            if json_obj.get('typeMessage') == 'textMessage' or json_obj.get('typeMessage') == 'extendedTextMessage':

                message_text = json_obj.get('textMessage')

            # Если это был не текст
            else:
                message_text = 'ERROR: MESSAGE IS NOT TEXT'

            # Обрабатываем метку даты и времени сообщения
            unix_timestamp = json_obj.get('timestamp')
            date_time = datetime.datetime.utcfromtimestamp(unix_timestamp)

            # Сформируем словарь содержания одного сообщения
            one_message_dict = {
                'id': history_message_id,
                'date_time': date_time,
                'sender_name': sender_name,
                'message_text': message_text
            }

            history_list.append(one_message_dict)
            history_message_id += 1

        # Добавим в промпт только переписку не ранее chat_memo
        reference_time = history_list[0]['date_time']   # Время самого нового сообщения
        for message in history_list:
            # Разница по времени между сообщением и самым первым сообщением
            time_difference = abs(reference_time - message['date_time'])

            # Проверяем, меньше ли разница одного часа
            if time_difference < datetime.timedelta(minutes=chat_memo):
                # Преобразуем формат времени
                str_date_time = message['date_time'].strftime('%d-%m-%Y %H:%M:%S')
                message['date_time'] = str_date_time
                final_msg_list.append(message)

        for message in final_msg_list:
            print(message)

        return final_msg_list

class YClientsCRM:

    def __init__(self):
        self.login = "YOUR_LOGIN"
        self.password = "YOUR_PASSWORD"
        self.partner_token = "YOUR_PARTNER_TOKEN"
        self.company_id = "YOUR_COMPANY_ID"

    def authorization(self):
        values = {
            "login": f"{self.login}",
            "password": f"{self.password}"
        }
        data = json.dumps(values).encode('utf-8')  # Convert the dictionary to a JSON-encoded byte string

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.yclients.v2+json',
            'Authorization': f'{self.partner_token}'
        }

        # Create the request object with headers
        req = urllib.request.Request('https://api.yclients.com/api/v1/auth', data=data, headers=headers)

        # Perform the request
        with urllib.request.urlopen(req) as response:
            html = response.read()

        # Parse the response as JSON
        response_json = json.loads(html.decode('utf-8'))

        # Extract user_token from the response
        user_token = response_json['data']['user_token']

        # Print the user_token
        print(f"User Token: {user_token}")
        print(response_json)
        return user_token

    def get_staff(self):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'{self.partner_token},  {user_token}',
            'Accept': 'application/vnd.api.v2+json'  # Добавляем нужный Accept заголовок
        }
        url = f'https://api.yclients.com/api/v1/company/{self.company_id}/staff/'

        response = requests.get(url, headers=headers).json()
        staff_dict_inner = {staff['id']: [staff['name'], staff['specialization']] for staff in response['data']}

        # Фильтруем только тех, кто не является "Администратором"
        filtered_dict = {key: value for key, value in staff_dict_inner.items() if value[1] != 'Администратор'}

        return filtered_dict

    
    def get_available_staff(self, user_token, staff_dict, start_date, end_date):

        def get_staff_schedule(staff_id):
            """Получить расписание сотрудника. Используется в function calling"""
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.yclients.v2+json',
                'Authorization': f'{self.partner_token}, {user_token}'
            }

            url = f'https://api.yclients.com/api/v1/schedule/{self.company_id}/{staff_id}/{start_date}/{end_date}'
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req) as response:
                html = response.read()
            # Parse the response as JSON
            response_json = json.loads(html.decode('utf-8'))['data'][0]['is_working']

            return response_json

        def get_records():
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.yclients.v2+json',
                'Authorization': f'{self.partner_token}, {user_token}'
            }

            url = (
                f"https://api.yclients.com/api/v1/records/{self.company_id}?"
                f"start_date={start_date}&"
                f"end_date={end_date}"
            )
            response = requests.get(url, headers=headers).json()

            records = [
                {
                    'staff_id': staff['staff_id'],
                    'date': staff['date'],
                    'seance_length': int(staff['seance_length']) / 60
                } for staff in response['data']
            ]
            return records

        records = get_records()

        # Убедитесь, что staff_id не является списком
        existing_staff_ids = {record['staff_id'] for record in records}
        # Проходим по всем сотрудникам в словаре staff_dict
        for staff_id in staff_dict:
            # Проверяем, есть ли сотрудник в записях
            if staff_id not in existing_staff_ids:
                # Если сотрудника нет в записях, но он работает
                if get_staff_schedule(staff_id) == '1':
                    # Добавляем запись с пустыми 'date' и 'seance_length'
                    records.append(
                        {
                            'staff_id': staff_id,
                            'date': '',
                            'seance_length': 0
                        }
                    )
        return records


def gpt_req(messages, user_token, staff_dict):
    """Отправка запроса в gpt и возврат ответа"""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_available_staff",
                "description": "Use this function to get staff schedule",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start of the date diapason to search. 2024 year. Date format: 'YYYY-MM-DD'",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End of the date diapason to search. 2024 year. Date format: 'YYYY-MM-DD'",
                        },
                        "user_token": {
                            "type": "string",
                            "description": f"The authorization token to use: {user_token}"
                        }
                    },
                    "required": ["start_date", "end_date", "user_token"],
                    "additionalProperties": False,
                }
            }
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",  # "gpt-4-turbo"
        messages=messages,
        tools=tools,
        temperature=1.0
    )

    gpt_out = completion.choices[0].message.content
    print(gpt_out, "\n\t")
    print(f'{completion.usage.total_tokens} токенов использовано\n\t')

    # Проверка вызова функции
    function_call = completion.choices[0].message.function_call
    tool_calls = completion.choices[0].message.tool_calls

    # Проверка tool_calls
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_arguments = tool_call.function.arguments
            print(f"Tool called: {function_name}, with arguments: {function_arguments}")

            # Выполни функцию здесь, если вызвана
            staff_schedule = CRM.get_available_staff(**json.loads(function_arguments), staff_dict=staff_dict)  # Распакуй аргументы
            # Создание нового сообщения с результатом функции
            new_message = f"{messages}\n\nРасписание сотрудника:\n{staff_schedule}"

            # Создание нового запроса в модель с обновленным сообщением
            updated_completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": new_message}],
                temperature=1.4,
            )

            final_output = updated_completion.choices[0].message.content
            print(final_output)
            return final_output  # Возврат ответа от модели с встроенным результатом функции

    else:
        print('Функция не вызвана')
        return gpt_out

staff_dict = CRM.get_staff()

CRM = YClientsCRM()

user_token = CRM.authorization()
# CRM.booking(user_token=user_token)
staff_dict = CRM.get_staff()

prompt_path = 'YOUR_PROMPT_PATH'
prompt_file_txt = "ChatBotPromptEng.txt"  # prompt file

# read prompt file
with open(f"{prompt_path}{prompt_file_txt}", "r", encoding="utf-8") as prompt_file:
    system_prompt = prompt_file.read()

client = OpenAI()

Wh = WhatsAppProcess()

Wh.set_settings()
Wh.get_settings()

# Проверим авторизован ли инстанс
while True:
    try:
        # Если инстанс авторизован
        if Wh.get_state_instance() == "authorized":
            break

        # Если инстанс не авторизован
        else:
            print('Instance is not authorized')
            time.sleep(5)
            continue

    # Ошибка 200: Инстанс долго (более 5 минут) в состоянии starting
    except '200' as error:
        print(error)
        print('Reboot...')
        # Перезагружаем инстанс
        Wh.reboot()
        time.sleep(60)

# Очистка пула
Wh.clear_pull()

# Цикл мониторинга сообщений
while True:

    # Получаем первое в очереди уведомление
    Wh.receive_incoming_notifications()

    # Отправляем сообщение в ответ только тогда, когда было новое уведомление и это не stateInstanceChanged
    if response_receive_notification_json and type_webhook != 'stateInstanceChanged':

        # Добавляем в промпт историю сообщений  и список сотрудников
        prompt_ar = [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "system", "content": f"{staff_dict}"},
            {"role": "user", "content": f"{Wh.get_chat_history()}"}
        ]
        print('')
        print('prompt_ar:', prompt_ar)

        # Запрос и ответ gpt
        bot_answer = gpt_req(prompt_ar, staff_dict=staff_dict, user_token=user_token)
        # Отправка сообщения от бота
        Wh.send_message(bot_answer)

    time.sleep(10)


