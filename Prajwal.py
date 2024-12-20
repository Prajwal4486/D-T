import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Define card values
cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Function to create a card in a rectangular style
def create_card(card, side):
    emoji = '🐉' if side == 'dragon' else '🐯'
    return f"┌─────────┐\n│{card:<2}       │\n│         │\n│    {emoji}  │\n│         │\n│       {card:>2}│\n└─────────┘"

# Initialize player balances
player_balances = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in player_balances:
        player_balances[user_id] = 20000
    await update.message.reply_text(
        f"Welcome to the Dragon 🐉 and Tiger 🐯 Casino! Your initial balance is ${player_balances[user_id]}\n"
        "Use /play to start a game."
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in player_balances:
        player_balances[user_id] = 20000
    
    balance = player_balances[user_id]
    await update.message.reply_text(f"Your balance: ${balance}\nEnter your bet amount (1-{balance}):")
    context.user_data['waiting_for_amount'] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if context.user_data.get('waiting_for_amount'):
        await handle_amount(update, context)
    elif context.user_data.get('hack'):
        await handle_hack(update, context)

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    balance = player_balances[user_id]
    
    try:
        amount = int(update.message.text)
        if 0 < amount <= balance:
            context.user_data['bet_amount'] = amount
            context.user_data['waiting_for_amount'] = False
            
            keyboard = [
                [InlineKeyboardButton("Dragon 🐉", callback_data="bet_dragon"),
                 InlineKeyboardButton("Tiger 🐯", callback_data="bet_tiger"),
                 InlineKeyboardButton("Tie", callback_data="bet_tie")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"You bet ${amount}. Now choose Dragon, Tiger, or Tie:", reply_markup=reply_markup)
        else:
            await update.message.reply_text(f"Please enter a valid amount between 1 and {balance}")
    except ValueError:
        await update.message.reply_text("Please enter a valid number")

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    balance = player_balances[user_id]
    bet_choice = query.data.split('_')[1]
    amount = context.user_data['bet_amount']
    
    # Play the game
    dragon_card = random.choice(cards)
    tiger_card = random.choice(cards)
    
    result_message = "Dragon 🐉 Card:\n"
    result_message += f"<pre>{create_card(dragon_card, 'dragon')}</pre>\n\n"
    result_message += "Tiger 🐯 Card:\n"
    result_message += f"<pre>{create_card(tiger_card, 'tiger')}</pre>\n\n"
    
    dragon_value = cards.index(dragon_card)
    tiger_value = cards.index(tiger_card)
    
    if dragon_value > tiger_value:
        result = 'dragon'
        result_message += "Dragon Wins!"
    elif tiger_value > dragon_value:
        result = 'tiger'
        result_message += "Tiger Wins!"
    else:
        result = 'tie'
        result_message += "It's a Tie!"
    
    if bet_choice == result:
        if result == 'tie':
            winnings = amount * 12
            balance += winnings - amount
            result_message += f"\nYou won ${winnings}!"
        else:
            balance += amount
            result_message += f"\nYou won ${amount}!"
    else:
        if result == 'tie':
            refund = amount // 2
            balance -= refund
            result_message += f"\nHalf of your bet (${refund}) is returned."
        else:
            balance -= amount
            result_message += f"\nYou lost ${amount}."
    
    player_balances[user_id] = balance
    result_message += f"\nCurrent balance = ${balance}"
    
    await query.edit_message_text(result_message, parse_mode='HTML')
    await query.message.reply_text("Use /play to play again.")

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text("Enter your desired balance:")
    context.user_data['hack'] = True

async def handle_hack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        new_balance = int(update.message.text)
        user_id = update.effective_user.id
        player_balances[user_id] = new_balance
        await update.message.reply_text(f"Your new balance is ${new_balance}")
        context.user_data['hack'] = False
        await play(update, context)
    except ValueError:
        await update.message.reply_text("Invalid input. Please enter a valid number.")

def main() -> None:
    application = Application.builder().token("token_here").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("hack", hack))
    application.add_handler(CallbackQueryHandler(handle_bet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()
