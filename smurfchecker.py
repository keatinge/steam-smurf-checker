import re
import requests
import json
import time
import colorama
import tabulate

#steam api key
APIKEY = ""
colorama.init()


class User:
    def __init__ (self, steamID64, personaName, isProfilePublic, profileUrl, timeCreated = None):
        self.steamID64 = steamID64
        self.isProfilePublic = isProfilePublic
        self.personaName = personaName
        self.timeCreated = timeCreated
        self.profileUrl = profileUrl


    def get_playtime_stats(self):
        """
        For public profiles only, this gets the following statistics and adds them as variables to self
        number of games owned, playtime in csgo all time, playtime in csgo past 2 weeks, it also creates
        the variable accountAge to self which contains the age of the account in years
        """


        assert self.isProfilePublic == True, "Cant get playtime stats for private profile"

        reqUrl = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + APIKEY + "&steamid=" + self.steamID64

        #resp = requests.get(reqUrl).text
        resp = api_call(reqUrl)

        jsonResp = json.loads(resp)

        gameCount = jsonResp["response"]["game_count"]
        csgoForever = None
        csgo2Week = None
        for game in jsonResp["response"]["games"]:
            if game['appid'] == 730:
                csgoForever = game["playtime_forever"]
                csgo2Week = game["playtime_2weeks"]

        self.gameCount = gameCount
        self.csgoForever = round(csgoForever / 60)
        self.csgo2Week = csgo2Week

        #convert to years
        self.accountAge = (round((time.time() - self.timeCreated)/(60*60*24*365), 1))

    def get_friends(self):
        """
        Gets a list of tuples containing all the friends that a user has and the unix timestamp that is the date
        that the two users became friends. Returns nothing, just adds it to self
        """


        url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=" + APIKEY + "&steamid=" + self.steamID64 + "&relationship=friend"
        #resp = requests.get(url).text
        resp = api_call(url)

        jsonResp = json.loads(resp)

        friendList = []

        for friend in jsonResp['friendslist']['friends']:
            friendList.append((friend['steamid'], friend['friend_since']))

        self.friendsList = friendList



def get_player_summaries(steamID64List):
    """
    Takes a list of steamID64s and returns a list of User objects containing the following information
    username, steamid64, profileurl, isprofileprivate, and if the profile is not private it also adds the
    date the account was created in unix timestamp
    """


    #create comma separated list of steamID64s
    fullSteamIDsString = ",".join(steamID64List)

    url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=" + APIKEY + "&steamIDS=" + fullSteamIDsString
    #response = requests.get(url).text
    response = api_call(url)
    jsonResp = json.loads(response)

    returnUserList = []

    for player in jsonResp['response']['players']:
        name = player['personaname']
        steamID64 = player['steamid']
        profileUrl = player['profileurl']

        if player['communityvisibilitystate'] == 3: #public profile
            timeCreated = player['timecreated']
            returnUserList.append(User(steamID64, name, True, profileUrl, timeCreated))
        else: #private profile
            returnUserList.append(User(steamID64, name, False, profileUrl))
    return returnUserList


def steamid_to_64bit(steamid):
    """
    credit to MattDMo at http://stackoverflow.com/a/36463885/2056979
    converts a steamid in format (STEAM_0:XXXXXXX) to a steamID64 (83294723984234)
    """


    steam64id = 76561197960265728
    id_split = steamid.split(":")
    steam64id += int(id_split[2]) * 2
    if id_split[1] == "1":
        steam64id += 1
    return steam64id

def get_steam_users_from_status(status):
    """
    Uses regex to create a list of steamID64s from a string that was obtained by typing status into the csgo
    console then uses get_player_summaries to in the end return a list of Users
    """


    steamID64List = []

    for currentUser in re.findall(r'#\s+\d+\s\d+\s"(.+?)"\s(.+?) ', status):
        #add a new steamID64 to the list
        steamID64List.append(str(steamid_to_64bit(currentUser[1])))

    return get_player_summaries(steamID64List)

def check_friends(listOfUsers):
    """
    Checks for users inside listOfUsers that are friends with each other, it loops through every user, then for every
    user loops through every friend, then for every friend it loops through every user again, it checks if the
    friend has the same steamID64 as the user

    Returns a list of tuples that contain (username1, username2, howLongInDaysBeenFriends)
    """


    currentFriends = []
    for user in listOfUsers:
        if user.isProfilePublic == False:
            continue
        for friend in user.friendsList:
            for checkUser in listOfUsers:
                if checkUser.steamID64 == friend[0]:

                    #convert to days
                    timeFriends = round((time.time() - friend[1])/(60*60*24), 1)

                    #make sure they haven't already been logged as friends, the reversal is extremely important
                    if (checkUser.personaName, user.personaName, timeFriends) not in currentFriends:
                        currentFriends.append((user.personaName, checkUser.personaName, timeFriends))

    return currentFriends

def hours_played_key(itemToCheck):
    """
    Custom key function to private profiles to be calculated as 0 hours played when sorting
    """
    if itemToCheck[1] == "":
        return 0
    return itemToCheck[1]


def api_call(url):
    """
    All API calls get passed through here so the program can have a single way to keep track of how long api calls
    are taking
    """

    startTime = time.time()
    respText = requests.get(url).text
    totalTime = round(time.time() - startTime, 2)

    with open("apiCalls.txt", "a") as f:
        f.write(str(totalTime) + "s" + " -- " +  url + "\n")

    #debug only, print api call too
    print(str(totalTime) + "s", "--", url)

    return respText



#reset apiCalls file
open("apiCalls.txt", "w").close()

with open("status.txt", "r") as f:
    status = f.read()

usersList = get_steam_users_from_status(status)

for user in usersList:
    if user.isProfilePublic:
        user.get_playtime_stats()
        user.get_friends()


printTupleList = []
for user in usersList:
    if user.isProfilePublic:
        printTupleList.append((user.personaName, user.csgoForever, user.accountAge))
    else:
        printTupleList.append((colorama.Fore.RED + user.personaName + colorama.Fore.RESET, "", ""))

#sort by hours played
printTupleList.sort(key=hours_played_key)

print("\n")
print(tabulate.tabulate(printTupleList, headers=["Name", "HRS", "YR"], tablefmt="orgtbl"))

print("\n")
for friend in check_friends(usersList):
    print(colorama.Fore.CYAN + friend[0], "and", friend[1], "have been friends for", friend[2], "days" + colorama.Fore.RESET)