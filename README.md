# Speedrun.com Leaderboard Saver
This script will check runs from a speedrun.com leaderboard, and send an output of those that are currently ssubmitted with Twitch links. It does not download automatically.

## Dependencies
[tqdm](https://pypi.org/project/tqdm/2.2.3/)

## How to use
The program will ask for a game name, you can use either a game's abreviation (ex: tmc) or a partial or full match of a game's name (ex: Minish Cap). It will then create an output for leaderboard_[game abreviation].csv with the format of Place, Runner, Run link, Twitch link. If the Place is marked as "N/A", it means it's an obsoleted run. 
