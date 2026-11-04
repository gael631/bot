import os
import json
import random
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

RAREZA_FILE = BASE_DIR / "rareza.json"
PESO_POR_DEFECTO = 1.0

EXTENSIONES = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger('ambi')

load_dotenv(BASE_DIR / '.env')
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise SystemExit('Falta DISCORD_TOKEN en el archivo .env')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('AMBI'),
    description='Un bot medioambiental',
    intents=intents,
    help_command=commands.DefaultHelpCommand(no_category='Comandos'),
)


def listar_imagenes() -> list[str]:
    return sorted(
        f.name for f in IMAGES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES
    )


def nombre_seguro(nombre: str) -> str:
    nombre = os.path.basename(nombre).replace('\x00', '')
    return nombre or 'imagen'


def ruta_libre(nombre: str, carpeta: Path | None = None) -> Path:
    carpeta = carpeta or IMAGES_DIR
    base, ext = os.path.splitext(nombre)
    destino = carpeta / nombre
    n = 1
    while destino.exists():
        destino = carpeta / f'{base}_{n}{ext}'
        n += 1
    return destino


def categorias_disponibles() -> list[str]:
    if not IMAGES_DIR.exists():
        return []
    cats = []
    for d in sorted(IMAGES_DIR.iterdir()):
        if d.is_dir():
            if any(f.suffix.lower() in EXTENSIONES for f in d.iterdir() if f.is_file()):
                cats.append(d.name)
    return cats


def listar_imagenes_categoria(categoria: str | None = None) -> list[str]:
    carpeta = IMAGES_DIR / categoria if categoria else IMAGES_DIR
    if not carpeta.is_dir():
        return []
    return sorted(
        f.name for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES
    )


