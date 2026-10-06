import os
import re
import unicodedata
from pathlib import Path

import gspread
from dotenv import load_dotenv


# Cargar variables del archivo .env
load_dotenv()


def normalizar_texto(valor: object) -> str:
    """
    Normaliza texto para las búsquedas.

    - Convierte a texto.
    - Normaliza caracteres Unicode.
    - Elimina espacios al inicio y final.
    - Convierte a mayúsculas.
    - Convierte múltiples espacios en uno solo.
    """
    if valor is None:
        return ""

    texto = str(valor)

    texto = unicodedata.normalize("NFKC", texto)

    texto = texto.strip()

    texto = texto.upper()

    texto = re.sub(r"\s+", " ", texto)

    return texto


def normalizar_codigo(valor: object) -> str:
    """
    Normaliza códigos como DNI/CE y FOTOCHECK.

    Ejemplo:

        " 123 456 789 " -> "123456789"
        "ab 123"        -> "AB123"
    """
    return normalizar_texto(valor).replace(" ", "")


class GoogleSheetsService:
    """
    Servicio para conectarse y consultar Google Sheets.

    Prioridad para abrir el archivo:

    1. GOOGLE_SHEET_ID
    2. GOOGLE_SHEET_NAME

    El ID es recomendado porque evita problemas si el archivo
    cambia de nombre o existen varios archivos con nombres similares.
    """

    def __init__(self):

        # ---------------------------------------------------------
        # CONFIGURACIÓN
        # ---------------------------------------------------------

        credentials_file = os.getenv(
            "GOOGLE_CREDENTIALS_FILE",
            "credentials/google-service-account.json",
        ).strip()

        spreadsheet_id = os.getenv(
            "GOOGLE_SHEET_ID",
            "",
        ).strip()

        spreadsheet_name = os.getenv(
            "GOOGLE_SHEET_NAME",
            "Firmas Autorizadas - 2026",
        ).strip()

        worksheet_name = os.getenv(
            "GOOGLE_WORKSHEET_NAME",
            "",
        ).strip()

        # ---------------------------------------------------------
        # VALIDAR ARCHIVO DE CREDENCIALES
        # ---------------------------------------------------------

        credentials_path = Path(credentials_file)

        if not credentials_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de credenciales de Google:\n"
                f"{credentials_path.resolve()}\n\n"
                f"Verifica la variable GOOGLE_CREDENTIALS_FILE en el archivo .env."
            )

        # ---------------------------------------------------------
        # CONECTAR CON GOOGLE
        # ---------------------------------------------------------

        try:
            self.client = gspread.service_account(
                filename=str(credentials_path)
            )
        except Exception as error:
            raise RuntimeError(
                "No se pudo conectar con Google Sheets.\n"
                f"Detalle: {error}"
            ) from error

        # ---------------------------------------------------------
        # ABRIR GOOGLE SHEET
        # ---------------------------------------------------------
        #
        # PRIORIDAD:
        #
        # 1. GOOGLE_SHEET_ID
        # 2. GOOGLE_SHEET_NAME
        #
        # ---------------------------------------------------------

        try:

            if spreadsheet_id:

                print("🔗 Abriendo Google Sheet mediante GOOGLE_SHEET_ID...")

                self.spreadsheet = self.client.open_by_key(
                    spreadsheet_id
                )

            else:

                print(
                    "⚠️ GOOGLE_SHEET_ID no está configurado."
                )

                print(
                    f"📄 Abriendo Google Sheet mediante nombre: "
                    f"{spreadsheet_name}"
                )

                self.spreadsheet = self.client.open(
                    spreadsheet_name
                )

        except gspread.exceptions.SpreadsheetNotFound as error:

            if spreadsheet_id:

                raise RuntimeError(
                    "No se pudo encontrar o acceder al Google Sheet mediante "
                    "GOOGLE_SHEET_ID.\n\n"
                    f"ID utilizado: {spreadsheet_id}\n\n"
                    "Verifica que:\n"
                    "1. El ID del Google Sheet sea correcto.\n"
                    "2. El Google Sheet esté compartido con el "
                    "client_email de tu cuenta de servicio.\n"
                    "3. La cuenta de servicio tenga al menos permiso de "
                    "Lector."
                ) from error

            else:

                raise RuntimeError(
                    "No se encontró el Google Sheet mediante su nombre.\n\n"
                    f"Nombre utilizado: {spreadsheet_name}\n\n"
                    "Se recomienda configurar GOOGLE_SHEET_ID en el archivo .env."
                ) from error

        except Exception as error:

            raise RuntimeError(
                "Ocurrió un error al abrir el Google Sheet.\n"
                f"Detalle: {error}"
            ) from error

        # ---------------------------------------------------------
        # MOSTRAR INFORMACIÓN DEL ARCHIVO
        # ---------------------------------------------------------

        print(
            f"✅ Google Sheet conectado: "
            f"{self.spreadsheet.title}"
        )

        # ---------------------------------------------------------
        # SELECCIONAR HOJA / PESTAÑA
        # ---------------------------------------------------------

        try:

            if worksheet_name:

                print(
                    f"📑 Seleccionando pestaña: {worksheet_name}"
                )

                self.worksheet = self.spreadsheet.worksheet(
                    worksheet_name
                )

            else:

                print(
                    "📑 No se indicó GOOGLE_WORKSHEET_NAME."
                )

                print(
                    "📑 Se utilizará la primera pestaña del archivo."
                )

                self.worksheet = self.spreadsheet.sheet1

        except gspread.exceptions.WorksheetNotFound as error:

            raise RuntimeError(
                "No se encontró la pestaña indicada en el Google Sheet.\n\n"
                f"Nombre de pestaña: {worksheet_name}\n\n"
                "Verifica GOOGLE_WORKSHEET_NAME en el archivo .env."
            ) from error

        except Exception as error:

            raise RuntimeError(
                "No se pudo seleccionar la pestaña del Google Sheet.\n"
                f"Detalle: {error}"
            ) from error

        print(
            f"✅ Pestaña seleccionada: "
            f"{self.worksheet.title}"
        )

    # =============================================================
    # OBTENER REGISTROS
    # =============================================================

    def obtener_registros(self) -> list[dict]:
        """
        Obtiene todos los registros del Google Sheet.

        La primera fila se utiliza como encabezado.
        """

        try:

            registros = self.worksheet.get_all_records()

            return registros

        except Exception as error:

            raise RuntimeError(
                "No se pudieron obtener los registros del Google Sheet.\n"
                f"Detalle: {error}"
            ) from error

    # =============================================================
    # BUSCAR DNI / CE
    # =============================================================

    def buscar_dni_ce(self, consulta: str) -> list[dict]:
        """
        Busca por DNI / CE.

        Ignora espacios, mayúsculas/minúsculas y ceros iniciales.
        Por ejemplo, "01234567" también encuentra "1234567".
        """
        buscado = normalizar_codigo(consulta).lstrip("0")

        if not buscado:
            return []

        resultados = []

        for registro in self.obtener_registros():
            valor = normalizar_codigo(
                registro.get("DNI / CE", "")
            ).lstrip("0")

            if valor and valor == buscado:
                resultados.append(registro)

        return resultados

    # =============================================================
    # BUSCAR FOTOCHECK
    # =============================================================

    def buscar_fotocheck(self, consulta: str) -> list[dict]:
        """
        Busca por FOTOCHECK.

        Ignora:
        - Espacios
        - Mayúsculas/minúsculas
        """

        buscado = normalizar_codigo(consulta)

        if not buscado:
            return []

        resultados = []

        for registro in self.obtener_registros():

            valor = normalizar_codigo(
                registro.get("FOTOCHECK", "")
            )

            if valor == buscado:

                resultados.append(registro)

        return resultados

    # =============================================================
    # BUSCAR POR NOMBRE
    # =============================================================

    def buscar_nombre(self, consulta: str) -> list[dict]:
        """
        Busca por NOMBRES Y APELLIDOS.

        Permite coincidencias parciales.

        Ejemplo:

        Google Sheet:
            JUAN CARLOS PEREZ GOMEZ

        Consulta:
            juan carlos

        Resultado:
            Coincide.

        También ignora diferencias entre mayúsculas/minúsculas
        y espacios adicionales.
        """

        buscado = normalizar_texto(consulta)

        if not buscado:
            return []

        resultados = []

        for registro in self.obtener_registros():

            nombre = normalizar_texto(
                registro.get("NOMBRES Y APELLIDOS", "")
            )

            if buscado in nombre:

                resultados.append(registro)

        return resultados

    # =============================================================
    # BUSCAR SEGÚN TIPO
    # =============================================================

    def buscar(
        self,
        tipo: str,
        consulta: str
    ) -> list[dict]:
        """
        Método general de búsqueda.

        Tipos disponibles:

        - dni
        - dni_ce
        - nombre
        - fotocheck
        """

        tipo_normalizado = normalizar_texto(tipo)

        if tipo_normalizado in (
            "DNI",
            "DNI/CE",
            "DNI / CE",
            "DNI_CE",
            "DNI CE",
        ):

            return self.buscar_dni_ce(consulta)

        if tipo_normalizado in (
            "NOMBRE",
            "NOMBRES",
            "NOMBRES Y APELLIDOS",
        ):

            return self.buscar_nombre(consulta)

        if tipo_normalizado in (
            "FOTOCHECK",
            "FOTO CHECK",
        ):

            return self.buscar_fotocheck(consulta)

        return []

    # =============================================================
    # RECARGAR / ACTUALIZAR CONEXIÓN
    # =============================================================

    def recargar_hoja(self):
        """
        Vuelve a seleccionar la pestaña configurada.

        Útil si se cambia de pestaña durante la ejecución.
        """

        worksheet_name = os.getenv(
            "GOOGLE_WORKSHEET_NAME",
            "",
        ).strip()

        try:

            if worksheet_name:

                self.worksheet = self.spreadsheet.worksheet(
                    worksheet_name
                )

            else:

                self.worksheet = self.spreadsheet.sheet1

            print(
                f"🔄 Pestaña actualizada: "
                f"{self.worksheet.title}"
            )

        except Exception as error:

            raise RuntimeError(
                "No se pudo recargar la pestaña del Google Sheet.\n"
                f"Detalle: {error}"
            ) from error