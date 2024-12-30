import asyncio

# ThemeParks API: https://api.themeparks.wiki/docs/v1/
API_URL = "https://api.themeparks.wiki/v1"


async def get_destinations(session):
    """Get destinations via an API call."""

    async with session.get(f"{API_URL}/destinations") as response:
        json = await response.json()
        return json["destinations"]


async def get_entity(session, entity_id, type=None, year=None, month=None):
    """Get entity via an API call."""

    url = f"{API_URL}/entity/{entity_id}"

    if type is not None:
        url += f"/{type}"

        if type == "schedule" and None not in (year, month):
            url += f"/{year}/{month}"

    async with session.get(url) as response:
        return await response.json()


async def search_for_entities(
    session,
    query,
    destination_ids,
    park_query=None,
    destination_query=None,
    entity_type=None,
):
    """Search for entities with the given queries and destination IDs.

    Returns a list of matching entities.
    """

    if destination_query is not None:
        if park_query is not None:
            parks = await search_for_parks(
                session, park_query, destination_ids, destination_query
            )
        else:
            parks = await search_for_parks(
                session, "", destination_ids, destination_query
            )
    elif park_query is not None:
        parks = await search_for_parks(session, park_query, destination_ids)
    else:
        parks = await search_for_parks(session, "", destination_ids)

    if entity_type is not None:
        entity_type = entity_type.upper()

    tasks = []
    for park in parks:
        tasks.append(
            asyncio.create_task(get_entity(session, park["id"], "children"))
        )

    park_data = await asyncio.gather(*tasks)

    query = query.strip().lower()

    matches = []

    for park in park_data:
        for child in park["children"]:
            if entity_type is not None and entity_type != child["entityType"]:
                continue

            if query in child["name"].lower():
                matches.append(child)

    return matches


async def search_for_destinations(session, query, destination_ids=None):
    """Search for a destination with the given queries and destination IDs.

    Returns a list of matching destinations.
    """

    destinations = await get_destinations(session)

    if destination_ids is not None:
        destinations_to_search = []

        for destination in destinations:
            if destination["id"] in destination_ids:
                destinations_to_search.append(destination)
    else:
        destinations_to_search = destinations

    query = query.strip().lower()

    matches = []

    for destination in destinations_to_search:
        if query in destination["name"].lower():
            matches.append(destination)

    return matches


async def search_for_parks(
    session, query, destination_ids, destination_query=None
):
    """Search for a park with the given queries and destination IDs.

    Returns a list of matching parks.
    """

    if destination_query is not None:
        destinations = await search_for_destinations(
            session, destination_query, destination_ids
        )
    else:
        destinations = await search_for_destinations(
            session, "", destination_ids
        )

    query = query.strip().lower()

    matches = []

    for destination in destinations:
        for park in destination["parks"]:
            if query in park["name"].lower():
                matches.append(park)

    return matches
