import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from stripe_Auth import stripe_cmd, handle_braintree
from tools import handle_bin, handle_fake, handle_scr

ADMIN_ID = 5387926427  # <-- Set your Telegram user ID here

# ---- Registration System ----
def load_registered_users(filename="users.txt"):
    try:
        with open(filename, "r") as f:
            return set(int(line.strip()) for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_registered_user(user_id, filename="users.txt"):
    with open(filename, "a") as f:
        f.write(f"{user_id}\n")

def remove_registered_user(user_id, filename="users.txt"):
    users = load_registered_users(filename)
    users.discard(user_id)
    with open(filename, "w") as f:
        for uid in users:
            f.write(f"{uid}\n")
    return users

registered_users = load_registered_users()

menu_status = {
    "b3": True,
    "chk": True,
    "bin": True,
    "fake": True,
    "scr": False
}

def get_anime_banner():
    try:
        r = requests.get("https://api.waifu.pics/sfw/waifu", timeout=8)
        return r.json()["url"]
    except Exception:
        return "https://i.waifu.pics/I9ynlMu.jpg"

def username_fancy(name):
    # Bold, spaced-out, all-caps style for name
    return " ".join(f"<b>{c.upper()}</b>" for c in (name or "User"))

def panel_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 Gateway", callback_data="menu_gateway"),
            InlineKeyboardButton("🛠️ Tools", callback_data="menu_lookup"),
            InlineKeyboardButton("📈 Status", callback_data="menu_stats")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
    ])

def reg_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Register", callback_data="menu_register")],
        [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
    ])

async def send_main_panel(context, chat_id, username, is_registered):
    banner = get_anime_banner()
    if is_registered:
        text = (
            f"🌸 <b>Welcome back, {username}!</b>\n\n"
            "✅ <b>You're now a verified user!</b>\n"
            "Choose a feature below to explore the bot 🚀\n\n"
            "✨ Have fun!"
        )
        reply_markup = panel_menu()
    else:
        text = (
            f"👋 <b>WELCOME {username}!</b>\n\n"
            "🔒 <b>Registration Required!</b>\n"
            "To unlock all features, please tap <b>Register</b> below.\n\n"
            "🛡️ It's quick and safe — join our community now!"
        )
        reply_markup = reg_menu()
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=banner,
        caption=text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_registered = user_id in registered_users
    username = username_fancy(update.effective_user.first_name)
    await send_main_panel(context, update.effective_chat.id, username, is_registered)

async def menu_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users
    query = update.callback_query
    user_id = query.from_user.id
    is_registered = user_id in registered_users
    username = username_fancy(query.from_user.first_name)

    if query.data == "menu_close":
        await query.message.delete()
        return

    if query.data == "menu_register":
        if not is_registered:
            registered_users.add(user_id)
            save_registered_user(user_id)
            await query.message.delete()
            await send_main_panel(context, query.message.chat_id, username, True)
            return
        else:
            await query.answer("Already registered!", show_alert=True)
            return

    if not is_registered:
        await query.answer("❗ Please register first!", show_alert=True)
        return

    if query.data == "menu_gateway":
        gateway_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_back")],
            [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
        ])
        gateways_text = (
            f"[ϟ] Name: Braintree Auth\n"
            f"[ϟ] Command: /b3 cc|mes|ano|cvv\n"
            f"[ϟ] Status: {'Active ✅' if menu_status['b3'] else 'Off ❌'}\n"
            "━━━━━━━━━━━━━\n"
            f"[ϟ] Name: Stripe Auth\n"
            f"[ϟ] Command: /chk cc|mes|ano|cvv\n"
            f"[ϟ] Status: {'Active ✅' if menu_status['chk'] else 'Off ❌'}"
        )
        await query.answer()
        await query.edit_message_caption(
            caption=f"<pre>{gateways_text}</pre>",
            parse_mode="HTML",
            reply_markup=gateway_menu
        )

    elif query.data == "menu_lookup":
        tools_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_back")],
            [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
        ])
        tools_text = (
            f"[ϟ] Name: BIN Lookup\n"
            f"[ϟ] Command: /bin\n"
            f"[ϟ] Status: {'Active ✅' if menu_status['bin'] else 'Off ❌'}\n"
            "━━━━━━━━━━━━━\n"
            f"[ϟ] Name: Fake Address\n"
            f"[ϟ] Command: /fake us\n"
            f"[ϟ] Status: {'Active ✅' if menu_status['fake'] else 'Off ❌'}\n"
            "━━━━━━━━━━━━━\n"
            f"[ϟ] Name: Scrapper\n"
            f"[ϟ] Command: /scr\n"
            f"[ϟ] Status: {'Active ✅' if menu_status['scr'] else 'Coming Soon 🕓'}"
        )
        await query.answer()
        await query.edit_message_caption(
            caption=f"<pre>{tools_text}</pre>",
            parse_mode="HTML",
            reply_markup=tools_menu
        )

    elif query.data == "menu_stats":
        stats_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_back")],
            [InlineKeyboardButton("❌ Close", callback_data="menu_close")]
        ])
        await query.answer()
        await query.edit_message_caption(
            caption="📈 <b>Status</b>\nBot is online!\nMore stats coming soon...",
            parse_mode="HTML",
            reply_markup=stats_menu
        )

    elif query.data == "menu_back":
        await query.message.delete()
        await send_main_panel(context, query.message.chat_id, username, True)

# --- Admin panel and status remains as before ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❗ You are not authorized to use this command.")
        return
    await update.message.reply_text(
        "<b>🛡️ Admin Panel</b>\n\n"
        "<b>/remove_user &lt;user_id&gt;</b> — Remove a user from database.\n"
        "<b>/set_status &lt;item&gt; &lt;on|off&gt;</b> — Change menu status (Active/Off).\n\n"
        "<b>Items:</b> <code>b3</code> (Braintree), <code>chk</code> (Stripe), <code>bin</code> (BIN Lookup), <code>fake</code> (Fake Address), <code>scr</code> (Scrapper)\n\n"
        "Example: <code>/set_status chk off</code>\n"
        "Example: <code>/remove_user 123456789</code>",
        parse_mode="HTML"
    )

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❗ You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove_user <user_id>")
        return
    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text("Invalid user_id.")
        return
    if uid in registered_users:
        registered_users = remove_registered_user(uid)
        await update.message.reply_text(f"✅ User {uid} removed from database.")
    else:
        await update.message.reply_text(f"User {uid} not found in database.")

async def set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❗ You are not authorized.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /set_status <item> <on|off>")
        return
    item, value = context.args
    if item not in menu_status:
        await update.message.reply_text(f"No such menu item: {item}")
        return
    menu_status[item] = (value.lower() == "on")
    await update.message.reply_text(
        f"Set {item} status to {'Active ✅' if menu_status[item] else 'Off ❌'}"
    )

def main():
    app = Application.builder().token("8039426526:AAFSqWU-fRl_gwTPqYLK8yxuS0N9at1hC4s").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_nav))

    # Gateway & Tool commands
    app.add_handler(CommandHandler("chk", handle_stripe))
    app.add_handler(CommandHandler("b3", handle_braintree))
    app.add_handler(CommandHandler("bin", handle_bin))
    app.add_handler(CommandHandler("fake", handle_fake))
    app.add_handler(CommandHandler("scr", handle_scr))

    # Admin commands
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("remove_user", remove_user))
    app.add_handler(CommandHandler("set_status", set_status))

    app.run_polling()

if __name__ == "__main__":
    main()