def cargar_rareza() -> dict[str, float]:
    if not RAREZA_FILE.exists():
        return {}
    try:
        data = json.loads(RAREZA_FILE.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return {}
        return {str(k): float(v) for k, v in data.items() if float(v) > 0}
    except (json.JSONDecodeError, ValueError, TypeError):
        log.warning('rareza.json invalido, se usan pesos por defecto')
        return {}


def elegir_con_rareza(archivos: list[str], rareza: dict[str, float]) -> str:
    pesos = [rareza.get(nombre, PESO_POR_DEFECTO) for nombre in archivos]
    if not pesos or sum(pesos) <= 0:
        return random.choice(archivos)
    return random.choices(archivos, weights=pesos, k=1)[0]


def elegir(opciones: list[str]) -> str:
    return random.choice(opciones)


@bot.event
async def on_ready():
    log.info('Conectado como %s (id=%s)', bot.user, bot.user.id)
    log.info('Prefijo: mencion o "AMBI"')
    try:
        await bot.tree.sync()
    except Exception as e:
        log.warning('No se pudieron sincronizar los slash commands: %s', e)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Falta un argumento: `{error.param.name}`')
        return
    log.exception('Error en comando %s', ctx.command, exc_info=error)
    await ctx.send('Ocurrio un error procesando el comando.')


@bot.command()
async def meme(ctx, categoria: str | None = None):
    """Envia un meme aleatorio. Opcional: AMBImeme <categoria>"""
    loop = asyncio.get_running_loop()

    if categoria and categoria not in categorias_disponibles():
        cats = categorias_disponibles()
        if cats:
            await ctx.send(
                f'Categoria `{categoria}` no existe. Disponibles: '
                + ', '.join(f'`{c}`' for c in cats)
            )
        else:
            await ctx.send('No hay categorias todavia. Crea subcarpetas en `images/`.')
        return

    archivos = await loop.run_in_executor(None, listar_imagenes_categoria, categoria)
    if not archivos:
        donde = f'`images/{categoria}`' if categoria else '`images`'
        await ctx.send(f'No hay memes en {donde}.')
        return

    rareza = await loop.run_in_executor(None, cargar_rareza)
    nombre = elegir_con_rareza(archivos, rareza)
    carpeta = IMAGES_DIR / categoria if categoria else IMAGES_DIR
    ruta = carpeta / nombre

    try:
        await ctx.send(file=discord.File(ruta))
    except discord.HTTPException as e:
        log.exception('No se pudo enviar %s', ruta)
        await ctx.send(f'No pude enviar `{nombre}`: {e.status}')


@bot.command(name='memes')
async def listar_memes(ctx, categoria: str | None = None):
    """Lista los memes disponibles. Opcional: AMBImemes <categoria>"""
    loop = asyncio.get_running_loop()
    archivos = await loop.run_in_executor(None, listar_imagenes_categoria, categoria)

    if not archivos:
        donde = f'`images/{categoria}`' if categoria else '`images`'
        await ctx.send(f'Todavia no hay memes en {donde}.')
        return

    lista = '\n'.join(f'- `{n}`' for n in archivos)
    if len(lista) > 1900:
        lista = lista[:1900] + '\n... (lista truncada)'
    titulo = f'Memes en `{categoria}`' if categoria else 'Memes disponibles'
    await ctx.send(f'{titulo} ({len(archivos)}):\n{lista}')


@bot.command()
async def addmem(ctx, categoria: str | None = None):
    """Guarda las imagenes adjuntas: AMBIaddmem [categoria] + adjunto"""
    if not ctx.message.attachments:
        await ctx.send('Adjunta una imagen al mensaje junto con `AMBIaddmem`.')
        return

    if categoria:
        if categoria not in categorias_disponibles():
            await ctx.send(
                f'Categoria `{categoria}` no existe. '
                f'Crea la carpeta `images/{categoria}/` primero.'
            )
            return
        carpeta = IMAGES_DIR / categoria
    else:
        carpeta = IMAGES_DIR

    guardados, ignorados = [], []

    for adjunto in ctx.message.attachments:
        nombre = nombre_seguro(adjunto.filename)
        if Path(nombre).suffix.lower() not in EXTENSIONES:
            ignorados.append(nombre)
            continue

        destino = ruta_libre(nombre, carpeta)
        try:
            await adjunto.save(destino)
            guardados.append(destino.name)
            log.info('Guardado %s (%d bytes)', destino, adjunto.size)
        except (discord.HTTPException, OSError):
            log.exception('Fallo guardando %s', nombre)
            ignorados.append(nombre)

    partes = []
    if guardados:
        partes.append('Guardado: ' + ', '.join(f'`{g}`' for g in guardados))
    if ignorados:
        partes.append('Ignorado: ' + ', '.join(f'`{i}`' for i in ignorados))
    if partes:
        await ctx.send('\n'.join(partes))


@bot.command(name='categorias')
async def listar_categorias(ctx):
    """Lista las categorias de memes disponibles."""
    loop = asyncio.get_running_loop()
    cats = await loop.run_in_executor(None, categorias_disponibles)
    if not cats:
        await ctx.send(
            'No hay categorias. Crea subcarpetas dentro de `images/` '
            '(por ejemplo `images/animales/`).'
        )
        return
    lineas = []
    for c in cats:
        n = len(await loop.run_in_executor(None, listar_imagenes_categoria, c))
        lineas.append(f'- `{c}` ({n} memes)')
    await ctx.send('Categorias disponibles:\n' + '\n'.join(lineas))


@bot.command(name='rareza')
async def ver_rareza(ctx):
    """Muestra el peso de rareza de cada meme de la carpeta principal."""
    loop = asyncio.get_running_loop()
    archivos = await loop.run_in_executor(None, listar_imagenes_categoria)
    if not archivos:
        await ctx.send('No hay memes para mostrar rareza.')
        return

    rareza = await loop.run_in_executor(None, cargar_rareza)
    total = sum(rareza.get(n, PESO_POR_DEFECTO) for n in archivos) or 1

    lineas = []
    for n in archivos:
        peso = rareza.get(n, PESO_POR_DEFECTO)
        prob = peso / total * 100
        lineas.append(f'- `{n}`: peso {peso:g} ({prob:.1f}%)')

    texto = 'Rareza de memes:\n' + '\n'.join(lineas)
    if len(texto) > 1900:
        texto = texto[:1900] + '\n... (truncado)'
    await ctx.send(texto)


@bot.command()
async def perro(ctx):
    """Envia una imagen aleatoria de perro desde dog.ceo."""
    url_api = 'https://dog.ceo/api/breeds/image/random'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_api, timeout=aiohttp.ClientTimeout(total=10)) as r:
                r.raise_for_status()
                data = await r.json()
        url_img = data.get('message')
        if not url_img:
            await ctx.send('La API no devolvio una imagen valida.')
            return
        embed = discord.Embed(title='Perro aleatorio', color=0x2ecc71)
        embed.set_image(url=url_img)
        await ctx.send(embed=embed)
    except aiohttp.ClientError as e:
        log.exception('Error consultando dog.ceo')
        await ctx.send(f'No pude obtener la imagen: `{e}`')


@bot.command()
async def comandos(ctx):
    """Lista todos los comandos disponibles."""
    lista = [
        'AMBIhola', 'AMBIapoyo', 'AMBIconsecuencias', 'AMBIayuda',
        'AMBImotivar', 'AMBIdatos', 'AMBIconsejos', 'AMBIbolsa',
        'AMBIreciclaje', 'AMBImeme [categoria]', 'AMBImemes [categoria]',
        'AMBIaddmem [categoria]', 'AMBIcategorias', 'AMBIrareza',
        'AMBIperro', 'AMBIroll', 'AMBIchoose', 'AMBIrepeat',
        'AMBIjoined', 'AMBIcool', 'AMBIcomandos',
    ]
    await ctx.send('Comandos disponibles:\n' + '\n'.join(lista))


