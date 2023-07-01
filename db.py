import enum
import time
import aiosqlite
from typing import AsyncIterator, Dict, Any

from common import ForecastType

db_path = './data.db'

async def ensure_schema():
  async with aiosqlite.connect(db_path) as db:
    await db.execute('''
      CREATE TABLE IF NOT EXISTS forecasts (
        shortname TEXT PRIMARY KEY,
        description TEXT,
        author TEXT,
        forecast_type INT DEFAULT 1,
        resolution REAL
      )
    ''')
    await db.execute('''
      CREATE TABLE IF NOT EXISTS estimates (
        shortname TEXT,
        author TEXT,
        time INT,
        estimate REAL,
        FORIEGN KEY shortname
          REFERENCES forecasts (shortname)
            ON DELETE CASCADE
            ON UPDATE NO ACTION
      )
    ''')

async def create_forecast(
  shortname: str,
  description: str,
  author: str,
  forecast_type: ForecastType,
) -> int:
  async with aiosqlite.connect(db_path) as db:
    result = await db.execute(
      '''
      INSERT INTO forecasts values (?, ?, ?, ?, NULL)
      ''',
      (shortname, description, author, forecast_type.value),
    )
    await db.commit()
  return result.rowcount

async def create_estimate(
  shortname: str,
  author: str,
  estimate: float,
) -> int:
  cur_time = int(time.time())
  async with aiosqlite.connect(db_path) as db:
    result = await db.execute(
      '''
      INSERT INTO estimates (shortname, author, time, estimate) values (?, ?, ?, ?)
      ''',
      (shortname, author, cur_time, estimate),
    )
    await db.commit()
  return result.rowcount

async def get_forecasts() -> AsyncIterator[Dict[str, Any]]:
  async with aiosqlite.connect(db_path) as db:
    async with db.execute(
      'SELECT shortname, description, author, resolution FROM forecasts'
    ) as cursor:
      async for row in cursor:
        yield {'shortname': row[0],
               'description': row[1],
               'author': row[2],
               'resolution': row[3]}

async def get_forecast(shortname: str) -> Dict[str, Any]:
  async with aiosqlite.connect(db_path) as db:
    async with db.execute(
      '''
      SELECT shortname, description, author, forecast_type, resolution
      FROM forecasts WHERE shortname = ?
      ''',
      (shortname,),
    ) as cursor:
      row = await cursor.fetchone()
  return {
    'shortname': row[0],
    'description': row[1],
    'author': row[2],
    'forecast_type': ForecastType(row[3]),
    'resolution': row[4],
  }

async def get_estimates(
  shortname: str,
):
  async with aiosqlite.connect(db_path) as db:
    async with db.execute(
      '''
      SELECT author, time, estimate FROM estimates WHERE shortname = ?
      ORDER BY time ASC
      ''',
      (shortname,),
    ) as cursor:
      async for row in cursor:
        yield {'author': row[0], 'time': row[1], 'estimate': row[2]}

async def resolve_forecast(
  shortname: str,
  resolution: float,
) -> int:
  async with aiosqlite.connect(db_path) as db:
    result = await db.execute(
      '''
      UPDATE forecasts SET resolution = ? WHERE shortname = ?
      ''',
      (resolution, shortname),
    )
    await db.commit()
  return result.rowcount
