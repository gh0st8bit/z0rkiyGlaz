import nextcord
import requests
import nextcord as discord
from nextcord.ext import commands
from geopy.distance import distance
from geopy.geocoders import Nominatim

import config


intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)


# BOT EVENTS
@bot.event
async def on_member_join(member):
    # Определяем канал welcome по его ID
    welcome_channel = await bot.fetch_channel(config.WELCOME_CHANNEL_ID)
    if welcome_channel is not None:
        # Генерируем сообщение с приветствием и стилистикой
        welcome_message = f"```diff\n+ Добро пожаловать на сервер, {member.name}! +\n+ Мы рады видеть вас здесь. +\n- Помните, что нужно следовать нашим правилам и оставаться в безопасности! -\n```"
        # Отправляем сообщение в канал welcome
        await welcome_channel.send(welcome_message)

        role = member.guild.get_role(config.GUEST_ROLE_ID)
        if role is not None:
            await member.add_roles(role)

        # Отправляем сообщение в канал logs
        logs_channel = await bot.fetch_channel(config.LOGS_CHANNEL_ID)
        if logs_channel is not None:
            logs_message = f"```diff\n+          Зашел на сервер        +```" \
                           f"{member.mention} (ID: {member.id})\n"
            await logs_channel.send(logs_message)

            role_message = f"```diff\n+ Пользователю {member.name} ({member.id}) выдана роль Guest +```"
            await logs_channel.send(role_message)
        else:
            # Генерируем сообщение с уведомлением об ошибке при выдаче роли
            error_message = f"```diff\n- Не удалось выдать роль пользователю {member.name} ({member.id}). Роль с ID {config.GUEST_ROLE_ID} не найдена. -```"
            await logs_channel.send(error_message)


@bot.event
async def on_member_remove(member):
    # Отправляем сообщение в канал logs
    logs_channel = await bot.fetch_channel(config.LOGS_CHANNEL_ID)
    if logs_channel is not None:
        logs_message = f"```diff\n-          Покинул сервер          -```" \
                       f"{member.mention} (ID: {member.id})\n"
        await logs_channel.send(logs_message)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    activity = nextcord.Activity(type=nextcord.ActivityType.playing, name="Wireshark")
    await bot.change_presence(activity=activity)


@bot.command()
async def userblock(ctx, member: nextcord.Member, *, reason=None):
    # Проверяем, имеет ли автор команды определенную роль
    authorized_role_id = config.BOT_COMMANDER_ROLE_ID  # замените это на ID вашей роли
    authorized_role = nextcord.utils.get(ctx.guild.roles, id=authorized_role_id)
    if authorized_role not in ctx.author.roles:
        await ctx.send("Вы не имеете права использовать эту команду!")
        return

    # Получаем роль забаненого пользователя
    banned_role_id = config.BANNED_ROLE_ID  # замените это на ID роли забаненного
    banned_role = nextcord.utils.get(ctx.guild.roles, id=banned_role_id)

    # Проверяем, указана ли причина бана
    if reason is None:
        await ctx.send("Вы должны указать причину бана!")
        return

    # Выдаём пользователю роль забаненого
    await member.add_roles(banned_role)

    # Отправляем уведомление об успешном бане в канал logs
    logs_channel_id = config.LOGS_CHANNEL_ID  # замените это на ID вашего канала для логов
    logs_channel = bot.get_channel(logs_channel_id)
    if logs_channel is not None:
        ban_message = f"```diff\n-           Блокировка пользователя           -\n```" \
                      f"{ctx.author.top_role} {ctx.author.mention} (ID: {ctx.author.id}) забанил {member.mention} (ID: {member.id}). Причина: {reason}\n"
        await logs_channel.send(ban_message)


@bot.command()
async def userunblock(ctx, member: nextcord.Member):
    # Проверяем, имеет ли автор команды определенную роль
    authorized_role_id = config.BOT_COMMANDER_ROLE_ID  # замените это на ID вашей роли
    authorized_role = nextcord.utils.get(ctx.guild.roles, id=authorized_role_id)
    if authorized_role not in ctx.author.roles:
        await ctx.send("Вы не имеете права использовать эту команду!")
        return

    # Получаем роль забаненного пользователя
    banned_role_id = config.BANNED_ROLE_ID # замените это на ID роли забаненного
    banned_role = nextcord.utils.get(ctx.guild.roles, id=banned_role_id)

    # Проверяем, имеет ли участник забаненную роль
    if banned_role not in member.roles:
        await ctx.send(f"{member.mention} не имеет забаненной роли!")
        return

    # Снимаем роль забаненного пользователя
    await member.remove_roles(banned_role)

    # Отправляем уведомление об успешном бане в канал logs
    logs_channel_id = config.LOGS_CHANNEL_ID  # замените это на ID вашего канала для логов
    logs_channel = bot.get_channel(logs_channel_id)
    if logs_channel is not None:
        ban_message = f"```diff\n+           Разблокировка пользователя           +\n```" \
                      f"{ctx.author.top_role} {ctx.author.mention} (ID: {ctx.author.id}) разбанил {member.mention} (ID: {member.id}).\n"
        await logs_channel.send(ban_message)


