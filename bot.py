import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from google_sheets import GoogleSheetsService

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en el archivo .env")

try:
    ALLOWED_GROUP_ID = int(TELEGRAM_GROUP_ID) if TELEGRAM_GROUP_ID else None
except ValueError:
    raise RuntimeError("TELEGRAM_GROUP_ID debe ser un número entero.")

sheets = GoogleSheetsService()


def es_grupo_permitido(update: Update) -> bool:
    """Permite trabajar solo en el grupo configurado."""
    chat = update.effective_chat
    if chat is None:
        return False

    # Si no se configura grupo, permite cualquier chat.
    if ALLOWED_GROUP_ID is None:
        return True

    return chat.id == ALLOWED_GROUP_ID


async def acceso_denegado(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer(
            "Este bot no está habilitado en este grupo.",
            show_alert=True,
        )
    elif update.effective_message:
        await update.effective_message.reply_text(
            "⛔ Este bot no está habilitado en este grupo."
        )


def menu_principal() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔎 Consultar DNI/CE", callback_data="buscar_dni")],
        [InlineKeyboardButton("📋 Consultar por nombre", callback_data="buscar_nombre")],
        [InlineKeyboardButton("🎫 Consultar por fotocheck", callback_data="buscar_fotocheck")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
    ]
    return InlineKeyboardMarkup(keyboard)


def botones_cancelar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ])


def botones_resultado() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Nueva consulta", callback_data="menu")]
    ])


def normalizar_encabezado(valor) -> str:
    """Normaliza encabezados de Google Sheets."""
    if valor is None:
        return ""

    texto = str(valor).strip().upper()

    # Convierte múltiples espacios/saltos de línea en un solo espacio
    texto = " ".join(texto.split())

    return texto


def obtener_campo(registro: dict, nombre_columna: str):
    """
    Obtiene un campo del registro aunque el encabezado de Google Sheets
    tenga diferencias de espacios, mayúsculas/minúsculas o saltos de línea.
    """

    encabezado_buscado = normalizar_encabezado(nombre_columna)

    # Primero intenta encontrar coincidencia exacta normalizada
    for clave, valor in registro.items():
        if normalizar_encabezado(clave) == encabezado_buscado:
            return valor

    return None


def formatear(valor) -> str:
    if valor is None:
        return "-"

    texto = str(valor).strip()

    return texto if texto else "-"


