import asyncio
import discord
import pymorphy2
import requests
import logging

from discord.ext import commands

TOKEN = "token"

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
headers = {"X-Yandex-API-Key": "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}"}
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
hours, minutes, flag = 0, 0, False
time = None
clock = '⏰'
bot = commands.Bot(command_prefix='#', intents=intents)
COMMAND_PREFIX = '/'
src = 'en'
dest = 'ru'


def get_coords(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        return toponym_coodrinates.split(" ")
    else:
        return None, None


def weather_response(place):
    coords = get_coords(place)
    weather_api_server = 'https://api.weather.yandex.ru/v1/forecast?'
    weather_params = {
        "lon": float(coords[0]),
        "lat": float(coords[1]),
        "lang": "ru_RU"
    }
    response = requests.get(weather_api_server, weather_params, headers=headers)
    return response.json()


def current_weather(response):
    city = response["info"]["tzinfo"]["name"].split('/')[-1]
    date = response["now_dt"][:10]
    offset = response["info"]["tzinfo"]["offset"] // 3600
    time = response["now_dt"][11:16]
    h, m = map(int, time.split(':'))
    time = f'{h + offset}:{m:02}'
    fact = response["fact"]
    temp = fact["temp"]
    condition = fact["condition"]
    wind_dir = fact["wind_dir"]
    wind_speed = fact["wind_speed"]
    pressure = fact["pressure_mm"]
    humidity = fact["humidity"]
    return f'Current weather in {city} today {date} at time {time}:\n' \
           f'Temperature: {temp},\n' \
           f'Pressure: {pressure} mm,\n' \
           f'Humidity: {humidity}%,\n' \
           f'{condition},\n' \
           f'Wind {wind_dir}, {wind_speed} m/s.'


def forecast_weather(response, days):
    city = response["info"]["tzinfo"]["name"].split('/')[-1]
    forecasts = response["forecasts"]
    result = []
    for forecast in forecasts[1:days + 1]:
        date = forecast["date"]
        temp = forecast["parts"]["day"]["temp_avg"]
        condition = forecast["parts"]["day"]["condition"]
        wind_dir = forecast["parts"]["day"]["wind_dir"]
        wind_speed = forecast["parts"]["day"]["wind_speed"]
        pressure = forecast["parts"]["day"]["pressure_mm"]
        humidity = forecast["parts"]["day"]["humidity"]
        result.append(f'Weather forecast in {city} for {date}:\n'
                      f'Temperature: {temp},\n'
                      f'Pressure: {pressure} mm,\n'
                      f'Humidity: {humidity}%,\n'
                      f'{condition},\n'
                      f'Wind {wind_dir}, {wind_speed} m/s.')
    return '\n\n'.join(result)


class TranslatorBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello_bot')
    async def hello(self, message):
        await message.channel.send('Check what I can: #help_bot')

    async def on_ready(self):
        print(f'{client.user} подключен к Discord!')
        for guild in client.guilds:
            print(
                f'{client.user} подключились к чату:\n'
                f'{guild.name}(id: {guild.id})'
            )

    @commands.command(name='cat')
    async def cat(self, message):
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        data = response.json()
        await message.channel.send(data[0]['url'])

    @commands.command(name='dog')
    async def dog(self, message):
        response = requests.get("https://dog.ceo/api/breeds/image/random")
        data = response.json()
        await message.channel.send(data['message'])

    @commands.command(name='help_bot')
    async def help(self, ctx):
        message = 'Чтобы ознакомиться с функциями бота перейдите по ссылке: http://127.0.0.1:8080'
        await ctx.send(message)

    async def on_member_join(self, member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Привет, {member.name}!'
        )

    @commands.command(name='ku')
    async def Ku(self, message):
        await message.channel.send("Ку")

    @commands.command(name='hello')
    async def hello(self, message):
        await message.channel.send("И тебе привет")

    @commands.command(name='numerals')
    async def numerals(self, ctx, word, num):
        morph = pymorphy2.MorphAnalyzer()
        word_parse = morph.parse(word)[0].make_agree_with_number(int(num)).word
        await ctx.send(f'{num} {word_parse}')

    @commands.command(name='alive')
    async def alive(self, ctx, word):
        morph = pymorphy2.MorphAnalyzer()
        alive = morph.parse('Живое')[0]
        p = morph.parse(word)
        word_ = None
        for par in p:
            if 'NOUN' in par.tag:
                word_ = par
                break
        try:
            f = word_.tag.gender
            num = word_.tag.number
            if 'anim' in word_.tag:
                if 'plur' in word_.tag:
                    message = f'{word.capitalize()} {alive.inflect({num}).word}'
                else:
                    message = f'{word.capitalize()} {alive.inflect({f, num}).word}'
            else:
                if 'plur' in word_.tag:
                    message = f'{word.capitalize()} не {alive.inflect({num}).word}'
                else:
                    message = f'{word.capitalize()} не {alive.inflect({f, num}).word}'
        except Exception:
            message = 'Не существительное'
        await ctx.send(message)

    @commands.command(name='noun')
    async def noun(self, ctx, word, case, number):
        morph = pymorphy2.MorphAnalyzer()
        word_parse = morph.parse(word)[0]
        if 'NOUN' in word_parse[1]:
            message = word_parse.inflect({case})[0] \
                if number == 'single' else \
                word_parse.inflect({case, 'plur'})[0]
        else:
            message = f'{word.capitalize()} не существительное'
        await ctx.send(message)

    @commands.command(name='inf')
    async def infinitive(self, ctx, word):
        morph = pymorphy2.MorphAnalyzer()
        word_parse = morph.parse(word)[0]
        message = word_parse.normal_form
        await ctx.send(message)

    @commands.command(name='morph')
    async def morph(self, ctx, word):
        morph = pymorphy2.MorphAnalyzer()
        message = morph.parse(word)[0].tag.cyr_repr
        await ctx.send(message)

    @commands.command('set_lang')
    async def set_lang(self, ctx: commands.Context, languages):
        self.src, self.dest = languages.strip().split('-')
        await ctx.send(f'Enter "{COMMAND_PREFIX}text <text>" for translate')

    @commands.command('text')
    async def text(self, ctx: commands.Context, *text):
        text = ' '.join(text)
        response = requests.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': '|'.join((self.src, self.dest))}
        ).json()
        text = response['responseData']['translatedText']
        await ctx.send(text)

    place = 'Москва'

    @commands.command(name='place')
    async def place(self, ctx, city):
        self.place = city
        message = f'Place changed to {self.place}'
        await ctx.send(message)

    @commands.command(name='current')
    async def current(self, ctx):
        response = weather_response(self.place)
        message = current_weather(response)
        await ctx.send(message)

    @commands.command(name='forecast')
    async def forecast_days(self, ctx, days):
        message = forecast_weather(weather_response(self.place), int(days))
        await ctx.send(message)

    @commands.command('set_lang')
    async def set_lang(self, ctx: commands.Context, languages):
        self.src, self.dest = languages.strip().split('-')
        await ctx.send(f'Enter "#text <text>" for translate')

    src = 'en'
    dest = 'ru'

    @commands.command('text')
    async def text(self, ctx: commands.Context, *text):
        text = ' '.join(text)
        response = requests.get(
            'https://api.mymemory.translated.net/get',
            params={'q': text, 'langpair': '|'.join((self.src, self.dest))}
        ).json()
        text = response['responseData']['translatedText']
        await ctx.send(text)


async def main():
    await bot.add_cog(TranslatorBot(bot))
    await bot.start(TOKEN)


asyncio.run(main())
