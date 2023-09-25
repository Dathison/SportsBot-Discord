import secrets_file
import discord
import requests
from tabulate import tabulate
from discord.ext import commands
import pandas as pd
import datetime
import json
from dateutil import parser
import configparser
import asyncio
import git
import os
import sys
import shutil
import time

TOKEN = secrets_file.botToken  # Token for Discord bot.
API_TOKEN = secrets_file.apiToken  # Token for The Sports DB.

intents = discord.Intents.all() # or .all() if you ticked all, that is easier
intents.members = True # If you ticked the SERVER MEMBERS INTENT
description = '''The new and improved Gaudium you never knew you needed!'''
bot = commands.Bot(command_prefix='g!', description=description, help_command=commands.DefaultHelpCommand(), intents=intents)

def timeConverter(timestamp):  # Converts ISO 8601 timestamps into Unix Epoch timestamps, something that Discord can use for its dynamic timestamps.
    # DEP: dateutil.parser

    dt_object = parser.isoparse(timestamp)  # Parse the input timestamp with timezone support
    epoch_timestamp = int(dt_object.timestamp())  # Converts the output to an epoch timestamp in the form of an int.

    return str(epoch_timestamp)  # Then converts back to a string. This automatically removes the decimal number. There is probably a more correct way to do this, but this seemed the easiest.

def findTeamId(team):  # Finds the corresponding The Sports DB team ID for the give input.

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/searchteams.php?t={team}')
    output = response.json()

    if output['teams'] is not None and team == output['teams'][0]['strTeam'] or output['teams'] is not None and team == output['teams'][0]['strAlternate']:     # If the API returns something not empty AND the input of `team` value is that
        output_team = output['teams'][0]['idTeam']  #Sets the `output_team` variable to be that of `idTeam` from the first object.                              # of either the `strTeam` or `strAlternate` keys in the first object:

    else:
        output_team = None

    return output_team  # Returns the `output_team` variable for use in other functions.

def findLeagueId(league):  # This function can be rewritten to be like the one above.

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/all_leagues.php')
    output = response.json()


    if output['leagues'] is not None:

        for leagues in output['leagues']:

            if leagues['strLeague'] == league or leagues['strLeagueAlternate'] == league:
                output_league = leagues['idLeague']

    return output_league


def leagueMatcher(input):  # Takes the input and matches it to a league name. Generally used for printing to user and for inputting into `findLeagueId()`
    match input:
        case "pl":  # If input is 'pl'
            league = "English Premier League"  # Set `league variable` to 'English Premier League'

        case "ch":
            league = "English League Championship"

        case "l1":
            league = "English League 1"

        case "l2":
            league = "English League 2"

        case "ll":
            league = "Spanish La Liga"

        case "bl":
            league = "German Bundesliga"

        case "lu":
            league = "French Ligue 1"

        case "sa":
            league = "Italian Serie A"

        case "ed":
            league = "Dutch Eredivisie"

        case "fr":
            league = "Club Friendlies"

        case "ucl":
            league = "UEFA Champions League"

        case "uel":
            league = "UEFA Europa League"

        case "uecl":
            league = "UEFA Europa Conference League"

        case "fac":
            league = "FA Cup"

        case "efl":
            league = "EFL Cup"

        case "wc":
            league = "FIFA World Cup"

        case "ec":
            league = "UEFA European Championships"

        case _:  # If input matches none of the above, this is the default catch-all.
            league = input

    return league

