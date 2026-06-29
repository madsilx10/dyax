import requests
import random
import string
import json
import time
import sys

BASE_URL = "https://dyax.io"
REF = "5b5f8c29-f3b9-4106-bfc6-c6ef5d879b3e"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://dyax.io",
    "Referer": f"https://dyax.io/?ref={REF}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Sec-Ch-Ua": '"Mises";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=1, i",
}

# Kata-kata unik buat generate nama
PREFIXES = ["zyr","xen","kael","vyn","astr","quel","drex","fyn","myr","thal",
            "cryx","vel","sor","brix","nox","lyr","wyx","phen","grav","zeth"]
SUFFIXES = ["ion","ax","os","ix","en","ar","yx","um","el","or",
            "an","is","eth","yx","ron","al","us","ek","yn","az"]

def random_name():
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    name = prefix + suffix
    # Mixed case random
    result = ""
    for ch in name:
        if random.random() > 0.5:
            result += ch.upper()
        else:
            result += ch.lower()
    # Pastiin huruf pertama random kapital atau tidak
    return result

def random_login_id():
    name = random_name()
    num = random.randint(10, 9999)
    return f"{name}{num}"

def check_email(session, email):
    r = session.post(f"{BASE_URL}/api/auth/email/check", json={"email": email})
    data = r.json()
    return data.get("exists", True) == False  # True = email bisa dipakai

def send_code(session, email):
    payload = {"email": email, "recaptchaToken": ""}
    r = session.post(f"{BASE_URL}/api/auth/email/send-code", json=payload)
    data = r.json()
    return data.get("ok", False)

def verify_code(session, email, code):
    r = session.post(f"{BASE_URL}/api/auth/email/verify-code", json={"email": email, "code": code})
    data = r.json()
    return data.get("ok", False)

def register(session, email, code, password, login_id, nickname):
    payload = {
        "email": email,
        "code": code,
        "password": password,
        "loginId": login_id,
        "nickname": nickname,
        "preferredLang": "en",
        "ref": REF
    }
    r = session.post(f"{BASE_URL}/api/auth/email/register", json=payload)
    data = r.json()
    return data.get("ok", False)

def process_account(email, password, results_file):
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"\n{'='*40}")
    print(f"[*] Proses: {email}")

    # 1. Check email
    print("[*] Cek email...")
    if not check_email(session, email):
        print("[!] Email sudah terdaftar, skip.")
        return False

    # 2. Send OTP
    print("[*] Kirim OTP...")
    if not send_code(session, email):
        print("[!] Gagal kirim OTP. Mungkin recaptcha block.")
        return False

    # 3. Input OTP manual
    code = input(f"[?] Masukkan OTP untuk {email}: ").strip()

    # 4. Verify OTP
    print("[*] Verifikasi OTP...")
    if not verify_code(session, email, code):
        print("[!] OTP salah atau expired.")
        return False

    # 5. Generate data
    login_id = random_login_id()
    nickname = random_name()
    print(f"[*] LoginId: {login_id}")
    print(f"[*] Nickname: {nickname}")

    # 6. Register
    print("[*] Registrasi...")
    if not register(session, email, code, password, login_id, nickname):
        print("[!] Gagal registrasi.")
        return False

    print(f"[+] SUKSES: {email}")
    with open(results_file, "a") as f:
        f.write(f"email={email} | loginId={login_id} | nickname={nickname} | password={password}\n")

    return True

def main():
    print("=== DYAX.IO Auto Register ===")
    print("Mode: 1=satu akun, 2=semua, 3=from X to end")
    mode = input("Pilih mode: ").strip()

    with open("emails.txt", "r") as f:
        emails = [e.strip() for e in f.readlines() if e.strip()]

    if mode == "1":
        idx = int(input(f"Nomor akun (1-{len(emails)}): ")) - 1
        emails = [emails[idx]]
    elif mode == "2":
        pass  # semua
    elif mode == "3":
        start = int(input(f"Dari nomor (1-{len(emails)}): ")) - 1
        emails = emails[start:]
    else:
        print("Mode tidak valid.")
        sys.exit(1)

    password = input("Password untuk semua akun: ").strip()
    results_file = "results.txt"

    sukses = 0
    gagal = 0

    for email in emails:
        ok = process_account(email, password, results_file)
        if ok:
            sukses += 1
        else:
            gagal += 1
        time.sleep(2)

    print(f"\n{'='*40}")
    print(f"[+] Selesai. Sukses: {sukses} | Gagal: {gagal}")
    print(f"[+] Hasil tersimpan di: {results_file}")

if __name__ == "__main__":
    main()
