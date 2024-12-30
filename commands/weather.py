import asyncio
import datetime as dt
import io
import os

import aiohttp
import discord
import matplotlib.pyplot as plt
from dotenv import load_dotenv

import helpers.database as database
import helpers.decorators as decorators
import helpers.embed as embed
import helpers.themeparks as themeparks
from commands.destination import validate_destinations

load_dotenv()

BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?"
API_KEY = os.getenv("WEATHER_API_KEY")
UNIT = "Imperial"


@decorators.require_destinations
async def forecast(interaction, destination_name):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        destinations = database.get_user_destination_ids(interaction.user.id)
        matches = await themeparks.search_for_destinations(
            session, destination_name, destinations
        )

        if not await validate_destinations(
            interaction, matches, destination_name
        ):
            return

        if len(matches) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple destinations", destination_name
            )

            tasks = []
            for i, destination in enumerate(matches):
                tasks.append(
                    asyncio.create_task(
                        themeparks.get_entity(session, destination["id"])
                    )
                )

                if i >= embed.MAX_FIELDS - 1:
                    break

            entities = await asyncio.gather(*tasks)
            await embed.add_addresses(error_embed, entities, session)

            return await interaction.followup.send(embed=error_embed)

        entity_data = await themeparks.get_entity(session, matches[0]["id"])

        if "location" not in entity_data:
            error_embed = embed.create_error_embed(
                f"No location was found for `{entity_data['name']}`."
            )
            return await interaction.followup.send(embed=error_embed)

        lon = entity_data["location"]["longitude"]
        lat = entity_data["location"]["latitude"]

        url = (
            f"{BASE_URL}&appid={API_KEY}"
            f"&lat={lat}&lon={lon}&units={UNIT}&cnt=40"
        )

        weather_embed = embed.create_embed(
            "Weather Forecast",
            f"Here is the 5-day forecast for **{entity_data['name']}**.",
        )

        # https://www.geeksforgeeks.org/saving-a-plot-as-an-image-in-python/
        # https://is.gd/cay9cz
        async with session.get(url) as response:
            weather = await response.json()

            image_code = weather["list"][0]["weather"][0]["icon"]
            image_link = f"http://openweathermap.org/img/w/{image_code}.png"
            embed.add_icon(weather_embed, image_link)

            plt.figure()

            plt.title(entity_data["name"])
            plt.xlabel("Day")
            plt.ylabel("Temperature (°F)")
            plt.grid()

            days = []
            temps = []

            # Graphing the weather
            for forecast in weather["list"]:
                days.append(dt.datetime.fromtimestamp(forecast["dt"]))
                temps.append(forecast["main"]["temp"])

            plt.plot(days, temps)
            fig = plt.gcf()

            buf = io.BytesIO()
            fig.savefig(buf)
            buf.seek(0)

            file = discord.File(buf, filename="graph.png")
            weather_embed.set_image(url="attachment://graph.png")

        return await interaction.followup.send(embed=weather_embed, file=file)
