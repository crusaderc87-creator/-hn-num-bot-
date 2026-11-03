# rsayel_monitor.py  
import requests
import re
import time
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import urllib.parse
import sys,dns.resolver 
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']
# ----------------------- MongoDB -----------------------
USERNAME = "tawfiqur464_db_user"
PASSWORD = "Xsu6en9YmUqVjziB"
encoded = urllib.parse.quote(PASSWORD)
mongo = MongoClient(
    f"mongodb+srv://{USERNAME}:{encoded}@cluster0.uek3dsd.mongodb.net/?appName=Cluster0"
)
sms_col = mongo["HNDATA"]["sms"]

# ----------------------- Rsayel API -----------------------
API_BASE  = "https://rsayel.org"
API_TOKEN = "tUmm8Mr5VWZdvFhfgSJ5foH6X1IQbEYdCFGoEOqpBQk"
MESSAGES_URL = f"{API_BASE}/api/v1/messages"

POLL_INTERVAL      = 1.5
RECORDS_PER_FETCH  = 100
FULL_SCAN_INTERVAL = 60

# ----------------------- Telegram -----------------------
TG_TOKEN = "8948390507:AAHxVnmxA1Dpl3f_MdsjvgTXYm-GYawe1wY"
TG_CHAT  = "-1002234202783"
TG_URL   = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

# ----------------------- dedup -----------------------
PROCESSED_KEYS = set()
MAX_KEYS = 20000

