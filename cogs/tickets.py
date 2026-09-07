import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import datetime

# ====== CONFIGURE AQUI ======
TICKET_CATEGORY_ID = 123456789012345678  # ID da categoria onde os tickets serão criados
STAFF_ROLE_ID = 123456789012345678       # ID do cargo da staff
LOG_CHANNEL_ID = 123456789012345678      # ID do canal de logs (opcional)
# ============================

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, emoji="🎫", custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Escolha a categoria do ticket:", view=CategorySelect(), ephemeral=True)

class CategorySelect(View):
    def __init__(self):
        super().__init__(timeout=60)

        select = Select(
            placeholder="Selecione a categoria...",
            options=[
                discord.SelectOption(label="Suporte", description="Problemas gerais", emoji="🛠️", value="suporte"),
                discord.SelectOption(label="Compras", description="Dúvidas sobre compras", emoji="🛒", value="compras"),
                discord.SelectOption(label="Denúncia", description="Reportar alguém", emoji="🚨", value="denuncia"),
                discord.SelectOption(label="Outros", description="Outros assuntos", emoji="❓", value="outros"),
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        categoria = interaction.data["values"][0]
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            await interaction.response.send_message("Erro: Categoria de tickets não configurada. Avise um administrador.", ephemeral=True)
            return

        # Verifica se o usuário já tem um ticket aberto
        for channel in category.channels:
            if channel.name == f"ticket-{interaction.user.id}":
                await interaction.response.send_message(f"Você já possui um ticket aberto: {channel.mention}", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
        }

        channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            overwrites=overwrites,
            topic=f"Ticket de {interaction.user} | Categoria: {categoria}"
        )

        embed = discord.Embed(
            title=f"Ticket - {categoria.upper()}",
            description=f"Olá {interaction.user.mention}!\n\nAguarde um membro da staff.\nUse o botão abaixo para fechar o ticket.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"ID do usuário: {interaction.user.id}")

        await channel.send(content=f"{interaction.user.mention} | <@&{STAFF_ROLE_ID}>", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket criado com sucesso: {channel.mention}", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if not interaction.user.guild_permissions.manage_channels and (staff_role is None or staff_role not in interaction.user.roles):
            await interaction.response.send_message("Apenas a staff pode fechar o ticket.", ephemeral=True)
            return

        await interaction.response.send_message("Fechando o ticket em 5 segundos...")
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=5))
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel_ticket", description="Envia o painel de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Sistema de Tickets",
            description="Clique no botão abaixo para abrir um ticket de suporte.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("Painel enviado!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
    bot.add_view(TicketView())  # Persistent view
