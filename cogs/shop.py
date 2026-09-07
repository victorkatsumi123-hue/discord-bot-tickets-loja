import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import json
import os

PRODUCTS_FILE = "products.json"

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w") as f:
            json.dump({}, f)
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(data):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ShopView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ver Produtos", style=discord.ButtonStyle.blurple, emoji="🛒", custom_id="ver_produtos")
    async def ver_produtos(self, interaction: discord.Interaction, button: Button):
        products = load_products()
        if not products:
            await interaction.response.send_message("Nenhum produto cadastrado no momento.", ephemeral=True)
            return

        embed = discord.Embed(title="🛒 Loja", color=discord.Color.gold())
        for product_id, data in products.items():
            embed.add_field(
                name=f"{data['name']} — R${data['price']}",
                value=f"{data['description']}\nEstoque: {data['stock']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, view=BuyView(), ephemeral=True)

class BuyView(View):
    def __init__(self):
        super().__init__(timeout=120)

        products = load_products()
        options = []
        for pid, data in products.items():
            if data["stock"] > 0:
                options.append(discord.SelectOption(
                    label=data["name"],
                    description=f"R${data['price']} | Estoque: {data['stock']}",
                    value=pid
                ))

        if options:
            select = Select(placeholder="Escolha o produto para comprar...", options=options[:25])
            select.callback = self.buy_callback
            self.add_item(select)

    async def buy_callback(self, interaction: discord.Interaction):
        product_id = interaction.data["values"][0]
        products = load_products()
        product = products[product_id]

        if product["stock"] <= 0:
            await interaction.response.send_message("Este produto está sem estoque.", ephemeral=True)
            return

        # Aqui você pode integrar pagamento real (Pix, Stripe, etc)
        # Por enquanto vamos simular a compra e entregar o cargo/item

        product["stock"] -= 1
        save_products(products)

        # Entrega automática (exemplo: dar um cargo)
        if product.get("role_id"):
            role = interaction.guild.get_role(int(product["role_id"]))
            if role:
                await interaction.user.add_roles(role)

        embed = discord.Embed(
            title="✅ Compra realizada!",
            description=f"Você comprou **{product['name']}** por **R${product['price']}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log da compra (opcional)
        # log_channel = interaction.guild.get_channel(123456789012345678)
        # if log_channel:
        #     await log_channel.send(f"💰 {interaction.user.mention} comprou **{product['name']}**")

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel_loja", description="Envia o painel da loja")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_loja(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Loja Oficial",
            description="Clique no botão abaixo para ver os produtos disponíveis.",
            color=discord.Color.gold()
        )
        await interaction.channel.send(embed=embed, view=ShopView())
        await interaction.response.send_message("Painel da loja enviado!", ephemeral=True)

    @app_commands.command(name="adicionar_produto", description="Adiciona um produto na loja")
    @app_commands.describe(
        nome="Nome do produto",
        preco="Preço em R$",
        descricao="Descrição do produto",
        estoque="Quantidade em estoque",
        role_id="ID do cargo que será entregue (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def adicionar_produto(self, interaction: discord.Interaction, nome: str, preco: float, descricao: str, estoque: int, role_id: str = None):
        products = load_products()
        product_id = str(len(products) + 1)

        products[product_id] = {
            "name": nome,
            "price": preco,
            "description": descricao,
            "stock": estoque,
            "role_id": role_id
        }
        save_products(products)

        await interaction.response.send_message(f"Produto **{nome}** adicionado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Shop(bot))
    bot.add_view(ShopView())