COUNTRY_PREFIXES = {
    "93": ("Afghanistan", "🇦🇫"), "355": ("Albania", "🇦🇱"), "213": ("Algeria", "🇩🇿"), "376": ("Andorra", "🇦🇩"), "244": ("Angola", "🇦🇴"),
    "268": ("Antigua and Barbuda", "🇦🇬"), "54": ("Argentina", "🇦🇷"), "374": ("Armenia", "🇦🇲"), "61": ("Australia", "🇦🇺"), "43": ("Austria", "🇦🇹"),
    "994": ("Azerbaijan", "🇦🇿"), "242": ("Bahamas", "🇧🇸"), "973": ("Bahrain", "🇧🇭"), "880": ("Bangladesh", "🇧🇩"), "246": ("Barbados", "🇧🇧"),
    "375": ("Belarus", "🇧🇾"), "32": ("Belgium", "🇧🇪"), "501": ("Belize", "🇧🇿"), "229": ("Benin", "🇧🇯"), "975": ("Bhutan", "🇧🇹"),
    "591": ("Bolivia", "🇧🇴"), "387": ("Bosnia and Herzegovina", "🇧🇦"), "267": ("Botswana", "🇧🇼"), "55": ("Brazil", "🇧🇷"), "673": ("Brunei", "🇧🇳"),
    "359": ("Bulgaria", "🇧🇬"), "226": ("Burkina Faso", "🇧🇫"), "257": ("Burundi", "🇧🇮"), "855": ("Cambodia", "🇰🇭"), "237": ("Cameroon", "🇨🇲"),
    "1": ("Canada/USA", "🇨🇦"), "236": ("Central African Republic", "🇨🇫"), "235": ("Chad", "🇹🇩"), "56": ("Chile", "🇨🇱"), "86": ("China", "🇨🇳"),
    "57": ("Colombia", "🇨🇴"), "269": ("Comoros", "🇰🇲"), "506": ("Costa Rica", "🇨🇷"), "225": ("Côte d'Ivoire", "🇨🇮"), "385": ("Croatia", "🇭🇷"),
    "53": ("Cuba", "🇨🇺"), "357": ("Cyprus", "🇨🇾"), "420": ("Czech Republic", "🇨🇿"), "45": ("Denmark", "🇩🇰"), "253": ("Djibouti", "🇩🇯"),
    "767": ("Dominica", "🇩🇲"), "809": ("Dominican Republic", "🇩🇴"), "593": ("Ecuador", "🇪🇨"), "20": ("Egypt", "🇪🇬"), "503": ("El Salvador", "🇸🇻"),
    "240": ("Equatorial Guinea", "🇬🇶"), "291": ("Eritrea", "🇪🇷"), "372": ("Estonia", "🇪🇪"), "268": ("Eswatini", "🇸🇿"), "251": ("Ethiopia", "🇪🇹"),
    "679": ("Fiji", "🇫🇯"), "358": ("Finland", "🇫🇮"), "33": ("France", "🇫🇷"), "241": ("Gabon", "🇬🇦"), "220": ("Gambia", "🇬🇲"),
    "995": ("Georgia", "🇬🇪"), "49": ("Germany", "🇩🇪"), "233": ("Ghana", "🇬🇭"), "30": ("Greece", "🇬🇷"), "473": ("Grenada", "🇬🇩"),
    "502": ("Guatemala", "🇬🇹"), "224": ("Guinea", "🇬🇳"), "245": ("Guinea-Bissau", "🇬🇼"), "592": ("Guyana", "🇬🇾"), "509": ("Haiti", "🇭🇹"),
    "504": ("Honduras", "🇭🇳"), "36": ("Hungary", "🇭🇺"), "354": ("Iceland", "🇮🇸"), "91": ("India", "🇮🇳"), "62": ("Indonesia", "🇮🇩"),
    "98": ("Iran", "🇮🇷"), "964": ("Iraq", "🇮🇶"), "353": ("Ireland", "🇮🇪"), "972": ("Israel", "🇮🇱"), "39": ("Italy", "🇮🇹"),
    "876": ("Jamaica", "🇯🇲"), "81": ("Japan", "🇯🇵"), "962": ("Jordan", "🇯🇴"), "77": ("Kazakhstan", "🇰🇿"), "254": ("Kenya", "🇰🇪"),
    "686": ("Kiribati", "🇰🇮"), "383": ("Kosovo", "🇽🇰"), "965": ("Kuwait", "🇰🇼"), "996": ("Kyrgyzstan", "🇰🇬"), "856": ("Laos", "🇱🇦"),
    "371": ("Latvia", "🇱🇻"), "961": ("Lebanon", "🇱🇧"), "266": ("Lesotho", "🇱🇸"), "231": ("Liberia", "🇱🇷"), "218": ("Libya", "🇱🇾"),
    "423": ("Liechtenstein", "🇱🇮"), "370": ("Lithuania", "🇱🇹"), "352": ("Luxembourg", "🇱🇺"), "261": ("Madagascar", "🇲🇬"), "265": ("Malawi", "🇲🇼"),
    "60": ("Malaysia", "🇲🇾"), "960": ("Maldives", "🇲🇻"), "223": ("Mali", "🇲🇱"), "356": ("Malta", "🇲🇹"), "692": ("Marshall Islands", "🇲🇭"),
    "222": ("Mauritania", "🇲🇷"), "230": ("Mauritius", "🇲🇺"), "52": ("Mexico", "🇲🇽"), "691": ("Micronesia", "🇫🇲"), "373": ("Moldova", "🇲🇩"),
    "377": ("Monaco", "🇲🇨"), "976": ("Mongolia", "🇲🇳"), "382": ("Montenegro", "🇲🇪"), "212": ("Morocco", "🇲🇦"), "258": ("Mozambique", "🇲🇿"),
    "95": ("Myanmar", "🇲🇲"), "264": ("Namibia", "🇳🇦"), "674": ("Nauru", "🇳🇷"), "977": ("Nepal", "🇳🇵"), "31": ("Netherlands", "🇳🇱"),
    "64": ("New Zealand", "🇳🇿"), "505": ("Nicaragua", "🇳🇮"), "227": ("Niger", "🇳🇪"), "234": ("Nigeria", "🇳🇬"), "850": ("North Korea", "🇰🇵"),
    "389": ("North Macedonia", "🇲🇰"), "47": ("Norway", "🇳🇴"), "968": ("Oman", "🇴🇲"), "92": ("Pakistan", "🇵🇰"), "680": ("Palau", "🇵🇼"),
    "507": ("Panama", "🇵🇦"), "675": ("Papua New Guinea", "🇵🇬"), "595": ("Paraguay", "🇵🇾"), "51": ("Peru", "🇵🇪"), "63": ("Philippines", "🇵🇭"),
    "48": ("Poland", "🇵🇱"), "351": ("Portugal", "🇵🇹"), "974": ("Qatar", "🇶🇦"), "40": ("Romania", "🇷🇴"), "250": ("Rwanda", "🇷🇼"),
    "869": ("Saint Kitts and Nevis", "🇰🇳"), "758": ("Saint Lucia", "🇱🇨"), "784": ("Saint Vincent and the Grenadines", "🇻🇨"), "685": ("Samoa", "🇼🇸"), "378": ("San Marino", "🇸🇲"),
    "239": ("São Tomé and Príncipe", "🇸🇹"), "966": ("Saudi Arabia", "🇸🇦"), "221": ("Senegal", "🇸🇳"), "381": ("Serbia", "🇷🇸"), "248": ("Seychelles", "🇸🇨"),
    "232": ("Sierra Leone", "🇸🇱"), "65": ("Singapore", "🇸🇬"), "421": ("Slovakia", "🇸🇰"), "386": ("Slovenia", "🇸🇮"), "677": ("Solomon Islands", "🇸🇧"),
    "252": ("Somalia", "🇸🇴"), "27": ("South Africa", "🇿🇦"), "82": ("South Korea", "🇰🇷"), "211": ("South Sudan", "🇸🇸"), "34": ("Spain", "🇪🇸"),
    "94": ("Sri Lanka", "🇱🇰"), "249": ("Sudan", "🇸🇩"), "597": ("Suriname", "🇸🇷"), "46": ("Sweden", "🇸🇪"), "41": ("Switzerland", "🇨🇭"),
    "963": ("Syria", "🇸🇾"), "992": ("Tajikistan", "🇹🇯"), "255": ("Tanzania", "🇹🇿"), "66": ("Thailand", "🇹🇭"), "670": ("Timor-Leste", "🇹🇱"),
    "228": ("Togo", "🇹🇬"), "676": ("Tonga", "🇹🇴"), "868": ("Trinidad and Tobago", "🇹🇹"), "216": ("Tunisia", "🇹🇳"), "90": ("Turkey", "🇹🇷"),
    "993": ("Turkmenistan", "🇹🇲"), "688": ("Tuvalu", "🇹🇻"), "256": ("Uganda", "🇺🇬"), "380": ("Ukraine", "🇺🇦"), "971": ("United Arab Emirates", "🇦🇪"),
    "44": ("United Kingdom", "🇬🇧"), "598": ("Uruguay", "🇺🇾"), "998": ("Uzbekistan", "🇺🇿"), "678": ("Vanuatu", "🇻🇺"), "379": ("Vatican City", "🇻🇦"),
    "58": ("Venezuela", "🇻🇪"), "84": ("Vietnam", "🇻🇳"), "967": ("Yemen", "🇾🇪"), "260": ("Zambia", "🇿🇲"), "7": ("Russia", "🇷🇺"),
}


