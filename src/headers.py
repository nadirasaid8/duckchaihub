from src.agent import generate_random_user_agent

def headers(authorization):
    return {
            "accept": "*/*",
            "authorization": f'tma {authorization}',
            "origin": "https://tgdapp.duckchain.io",
            "referer": "https://tgdapp.duckchain.io/",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Android WebView\";v=\"127\", \"Chromium\";v=\"127\"",
            "user-agent": generate_random_user_agent()
        }