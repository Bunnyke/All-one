import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from gateways import handle_stripe, handle_braintree
from tools import handle_bin, handle_fake, handle_scr

ADMIN_ID = 5387926427  # <-- Replace with your UID

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
    r = requests.get("https://api.waifu.pics/sfw/waifu", timeout=8)
    return r.json()["url"]

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Gateway", callback_data="menu_gateway")],
        [InlineKeyboardButton("🛠️ Tools", callback_data="menu_lookup")],
        [InlineKeyboardButton("📈 Status", callback_data="menu_stats")]
    ])

def reg_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Register", callback_data="menu_register")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    img_url = get_anime_banner()
    if user_id in registered_users:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_url,
            caption="<b>Welcome back! Choose an option below:</b>",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_url,
            caption="✨ <b>Welcome!</b>\n\nPlease register to use this bot.",
            parse_mode="HTML",
            reply_markup=reg_menu()
        )

async def menu_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global registered_users
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "menu_register":
        registered_users.add(user_id)
        save_registered_user(user_id)  # Save user to file
        img_url = get_anime_banner()
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=img_url,
            caption="✅ <b>Registration complete!</b>\nChoose an option below:",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        return

    if user_id not in registered_users:
        await query.answer("❗ Please register first.", show_alert=True)
        await query.message.delete()
        img_url = get_anime_banner()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=img_url,
            caption="✨ <b>Welcome!</b>\n\nPlease register to use this bot.",
            parse_mode="HTML",
            reply_markup=reg_menu()
        )
        return

    if query.data == "menu_gateway":
        gateway_menu = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_back")]
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
            [InlineKeyboardButton("🔙 Back", callback_data="menu_back")]
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
        await query.answer()
        await query.edit_message_caption(
            caption="📈 <b>Status</b>\nBot is online!\nMore stats coming soon...",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="menu_back")]
            ])
        )

    elif query.data == "menu_back":
        img_url = get_anime_banner()
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=img_url,
            caption="<b>Welcome! Choose an option below 👇</b>",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

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
