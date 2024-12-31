import asyncio
import io

import aiohttp
import discord
import matplotlib.pyplot as plt
from dateutil import parser

import helpers.database as db
import helpers.decorators as decorators
import helpers.embed as embed
import helpers.themeparks as themeparks


async def clear_tracked(interaction):
    await interaction.response.defer()

    db.execute("DELETE FROM tracks WHERE user_id = ?", interaction.user.id)

    success_embed = create_attractions_embed("Cleared tracked attractions!")
    add_no_attractions(success_embed)

    await interaction.followup.send(embed=success_embed)


@decorators.require_destinations
async def get(interaction: discord.Interaction, attraction_name, park_name, destination_name):
    await interaction.response.defer()

    destination_ids = db.get_user_destination_ids(interaction.user.id)

    async with aiohttp.ClientSession() as session:
        attractions = await themeparks.search_for_entities(
            session,
            attraction_name,
            destination_ids,
            park_name,
            destination_name,
            "attraction",
        )

        if not await validate_attractions(
            interaction, attractions, attraction_name
        ):
            return

        if len(attractions) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple attractions", attraction_name
            )

            tasks = []
            for i, attraction in enumerate(attractions):
                tasks.append(
                    asyncio.create_task(
                        themeparks.get_entity(session, attraction["id"])
                    )
                )

                if i >= embed.MAX_FIELDS - 1:
                    break

            entities = await asyncio.gather(*tasks)
            await embed.add_addresses(error_embed, entities, session)

            return await interaction.followup.send(embed=error_embed)

        attraction_entity = await themeparks.get_entity(
            session, attractions[0]["id"]
        )

        attraction_task, park_task = (
            asyncio.create_task(
                themeparks.get_entity(session, attractions[0]["id"], "live")
            ),
            asyncio.create_task(
                themeparks.get_entity(session, attraction_entity["parkId"])
            ),
        )

        live_attraction, park = await attraction_task, await park_task

    message_embed = embed.create_embed(live_attraction["name"], park["name"])

    live_data = live_attraction["liveData"][0]

    if "queue" in live_data:
        queue = live_data["queue"]
        wait = queue["STANDBY"]["waitTime"]
        has_queue = True
    else:
        wait = None
        has_queue = False

    message_embed.add_field(
        name="Wait time",
        value=f"`{wait}` minutes" if wait is not None else f"`{wait}`",
    )

    message_embed.add_field(name="Status", value=f"`{live_data['status']}`")

    if has_queue:
        if "RETURN_TIME" in queue:
            return_key = "RETURN_TIME"
        elif "PAID_RETURN_TIME" in queue:
            return_key = "PAID_RETURN_TIME"
        else:
            return_key = None

        if return_key is not None:
            return_data = queue[return_key]

            state = return_data["state"]

            if state == "AVAILABLE":
                start = parser.parse(return_data["returnStart"])
                return_string = f"`{start.hour}:{start.minute:02}`"
            else:
                return_string = f"`{state}`"

            if "price" in return_data:
                if state == "AVAILABLE":
                    return_string = f"Time: {return_string}"

                price = return_data["price"]
                price_string = (
                    "\nPrice: "
                    f"`{(price['amount'] / 100):.2f} {price['currency']}`"
                )
            else:
                price_string = ""

            message_embed.add_field(
                name="Return time",
                value=return_string + price_string,
                inline=False,
            )

    if "operatingHours" in live_data:
        for operation in live_data["operatingHours"]:
            start = parser.parse(operation["startTime"])
            end = parser.parse(operation["endTime"])

            message_embed.add_field(
                name=f"{operation['type']} hours",
                value=(
                    f"`{start.hour}:{start.minute:02}` "
                    f"to `{end.hour}:{end.minute:02}`"
                ),
            )

    # Adapted from
    # https://www.geeksforgeeks.org/saving-a-plot-as-an-image-in-python/
    if "forecast" in live_data:
        hours = []
        wait_times = []

        plt.figure()

        plt.title("Wait Forecast")
        plt.xlabel("Hour")
        plt.ylabel("Wait (minutes)")

        # https://stackoverflow.com/questions/10998621/rotate-axis-tick-labels
        # plt.xticks(rotation=45, ha='right')

        plt.grid()

        for entry in live_data["forecast"]:
            datetime = parser.parse(entry["time"])

            # hours.append(f"{datetime.hour}:{datetime.minute:02}")
            hours.append(datetime.hour)
            wait_times.append(entry["waitTime"])

        plt.plot(hours, wait_times)

        fig = plt.gcf()

        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)

        img_file = discord.File(buf, filename="image.png")

        message_embed.set_image(url="attachment://image.png")

        return await interaction.followup.send(
            file=img_file, embed=message_embed
        )

    # TODO: Add return times if it exists for that attraction

    # We can maybe add notifications
    # If a return time drops to within, say 1 hour of the current time

    # TODO: Add operating hours if they exist

    await interaction.followup.send(embed=message_embed)


