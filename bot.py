import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Así 'images/...' funciona aunque ejecutes el script desde otra carpeta
os.chdir(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()  # lee DISCORD_TOKEN desde el archivo .env

os.makedirs('images', exist_ok=True)
EXTENSIONES = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='AMBI',
    description='un bot medioambiental',
    intents=intents,
)


@bot.event
async def on_ready():
    print(f'Conectado como {bot.user}')


# ---------- Memes ----------

@bot.command()
async def meme(ctx):
    """Envía un meme aleatorio de la carpeta images."""
    # 1. Lista de todos los archivos de la carpeta
    archivos = [f for f in os.listdir('images')
                if f.lower().endswith(EXTENSIONES)]

    if not archivos:
        await ctx.send('Todavía no hay memes en la carpeta images.')
        return

    # 2. Elegimos uno al azar
    img_name = random.choice(archivos)

    # 3. Lo abrimos y lo enviamos (dentro del with)
    with open(f'images/{img_name}', 'rb') as f:
        picture = discord.File(f)
        await ctx.send(file=picture)


@bot.command()
async def memes(ctx):
    """Lista los memes disponibles."""
    archivos = [f for f in os.listdir('images')
                if f.lower().endswith(EXTENSIONES)]
    if not archivos:
        await ctx.send('Todavía no hay memes en la carpeta.')
        return
    await ctx.send('Memes disponibles:\n' + '\n'.join(f'• {n}' for n in sorted(archivos)))


@bot.command()
async def addmem(ctx):
    """Guarda las imágenes adjuntas: $addmem + adjunto"""
    if not ctx.message.attachments:
        await ctx.send('Adjunta una imagen al mensaje junto con `$addmem`.')
        return

    guardados = []
    for adjunto in ctx.message.attachments:
        nombre = os.path.basename(adjunto.filename)
        if not nombre.lower().endswith(EXTENSIONES):
            await ctx.send(f'`{nombre}` no es una imagen válida, lo ignoro.')
            continue

        base, ext = os.path.splitext(nombre)
        destino = f'images/{nombre}'
        n = 1
        while os.path.exists(destino):  # no sobrescribir
            destino = f'images/{base}_{n}{ext}'
            n += 1

        await adjunto.save(destino)
        guardados.append(os.path.basename(destino))

    if guardados:
        await ctx.send('Guardado: ' + ', '.join(guardados))


# ---------- Comandos de ejemplo ----------

