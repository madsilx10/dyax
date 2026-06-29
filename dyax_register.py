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
WORDS = [
    "zyrex","xenon","kaelon","vynor","astrel","quelth","drexon","fynix","myron","thalek",
    "cryxen","velorn","sorath","brixon","noxel","lyren","wyxon","phenar","gravon","zethen",
    "deko","winze","jiobs","volak","trexon","skaen","morvel","dunix","relkos","taeven",
    "briven","queloz","zenvox","draken","sylven","koreth","faylon","merxon","tolvyn","axren",
    "vorlen","caldex","syrion","belkos","thraven","nexorin","pyloth","skarath","drovin","zelkyn"
]

def random_word():
    word = random.choice(WORDS)
    # Huruf pertama random kapital atau kecil, sisanya lowercase
    if random.random() > 0.5:
        return word[0].upper() + word[1:]
    else:
        return word

def random_login_id():
    # Satu kata, huruf depan random kapital/kecil
    return random_word()

def random_nickname():
    # 1 atau 2 kata
    if random.random() > 0.5:
        return random_word()
    else:
        return random_word() + " " + random_word()

def check_login_id(session, login_id):
    r = session.get(f"{BASE_URL}/api/auth/email/check-login-id?loginId={login_id}")
    return r.json().get("available", False)

def check_nickname(session, nickname):
    # Nickname bisa 2 kata, encode spasi
    encoded = nickname.replace(" ", "%20")
    r = session.get(f"{BASE_URL}/api/auth/email/check-nickname?nickname={encoded}")
    return r.json().get("available", False)

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

    # 5. Generate data dengan cek availability
    print("[*] Generate loginId & nickname...")
    for _ in range(10):
        login_id = random_login_id()
        if check_login_id(session, login_id):
            break
        print(f"[!] loginId '{login_id}' tidak available, coba lagi...")
    else:
        print("[!] Gagal dapat loginId yang available.")
        return False

    for _ in range(10):
        nickname = random_nickname()
        if check_nickname(session, nickname):
            break
        print(f"[!] Nickname '{nickname}' tidak available, coba lagi...")
    else:
        print("[!] Gagal dapat nickname yang available.")
        return False
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