def colourToHex(colourInput):
    colourHex = colourInput.replace("#","0x")

    return int(colourHex, 0)  # Returns the output as a hex int.

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    channel = bot.get_channel(1138455667133382716)  # Get channel for bot testing room.
    await channel.send(f"{bot.user.name} is online!")

    repo_path = os.path.dirname(os.path.abspath(sys.argv[0]))   # Path to the local Git repository
    repo = git.Repo(repo_path)

    while True and '.bak' not in __file__:  # While true and the file isn't a backup:

        print("Fetching changes from remote...")
        origin = repo.remote(name="origin")
        origin.fetch()

        local_branch = repo.active_branch
        remote_branch = origin.refs[local_branch.name]

        if local_branch.commit != remote_branch.commit:
            print("Shutting down for updates.")
            await channel.send("Shutting down for updates.")
            shutil.copy2(__file__, f'{__file__}.bak')
            origin.pull()
            os.execv(sys.executable, ['python3'] + sys.argv)

        await asyncio.sleep(1800)

@bot.command()
async def hello(ctx):
    """Used for debugging."""
    await ctx.send("Hello world!")

@bot.command()
async def next_matches(ctx, input_team):  # This command has one required argument (`input_team`) which means that the command name has to be followed by an argument in Discord.
    """Finds the next five matches for a team.
        Usage: {team}

        Parameters:
        -   team: The full name or nickname of the team to search for.
    """

    team_id = findTeamId(input_team)  # Takes the input and pushes it through the function for finding the team ID. `team_id` is set to this function to save it more permanently for use further in this command.
    print(team_id)

    if team_id == None:  # If input doesn't match any of the cases seen above:
        await ctx.send("Team not found. Try a different name and run the command again.")

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/eventsnext.php?id={team_id}')
    fixtures = response.json()

    status_table = []
    home_table = []
    away_table = []
    opponent_table = []
    venue_table = []
    competition_table = []
    time_table = []
    headers = ["H/A","Against","Competition","Time"]

    if fixtures['events'] is not None:

        for event in fixtures['events']:

            home_table.append(event['strHomeTeam'])
            away_table.append(event['strAwayTeam'])
            competition_table.append(event['strLeague'])

            if event['strTimestamp'] is not None:
                time_table.append('<t:' + timeConverter(event['strTimestamp']) + ':f>')

            elif event['strTimeLocal'] is not None:
                time_table.append(event['strTimeLocal'][:5])

            elif event['strTime'] is not None:
                time_table.append(event['strTime'][:5])

            else:
                time_table.append("n/a")

            if event['strVenue'] is not None:
                venue_table.append(event['strVenue'])

            else:
                venue_table.append("n/a")

            if input_team == event['strHomeTeam']:
                status_table.append('H')
                opponent_table.append(event['strAwayTeam'])

            elif input_team == event['strAwayTeam']:
                status_table.append('A')
                opponent_table.append(event['strHomeTeam'])

    table = tabulate(zip(status_table,opponent_table,competition_table,time_table), headers=headers)

    await ctx.send(f"Next five matches for {input_team}:")
    await ctx.send(table)

@bot.command()
async def matches(ctx, input_league, input_date):
    """Lists all matches on the specified in a given competition.
        Usage: {league} {date}

        Parameters:
        -   league: Two to four character code for the league name. 'pl' for Premier League, 'ucl' for Champions League, 'uecl' for Europa Conference League,
            and so on.
        -   date: The day to lookup, YYYY-mm-dd format.
    """

    league = leagueMatcher(input_league)

    if input_date == "now":
        current_date = datetime.datetime.date(datetime.datetime.now())
        date = current_date.isoformat()

    else:

        try:
            datetime.datetime.strptime(input_date, "%Y-%m-%d")

        except:
            print("Not a valid date!")
            await ctx.send("Date not recognised. Please double-check your input and try again.")

        else:
            print("Valid date!")
            date = input_date

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/eventsday.php?d={date}&s=Soccer&l={league}')
    if response == None:
        await ctx.send("League not recognised. Please check your input and try again.")

    else:
        fixtures = response.json()

    json_data = json.dumps(fixtures)
    data = json.loads(json_data)

    home_table = []
    away_table = []
    venue_table = []
    time_table = []
    headers = ["Home","Away","Time"]

    if fixtures['events'] is not None:

        for event in fixtures['events']:

    # for event in data['events']:
            home_table.append("`" + event['strHomeTeam'])
            away_table.append(event['strAwayTeam'] + '`')

