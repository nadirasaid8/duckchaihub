import time
import json
import random
import http.client
import urllib.request
import urllib.error
import urllib.parse
from colorama import *
from src.deeplchain import read_config, mrh, pth, kng, htm, bru, hju, countdown_timer, log, log_line
from src.headers import headers

init(autoreset=True)
config = read_config()

class DuckChainAPI:
    def __init__(self, authorization, proxy=None, timeout=10):
        self.base_url = "https://preapi.duckchain.io"
        self.authorization = f'tma {authorization}'
        self.headers = headers(authorization)
        self.proxy = proxy
        self.timeout = timeout

    def _make_request(self, endpoint, params=None, retries=3):
        url = f"{self.base_url}{endpoint}"

        if params:
            url += '?' + urllib.parse.urlencode(params)

        req = urllib.request.Request(url, headers=self.headers)

        if self.proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy, 'https': self.proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.load(response)
            except urllib.error.HTTPError as e:
                log(mrh + f"HTTPError: {e.code} - {e.reason}")
                return None
            except urllib.error.URLError as e:
                log(mrh + f"URLError: {e.reason}")
                log(htm + "~" * 38)
                return None
            except http.client.RemoteDisconnected:
                log(mrh + f"RemoteDisconnected: Attempt {attempt + 1} failed. Retrying...")
                time.sleep(2)
                continue
            except TimeoutError:
                log(mrh + f"TimeoutError: Attempt {attempt + 1} failed. Retrying...")
                time.sleep(2)
                continue
        log(bru + "All retry attempts failed.")
        return None

    def get_user_info(self):
        return self._make_request("/user/info")
    
    def check_in(self):
        return self._make_request("/task/sign_in?")

    def execute_tap(self):
        return self._make_request("/quack/execute")
    
    def perform_sign(self):
        check_in_response = self.check_in()
        if check_in_response and check_in_response.get("code") == 200:
            log(hju + f"Daily Check-in successfully")
        elif check_in_response.get("code") == 500:
            log(hju + f"Daily Check-in : {kng}was complete")
        else:
            log(mrh + f"Daily Check-in failed.")

    def claim_egg(self, task_id=1):
        url = f"/property/daily/finish?taskId={task_id}"
        response = self._make_request(url)
        
        if response is None:
            log(mrh + f"Failed to get response for claim_egg. Skipping...")
            return

        if response.get("code") == 200:
            if response.get("data") == 1:
                log(hju + f"Successfully claimed eggs today")
            else:
                log(f"Claim egg is not finished or invalid data received.")
        elif response.get('code') == 500:
            log(kng + f"You have claimed eggs today.")
        else:
            log(mrh + f"Failed to claim egg for task {task_id}. Response: {response}")

    def open_all_boxes(self, open_type=1):
        while True:
            endpoint = "/box/open"
            params = {'openType': open_type}

            response = self._make_request(endpoint, params)
            if response and response['code'] == 200 and response['message'] == "SUCCESS":
                data = response['data']
                quantity = data.get('quantity', 0)
                obtain = data.get('obtain', 0)
                boxes_left = data.get('boxesLeft', 0)
                log(hju + f"Box opened successfully!")
                log(hju + f"Quantity: {pth}{quantity} {hju}| Points : {pth}{obtain} {hju}| Boxes left: {pth}{boxes_left}")

                if boxes_left == 0:
                    log(f"{kng}All boxes opened! {pth}No more boxes left.")
                    break
            elif response['code'] == 500:
                log(f"{kng}You have {pth}0 {kng}boxes to open, {bru}skipping..")
                break
            else:
                log(f"{Fore.RED}Failed to open the box. Code: {response.get('code', 'N/A')}, {response.get('message', 'Unknown error')}")
                break

    def handle_tasks(self):
        tasks_response = self._make_request("/task/task_list")
        
        if not isinstance(tasks_response, dict):
            log(mrh + f"Unexpected tasks format: {tasks_response}")
            return

        tasks = tasks_response.get('data')
        if not tasks:
            log(kng + "No tasks found in the 'data' field.")
            return

        task_info_response = self._make_request("/task/task_info")
        if not isinstance(task_info_response, dict):
            log(mrh + f"Unexpected task info format: {task_info_response}")
            return

        task_info = task_info_response.get('data', {})

        completed_task_ids = set(
            task_info.get('socialMedia', []) +
            task_info.get('daily', []) +
            task_info.get('partner', []) +
            task_info.get('oneTime', [])
        )

        for category, task_list in tasks.items():
            if isinstance(task_list, list):
                for task in task_list:
                    task_id = task.get('taskId')
                    content = task.get('content')
                    integral = task.get('integral')

                    if task_id == 137:
                        log(kng + f"Task {pth}{content} {pth}is skipped.")
                        continue

                    if task_id in completed_task_ids:
                        log(kng + f"Task {pth}{content} {kng}already completed.")
                        continue

                    type_task = self.get_task_type(category)
                    if not type_task:
                        continue

                    completion_response = self._make_request(f"/task/{type_task}?taskId={task_id}")

                    if completion_response is None:
                        log(mrh + f"Failed to get response for task {content} {task_id}")
                        continue 

                    if completion_response.get("code") == 500 and 'task not open' in completion_response.get("message", "").lower():
                        log(mrh + f"Task {content} is no longer open. Skipping...")
                        continue 

                    if completion_response.get("code") == 200:
                        log(hju + f"Successfully {pth}{content}! {hju}Reward: {pth}{integral} {hju}Points")
                        completed_task_ids.add(task_id)
                        countdown_timer(3)
                    elif completion_response.get("code") == 500:
                        log(kng + f"Task {content} was finished!")
                    else:
                        log(mrh + f"Failed to complete task {content}. Response: {completion_response}.")
            else:
                log(mrh + f"Unexpected task_list format for category {category}: {task_list}")

    def get_task_type(self, category):
        """Return the task type based on the category."""
        if category == 'socialMedia':
            return 'socialMedia'
        elif category == 'daily':
            return 'daily'
        elif category == 'partner':
            return 'partner'
        elif category == 'oneTime':
            return 'oneTime'
        else:
            log(f"Unexpected category {category}. Skipping...")
            return None