@bot.command()
async def comandos(ctx):
    """Saludo al usuario."""
    await ctx.send("AMBIhola" +
                   "AMBIapoyo" +
                   "AMBIconsecuencias" +
                   "AMBIayuda" +
                   "AMBImotivar" +
                   "AMBIdatos" +
                   "AMBIconsejos" +
                   "AMBIbolsa" +
                   "AMBIreciclaje" +
                   "AMBImeme" +
                   "AMBImemes" +
                   "AMBIaddmem" +
                   "AMBIroll" +
                   "AMBIchoose" +
                   "AMBIrepeat" +
                   "AMBIjoined" +
                   "AMBIcool" +
                   "AMBIadd"
@bot.command()
async def hola(ctx):
    """Saludo al usuario."""
    await ctx.send("Hola, " + ctx.author.name + ", Bienvenido al grupo" + "! ")
    
@bot.command()
async def apoyo(ctx):
    consejo_random=random.randint(1,2)
    consejor_randoms=random.randint(1,2)
    if consejo_random == consejor_randoms:
        consejo_random=random.randint(1,2)
        consejor_randoms=random.randint(1,2)
    """le dice al usuario como apoyar al medio ambiente."""
    if consejor_random == 1:
        await ctx.send("Un apoyo concreto al medio ambiente que puedes practicar desde hoy es separar y reciclar tus residuos en casa.")
    if consejor_random == 2:
        await ctx.send("Un apoyo concreto al medio ambiente que puedes practicar desde hoy es reducir el consumo de plásticos de un solo uso, como bolsas, botellas y pajillas.")
@bot.command()
async def consecuencias(ctx):
    consecuencia_random=random.randint(1,3)
    consecuencia_randoms=random.randint(1,3)
    if consecuencia_random == consecuencia_randoms:
        consecuencia_random=random.randint(1,3)
        consecuencia_randoms=random.randint(1,3)
    """le dice la consecuensia de no cuidar el medio ambiente."""  
    if consecuencia_random == 1:
        await ctx.send("una consecuencia de no cuidar al medio ambiente es el calentamiento global, que provoca el aumento de la temperatura del planeta y el derretimiento de los polos.")
    if consecuencia_random == 2:
        await ctx.send("una consecuencia de no cuidar al medio ambiente es la contaminación del aire, que provoca enfermedades respiratorias y cardiovasculares.")
    if consecuencia_random == 3:
        await ctx.send("una consecuencia de no cuidar al medio ambiente es la contaminación del agua, que provoca la muerte de especies acuáticas y la escasez de agua potable.")
@bot.command()
async def ayuda(ctx):
    random_ayuda=random.randint(1,2)
    random_ayudas=random.randint(1,2)
    if random_ayuda == random_ayudas:
        random_ayuda=random.randint(1,2)
        random_ayudas=random.randint(1,2)
    """le dice como ayudar al medioambiente."""
    if random_ayuda == 1:
        await ctx.send("Un forma de ayudar al medio ambiente es usar transporte público o bicicleta en lugar de un vehículo privado.")
    if random_ayuda == 2:
        await ctx.send("Un forma de ayudar al medio ambiente es consumir productos locales y de temporada para reducir la huella de carbono.")
@bot.command()
async def motivar(ctx):
    random_motivar=random.randint(1,2)
    random_motiva=random.randint(1,2)
    if random_motivar == random_motiva:
        random_motivar=random.randint(1,2)
        random_motiva=random.randint(1,2)
    """motiva al usuario a cuidar el medio ambiente."""
    if random_motivar == 1:
       await ctx.send("recuerda un paso tuyo es un paso de la humanidad.")
    if random_motivar == 2:
       await ctx.send("recuerda que el medio ambiente es nuestra casa y debemos cuidarlo.")
    
@bot.command()
async def datos(ctx):
    random_dato=random.randint(1,3)
    random_datos=random.randint(1,3)
    if random_datos == random_datos:
        random_dato=random.randint(1,3)
        random_datos=random.randint(1,3)
    """le dice al usuario datos interesantes sobre el medio ambiente."""
    if random_dato == 1:
        await ctx.send("El 80% de los océanos están contaminados por plásticos.")
    if random_dato == 2:
        await ctx.send("Cada año se tiran 12.000 millones de toneladas de plástico en los océanos.")
    if random_dato == 3:
        await ctx.send("El plástico tarda hasta 1.000 años en biodegradarse.")

@bot.command()
async def consejos(ctx):
    random_consejo=random.randint(1,3)
    random_consejos=random.randint(1,3)
    if random_consejo == random_consejos:
        random_consejo=random.randint(1,3)
        random_consejos=random.randint(1,3)
    """le dice al usuario consejos para cuidar el medio ambiente."""
    if random_consejo == 1:
        await ctx.send("reduce el consumo de plasticos de un solo uso")
    if random_consejo == 2:
        await ctx.send("usa productos reutilizables en lugar de desechables")
    if random_consejo == 3:
        await ctx.send("participa en actividades de limpieza ambiental")

@bot.command()
async def bolsa(ctx):
    random_bolsa=random.randint(1,2)
    random_bolsas=random.randint(1,2)
    if random_bolsa == random_bolsas:
        random_bolsa=random.randint(1,2)
        random_bolsas=random.randint(1,2)
    """le dice que es mejor usar bolsas de tela que de plastico."""
    if random_bolsa == 1:
        await ctx.send("la bolsa de tela es mejor que la de plastico, ya que la bolsa de plastico tarda 100 años en degradarse y la bolsa de tela tarda 6 meses en degradarse.")
    if random_bolsa == 2:
        await ctx.send("la bolsa de tela es mejor que la de plastico, ya que la bolsa de plastico tarda 100 años en degradarse y la bolsa de tela tarda 6 meses en degradarse.")

@bot.command()
async def reciclaje(ctx):
    random_reciclaje=random.randint(1,2)
    random_reciclajes=random.randint(1,2)
    if random_reciclaje == random_reciclajes:
        random_reciclaje=random.randint(1,2)
        random_reciclajes=random.randint(1,2)
    """le dice al usuario como reciclar."""
    if random_reciclaje == 1:
        await ctx.send("Reciclar es el proceso de convertir materiales usados en nuevos productos para evitar el desperdicio.")
    if random_reciclaje == 2:
        await ctx.send("Reciclar es el proceso de convertir materiales usados en nuevos productos para evitar el desperdicio.")

@bot.command()
async def roll(ctx, dice: str):
    """Tira dados en formato NdN."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('¡El formato debe ser NdN!')
        return
    await ctx.send(', '.join(str(random.randint(1, limit)) for _ in range(rolls)))


@bot.command()
async def choose(ctx, *choices: str):
    """Elige entre varias opciones."""
    await ctx.send(random.choice(choices))


@bot.command()
async def repeat(ctx, times: int, content='repitiendo...'):
    """Repite un mensaje (máximo 10 veces)."""
    for _ in range(min(times, 10)):
        await ctx.send(content)


@bot.command()
async def joined(ctx, member: discord.Member):
    """Dice cuándo se unió un miembro."""
    if member.joined_at is None:
        await ctx.send(f'{member} no tiene fecha de ingreso.')
    else:
        await ctx.send(f'{member} se unió {discord.utils.format_dt(member.joined_at)}')


@bot.group()
async def cool(ctx):
    """Dice si un usuario es cool."""
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} no es cool')


@cool.command(name='bot')
async def _bot(ctx):
    """¿El bot es cool?"""
    await ctx.send('Sí, el bot es cool.')


# ---------- Arranque ----------

token = os.getenv('DISCORD_TOKEN')
if not token:
    raise SystemExit('Falta DISCORD_TOKEN en el archivo .env')

bot.run(token)