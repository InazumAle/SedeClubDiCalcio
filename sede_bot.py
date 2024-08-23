import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os

# Carica il token dal file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configura gli intenti per consentire al bot di rilevare nuovi membri
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.reactions = True

# Inizializza il bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Persistenza della View
class TicketView(View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Apri un Ticket", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Ticket")  # Nome della categoria

        # Controlla se l'utente ha già un ticket aperto
        ticket_channel_name = f"🎫┃ticket-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.text_channels, name=ticket_channel_name)

        if existing_channel:
            await interaction.response.send_message(
                "Hai già un ticket aperto. Chiudi il ticket corrente prima di aprirne un altro.",
                ephemeral=True
            )
            return

        # Controlla se la categoria esiste, se no, la crea
        if not category:
            print("Categoria 'Ticket' non trovata, creando una nuova categoria.")
            category = await guild.create_category("Ticket")
        
        # Crea il canale per il ticket
        ticket_channel = await guild.create_text_channel(ticket_channel_name, category=category)
        print(f"Canale creato: {ticket_channel.name}")

        # Imposta i permessi
        await ticket_channel.set_permissions(guild.default_role, read_messages=False)  # Nessun accesso per @everyone
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)  # Accesso per l'utente che ha creato il ticket

        # Invia il messaggio di benvenuto e opzione per chiudere il ticket
        await ticket_channel.send(f"Ciao {interaction.user.mention}, benvenuto nel tuo ticket! Invia un consiglio, una precisazione oppure dei contenuti che possano tornarci utili!")

        # Crea e invia il pulsante di chiusura
        close_view = TicketCloseView()
        await ticket_channel.send("Chiusura ticket:", view=close_view)

        # Risponde all'interazione per confermare la creazione del ticket
        await interaction.response.send_message(f"Ticket creato: {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Chiudi Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        role_names = ["Mark Evans", "Preside", "Allenatore", "Manager"]
        roles = [discord.utils.get(guild.roles, name=role_name) for role_name in role_names]

        # Verifica se l'utente ha uno dei ruoli specificati
        if any(role in interaction.user.roles for role in roles):
            await interaction.channel.delete()
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention}, non hai il permesso di chiudere questo ticket.",
                ephemeral=True
            )

# Evento che viene attivato quando il bot è online
@bot.event
async def on_ready():
    print(f'Bot online as {bot.user}')
    # Trova il canale "🎫┃ticket" e invia il messaggio iniziale
    channel = discord.utils.get(bot.get_all_channels(), name="🎫┃ticket")
    if channel:
        print(f"Canale trovato: {channel.name}")
        await send_ticket_message(channel)  # Usa la nuova funzione per inviare il messaggio di ticket
    else:
        print("Canale 🎫┃ticket non trovato.")

# Evento che viene attivato quando un nuovo membro si unisce al server
@bot.event
async def on_member_join(member):
    role_name = "Studente"  # Sostituisci con il nome del ruolo che vuoi assegnare
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        try:
            await member.add_roles(role)
            print(f"Role {role.name} assigned to {member.name}")
        except discord.DiscordException as e:
            print(f"Failed to assign role: {e}")

# Funzione per inviare il messaggio di ticket con pulsante in un canale specifico
async def send_ticket_message(channel):
    print(f"Inviando messaggio di ticket nel canale: {channel.name}")
    embed = discord.Embed(
        title="Ticket", 
        description="I ticket vanno aperti solo ed esclusivamente per aiutarci nel completismo dei contenuti del server fornendoci un consiglio, delle precisazioni oppure dei contenuti mancanti. Se invece vuoi entrare a far parte della nostra squadra specifica in quale campo di Inazuma Eleven sei competente! Clicca il pulsante qui sotto per creare un ticket:", 
        color=0x84b1b8
    )
    
    # Crea una View persistente e la invia
    view = TicketView(timeout=None)
    await channel.send(embed=embed, view=view)

# Comando per inviare il messaggio di ticket
@bot.command()
async def ticket_message(ctx):
    await send_ticket_message(ctx.channel)

# Avvia il bot
bot.run(TOKEN)