def get_country(number: str):
    digits = re.sub(r"\D", "", number)
    for length in (4, 3, 2, 1):
        prefix = digits[:length]
        if prefix in COUNTRY_PREFIXES:
            return COUNTRY_PREFIXES[prefix]
    return ("Unknown", "🌍")


def format_number(number: str) -> str:
    digits = re.sub(r"\D", "", number)
    if len(digits) >= 8:
        return digits[:4] + "WzN" + digits[-4:]
    return digits


def extract_otp(message: str) -> str:
    """
    Extracts a numeric code from SMS content. Handles:
      • plain numbers 21527, 54001
      • hyphenated codes 404-038, 806-173, 541-797   (WhatsApp)
      • Arabic messages with hidden LTR/RTL marks  ‎697-460
      • spaced codes 404 038
    """
    if not message:
        return ""
    # strip bidi / zero-width marks that sit around Arabic code digits
    message = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2066-\u2069]', '', message)
    message = message.replace("–", "-").replace("—", "-")

    # collapse spaced digits:  4 0 4 0 3 8  ->  404038
    message = re.sub(
        r'(?<!\d)(\d{3}\s\d{3}|\d{2,3}\s\d{2,3}|\d\s\d\s\d\s\d\s\d\s\d)(?!\d)',
        lambda m: m.group(0).replace(" ", ""),
        message
    )
    # collapse hyphenated digits: 404-038 -> 404038
    message = re.sub(r'(\d{3,4})-(\d{3,4})', r'\1\2', message)

    matches = re.findall(r'\d{3,7}', message)
    if matches:
        return matches[0]
    return ""


