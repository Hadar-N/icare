# iCare

**iCare** is a physical platform designed for teaching English vocabulary through an interactive sandpit interface. The interface is controlled by the [iCareControl](https://github.com/Hadar-N/icarecontrol) project, using MQTT protocol.

The project is developed under the supervision of National Tsing Hua University.

## Resources

The project incorporates the following external resources, located in the "public" folder:
- *vocab.json*- contains the relevant English vocabulary and their Chinese translations, extracted from the article [兒童英文單字學習方法推薦：讓孩子輕鬆記 100 個基礎英文單字
](https://tw.amazingtalker.com/blog/zh-tw/zh-eng/69460/) on the AmazingTalker teaching platform.
- *Taipei Sans TC (台北黑體)*- A Chinese font downloaded from [翰字鑄造 JT Foundry's website](https://sites.google.com/view/jtfoundry/zh-tw), licensed under the [SIL Open Font License, Version 1.1](https://openfontlicense.org/)

## Hardware

The project is designed to run on a RaspberryPi4, connected to the following components:
- Speakers for audio output
- Pi NoIR Camera V2 to detect the changes in the interface
- Projector to display the data/vocabulary

The setup includes a rack with a non-clear acrylic board serving as a base layer, above which lies a sand cover. The sand acts as the interface for the user. The projector displays the information onto the acrylic board beneath the sand, so the content is revealed through sand manipulation. All listed components are housed below the rack.

For testing purposes, the project is also compatible with PCs using a standard webcam.

## Software

The program makes use of 2 main libraries:
- *OpenCV* - used for the image processing, analyzing the covered areas.
- *pygame* - runs the game itself.
- *paho-mqtt* - responsible for managing the connection with the iCareControl remote. 

The game is first run in the *main.py* file, which includes the game's setup and gameloop.

## Required Config

The programs uses a .env file specific to the environment and acts as a config file, required for a smooth run of the program.

The relevant information expected in the file:

```bash
# used for running the code using SSH for choosing the relevant display.
# ENV can be pi or pc
ENV=pi
DISPLAY=00
PROJECTOR_RESOLUTION=848x480

# MQTT connection information
HOST=XXX
PORT=XXX
USERNAME=XXX
PASSWORD=XXX
``` 

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/)