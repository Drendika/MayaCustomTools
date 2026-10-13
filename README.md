
<p align="center">
  <strong>English</strong> |
  <a href="README.uk.md">Українська</a>
</p>
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/remaniuk-mykyta)[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Drendika)[![ArtStation](https://img.shields.io/badge/ArtStation-13 narrow-131013?style=for-the-badge&logo=artstation&logoColor=white)](https://www.artstation.com/drendika)


# Table of Contents

- [About](#about)
- [Tools](#tools)
	- [rmGimbalMonitor](#rmgimbalmonitor)
		  - [Features](#features)
		  - [Compatibility](#compatibility)
		  - [Known bugs](#known-bugs)
		  - [Roadmap](#roadmap)
	- [Snippets](#snippets)
		- [Hot reload](#hot-reload)

# About

Hi! My name is Mykyta aka Drendika. Here, I'm sharing all of my tools for Autodesk Maya.
I'm mainly focusing on tools for animators and technical animators/riggers.
As of today, you can find here:
- [rmGimbalMonitor](#rmgimbalmonitor)
- [Hot reload](#hot-reload)



# Tools
## rmGimbalMonitor
### Installation
1) Go to [Releases](https://github.com/Drendika/MayaCustomTools/releases).
2) Download the latest version of the tool(rmGimbalMonitor_V2.zip).
3) Extract the files to the desktop.
4) Drag and drop the file `Drug&Drop Install.py` into Maya.
5) A new icon should appear on your shelf.
The exact step-by-step process is shown in this video (Як запишу відео то вставлю сюди посилання). 

### Features
You can monitor the gimbal lock of any control of any character in real time. Create custom setups to sort and skip controls if you want.

### Compatibility

Tested and confirmed working on:
- Maya 2022
- Maya 2023
- Maya 2024 / 2024.2

**Not currently supported: Maya 2016-2020/2025 and newer.**

### Known bugs
- Incorrect display of custom icons that are less than 32x32
- An overly long category name does not fit in the column of the tables and Edit Controls.
- After adding a custom icon, it is copied to the `icons` folder, yet the system still uses the icon originally selected by the user from its original location rather than the one in the `icons` folder.

## Roadmap

Development plans are tracked in the [Roadmap](ROADMAP.md).


## Snippets
### Hot reload
#### Features
Code snippet for rapid UI development using PySide. Hot reload deletes all modules from `sys.modules` and closes+deletes Qt window.

#### Compatibility
Hot reaload should work on Maya 2016 - 2027
Tested and confirmed working on:
- Maya 2022
- Maya 2023
- Maya 2024