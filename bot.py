import asyncio
import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import commands
import commands.attraction as attraction
import commands.destination as destination
#import commands.List as List
#import commands.weather as weather
import helpers.track_attractions as track_attractions

logging.getLogger().setLevel(logging.INFO)

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents,
                   case_insensitive=False,)
                   
                   
#tree = app_commands.CommandTree(bot)
def main():
    #attractions
    bot.tree.add_command(ride_info)
    bot.tree.add_command(clear_all_tracked_rides)
    bot.tree.add_command(track_a_ride)
    bot.tree.add_command(untrack_a_ride)
    bot.tree.add_command(view_tracked_rides)
    #destinations
    bot.tree.add_command(add_destination)
    bot.tree.add_command(remove_destination)
    bot.tree.add_command(clear_all_your_destinations)
    bot.tree.add_command(view_all_your_destinations)
    
    
    
    bot.run(DISCORD_TOKEN)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}!")

    while True:
        await track_attractions.track(bot)
        await asyncio.sleep(5)



@bot.command()
async def sync(ctx):
    print("sync command")
    if ctx.author.id == 613030812501278740:
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
    else:
        await ctx.send('You must be the owner to use this command!')


#@bot.tree.command(description="Sync application commands.")
#async def List_Parks(interaction):
#    await List.List_Parks(interaction, tree)





        
    #@app_commands.command(description="List all available parks.")
    #sync def list_parks(interaction):
    #    await interaction.followup.send("All parks listed here: https://themeparks.wiki/browse")

@app_commands.command(description="Get information for an attraction.")
@app_commands.describe(
    attraction_name=(
        "The attraction to search for. Type all of part of the name."
    ),
    park_name=("The theme park to search. Type all or part of the name."),
)
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def ride_info(interaction, attraction_name: str, park_name: str = None, destination_name: str = None) -> None:
    await attraction.get(
        interaction, attraction_name, park_name, destination_name
    )
    
    
@app_commands.command(description="Clear all tracked attractions.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def clear_all_tracked_rides(interaction) -> None:
    await attraction.clear_tracked(interaction)

@app_commands.command(description="Track an attraction.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def track_a_ride(
    interaction,
    attraction_name: str,
    wait_threshold: app_commands.Range[int, 0],
    park_name: str = None,
    destination_name: str = None
) -> None:
    await attraction.track(
        interaction,
        attraction_name,
        wait_threshold,
        park_name,
        destination_name,
    )



@app_commands.command(description="Untrack an attraction.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def untrack_a_ride(
    interaction,
    attraction_name: str,
    park_name: str = None,
    destination_name: str = None,
) -> None:
    await attraction.untrack(
        interaction,
        attraction_name,
        park_name,
        destination_name,
    )
    
    
    
@app_commands.command(description="View all your tracked attractions.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def view_tracked_rides(interaction) -> None:
    await attraction.view_tracked(interaction)
    
    
    
    
    
    
    
    
    
@app_commands.command(description="Add a destination to the search list.")
@app_commands.describe(
    destination_name=(
        "The destination to add. Type all of part of the name."
    )
)
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def add_destination(interaction, destination_name: str) -> None:
    await destination.add(interaction, destination_name)




@app_commands.command(description="Clear your destination list.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def clear_all_your_destinations(interaction) -> None:
    await destination.clear_added(interaction)



@app_commands.command(
    description="Remove a destination from the search list."
)
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
@app_commands.describe(
    destination_name=(
        "The destination to remove. Type all of part of the name."
    )
)
async def remove_destination(interaction, destination_name: str):
    await destination.remove(interaction, destination_name)



@app_commands.command(description="View added destinations.")
@app_commands.allowed_installs(guilds=True, users=True) # users only, no guilds for install
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) # all allowed
async def view_all_your_destinations(interaction) -> None:
    await destination.view_added(interaction)




#class Weather(app_commands.Group):
#    # Weather related commands
#
#    @app_commands.command(
#        description="Get the weather forecast for a destination."
#    )
#    @app_commands.describe(
#        destination_name=("The destination to get the weather forcast of.")
#    )
#    async def forecast(self, interaction, destination_name: str):
#        await weather.forecast(interaction, destination_name)


if __name__ == "__main__":
    main()
