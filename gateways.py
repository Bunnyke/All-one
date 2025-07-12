# gateways.py

async def handle_stripe(update, context):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /chk <code>cc|mm|yy|cvv</code>", parse_mode="HTML")
        return
    cc_input = " ".join(context.args)
    # --- PLACE YOUR STRIPE CHECK LOGIC HERE ---
    await update.message.reply_text(
        f"Result for <code>{cc_input}</code>:\n<b>Demo: Stripe Auth checker (add your logic here).</b>",
        parse_mode="HTML"
    )

async def handle_braintree(update, context):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /b3 <code>cc|mes|ano|cvv</code>", parse_mode="HTML")
        return
    cc_input = " ".join(context.args)
    # --- PLACE YOUR BRAINTREE CHECK LOGIC HERE ---
    await update.message.reply_text(
        f"Result for <code>{cc_input}</code>:\n<b>Demo: Braintree Auth checker (add your logic here).</b>",
        parse_mode="HTML"
    )