#            if event['strVenue'] != "":
#                venue_table.append(event['strVenue'])

#            else:
#                venue_table.append('n/a')


            if event['strTimestamp'] is not None:
                time_table.append('<t:' + timeConverter(event['strTimestamp']) + ':t>')

            elif event['strTimeLocal'] is not None:
                time_table.append(event['strTimeLocal'][:5])

            elif event['strTime'] is not None:
                time_table.append(event['strTime'][:5])

            else:
                time_table.append("`time not found`")

    table = tabulate(zip(home_table,away_table,time_table), headers=headers)
#    table = zip(home_table,away_table,venue_table,time_table)
#    df = pd.DataFrame(table, columns=['`Home', 'Away', 'Venue', 'Time`'])
#    sorted_df = df.sort_values(by='Time`')



    await ctx.send(table)
#    await ctx.send(sorted_df.to_string(index=False))

@bot.command()
async def matchweek(ctx, input_league, input_mw, input_season=None):
    """Shows all matches for a given league on the specified matchweek.
        Usage: {league} {matchweek} {season}

        Parameters:
        -   league: Two to four character code for the league name. 'pl' for Premier League, 'ucl' for Champions League, 'uecl' for Europa Conference League,
            and so on.
        -   matchweek: The matchweek number.
        -   season: (Optional) Season to look up, defaults to current season if not specified. Formatted as YYYY-YYYY, e.g. 2020-2021.
    """

    league_input = leagueMatcher(input_league)
    league_id = findLeagueId(league_input)

    if input_season == None:
        season = ""

    else:
        season = "&s=" + input_season

    if league_id == None:
        await ctx.send("League not found. Please check your input and try again.")

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/eventsround.php?id={league_id}&r={input_mw}{season}')
    fixtures = response.json()

    home_table = []
    away_table = []
    venue_table = []
    time_table = []
    headers = ["Home","Away","Time"]

    if fixtures['events'] is not None:

        for event in fixtures['events']:

            home_table.append('`' + event['strHomeTeam'])
            away_table.append(event['strAwayTeam'] + '`')

            if event['strTimestamp'] is not None:
                time_table.append('<t:' + timeConverter(event['strTimestamp']) + ':f>')

            elif event['strTimeLocal'] is not None:
                time_table.append(event['strTimeLocal'][:5])

            elif event['strTime'] is not None:
                time_table.append(event['strTime'][:5])

            else:
                time_table.append("n/a")

            if event['strVenue'] is not None:
                venue_table.append(event['strVenue'])

            else:
                venue_table.append("n/a")

    table = tabulate(zip(home_table,away_table,time_table), headers=headers)

    await ctx.send(f"Matches for {league_input} matchweek {input_mw}:")
    await ctx.send(table)

@bot.command()
async def next_match(ctx):
    """Announces matchday for your club or says when the next match is if it isn't today.

        No parameters.
    """

    try:
        print("Initialising config.")
        config = configparser.ConfigParser()
        config.read('config.ini')
        config['General']['MainClub']

    except:
        try:
            print("No config found!")
            await ctx.send("Config not found. Is this a new installation? Please enter the team that this bot supports.")

            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel

            try:
                user_input = await bot.wait_for('message', timeout=30.0, check=check)
                club = user_input.content

            except asyncio.TimeoutError:
                await ctx.send("You took too long to respond. Please run the command again.")

