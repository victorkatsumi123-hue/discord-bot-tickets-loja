import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import datetime

# ====== CONFIGURE AQUI ======
TICKET_CATEGORY_ID = 1546501279776505906  # ID da categoria onde os tickets serão criados
STAFF_ROLE_ID = 1546500993431113819       # ID do cargo da staff
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
        await interaction.response.defer(ephemeral=True)

        categoria = interaction.data["values"][0]
        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None:
            await interaction.followup.send("❌ Erro: Categoria de tickets não encontrada. Avise um administrador.", ephemeral=True)
            return

        # Verifica se já tem ticket aberto
        for channel in category.text_channels:
            if str(interaction.user.id) in channel.name:
                await interaction.followup.send(f"Você já possui um ticket aberto: {channel.mention}", ephemeral=True)
                return

        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            ),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                attach_files=True
            )

        try:
            channel = await category.create_text_channel(
                name=f"ticket-{interaction.user.name[:20]}-{str(interaction.user.id)[-4:]}",
                overwrites=overwrites,
                topic=f"Ticket de {interaction.user} ({interaction.user.id}) | Categoria: {categoria}",
                reason=f"Ticket aberto por {interaction.user}"
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Erro de permissão! O bot precisa da permissão **Gerenciar Canais** e o cargo dele precisa estar acima da categoria.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao criar o ticket: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🎫 Ticket - {categoria.upper()}",
            description=(
                f"Olá {interaction.user.mention}!\n\n"
                f"Aguarde um membro da staff responder.\n"
                f"Use os botões abaixo para gerenciar o ticket."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"ID do usuário: {interaction.user.id}")

        await channel.send(
            content=f"{interaction.user.mention} | <@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=TicketControlView()
        )

        await interaction.followup.send(f"✅ Ticket criado com sucesso: {channel.mention}", ephemeral=True)


class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assumir Ticket", style=discord.ButtonStyle.blurple, emoji="🙋", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff_role is None or staff_role not in interaction.user.roles:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Apenas a staff pode assumir o ticket.", ephemeral=True)
                return

        embed = discord.Embed(
            title="Ticket Assumido",
            description=f"Este ticket foi assumido por {interaction.user.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        is_staff = staff_role and staff_role in interaction.user.roles
        is_admin = interaction.user.guild_permissions.administrator
        is_owner = str(interaction.user.id) in interaction.channel.name

        if not (is_staff or is_admin or is_owner):
            await interaction.response.send_message("Você não tem permissão para fechar este ticket.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Fechando o ticket em 5 segundos...")
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=5))

        try:
            await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user}")
        except:
            pass


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel_ticket", description="Envia o painel de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Sistema de Tickets",
            description=(
                "Clique no botão abaixo para abrir um ticket de suporte.\n\n"
                "**Categorias disponíveis:**\n"
                "🛠️ Suporte\n"
                "🛒 Compras\n"
                "🚨 Denúncia\n"
                "❓ Outros"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Nossa equipe responderá o mais rápido possível")

        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("Painel de tickets enviado!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
    bot.add_view(TicketView())
    bot.add_view(TicketControlView())
