import asyncio
import os

import aiohttp


import helpers.database as db
import helpers.embed as embed
import helpers.themeparks as themeparks




async def track(client):
    #channel = client.get_channel(STATUS_CHANNEL_ID)

    tracks = db.execute("SELECT * FROM tracks")

    live_tasks = []
    entity_tasks = []

    async with aiohttp.ClientSession() as session:
        for row in tracks:
            live_tasks.append(
                asyncio.create_task(
                    themeparks.get_entity(
                        session, row["attraction_id"], "live"
                    )
                )
            )
            entity_tasks.append(
                asyncio.create_task(
                    themeparks.get_entity(session, row["attraction_id"])
                )
            )

        live_attractions = await asyncio.gather(*live_tasks)
        entities = await asyncio.gather(*entity_tasks)

        park_tasks = []
        destination_tasks = []

        for entity in entities:
            park_tasks.append(
                asyncio.create_task(embed.get_park(session, entity))
            )
            destination_tasks.append(
                asyncio.create_task(embed.get_destination(session, entity))
            )

        parks = await asyncio.gather(*park_tasks)
        destinations = await asyncio.gather(*destination_tasks)

    for row, attraction_data, entity, park, destination in zip(
        tracks, live_attractions, entities, parks, destinations
    ):
        if "location" in entity:
            place = f"{park['name']} - {destination['name']}"

            location = entity["location"]
            address = (
                f"[{place}]"
                "(https://www.google.com/maps/place/"
                f"{location['latitude']},{location['longitude']})"
            )
        else:
            address = ""

        live_data = attraction_data["liveData"][0]

        status = live_data["status"]

        if status == "OPERATING":
            wait = live_data["queue"]["STANDBY"]["waitTime"]
            threshold = row["wait_threshold"]

            if row["reached_threshold"]:
                if wait > threshold:
                    status_embed = embed.create_embed(
                        "Above threshold",
                        f"**{live_data['name']}** is over your threshold.\n"
                        + address,
                    )
                    status_embed.add_field(
                        name="Wait time",
                        value=f"`{wait}` minutes",
                        inline=False,
                    )
                    status_embed.add_field(
                        name="Threshold",
                        value=f"`{threshold}` minutes",
                        inline=False,
                    )

                    db.execute(
                        "UPDATE tracks "
                        "SET reached_threshold = 0 "
                        "WHERE user_id = ? AND attraction_id = ?",
                        row["user_id"],
                        row["attraction_id"],
                    )
                    
                    Id = row["user_id"]
                    
                    user = client.get_user(Id)
                    await user.send(
                        content=f"<@{row['user_id']}>", embed=status_embed
                    )

                    #await channel.
            elif wait <= threshold:
                status_embed = embed.create_embed(
                    "Reached threshold!",
                    f"**{live_data['name']}** "
                    "has reached your threshold.\n" + address,
                )
                status_embed.add_field(
                    name="Threshold",
                    value=f"`{threshold}` minutes",
                    inline=False,
                )
                status_embed.add_field(
                    name="Wait time", value=f"`{wait}` minutes", inline=False
                )

                db.execute(
                    "UPDATE tracks "
                    "SET reached_threshold = 1 "
                    "WHERE user_id = ? AND attraction_id = ?",
                    row["user_id"],
                    row["attraction_id"],
                )
                
                Id = row["user_id"]
                    
                user = client.get_user(Id)
                await user.send(
                    content=f"<@{row['user_id']}>", embed=status_embed
                )


                #await channel.send(
                #    content=f"<@{row['user_id']}>", embed=status_embed
                #)
        else:
            if row["reached_threshold"]:
                status_message = (
                    f"under {status.lower()}"
                    if status == "REFURBISHMENT"
                    else status.lower()
                )
                status_embed = embed.create_embed(
                    f"{live_data['name']} is {status_message}.",
                    f"{address}\n"
                    "You will be notified when the attraction is up "
                    "and has reached your threshold.",
                )

                db.execute(
                    "UPDATE tracks "
                    "SET reached_threshold = 0 "
                    "WHERE user_id = ? AND attraction_id = ?",
                    row["user_id"],
                    row["attraction_id"],
                )
                
                Id = row["user_id"]
                    
                user = client.get_user(Id)
                await user.send(
                    content=f"<@{row['user_id']}>", embed=status_embed
                )

                #await channel.send(
                #    content=f"<@{row['user_id']}>", embed=status_embed
                #)