#            club = input("Config not found. Is this a new installation? Please enter the team that this bot supports:")
            print("Writing configs.")

            config['General'] = {'MainClub': club}

            with open('config.ini', 'w') as configfile:
                config.write(configfile)

        except Exception as error:
            print(error)

    print("Reading config.")
    main_club = config['General']['MainClub']

    team_id = findTeamId(main_club)

    today = datetime.date.today().strftime('%Y-%m-%d')

    club_response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/searchteams.php?t={main_club}')
    match_response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/eventsnext.php?id={team_id}')
    club = club_response.json()
    fixtures = match_response.json()

    if fixtures['events'] is not None and int(timeConverter(fixtures['events'][0]['strTimestamp'])) > int(time.time()): # If the first listed match start time is ahead of the time now (If it has yet to start):

        if today == fixtures['events'][0]['dateEvent']:
            matchLeague = fixtures['events'][0]['strLeague']
            matchHomeTeam = fixtures['events'][0]['strHomeTeam']
            matchAwayTeam = fixtures['events'][0]['strAwayTeam']

            if fixtures['events'][0]['strTimestamp'] is not None:
                    matchTime = ('<t:' + timeConverter(fixtures['events'][0]['strTimestamp']) + ':t>')

            elif fixtures['events'][0]['strTimeLocal'] is not None:
                    matchTime = (fixtures['events'][0]['strTimeLocal'][:5] + ' local time')

            elif fixtures['events'][0]['strTime'] is not None:
                    matchTime = (fixtures['events'][0]['strTime'][:5])

            else:
                    matchTime = "`time not found`"

            if fixtures['events'][0]['strVenue'] != "":
                    matchVenue = fixtures['events'][0]['strVenue']

            else:
                    matchVenue = "`stadium not found`"

            matchWeek = fixtures['events'][0]['intRound']
            matchHomeTeam = fixtures['events'][0]['strHomeTeam']
            matchAwayTeam = fixtures['events'][0]['strAwayTeam']
            matchCompetition = fixtures['events'][0]['strLeague']

            if main_club in fixtures['events'][0]['strHomeTeam']:
                matchOpponent = fixtures['events'][0]['strAwayTeam']
                matchStatus = "H"

            else:
                matchOpponent = fixtures['events'][0]['strHomeTeam']
                matchStatus = 'A'

            # Extract the image link from JSON data
            if fixtures['events'][0]['strThumb'] is not None:
                image_link = fixtures['events'][0]['strThumb']

            elif fixtures['events'][0]['strSquare'] is not None:
                image_link = fixtures['events'][0]['strSquare']

            elif fixtures['events'][0]['strPoster'] is not None:
                image_link = fixtures['events'][0]['strPoster']

            elif fixtures['events'][0]['strBanner'] is not None:
                image_link = fixtures['events'][0]['strBanner']

            await ctx.send(f"Matchday!\n({matchStatus}) **{matchHomeTeam}** - **{matchAwayTeam}** @ {matchVenue} at **{matchTime}**!\n{matchCompetition} Matchweek {matchWeek}.")

            if image_link != "":  # If there is an image to embed:
                # Create an embed with the image
                image_name = f"{matchLeague} matchweek {matchWeek}: {matchHomeTeam} - {matchAwayTeam}"
                embed = discord.Embed(title=image_name, color=discord.Color(colourToHex(club['teams'][0]['strKitColour1'])))  # Uses hex code for colouring embed line.
                embed.set_image(url=image_link)

                await ctx.send(embed=embed)  # Send the embed as a message

        else:
    
            if fixtures['events'][0]['strTimestamp'] is not None:
                matchTime = ('<t:' + timeConverter(fixtures['events'][0]['strTimestamp']) + ':F>')
                matchToGo = ('<t:' + timeConverter(fixtures['events'][0]['strTimestamp']) + ':R>')

            elif fixtures['events'][0]['strTimeLocal'] is not None:
                matchTime = (fixtures['events'][0]['strTimeLocal'][:5] + ' local time')

            elif fixtures['events'][0]['strTime'] is not None:
                matchTime = (fixtures['events'][0]['strTime'][:5])

            else:
                matchTime = "`time not found`"

            if main_club in fixtures['events'][0]['strHomeTeam']:
                matchOpponent = fixtures['events'][0]['strAwayTeam']
                matchStatus = "at home"

            else:
                matchOpponent = fixtures['events'][0]['strHomeTeam']
                matchStatus = 'away'

            if fixtures['events'][0]['strVenue'] != "":
                matchVenue = fixtures['events'][0]['strVenue']

            else:
                matchVenue = "`stadium not found`"

            matchWeek = fixtures['events'][0]['intRound']
            matchCompetition = fixtures['events'][0]['strLeague']

            await ctx.send(f"The next match is {matchStatus} against {matchOpponent} at {matchVenue}. It is on {matchTime} which is {matchToGo}.")

    elif fixtures['events'] is not None and int(timeConverter(fixtures['events'][0]['strTimestamp'])) < int(time.time()):   # If the first listed match start time is behind the current time (If a match has already started):

        if fixtures['events'][1]['strTimestamp'] is not None:
                matchTime = ('<t:' + timeConverter(fixtures['events'][1]['strTimestamp']) + ':f>')
                matchToGo = ('<t:' + timeConverter(fixtures['events'][1]['strTimestamp']) + ':R>')

        elif fixtures['events'][1]['strTimeLocal'] is not None:
                matchTime = (fixtures['events'][1]['strTimeLocal'][:5] + ' local time')

        elif fixtures['events'][1]['strTime'] is not None:
                matchTime = (fixtures['events'][1]['strTime'][:5])

        else:
                matchTime = "`time not found`"

        if main_club in fixtures['events'][1]['strHomeTeam']:
                    matchOpponent = fixtures['events'][1]['strAwayTeam']
                    matchStatus = "at home"

        else:
                    matchOpponent = fixtures['events'][1]['strHomeTeam']
                    matchStatus = 'away'

        if fixtures['events'][1]['strVenue'] != "":
                    matchVenue = fixtures['events'][1]['strVenue']

        else:
                    matchVenue = "`stadium not found`"

        matchWeek = fixtures['events'][1]['intRound']
        matchCompetition = fixtures['events'][1]['strLeague']

        await ctx.send(f"The next match is {matchStatus} against {matchOpponent} at {matchVenue}. It is on {matchTime} which is {matchToGo}.")


