# Steam Smurf Checker
Gets statistics like playtime and account age on all the players in your game including who is friends with who and
how long the two have been friends.

#How it works
 * Uses regex to extract all the steam id's from the status
 * Requests `GetPlayerSummaries` on steam api to find out username and account age
 * For each user with public profile it requests `GetOwnedGames` to find CSGO playtime
 * Uses `GetFriendList` to get all the friends of each user and put into a list
 * Then checks the list to people in the game who are friends on steam
 * Uses colorama and tabulate to print out a table with the results

#Usage
 * Type `status` in console in CSGO
 * Paste the result into the `status.txt` file
 * Call the program like `python smurfchecker.py`

 ###Reading the output
  * HRS is hours played in CSGO
  * YR is how many years that steam account has existed
  * Red username means that the profile is private
  * Currently the users are sorted by hours played on CSGO


#Screenshot

![screenshot](http://i.imgur.com/1gWETpI.png)