def resultado_a_texto(registro: dict) -> str:
    return (
        "╔════════════════════════════╗\n"
        "   📋 FIRMA AUTORIZADA\n"
        "╚════════════════════════════╝\n\n"

        f"👤 NOMBRES Y APELLIDOS:\n"
        f"{formatear(obtener_campo(registro, 'NOMBRES Y APELLIDOS'))}\n\n"

        f"🪪 DNI / CE:\n"
        f"{formatear(obtener_campo(registro, 'DNI / CE'))}\n\n"

        f"💼 CARGO:\n"
        f"{formatear(obtener_campo(registro, 'CARGO'))}\n\n"

        f"🎫 FOTOCHECK:\n"
        f"{formatear(obtener_campo(registro, 'FOTOCHECK'))}\n\n"

        "📑 AUTORIZACIONES\n"
        "━━━━━━━━━━━━━━━━━━━━\n"

        f"📄 Ficha de Ingreso: "
        f"{formatear(obtener_campo(registro, 'Ficha Ingreso de CONPRO y Visitantes (Solo para MCP)'))}\n"

        f"👷 Movimiento MCP: "
        f"{formatear(obtener_campo(registro, 'Movimiento de Personal MCP'))}\n"

        f"📦 Materiales/Equipos: "
        f"{formatear(obtener_campo(registro, 'Materiales y Equipos (MCP y CONPRO)'))}\n"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_grupo_permitido(update):
        await acceso_denegado(update)
        return

    context.user_data.clear()

    await update.effective_message.reply_text(
        "🤖 BOT DE CONSULTAS\n\n¿Qué deseas consultar?",
        reply_markup=menu_principal(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not es_grupo_permitido(update):
        await acceso_denegado(update)
        return

    accion = query.data

    if accion == "cancelar":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Consulta cancelada.\n\nPulsa /start para abrir nuevamente el menú."
        )
        return

    if accion == "menu":
        context.user_data.clear()
        await query.edit_message_text(
            "🤖 BOT DE CONSULTAS\n\n¿Qué deseas consultar?",
            reply_markup=menu_principal(),
        )
        return

    if accion == "buscar_dni":
        context.user_data["modo_busqueda"] = "dni"
        await query.edit_message_text(
            "🪪 CONSULTA POR DNI / CE\n\n"
            "Ingrese el número de DNI o CE:\n\n"
            "💡 Los espacios y mayúsculas/minúsculas no afectan la búsqueda.",
            reply_markup=botones_cancelar(),
        )
        return

    if accion == "buscar_nombre":
        context.user_data["modo_busqueda"] = "nombre"
        await query.edit_message_text(
            "📋 CONSULTA POR NOMBRE\n\n"
            "Ingrese nombres o apellidos:\n\n"
            "💡 No importa si escribe en mayúsculas o minúsculas.",
            reply_markup=botones_cancelar(),
        )
        return

    if accion == "buscar_fotocheck":
        context.user_data["modo_busqueda"] = "fotocheck"
        await query.edit_message_text(
            "🎫 CONSULTA POR FOTOCHECK\n\n"
            "Ingrese el número o código del fotocheck:\n\n"
            "💡 Los espacios y mayúsculas/minúsculas no afectan la búsqueda.",
            reply_markup=botones_cancelar(),
        )


async def recibir_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_grupo_permitido(update):
        await acceso_denegado(update)
        return

    modo = context.user_data.get("modo_busqueda")
    if not modo:
        return

    texto = (update.effective_message.text or "").strip()

    if not texto:
        await update.effective_message.reply_text(
            "⚠️ Ingrese un valor válido.",
            reply_markup=botones_cancelar(),
        )
        return

    try:
        if modo == "dni":
            resultados = sheets.buscar_dni_ce(texto)
        elif modo == "nombre":
            resultados = sheets.buscar_nombre(texto)
        elif modo == "fotocheck":
            resultados = sheets.buscar_fotocheck(texto)
        else:
            resultados = []

    except Exception:
        logger.exception("Error consultando Google Sheets")
        await update.effective_message.reply_text(
            "❌ Ocurrió un error al consultar Google Sheets.\n"
            "Revise la conexión y las credenciales.",
            reply_markup=menu_principal(),
        )
        return

    if not resultados:
        await update.effective_message.reply_text(
            "🔍 NO SE ENCONTRARON RESULTADOS\n\n"
            f"Consulta: {texto}\n\n"
            "Verifique el dato ingresado e intente nuevamente.",
            reply_markup=menu_principal(),
        )
        context.user_data.clear()
        return

    # Para DNI/CE y fotocheck normalmente habrá una coincidencia.
    # Para nombre pueden existir varias.
    if len(resultados) == 1:
        await update.effective_message.reply_text(
            resultado_a_texto(resultados[0]),
            reply_markup=botones_resultado(),
        )
    else:
        # Evitamos mensajes gigantes si existen muchas coincidencias.
        lineas = ["🔎 RESULTADOS ENCONTRADOS\n"]
        for i, registro in enumerate(resultados[:20], start=1):
            lineas.append(
                f"{i}. {formatear(registro.get('NOMBRES Y APELLIDOS'))}\n"
                f"   🪪 {formatear(registro.get('DNI / CE'))}\n"
                f"   🎫 {formatear(registro.get('FOTOCHECK'))}\n"
            )

        if len(resultados) > 20:
            lineas.append(f"\nMostrando 20 de {len(resultados)} resultados.")

        lineas.append("\n💡 Para ver una persona específica, consulte por DNI/CE o fotocheck.")

        await update.effective_message.reply_text(
            "\n".join(lineas),
            reply_markup=botones_resultado(),
        )

    context.user_data.clear()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Excepción no controlada", exc_info=context.error)


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(
        menu_callback,
        pattern="^(buscar_dni|buscar_nombre|buscar_fotocheck|cancelar|menu)$",
    ))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_busqueda)
    )
    application.add_error_handler(error_handler)

    # Configuración para Render Web Service.
    # Render proporciona PORT y RENDER_EXTERNAL_URL automáticamente.
    port = int(os.getenv("PORT", "10000"))
    external_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()

    if not external_url:
        raise RuntimeError(
            "No se encontró RENDER_EXTERNAL_URL. "
            "Este bot está configurado para ejecutarse como Web Service en Render."
        )

    # El token se utiliza como ruta del webhook para evitar exponer
    # un endpoint Telegram genérico.
    webhook_url = f"{external_url.rstrip('/')}/{TELEGRAM_BOT_TOKEN}"

    logger.info("Bot iniciado en modo webhook.")
    logger.info("Puerto HTTP: %s", port)
    logger.info("Webhook configurado en: %s/<TOKEN>", external_url.rstrip("/"))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()