@bot.command()
async def news(ctx, *, news_text: str):
    # Получаем объект канала по его ID
    channel = bot.get_channel(config.NEWS_CHANNEL_ID)
    if channel is None:
        await ctx.send(f"Канал с ID {config.NEWS_CHANNEL_ID} не найден!")
        return

    # Создаем богатое сообщение для новости
    news_embed = nextcord.Embed(title="Новости", description=f"{news_text}", color=nextcord.Color.green())

    # Отправляем сообщение в канал
    await channel.send("@everyone, появились свежие новости!")
    await channel.send(embed=news_embed)

    logs_channel = await bot.fetch_channel(config.LOGS_CHANNEL_ID)
    if logs_channel is not None:
        logs_message = f"```fix\n-          Использование команды /news          -```" \
                       f"Пользователь {ctx.author.mention} (ID: {ctx.author.id}) " \
                       f"использовал команду /news для публикации новости с текстом \n" \
                       f"{news_text}"
        await logs_channel.send(logs_message)


# BOT SLASH COMMANDS
@bot.slash_command(name='ipinfo', description='Показывает ГЕО информацию IP-адреса ')
async def ipinfo(interaction: nextcord.Interaction, ip_address: str):
    # отправляем запрос к ipinfo.io
    response = requests.get(f'https://ipinfo.io/{ip_address}?token={config.API_KEY}')
    data = response.json()

    # создаем вложение для вывода информации в красивом формате
    embed = discord.Embed(title=f'Информация об IP-адресе {ip_address}', color=0xff0000)
    embed.add_field(name='Страна', value=data['country'], inline=True)
    embed.add_field(name='Регион', value=data['region'], inline=True)
    embed.add_field(name='Город', value=data['city'], inline=True)
    if 'postal' in data:
        embed.add_field(name='Почтовый индекс', value=data['postal'], inline=True)
    embed.add_field(name='Широта', value=data['loc'].split(',')[0], inline=True)
    embed.add_field(name='Долгота', value=data['loc'].split(',')[1], inline=True)
    embed.set_footer(text='Информация предоставлена сервисом ipinfo.io')

    # отправляем вложение в канал, откуда была вызвана команда
    await interaction.response.send_message(embed=embed)

    logs_channel = await bot.fetch_channel(config.LOGS_CHANNEL_ID)
    if logs_channel is not None:
        logs_message = f"```fix\n-          Использование команды /ipinfo          -```" \
                       f"Пользователь {interaction.user.mention} (ID: {interaction.user.id}) " \
                       f"использовал команду /ipinfo для IP-адреса {ip_address}"
        await logs_channel.send(logs_message)


@bot.slash_command(name='ipdist', description='Показывает растояние между городами ')
async def ipdist(interaction: nextcord.Interaction, city1: str, city2: str):
    geolocator = Nominatim(user_agent="my_bot")
    loc1 = geolocator.geocode(city1)
    loc2 = geolocator.geocode(city2)
    dist = distance((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
    embed = discord.Embed(title=f'Расстояние между городами {city1} и {city2}', color=0xff0000)
    embed.add_field(name='Координаты города 1', value=f'Широта: {loc1.latitude}, Долгота: {loc1.longitude}',
                    inline=False)
    embed.add_field(name='Координаты города 2', value=f'Широта: {loc2.latitude}, Долгота: {loc2.longitude}',
                    inline=False)
    embed.add_field(name='Расстояние', value=f'{dist:.2f} км', inline=False)
    await interaction.response.send_message(embed=embed)

    logs_channel = await bot.fetch_channel(config.LOGS_CHANNEL_ID)
    if logs_channel is not None:
        logs_message = f"```fix\n-          Использование команды /ipdist          -```" \
                       f"Пользователь {interaction.user.mention} (ID: {interaction.user.id}) " \
                       f"использовал команду /ipdist для вычисления расстояния между {city1} и {city2}. " \
                       f"Результат: {dist:.2f} километров."
        await logs_channel.send(logs_message)