@bot.command()
async def table(ctx, input_league, input_season=None):
    """Shows the table for the specified competition.
        Usage: {league} {season}

        Parameters:
        -   league: Two to four character code for the league name. 'pl' for Premier League, 'ucl' for Champions League, 'uecl' for Europa Conference League,
            and so on.
        -   season: (Optional) Season to look up, defaults to current season if not specified. Formatted as YYYY-YYYY, e.g. 2020-2021.
    """

    league = leagueMatcher(input_league)
    league_id = findLeagueId(league)

    if league_id == None:
        await ctx.send("League not recognised. Please check your input and try again.")

    if input_season == None:
        season = ""

    else:
        season = "&s=" + input_season

    response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/lookuptable.php?l={league_id}{season}')

    try:
        json_table = response.json()

    except Exception as error:
        await ctx.send("No data found. Please alter your search and try again.")
        print(error)

    # Initialising a bunch of tables for use later.
    pos = []
    team = []
    played = []
    win = []
    draw = []
    loss = []
    gf = []
    ga = []
    gd = []
    points = []
    form = []
    headers = ['Pos','Team','GP','W','D','L','GF','GA','GD','P','Form']

    for i in range(len(json_table['table'])):

        pos.append(json_table['table'][i]['intRank'])
        team.append(json_table['table'][i]['strTeam'])
        played.append(json_table['table'][i]['intPlayed'])
        win.append(json_table['table'][i]['intWin'])
        draw.append(json_table['table'][i]['intDraw'])
        loss.append(json_table['table'][i]['intLoss'])
        gf.append(json_table['table'][i]['intGoalsFor'])
        ga.append(json_table['table'][i]['intGoalsAgainst'])
        gd.append(json_table['table'][i]['intGoalDifference'])
        points.append(json_table['table'][i]['intPoints'])
        form.append(json_table['table'][i]['strForm'])

    table = tabulate(zip(pos,team,played,win,draw,loss,gf,ga,gd,points,form), headers=headers)

    if league_id == None or json_table == None:  # If no league is found or if no output has been made to the tables:
        pass  # Don't do anything.

    elif league != None and input_season == None:
        await ctx.send(f"{league} table for the latest season.")
        await ctx.send(f"```{table}```")

    elif league != None and input_season != None:
        await ctx.send(f"{league} table for the {input_season} season.")
        await ctx.send(f"```{table}```")