@decorators.require_destinations
async def track(
    interaction, attraction_name, wait_threshold, park_name, destination_name
):
    await interaction.response.defer()

    current_tracks = db.get_user_tracks(interaction.user.id)

    if len(current_tracks) >= 25:
        error_embed = embed.create_error_embed(
            "You have reached the max number of "
            "tracked attractions allowed (25).\n"
            "Try removing some with `/attraction untrack`!"
        )

        return await interaction.followup.send(embed=error_embed)

    destination_ids = db.get_user_destination_ids(interaction.user.id)

    async with aiohttp.ClientSession() as session:
        attractions = await themeparks.search_for_entities(
            session,
            attraction_name,
            destination_ids,
            park_name,
            destination_name,
            "attraction",
        )

        if not await validate_attractions(
            interaction, attractions, attraction_name
        ):
            return

        if len(attractions) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple attractions", attraction_name
            )

            tasks = []
            for i, attraction in enumerate(attractions):
                tasks.append(
                    asyncio.create_task(
                        themeparks.get_entity(session, attraction["id"])
                    )
                )

                if i >= embed.MAX_FIELDS - 1:
                    break

            entities = await asyncio.gather(*tasks)
            await embed.add_addresses(error_embed, entities, session)

            return await interaction.followup.send(embed=error_embed)

        attraction_id = attractions[0]["id"]

        duplicates = db.execute(
            "SELECT * FROM tracks "
            "WHERE user_id = ? "
            "AND attraction_id = ?",
            interaction.user.id,
            attraction_id,
        )

        if duplicates:
            db.execute(
                "UPDATE tracks "
                "SET wait_threshold = ?, reached_threshold = 0 "
                "WHERE user_id = ? "
                "AND attraction_id = ?",
                wait_threshold,
                interaction.user.id,
                attraction_id,
            )
        else:
            db.execute(
                "INSERT INTO tracks (user_id, attraction_id, wait_threshold) "
                "VALUES (?, ?, ?)",
                interaction.user.id,
                attraction_id,
                wait_threshold,
            )

        success_embed = create_attractions_embed(
            f"Tracked {attractions[0]['name']}!"
        )

        tracks = db.get_user_tracks(interaction.user.id)

        tasks = []
        wait_thresholds = tuple(row["wait_threshold"] for row in tracks)
        for row in tracks:
            tasks.append(
                asyncio.create_task(
                    themeparks.get_entity(session, row["attraction_id"])
                )
            )

        entities = await asyncio.gather(*tasks)

        await embed.add_addresses(
            success_embed, entities, session, wait_thresholds
        )

    await interaction.followup.send(embed=success_embed)


@decorators.require_destinations
async def untrack(interaction, attraction_name, park_name, destination_name):
    await interaction.response.defer()

    destination_ids = db.get_user_destination_ids(interaction.user.id)

    async with aiohttp.ClientSession() as session:
        attractions = await themeparks.search_for_entities(
            session,
            attraction_name,
            destination_ids,
            park_name,
            destination_name,
            "attraction",
        )

        tracks = db.get_user_tracks(interaction.user.id)

        matching_ids = []
        matching_name = None
        for attraction in attractions:
            for row in tracks:
                if attraction["id"] == row["attraction_id"]:
                    matching_ids.append(attraction["id"])
                    matching_name = attraction["name"]

        if not await validate_attractions(
            interaction, matching_ids, attraction_name
        ):
            return

        if len(matching_ids) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple attractions", attraction_name
            )

            tasks = []
            for match in matching_ids:
                tasks.append(
                    asyncio.create_task(themeparks.get_entity(session, match))
                )

            entities = await asyncio.gather(*tasks)
            await embed.add_addresses(error_embed, entities, session)

            return await interaction.followup.send(embed=error_embed)

        db.execute(
            "DELETE FROM tracks " "WHERE user_id = ? " "AND attraction_id = ?",
            interaction.user.id,
            matching_ids[0],
        )

        success_embed = create_attractions_embed(f"Untracked {matching_name}!")

        tracks = db.get_user_tracks(interaction.user.id)

        if tracks:
            tasks = []
            wait_thresholds = tuple(row["wait_threshold"] for row in tracks)
            for row in tracks:
                tasks.append(
                    asyncio.create_task(
                        themeparks.get_entity(session, row["attraction_id"])
                    )
                )

            entities = await asyncio.gather(*tasks)

            await embed.add_addresses(
                success_embed, entities, session, wait_thresholds
            )
        else:
            add_no_attractions(success_embed)

    await interaction.followup.send(embed=success_embed)


async def view_tracked(interaction):
    await interaction.response.defer()

    tracks = db.get_user_tracks(interaction.user.id)

    message_embed = create_attractions_embed("Tracked attractions")

    if tracks:
        tasks = []

        thresholds = []

        async with aiohttp.ClientSession() as session:
            for row in tracks:
                tasks.append(
                    asyncio.create_task(
                        themeparks.get_entity(session, row["attraction_id"])
                    )
                )

                thresholds.append(row["wait_threshold"])

            entities = await asyncio.gather(*tasks)

            await embed.add_addresses(
                message_embed, entities, session, thresholds
            )
    else:
        add_no_attractions(message_embed)

    await interaction.followup.send(embed=message_embed)


def add_no_attractions(embed):
    embed.add_field(name="You have no tracked attractions.", value="")


def create_attractions_embed(title):
    message_embed = embed.create_embed(
        title, "Here are your currently tracked attractions."
    )
    return message_embed


def create_error_embed(error):
    error_embed = embed.create_embed("Error", error)
    return error_embed


def create_search_error_embed(error, query_name):
    error_embed = create_error_embed(
        f"{error} were found containing `{query_name}`."
    )
    return error_embed


async def validate_attractions(interaction, attractions, attraction_name):
    if attractions:
        return True

    message_embed = create_search_error_embed(
        "No attractions", attraction_name
    )
    await interaction.followup.send(embed=message_embed)

    return False
