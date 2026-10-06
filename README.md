# Bot Telegram - Firmas Autorizadas 2026

Bot de Telegram en Python para consultar el Google Sheet:

`Firmas Autorizadas - 2026`

## Funciones

- Consulta por DNI / CE
- Consulta por NOMBRES Y APELLIDOS
- Consulta por FOTOCHECK
- Ignora mayúsculas/minúsculas
- DNI/CE y fotocheck ignoran espacios
- Nombre tolera espacios repetidos y permite coincidencia parcial
- Puede limitarse a un grupo específico mediante TELEGRAM_GROUP_ID

## 1. Crear entorno virtual en Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
```

## 2. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Crear el bot de Telegram

En Telegram:

1. Abrir @BotFather
2. Ejecutar /newbot
3. Elegir nombre y username
4. Copiar el token
5. Colocarlo en `.env`

## 4. Google Cloud / Google Sheets

Crear un proyecto en Google Cloud, habilitar Google Sheets API y crear una cuenta de servicio.

Descargar el JSON de credenciales y guardarlo como:

```text
credentials/google-service-account.json
```

Compartir el Google Sheet `Firmas Autorizadas - 2026` con el correo `client_email` que aparece dentro del JSON de la cuenta de servicio.

## 5. Configurar .env

Copiar:

```text
.env.example
```

como:

```text
.env
```

y completar:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_GROUP_ID=-100...
GOOGLE_SHEET_NAME=Firmas Autorizadas - 2026
GOOGLE_WORKSHEET_NAME=
GOOGLE_CREDENTIALS_FILE=credentials/google-service-account.json
```

## 6. Obtener el ID del grupo

Agrega el bot al grupo y utiliza el método que prefieras para obtener el ID del grupo.

Normalmente un supergrupo tiene un ID parecido a:

```text
-1001234567890
```

Colócalo en `TELEGRAM_GROUP_ID`.

## 7. Ejecutar

```powershell
python bot.py
```

Si todo está correcto aparecerá en la consola:

```text
Bot iniciado.
```

## Estructura

```text
firmas_bot/
├── .venv/
├── .env
├── .env.example
├── bot.py
├── google_sheets.py
├── requirements.txt
├── README.md
├── .gitignore
└── credentials/
    └── google-service-account.json
```

## Encabezados esperados

La primera fila de la hoja debe contener exactamente:

- N°
- NOMBRES Y APELLIDOS
- Ficha Ingreso de CONPRO y Visitantes (Solo para MCP)
- Movimiento de Personal MCP
- Materiales y Equipos
- CARGO
- DNI / CE
- FOTOCHECK

No es necesario modificar los valores originales de la hoja para realizar las búsquedas.
