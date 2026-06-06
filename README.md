<div align="center">

# replaybuffer switcher

**simple tools that automatically switch obs based on what game you're playing (via discord rpc + lanyard)**

</div>

## python script (recommended)

this can switch the specific game window to capture based on what game you play

### setup

1. install python 3.12: eg. `winget install Python.Python.3.12`
2. find the install path by running `py -3.12 -c "import sys; print(sys.executable)"`, or just check `%LOCALAPPDATA%\Programs\Python\Python312\`
3. install the websocket dependency: `py -m pip install websocket-client`
4. in obs, go to **tools → scripts → python settings** and set the python install path to the folder from step 2, without `python.exe` at the end
5. go to **tools → scripts**, click `+` and add `game_capture_switcher.py`
6. join the [lanyard discord](https://discord.gg/lanyard) so the api can monitor your rpc
7. enter your discord user id
8. select your game capture source from the dropdown
9. to add a game:
    - launch it, let discord detect it, open your game capture source properties and set it to **capture specific window** and pick the game, then click **add current game** in the script panel.

## browser source

this will switch scenes based on what game you play

### setup

1. add [this url](https://girlglock.github.io/replaybuffer-scene-switcher/) as a browser source inside obs in an empty dedicated scene
2. in the browser source properties, set **page permissions** to **advanced** and make sure **shutdown source when not visible** is unchecked, this keeps it running when you switch scenes
3. join the [lanyard discord](https://discord.gg/lanyard) so the api can monitor your rpc
4. click on the browser source interact button and hover over the browser source preview in obs to open the config panel
5. enter your discord user id
6. set your **default scene**, this is where obs will switch when you're not in a game (this can be the empty scene from step 1.)
7. add your game scenes, the game name must match exactly what shows in your discord status, and the scene name must match exactly what you have in obs
