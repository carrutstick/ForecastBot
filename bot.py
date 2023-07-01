#! python3

### Jank to keep repl alive ###
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
  return "Your Bot Is Ready"
  
def run():
  app.run(host="0.0.0.0", port=8000)
  
def keep_alive():
  server = Thread(target=run)
  server.start()

keep_alive()
### /Jank ###

import os
import time
from itertools import cycle

import discord
from discord.ext import commands, tasks
from discord import app_commands

from common import ForecastType
import db

TOKEN = os.environ['DISCORD_TOKEN']
supported_guilds = [
  701576579041591346,
  1123295125565608016,
]
description = "A bot for lightweight tracking of forecasts"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot('?', intents=intents)

status = cycle(['with Python','JetHub'])

@tasks.loop(seconds=10)
async def change_status():
  await bot.change_presence(activity=discord.Game(next(status)))

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user} (ID: {bot.user.id})')
  change_status.start()
  for guild_id in supported_guilds:
    guild = bot.get_guild(guild_id)
    print(f'Guild: {guild}')
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
  await db.ensure_schema()
  print('------')

@bot.tree.command()
async def make_forecast(
  ctx,
  shortname: str,
  description: str,
  forecast_type: ForecastType,
):
  try:
    rowcount = await db.create_forecast(
      shortname,
      description,
      ctx.user.id,
      forecast_type
    )
  except Exception as e:
    msg = f'Failed to create forecast: {e}'
  else:
    if rowcount == 0:
      msg = 'Failed to create forecast'
    else:
      msg = (f'**{ctx.user.name}** created forecast `{shortname}`.\n'
             f'**Description:** {description}\n'
             f'**Forecast type:** `{forecast_type}`' )
  await ctx.response.send_message(msg)
  
@bot.tree.command()
async def estimate(
  ctx,
  shortname: str,
  estimate: str,
):
  try:
    estimate = estimate.strip()
    if estimate.endswith('%'):
      est_val = float(estimate[:-1]) / 100.0
    else:
      est_val = float(estimate)

    forecast = await db.get_forecast(shortname)
    if (est_val < 0 or est_val > 1) and forecast['forecast_type'] == ForecastType.PROB:
        raise ValueError('Probability estimates must be between 0 and 1 (between 0% and 100%)')
    
    rowcount = await db.create_estimate(
      shortname,
      str(ctx.user.id),
      float(estimate),
    )
  except Exception as e:
    msg = f'Failed to create estimate: {e}'
  else:
    if rowcount == 0:
      msg = 'Failed to create estimate'
    else:
      msg = f'**{ctx.user.name}** estimated **{estimate}** in forecast `{shortname}`'
  await ctx.response.send_message(msg)

@bot.tree.command()
async def list_forecasts(ctx):
  forecasts = []
  async for row in db.get_forecasts():
    forecasts.append(row)
  msgs = []
  for row in forecasts:
    author = bot.get_user(int(row["author"]))
    msgs.append( f'**Shortname:** `{row["shortname"]}`\n'
                 f'**Description:** {row["description"]}\n'
                 f'**Author:** {author.name}\n'
                 f'**Resolution:** {row["resolution"]}\n')
  msg = "---\n".join(msgs)
  await ctx.response.send_message(msg)

@bot.tree.command()
async def list_estimates(ctx, shortname: str):
  estimates = []
  async for row in db.get_estimates(shortname):
    estimates.append(row)
  msgs = []
  for row in estimates:
    author = bot.get_user(int(row['author']))
    created = time.strftime('%Y-%m-%d %H:%M', time.localtime(row['time']))
    estimate = row['estimate']
    msgs.append(f'{author.name} estimated \t**{estimate}**\t at {created}')
  msg = "\n".join(msgs)
  await ctx.response.send_message(msg)

@bot.tree.command()
async def user_forecasts(ctx, member: discord.Member):
  await ctx.response.send_message(f'This functionality is not yet implemented')

@bot.tree.command()
async def resolve(ctx, shortname: str, result: str):
  try:
    rowcount = await db.resolve_forecast(
      shortname,
      float(result),
    )
  except Exception as e:
    msg = f'Failed to record resolution: {e}'
  else:
    if rowcount == 0:
      msg = 'Failed to record resolution'
    else:
      msg = f'Forecast `{shortname}` resolved to **{result}**!'
  await ctx.response.send_message(msg)

bot.run(TOKEN)
