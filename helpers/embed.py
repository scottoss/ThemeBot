import asyncio

import discord

import helpers.themeparks as themeparks

EMBED_DEFAULTS = {"color": discord.Color(0x00A8FC)}

MAX_FIELDS = 25


async def add_addresses(embed, entities, session, wait_thresholds=None):
    if wait_thresholds is None:
        wait_thresholds = tuple(None for _ in entities)

    park_tasks = []
    destination_tasks = []
    for entity in entities:
        park_tasks.append(asyncio.create_task(get_park(session, entity)))
        destination_tasks.append(
            asyncio.create_task(get_destination(session, entity))
        )

    parks = await asyncio.gather(*park_tasks)
    destinations = await asyncio.gather(*destination_tasks)

    for entity, park, destination, threshold in zip(
        entities, parks, destinations, wait_thresholds
    ):
        threshold_string = (
            f"Threshold: `{threshold}` minutes"
            if threshold is not None
            else ""
        )

        if "location" in entity:
            place = ""

            if park is not None:
                place += f"{park['name']} - "
            if destination is not None:
                place += f"{destination['name']}"

            if not place:
                place = "Google Maps"

            location = entity["location"]
            address = (
                f"[{place}]"
                "(https://www.google.com/maps/place/"
                f"{location['latitude']},{location['longitude']})"
            )
        else:
            address = ""

        embed.add_field(
            name=f"{entity['name']}\n{threshold_string}",
            value=address,
            inline=False,
        )


def create_embed(title, description, color=EMBED_DEFAULTS["color"]):
    return discord.Embed(title=title, description=description, color=color)


def create_error_embed(error):
    error_embed = create_embed("Error", error)
    return error_embed


def create_search_error_embed(error, query_name):
    error_embed = create_error_embed(
        f"{error} were found containing `{query_name}`."
    )
    return error_embed


def add_icon(embed, image_link):
    embed.set_thumbnail(url=image_link)
    return embed


async def get_park(session, entity):
    if "parkId" in entity:
        return await themeparks.get_entity(session, entity["parkId"])


async def get_destination(session, entity):
    if "destinationId" in entity:
        return await themeparks.get_entity(session, entity["destinationId"])
