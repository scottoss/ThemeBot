import helpers.database as db
import helpers.embed as embed


def require_destinations(func):
    async def inner(interaction, *args, **kwargs):
        await interaction.response.defer()
        rows = db.execute(
            "SELECT * FROM destinations WHERE user_id = ?", interaction.user.id
        )

        if not rows:
            embed_message = embed.create_embed(
                "Error",
                "You have no destinations to search.\n"
                "Try using `/destination add`!",
            )

            return await interaction.followup.send(
                embeds=[embed_message]
            )

        await func(interaction, *args, **kwargs)

    return inner
