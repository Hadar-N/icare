# iCare

**iCare** is a physical platform designed for teaching English vocabulary through an interactive sandpit interface. The interface is controlled by the [iCareControl](https://github.com/Hadar-N/icarecontrol) interface, utilizing the [iCareComm](https://github.com/Hadar-N/icare-comm) private package for communication.

The project is developed under the supervision of National Tsing Hua University.

## Resources

The project incorporates the following external resources, located in the "public" folder:
- *vocab.json*- contains the relevant English vocabulary divided into levels and categories based on the 【臺北市國民小學英語聽說評量手冊】 handbook. All translations and option lists were created using ChatGPT and Claude AI tools, later verified and updated by the creator.

## Hardware

The project is designed to run on a RaspberryPi4, connected to the following components:
- Speakers for audio output
- PiCamera to track interface changes
- Projector to display the data/vocabulary

The setup includes a rack/desk with a non-clear acrylic board serving as a base layer, above which lies a sand cover. The sand acts as the interface for the user. The projector displays the information onto the acrylic board beneath the sand, so the content is revealed through sand manipulation. All listed components are installed beneath the base board.

For testing purposes, the project is also compatible with PCs using a standard webcam.

## Software Structure

```bash
├───public
│   └───vocab.json             # Vocabulary data
├───sprites
│   └───__init__.py            # Exports sprite classes
├───utils                      
│   ├───data_singleton.py      # Stores persistent game state information
│   ├───event_bus.py           # Handles message communication via MQTT
│   ├───game_engine.py         # Manages game setup and event handling
│   └───game_play.py           # Controls game flow
└───main.py                    # Entry point for the game
```

- `main.py`- The entry point for running the game
- `game_engine.py`- Defines the `GameEngine` class, which sets up the game and manages event handling
- `game_play.py`- Implements the `GamePlay` class, handling gameplay logic, manages vocabulary and controls sprite interactions

**Sprite Module**

Exports 2 main sprites:
1. `MainVocabSprite` - Represents a main vocabulary word. Linked to a GamePlay's vocabulary instance and updates it
2. `OptionVocabSprite` - represents an option for a main word. Implements an`test_match` method to check the status of English-to-Chinese vocab collision
Both sprites extend `GenVocabSprite`, which itself extends `MovingSprite`, and are linked through a `twin` property, allowing mutual communication and control

## Software Requirements

The program makes use of the following libraries:
- *python-dotenv* - loads environment variables from a .env file, which acts as the project’s configuration file
- *OpenCV* - used for the image processing, analyzing the covered areas
- *pygame* - runs the game itself
- *[iCareComm](https://github.com/Hadar-N/icare-comm)* - a private package storing required constants, structures and responsible for managing the MQTT client 

## Required Config

The programs requires a .env file to store environment-specific settings. This file serves as a configuration file, listing essential parameters for game setup.

The information expected in the file:

```bash
ENV=pi                          # ENV can be pi or pc
DISPLAY=00                      # used for running the code using SSH and choosing the relevant display.
PROJECTOR_RESOLUTION=848x480
FLIP=0

# MQTT connection information
HOST=XXX
PORT=XXX
USERNAME=XXX
PASSWORD=XXX
```

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/)