from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "8867542719:AAFsS6_GTq5D3WZ2eYWkTiakcU4_B4Ru8PQ"


async def obtener_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    print("\n==============================")
    print("NOMBRE DEL GRUPO:", chat.title)
    print("ID DEL GRUPO:", chat.id)
    print("TIPO:", chat.type)
    print("==============================\n")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.ALL, obtener_id)
    )

    print("🤖 Bot iniciado...")
    print("👉 Agrega el bot al grupo y envía un mensaje.")
    print("👉 El ID aparecerá aquí.\n")

    app.run_polling()


if __name__ == "__main__":
    main()