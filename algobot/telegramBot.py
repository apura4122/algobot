import random

from telegram import Bot
from telegram.ext import Updater, CommandHandler
from enums import LONG, SHORT, LIVE


class TelegramBot:
    def __init__(self, gui, token, botThread):
        self.token = token
        self.updater = Updater(token, use_context=True)
        self.bot = Bot(token=self.token)

        # Get the dispatcher to register handlers
        self.gui = gui
        self.botThread = botThread
        dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("help", self.help_telegram))
        dp.add_handler(CommandHandler("override", self.override_telegram))
        dp.add_handler(CommandHandler('trades', self.get_trades_telegram))
        dp.add_handler(CommandHandler('resume', self.resume_telegram))
        dp.add_handler(CommandHandler('pause', self.pause_telegram))
        dp.add_handler(CommandHandler('removecustomstoploss', self.remove_custom_stop_loss))
        dp.add_handler(CommandHandler('setcustomstoploss', self.set_custom_stop_loss))
        dp.add_handler(CommandHandler("forcelong", self.force_long_telegram))
        dp.add_handler(CommandHandler("forceshort", self.force_short_telegram))
        dp.add_handler(CommandHandler('exitposition', self.exit_position_telegram))
        dp.add_handler(CommandHandler(('stats', 'statistics'), self.get_statistics_telegram))
        dp.add_handler(CommandHandler(("position", 'getposition'), self.get_position_telegram))
        dp.add_handler(CommandHandler(("update", 'updatevalues'), self.update_values))
        dp.add_handler(CommandHandler(("thanks", 'thanksbot', 'thankyou'), self.thank_bot_telegram))
        dp.add_handler(CommandHandler(("print", 'makethatbread', 'printmoney'), self.print_telegram))

    def send_message(self, chatID, message):
        self.bot.send_message(chat_id=chatID, text=message)

    def start(self):
        # Start the Bot
        self.updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        # self.updater.idle()

    def stop(self):
        self.updater.stop()

    # noinspection PyUnusedLocal
    def get_trades_telegram(self, update, context):
        trader = self.gui.trader
        trades = trader.trades

        message = ''
        for index, trade in enumerate(trades, start=1):
            message += f'Trade {index}:\n'
            message += f'Date in UTC: {trade["date"].strftime("%m/%d/%Y, %H:%M:%S")}\n'
            message += f'Order ID: {trade["orderID"]}\n'
            message += f'Pair: {trade["pair"]}\n'
            message += f'Action: {trade["action"]}\n'
            message += f'Price: {trade["price"]}\n'
            message += f'Method: {trade["method"]}\n'
            message += f'Percentage: {trade["percentage"]}\n'
            message += f'Profit: {trade["profit"]}\n\n'

        if message == '':
            message = "No trades made yet."

        update.message.reply_text(message)

    # noinspection PyUnusedLocal
    @staticmethod
    def help_telegram(update, context):
        update.message.reply_text("Here are your help commands available:\n"
                                  "/help -> To get commands available.\n"
                                  "/forcelong  -> To force long.\n"
                                  "/forceshort -> To force short.\n"
                                  "/position or /getposition -> To get position.\n"
                                  "/stats or /statistics -> To get current statistics.\n"
                                  "/override -> To exit trade and wait for next cross.\n"
                                  "/resume -> To resume bot logic.\n"
                                  "/pause -> To pause bot logic.\n"
                                  "/removecustomstoploss -> To remove currently set custom stop loss.\n"
                                  "/setcustomstoploss (your stop loss value here) -> To set custom stop loss.\n"
                                  "/exitposition -> To exit position.\n"
                                  "/trades -> To get list of trades made.\n"
                                  "/update or /updatevalues -> To update current coin values.\n"
                                  "/thanks or /thankyou or /thanksbot -> to thank the bot. \n")

    # noinspection PyUnusedLocal
    def update_values(self, update, context):
        self.gui.trader.retrieve_margin_values()
        update.message.reply_text("Successfully retrieved new values from Binance.")

    def get_statistics(self):
        trader = self.gui.trader
        profit = trader.get_profit()
        profitLabel = trader.get_profit_or_loss_string(profit=profit)

        optionString = ''

        for option in self.botThread.optionDetails:  # previously trader.tradingOptions
            avg1, avg2, name1, name2 = option
            optionString += f'{name1}: ${avg1}\n'
            optionString += f'{name2}: ${avg2}\n'

        return (f'Symbol: {trader.symbol}\n'
                f'Position: {trader.get_position_string()}\n'
                f'Total trades made: {len(trader.trades)}\n'
                f"Coin owned: {trader.coin}\n"
                f"Coin owed: {trader.coinOwed}\n"
                f"Starting balance: ${round(trader.startingBalance, 2)}\n"
                f"Balance: ${round(trader.balance, 2)}\n"
                f'Net: ${round(trader.get_net(), 2)}\n'
                f"{profitLabel}: ${round(abs(profit), 2)}\n"
                f'{profitLabel} Percentage: {round(self.botThread.percentage, 2)}%\n'
                f'Daily Percentage: {round(self.botThread.dailyPercentage, 2)}%\n'
                f'Autonomous Mode: {not trader.inHumanControl}\n'
                f'Loss Strategy: {trader.get_stop_loss_strategy_string()}\n'
                f'Stop Loss Percentage: {round(trader.lossPercentageDecimal * 100, 2)}%\n'
                f'Stop Loss: {trader.get_safe_rounded_string(trader.get_stop_loss())}\n'
                f"Custom Stop Loss: {trader.get_safe_rounded_string(trader.customStopLoss)}\n"
                f"Current {trader.coinName} price: ${trader.currentPrice}\n"
                f'Elapsed time: {self.botThread.elapsed}\n'
                f'Stoic Enabled: {trader.stoicEnabled}\n'
                f'Stoic Trend: {trader.get_trend_string(trader.stoicTrend)}\n'
                f'Stoic Input 1: {trader.stoicOptions[0]}\n'
                f'Stoic Input 2: {trader.stoicOptions[1]}\n'
                f'Stoic Input 3: {trader.stoicOptions[2]}\n'
                f'{optionString}'
                )

    def send_statistics_telegram(self, chatID, period):
        message = f"Periodic statistics every {period}: \n"
        self.send_message(chatID, message + self.get_statistics())

    # noinspection PyUnusedLocal
    def get_statistics_telegram(self, update, context):
        message = "Here are your statistics as requested: \n"
        update.message.reply_text(message + self.get_statistics())

    # noinspection PyUnusedLocal
    @staticmethod
    def thank_bot_telegram(update, context):
        messages = [
            "You're welcome.",
            "My pleasure.",
            "Embrace monke.",
            "No problem.",
            "Don't thank me. Thank Monke.",
            "Sure thing."
        ]
        update.message.reply_text(random.choice(messages))

    # noinspection PyUnusedLocal
    @staticmethod
    def print_telegram(update, context):
        messages = [
            "Let's print this money. Printing...",
            "Opening a bakery soon. Printing...",
            "The FED will ask us for money.",
            "Alright. Printing in progress...",
            "it's literally free money. Printing...",
            "Puts on people who don't use AlgoBot. Printing....",
            "PRINTING IN PROGRESS....",
            "PRINTING INITIALIZED...."
        ]
        update.message.reply_text(random.choice(messages))

    # noinspection PyUnusedLocal
    def override_telegram(self, update, context):
        update.message.reply_text("Overriding.")
        self.botThread.signals.waitOverride.emit()
        update.message.reply_text("Successfully overrode.")

    # noinspection PyUnusedLocal
    def pause_telegram(self, update, context):
        if self.gui.trader.inHumanControl:
            update.message.reply_text("Bot is already in human control.")
        else:
            self.botThread.signals.pause.emit()
            update.message.reply_text("Bot has been paused successfully.")

    # noinspection PyUnusedLocal
    def resume_telegram(self, update, context):
        if not self.gui.trader.inHumanControl:
            update.message.reply_text("Bot is already in autonomous mode.")
        else:
            self.botThread.signals.resume.emit()
            update.message.reply_text("Bot logic has been resumed.")

    # noinspection PyUnusedLocal
    def remove_custom_stop_loss(self, update, context):
        if self.gui.trader.customStopLoss is None:
            update.message.reply_text("Bot already has no custom stop loss implemented.")
        else:
            self.botThread.signals.removeCustomStopLoss.emit()
            update.message.reply_text("Bot's custom stop loss has been removed.")

    def set_custom_stop_loss(self, update, context):
        stopLoss = context.args[0]

        try:
            stopLoss = float(stopLoss)
        except ValueError:
            update.message.reply_text("Please make sure you specify a number for the custom stop loss.")
            return
        except Exception as e:
            update.message.reply_text(f'An error occurred: {e}.')
            return

        if stopLoss < 0:
            update.message.reply_text("Please make sure you specify a non-negative number for the custom stop loss.")
        elif stopLoss > 10000000:
            update.message.reply_text("Please make sure you specify a number that is less than 10000000.")
        else:
            stopLoss = round(stopLoss, 2)
            self.botThread.signals.setCustomStopLoss.emit(LIVE, True, stopLoss)
            update.message.reply_text(f"Stop loss has been successfully set to ${stopLoss}.")

    # noinspection PyUnusedLocal
    def force_long_telegram(self, update, context):
        position = self.gui.trader.get_position()
        if position == LONG:
            update.message.reply_text("Bot is already in a long position.")
        else:
            update.message.reply_text("Forcing long.")
            self.botThread.signals.forceLong.emit()
            update.message.reply_text("Successfully forced long.")

    # noinspection PyUnusedLocal
    def force_short_telegram(self, update, context):
        position = self.gui.trader.get_position()
        if position == SHORT:
            update.message.reply_text("Bot is already in a short position.")
        else:
            update.message.reply_text("Forcing short.")
            self.botThread.signals.forceShort.emit()
            update.message.reply_text("Successfully forced short.")

    # noinspection PyUnusedLocal
    def exit_position_telegram(self, update, context):
        if self.gui.trader.get_position() is None:
            update.message.reply_text("Bot is not in a position.")
        else:
            update.message.reply_text("Exiting position.")
            self.botThread.signals.exitPosition.emit()
            update.message.reply_text("Successfully exited position.")

    # noinspection PyUnusedLocal
    def get_position_telegram(self, update, context):
        position = self.gui.trader.get_position()
        if position == SHORT:
            update.message.reply_text("Bot is currently in a short position.")
        elif position == LONG:
            update.message.reply_text("Bot is currently in a long position.")
        else:
            update.message.reply_text("Bot is currently not in any position.")