@bot.command()
async def past_matches(ctx, input_team):  # This command has one required argument (`input_team`) which means that the command name has to be followed by an argument in Discord.
    """Finds the past five matches for a team.
        Usage: {team}

        Parameters:
        -   team: The full name or nickname of the team to search for.
    """

    try:
        team_id = findTeamId(input_team)  # Takes the input and pushes it through the function for finding the team ID. `team_id` is set to this function to save it more permanently for use further in this command.

        try:
            match_response = requests.get(f'https://www.thesportsdb.com/api/v1/json/{API_TOKEN}/eventslast.php?id={team_id}')
            fixtures = match_response.json()
        except:
            await ctx.send(f"Fetching data failed.")

        try:
            status_table = []
            home_table = []
            score_table = []
            away_table = []
            venue_table = []
            competition_table = []
            time_table = []
            separator_table = []
            headers = ["H/A","Home","Score","Away","Venue","Competition","Time"]

        except:
            await ctx.send(f"Initialising tables failed.")

        if fixtures['results'] is not None:

            for event in fixtures['results']:

                try:
                    home_table.append(event['strHomeTeam'])
            
                except:
                    await ctx.send(f"Home team failed.")
                
                try:
                    score_table.append(event['intHomeScore'] + '-' + event['intAwayScore'])
                
                except:
                    await ctx.send(f"Home score failed.")
                    
                try:
                    away_table.append(event['strAwayTeam'])

                except:
                    await ctx.send(f"Away team failed.")               
                
                try:
                    competition_table.append(event['strLeague'] + '`')

                except:
                    await ctx.send(f"League failed.")                
                                
                separator_table.append("-")

                try:
                    if event['strTimestamp'] is not None:
                        time_table.append('<t:' + timeConverter(event['strTimestamp']) + ':f>')

                    elif event['strTimeLocal'] is not None:
                        time_table.append(event['strTimeLocal'][:5])

                    elif event['strTime'] is not None:
                        time_table.append(event['strTime'][:5])

                    else:
                        time_table.append("n/a")
                
                except:
                    await ctx.send(f"Time table failed.")

                if event['strVenue'] is not None:
                    venue_table.append(event['strVenue'])

                else:
                    venue_table.append("n/a")

                if input_team == event['strHomeTeam']:
                    status_table.append('`H')
                elif input_team == event['strAwayTeam']:
                    status_table.append('`A')

            table = tabulate(zip(status_table,home_table,score_table,away_table,venue_table,competition_table,time_table), headers=headers)

            await ctx.send(f"Last five matches for {input_team}, with the most recent one first:")
            await ctx.send(table)

    except Exception as error:
        print(error)
        await ctx.send(f"Command failed, please try again!")
        await ctx.send(error)

try:
    # Run the bot with the token to connect it to Discord
    bot.run(TOKEN)
except discord.LoginFailure:
    print("Invalid bot token. Please check your token.")
except discord.HTTPException as e:
    print(f"An error occurred while connecting to Discord: {e}")
    # You can implement custom logic to handle the error, like retrying the connection after a delay.
    asyncio.sleep(5)  # Wait for 5 seconds before retrying
    bot.loop.run_until_complete(bot.login(TOKEN))
    bot.loop.run_until_complete(bot.connect())