def sms_key(sms: dict) -> str:
    return f"{sms.get('time','')}|{sms.get('number','')}|{sms.get('content','')}"


def already_sent(sms: dict) -> bool:
    return sms_col.find_one({
        "time":     sms.get("time"),
        "number":   sms.get("number"),
        "full_sms": sms.get("content", "")
    }) is not None


def _api_get(params: dict):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }
    try:
        r = requests.get(MESSAGES_URL, headers=headers, params=params, timeout=10)
    except Exception as e:
        print(f"[!] Request exception: {e}")
        return None

    if r.status_code == 200:
        try:
            return r.json().get("records", [])
        except Exception as e:
            print(f"[!] Bad JSON: {e}")
            return None

    if r.status_code == 429:
        retry = r.headers.get("Retry-After", "5")
        try:
            wait = max(1, int(retry))
        except ValueError:
            wait = 5
        print(f"[!] 429 rate-limited — sleeping {wait}s")
        time.sleep(wait)
        return None

    if r.status_code in (401, 403):
        try:
            err = r.json().get("error", "")
        except Exception:
            err = ""
        print(f"[!] HTTP {r.status_code} {err}")
        return None

    print(f"[!] HTTP {r.status_code}: {r.text[:160]}")
    return None


def _to_utc_dt(iso_str: str):
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def fetch_incremental(latest_seen: datetime):
    buffer_seconds = 3
    fetch_from = latest_seen - timedelta(seconds=buffer_seconds)
    fetch_to   = datetime.now(timezone.utc) + timedelta(seconds=5)   # tolerate clock skew
    params = {
        "from":  fetch_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to":    fetch_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": RECORDS_PER_FETCH,
    }
    return _api_get(params)


def fetch_full_scan():
    return _api_get({"limit": RECORDS_PER_FETCH})


def send_telegram(sms: dict) -> bool:
    if already_sent(sms):
        return False

    raw_msg = sms.get("content", "")
    otp     = extract_otp(raw_msg)
    number  = sms.get("number", "")
    cli     = sms.get("cli", "")
    dt      = sms.get("time", "")
    payout  = sms.get("payout", "")
    rng     = sms.get("range", "")
    status  = sms.get("status", "")

    country_name, country_flag = get_country(number)
    fmt_number  = format_number(number)
    code_to_copy = otp if otp else raw_msg

    text = (
        f"<blockquote>{cli} {country_name} {country_flag}</blockquote>"
        f"<blockquote></blockquote>"
        f"\n<blockquote>Number: <code>{fmt_number}</code></blockquote>"
    )
    reply_markup = {
        "inline_keyboard": [
            [{"text": f"📋 Copy {code_to_copy}", "copy_text": {"text": code_to_copy}}],
            [{"text": "🤖 NUMBER BOT", "url": "https://t.me/HN_NUMBER_BOT"}]
        ]
    }

    try:
        resp = requests.post(
            TG_URL,
            json={
                "chat_id": TG_CHAT,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": reply_markup,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            sms_col.insert_one({
                "time":     dt,
                "number":   number,
                "cli":      cli,
                "otp":      otp if otp else raw_msg,
                "full_sms": raw_msg,
                "payout":   payout,
                "range":    rng,
                "status":   status,
                "panel":    "rsayel_API",
            })
            print("  [✈] Sent to Telegram ✅")
            return True
        else:
            print(f"  [✈] Telegram HTTP {resp.status_code}: {resp.text[:120]}")
        return False
    except Exception as e:
        print(f"  [✈] Telegram error: {e}")
        return False


