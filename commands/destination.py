import asyncio

import aiohttp

import helpers.database as db
import helpers.embed as embed
import helpers.themeparks as themeparks


async def add(interaction, destination_name):
    await interaction.response.defer()

    current_destination_ids = db.get_user_destination_ids(interaction.user.id)

    if len(current_destination_ids) >= 25:
        error_embed = embed.create_error_embed(
            "You have reached the max number of supported destinations (25).\n"
            "Try removing some with `/destination remove`!"
        )

        return await interaction.followup.send(embed=error_embed)

    async with aiohttp.ClientSession() as session:
        destinations = await themeparks.search_for_destinations(
            session, destination_name
        )

        if not await validate_destinations(
            interaction, destinations, destination_name
        ):
            return

        if len(destinations) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple destinations", destination_name
            )

            tasks = []
            for i, destination in enumerate(destinations):
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

        destination_id = destinations[0]["id"]

        duplicate_destinations = db.execute(
            "SELECT * FROM destinations "
            "WHERE user_id = ? "
            "AND destination_id = ?",
            interaction.user.id,
            destination_id,
        )

        if duplicate_destinations:
            error_embed = embed.create_error_embed(
                f"`{destinations[0]['name']}` "
                "is already in your list of destinations!"
            )

            return await interaction.followup.send(embed=error_embed)

        db.execute(
            "INSERT INTO destinations (user_id, destination_id) "
            "VALUES (?, ?)",
            interaction.user.id,
            destination_id,
        )

        success_embed = create_destinations_embed(
            f"Added {destinations[0]['name']}!"
        )

        current_destination_ids = db.get_user_destination_ids(
            interaction.user.id
        )

        tasks = []
        for id in current_destination_ids:
            tasks.append(
                asyncio.create_task(themeparks.get_entity(session, id))
            )

        entities = await asyncio.gather(*tasks)

        await embed.add_addresses(success_embed, entities, session)

    await interaction.followup.send(embed=success_embed)


async def clear_added(interaction):
    await interaction.response.defer()

    db.execute(
        "DELETE FROM destinations WHERE user_id = ?", interaction.user.id
    )

    success_embed = create_destinations_embed("Destinations cleared!")
    add_no_destinations(success_embed)

    await interaction.followup.send(embed=success_embed)


async def remove(interaction, destination_name):
    await interaction.response.defer()

    current_destination_ids = db.get_user_destination_ids(interaction.user.id)

    destination_name = destination_name.strip().lower()

    matches = []
    remaining_entities = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for id in current_destination_ids:
            tasks.append(
                asyncio.create_task(themeparks.get_entity(session, id))
            )

        entities = await asyncio.gather(*tasks)
        for entity in entities:
            if destination_name in entity["name"].lower():
                matches.append(entity)
            else:
                remaining_entities.append(entity)

        if not await validate_destinations(
            interaction, matches, destination_name
        ):
            return

        if len(matches) > 1:
            error_embed = embed.create_search_error_embed(
                "Multiple destinations", destination_name
            )

            await embed.add_addresses(error_embed, matches, session)

            return await interaction.followup.send(embed=error_embed)

        db.execute(
            "DELETE FROM destinations "
            "WHERE user_id = ? "
            "AND destination_id = ?",
            interaction.user.id,
            matches[0]["id"],
        )

        success_embed = create_destinations_embed(
            f"Removed {matches[0]['name']}!"
        )

        if remaining_entities:
            await embed.add_addresses(
                success_embed, remaining_entities, session
            )
        else:
            add_no_destinations(success_embed)

    await interaction.followup.send(embed=success_embed)


async def view_added(interaction):
    await interaction.response.defer()

    current_destination_ids = db.get_user_destination_ids(interaction.user.id)

    message_embed = create_destinations_embed("Destinations")

    if current_destination_ids:
        tasks = []

        async with aiohttp.ClientSession() as session:
            for id in current_destination_ids:
                tasks.append(
                    asyncio.create_task(themeparks.get_entity(session, id))
                )

            entities = await asyncio.gather(*tasks)

        await embed.add_addresses(message_embed, entities, session)
    else:
        add_no_destinations(message_embed)

    await interaction.followup.send(embed=message_embed)


def add_no_destinations(embed):
    embed.add_field(name="You have no added destinations.", value="")


def create_destinations_embed(title):
    message_embed = embed.create_embed(
        title, "Here are your currently added destinations."
    )
    return message_embed


async def validate_destinations(interaction, destinations, destination_name):
    if destinations:
        return True

    message_embed = embed.create_search_error_embed(
        "No destinations", destination_name
    )
    await interaction.followup.send(embed=message_embed)

    return False
