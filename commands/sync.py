async def sync_commands(interaction, tree, guild=None):
    await interaction.response.defer()

    if guild is not None:
        await tree.sync(guild=guild)
    else:
        await tree.sync()

    await interaction.followup.send("Synced!")