def print_sms(sms: dict):
    raw_msg = sms.get("content", "")
    otp     = extract_otp(raw_msg)
    number  = sms.get("number", "")
    cli     = sms.get("cli", "")
    dt      = sms.get("time", "")
    payout  = sms.get("payout", "")
    rng     = sms.get("range", "")
    status  = sms.get("status", "")
    country_name, country_flag = get_country(number)

    print("\n" + "━" * 55)
    print(f"  {country_flag}  📱 NEW SMS RECEIVED!")
    print("━" * 55)
    print(f"  🕐 Time    : {dt}")
    print(f"  🌍 Country : {country_name}")
    print(f"  📤 Sender  : {cli}")
    print(f"  📞 Number  : {number}")
    print(f"  📶 Range   : {rng}")
    print(f"  💰 Payout  : {payout} ({status})")
    if otp:
        print(f"  🔑 OTP     : {otp}")
    print(f"  📝 Message :")
    print(f"     {raw_msg}")
    print("━" * 55)


def process_batch(sms_list, latest_seen, message_count):
    global PROCESSED_KEYS
    batch_max = latest_seen

    for sms in reversed(sms_list):     # API returns newest-first → process oldest-first
        try:
            key = sms_key(sms)
            if key in PROCESSED_KEYS:
                continue

            sms_time = _to_utc_dt(sms.get("time", ""))

            if sms_time and sms_time < latest_seen - timedelta(minutes=10):
                PROCESSED_KEYS.add(key)
                continue

            if already_sent(sms):
                PROCESSED_KEYS.add(key)
                continue

            PROCESSED_KEYS.add(key)
            message_count += 1
            print_sms(sms)
            send_telegram(sms)

            if sms_time and sms_time > batch_max:
                batch_max = sms_time

        except Exception as e:
            print(f"[!] Error processing SMS: {e}")

    if len(PROCESSED_KEYS) > MAX_KEYS:
        PROCESSED_KEYS.clear()

    return batch_max, message_count


def main():
    print("╔" + "═" * 63 + "╗")
    print("║   Rsayel SMS Monitor — Reliable Version                     ║")
    print("║   API: /api/v1/messages                                     ║")
    print(f"║   Polling: every {POLL_INTERVAL}s                           ║")
    print("║   Telegram: ON  |  MongoDB: ON                              ║")
    print("╚" + "═" * 63 + "╝\n")

    print("[✓] Starting monitor. Waiting for SMS...\n")

    latest_seen = datetime.now(timezone.utc) - timedelta(minutes=4)
    print(f"[*] Baseline: {latest_seen.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("[*] Press Ctrl+C to stop\n")

    message_count = 0
    error_count   = 0
    last_full_scan = datetime.now(timezone.utc)

    while True:
        try:
            if (datetime.now(timezone.utc) - last_full_scan).total_seconds() > FULL_SCAN_INTERVAL:
                print("\n[*] Full scan (no date filter) to catch missed messages...")
                all_sms = fetch_full_scan()
                if all_sms:
                    print(f"[*] Full scan: {len(all_sms)} records")
                    latest_seen, message_count = process_batch(all_sms, latest_seen, message_count)
                    print(f"[*] Full scan done. Latest: {latest_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                last_full_scan = datetime.now(timezone.utc)

            sms_list = fetch_incremental(latest_seen)

            if sms_list is None:
                error_count += 1
                wait = min(30, error_count)
                print(f"[!] API error. Retry in {wait}s", end="\r")
                time.sleep(wait)
                continue

            error_count = 0

            if sms_list:
                latest_seen, message_count = process_batch(sms_list, latest_seen, message_count)
                print(f"\n[*] Total messages received: {message_count}")
                print(f"[*] Latest seen: {latest_seen.strftime('%Y-%m-%d %H:%M:%S')} UTC")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 55)
            print(f"[✓] Monitor stopped. Total messages received: {message_count}")
            print("=" * 55)
            break
        except Exception as e:
            print(f"\n[!] Unexpected error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()