def get_proxy():
    try:
        with open('proxies.txt', 'r') as file:
            proxies = [line.strip() for line in file if line.strip()]

        if not proxies:
            log("No proxies found in proxies.txt.")
            return None

        proxy = random.choice(proxies)

        if proxy.startswith("http://"):
            return proxy
        elif proxy.startswith("https://"):
            return proxy
        elif proxy.startswith("socks5://"):
            return proxy
        else:
            return f"http://{proxy}"
    except FileNotFoundError:
        log("File 'proxies.txt' not found.")

def log_user_info(user_info):
    if user_info['code'] == 200 and user_info['message'] == "SUCCESS":
        data = user_info['data']
        log(hju + f"Duck name: {pth}{data['duckName']}")
        log(hju + f"Balance: {pth}{data['decibels']}{hju}| Box : {pth}{data['boxAmount']} {hju}| Eggs : {pth}{data['eggs']}")
    else:
        log(mrh + f"Failed to retrieve user info. Code: {user_info['code']}, Message: {user_info['message']}")

def log_quack_result(quack_result, quack_number):
    if quack_result['code'] == 200 and quack_result['message'] == "SUCCESS":
        data = quack_result['data']
        quack_records = data.get('quackRecords', [])
        A = quack_records[8] if len(quack_records) > 8 else None
        B = quack_records[0] if len(quack_records) > 0 else None

        result = A if A else B if B else "No record available"
        
        log(f"{bru}Quack {pth}{quack_number}: {pth}{data['result']} {hju}| Result: {pth}{result}")
        log(f"{hju}Decibel Change: {pth}{data['decibel']} {hju}| Quack Times: {pth}{data['quackTimes']}")
    else:
        log(mrh + f"Failed to execute quack. Code: {quack_result['code']}, Message: {quack_result['message']}")

def main():
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        log("File 'config.json' not found.")
        return

    use_proxy = config.get("use_proxy", False)
    quack_delay = config.get("quack_delay", 0)
    quack_amount = config.get("quack_amount", 10)
    complete_task = config.get("complete_task", False)
    account_delay = config.get("account_delay", 5)
    countdown_loop = config.get("countdown_loop", 3800)

    try:
        with open('data.txt', 'r') as file:
            tokens = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        log("File 'data.txt' not found.")
        return

    if not tokens:
        log("No data found in data.txt")
        return

    total_accounts = len(tokens)
    for index, token in enumerate(tokens, start=1):
        proxy = get_proxy() if use_proxy else None
        
        if proxy:
            proxy_host = proxy.split('@')[-1] 
        else:
            proxy_host = "No proxy used"

        duck = DuckChainAPI(authorization=token, proxy=proxy)
        log(hju + f"Processing account {pth}{index} / {total_accounts}")
        log(hju + f"Using proxy: {pth}{proxy_host}") # <-- Comment out this line when no proxy is used!
        log(htm + "~" * 38)

        user_info = duck.get_user_info()
        if user_info:
            log_user_info(user_info)

            duck.perform_sign()
            duck.claim_egg()
            duck.open_all_boxes()

            for i in range(quack_amount):
                quack_result = duck.execute_tap()
                if quack_result:
                    log_quack_result(quack_result, i + 1)
                else:
                    log(f"{Fore.RED}Failed to execute quack #{i+1}.")
                time.sleep(quack_delay)

            if complete_task:
                duck.handle_tasks()
            else:
                log(kng + f"Auto complete task is disabled!")

            log_line()
            countdown_timer(account_delay)
    countdown_timer(countdown_loop)
