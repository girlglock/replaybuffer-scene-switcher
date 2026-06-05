<div align="center">

# obs-auto-game-switcher

**simple obs browser source that automatically switches scenes based on what game you're playing (via discord rpc + lanyard)**

</div>

## how it works

it reads your discord rich presence through [lanyard](https://github.com/Phineas/lanyard) and uses the obs browser source api to switch scenes automatically. when you stop playing it falls back to your default scene.

## setup

1. add [this url](https://girlglock.github.io/replaybuffer-scene-switcher/) as a browser source inside obs in an empty dedicated scene
2. in the browser source properties, set **page permissions** to **advanced** and make sure **shutdown source when not visible** is unchecked, this keeps it running when you switch scenes
3. join the [lanyard discord](https://discord.gg/lanyard) so the api can monitor your rpc
4. click on the browser source interact button and hover over the browser source preview in obs to open the config panel
5. enter your discord user id
6. set your **default scene**, this is where obs will switch when you're not in a game (this can be the empty scene from step 1.)
7. add your game scenes, the game name must match exactly what shows in your discord status, and the scene name must match exactly what you have in obs
