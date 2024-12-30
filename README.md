# ThemeBot
A Discord bot to assist with all things theme parks.




#### How to Run:
1. Create a new [Discord application](https://discord.com/developers/applications), or use an existing one. Invite the application's bot to your desired Discord server with `bot` and `application.commands` scopes.
2. Ensure you have [Python installed.](https://www.python.org/downloads/), and make sure it is added to PATH.
3. Clone this repository.
4. Open your terminal and navigate to the newly cloned repository.
4. Create a file in the root directory of the cloned repository named `.env` with the following:
    ```
    DISCORD_TOKEN=<YOUR_TOKEN>
    STATUS_CHANNEL_ID=<YOUR_CHANNEL_ID>
    
    ```
    where `<YOUR_TOKEN>` is your bot's token, `<YOUR_CHANNEL_ID>` is the ID of the channel you want status updates in.
5. Execute `pip install -r requirements.txt` in your terminal.
6. Open your terminal and navigate to the newly cloned repository.
7. Execute `python bot.py` in your terminal.

#### Description:
ThemepBot is a Discord bot that assists users with everything they need to plan their next trip to a theme park.

The bot includes features such as viewing the wait times, return times, operating hours, and wait forecasts for attractions. Users can also track when the wait time for a certain attraction reaches a certain threshold as well as get the weather forecast for a certain destination to get a sense of how hot/cold it may be.

This project revolves around the idea of adding destinations in which the user searches through to get the information they want. This improves the user experience so that the user doesn't have to worry about search errors resulting from attractions with the same name in different parks (e.g. Peter Pan's Flight in Disneyland California versus Disneyland Paris). Additionally, approaching the project this way improves searching times by reducing the number of destinations that must be searched.

To begin, `bot.py` is the bot's main entry point, containing all its registered commands. After initializing the bot with its token, it then begins the loop of checking attractions' wait times against the users' wait thresholds in the `themeparkify.db` database in the `tracks` table.

This process is facilitated by the `helpers/track_attractions.py` file, which loops through each attraction in the `tracks` table, gets the wait time associated with that attraction, then notifies the user if the wait time has reached their specified threshold. To add to the user experience, the location is also provided to differentiate between attractions in different destinations that may have the same name.

The bot's primary source for attraction data is the [ThemeParks API](https://themeparks.wiki/), which contains useful information about theme parks, such as attractions, locations, and more. In this project, the API is accessed through various helper methods in the `helpers/themeparks.py` file, which add the ability to search for certain entities as well as access them directly.

`commands/attraction.py` houses all the code executed by commands pertaining to attractions. For example, there are commands for getting information for an attraction, tracking and untracking an attraction, viewing the attractions currently tracked, and clearing all tracked attractions. Getting information for an attraction uses the API to retrieve information like wait time and operating hours.

An interesting feature in attraction data for Disney theme parks is the wait forecast, which provides predicted wait times by hour. When getting attraction information, a graph of this forecast will also be provided if it is available, using Matplotlib to easily generate a graph through Python.

`commands/destination.py` works similarly to `commands/attraction.py` in where there is the ability to add and remove a destination, view added destinations, and clear all added destinations.

`helpers/database.py` offers helper methods for interacting with the `themeparkify.db` database using CS50's SQL module. Adding on to the original ability to execute SQL code, commonly repeated code such as getting the user's destination IDs and tracked attractions is also bundled into helper methods in this file.

`helpers/decorators.py` includes a decorator that checks if the user has any added destinations. This is useful when the user wants to search for an attraction or get the weather as it will notify the user that the command will not work without any added destinations.

`helpers/embed.py` contains useful functions for creating and modifying Discord embeds, such as generating errors or adding entities and their locations to the embed as fields.

`.env` contains information like tokens, IDs, and API keys necessary for the bot to function. This file is declared in `.gitignore`.

`.gitignore` ignores any non-important or sensitive files that should not be committed to the Git repository.

`requirements.txt` lists the necessary `pip` modules for this project to work. These dependencies can be installed using `pip install -r requirements.txt`.

`themeparkify.db` is the database that contains users' added destinations and tracked attractions.

In the future, features such as showtime and attraction return time reminders as well as restaurant information may be added. Including the travel time from one destination to another may also prove to be useful to users.
