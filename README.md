# Oasis

**Oasis** is a physical platform designed for teaching English vocabulary through an interactive sandpit interface.
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

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/)