@bot.command()
async def hola(ctx):
    """Saludo al usuario."""
    await ctx.send(f'Hola, {ctx.author.name}, bienvenido al grupo.')


@bot.command()
async def apoyo(ctx):
    """Le dice al usuario como apoyar al medio ambiente."""
    opciones = [
        'Un apoyo concreto al medio ambiente que puedes practicar desde hoy es separar y reciclar tus residuos en casa.',
        'Un apoyo concreto al medio ambiente que puedes practicar desde hoy es reducir el consumo de plasticos de un solo uso, como bolsas, botellas y pajillas.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def consecuencias(ctx):
    """Le dice las consecuencias de no cuidar el medio ambiente."""
    opciones = [
        'Una consecuencia de no cuidar al medio ambiente es el calentamiento global, que provoca el aumento de la temperatura del planeta y el derretimiento de los polos.',
        'Una consecuencia de no cuidar al medio ambiente es la contaminacion del aire, que provoca enfermedades respiratorias y cardiovasculares.',
        'Una consecuencia de no cuidar al medio ambiente es la contaminacion del agua, que provoca la muerte de especies acuaticas y la escasez de agua potable.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def ayuda(ctx):
    """Le dice como ayudar al medio ambiente."""
    opciones = [
        'Una forma de ayudar al medio ambiente es usar transporte publico o bicicleta en lugar de un vehiculo privado.',
        'Una forma de ayudar al medio ambiente es consumir productos locales y de temporada para reducir la huella de carbono.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def motivar(ctx):
    """Motiva al usuario a cuidar el medio ambiente."""
    opciones = [
        'Recuerda: un paso tuyo es un paso de la humanidad.',
        'Recuerda que el medio ambiente es nuestra casa y debemos cuidarlo.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def datos(ctx):
    """Le dice al usuario datos interesantes sobre el medio ambiente."""
    opciones = [
        'El 80% de los oceanos estan contaminados por plasticos.',
        'Cada ano se tiran 12.000 millones de toneladas de plastico en los oceanos.',
        'El plastico tarda hasta 1.000 anos en biodegradarse.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def consejos(ctx):
    """Le dice al usuario consejos para cuidar el medio ambiente."""
    opciones = [
        'Reduce el consumo de plasticos de un solo uso.',
        'Usa productos reutilizables en lugar de desechables.',
        'Participa en actividades de limpieza ambiental.',
    ]
    await ctx.send(elegir(opciones))


@bot.command()
async def bolsa(ctx):
    """Explica por que es mejor usar bolsas de tela que de plastico."""
    await ctx.send(
        'La bolsa de tela es mejor que la de plastico: la de plastico tarda '
        'unos 100 anos en degradarse y la de tela unos 6 meses.'
    )


@bot.command()
async def reciclaje(ctx):
    """Explica que es reciclar."""
    await ctx.send(
        'Reciclar es el proceso de convertir materiales usados en nuevos '
        'productos para evitar el desperdicio.'
    )


@bot.command()
async def roll(ctx, dice: str = '1d6'):
    """Tira dados en formato NdN."""
    try:
        rolls, limit = map(int, dice.lower().split('d'))
        if rolls < 1 or limit < 1:
            raise ValueError
    except ValueError:
        await ctx.send('El formato debe ser NdN con numeros positivos.')
        return
    await ctx.send(', '.join(str(random.randint(1, limit)) for _ in range(rolls)))


@bot.command()
async def choose(ctx, *choices: str):
    """Elige entre varias opciones."""
    if not choices:
        await ctx.send('Debes darme al menos una opcion.')
        return
    await ctx.send(random.choice(choices))


@bot.command()
async def repeat(ctx, times: int = 1, content: str = 'repitiendo...'):
    """Repite un mensaje (maximo 10 veces)."""
    for _ in range(max(0, min(times, 10))):
        await ctx.send(content)


@bot.command()
async def joined(ctx, member: discord.Member):
    """Dice cuando se unio un miembro."""
    if member.joined_at is None:
        await ctx.send(f'{member} no tiene fecha de ingreso.')
    else:
        await ctx.send(f'{member} se unio {discord.utils.format_dt(member.joined_at)}')


@bot.command()
async def cool(ctx, member: discord.Member = None):
    """Dice si un usuario es cool."""
    member = member or ctx.author
    await ctx.send(f'{member.display_name} es cool.')


if __name__ == '__main__':
    bot.run(TOKEN, log_handler=None)
