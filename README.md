
<p align="center">
  <strong>English</strong> |
  <a href="README.uk.md">Українська</a>
</p>
<p align="center">
  <a href="https://www.linkedin.com/in/remaniuk-mykyta"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="https://github.com/Drendika"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
  <a href="https://www.artstation.com/drendika"><img src="https://img.shields.io/badge/ArtStation-131013?style=for-the-badge&logo=artstation&logoColor=white" alt="ArtStation"></a>
</p>

# Table of Contents

- [About](#about)
- [Tools](#tools)
	- [rmGimbalMonitor](#rmgimbalmonitor)
		  - [Features](#features)
		  - [Compatibility](#compatibility)
		  - [Installation](#installation)
		  - [Known issues](#known-issues)
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

**rmGimbalMonitor** is a real-time gimbal-lock monitoring and analysis tool for Autodesk Maya.

It analyses character controls using their actual rotation orders and shows how close each control is to gimbal lock. Controls are organised into configurable categories and displayed in an interactive table, allowing animators to identify potentially problematic rotations before they become difficult to fix.
### Features
#### Real-time monitoring
- Monitor gimbal-lock values of character controls in real time.
- Display the current rotation order of each control.
- Visualise gimbal-lock percentage with a colour-coded progress bar.
- Highlight high-risk controls with an additional warning indicator.
<img width="800" height="450" alt="1" src="https://github.com/user-attachments/assets/81998ebb-482e-4de7-ba6c-2a088efa7ceb" /><img width="800" height="390" alt="11" src="https://github.com/user-attachments/assets/424a5d8e-7456-4cfe-ab94-ffa384744ed9" />

#### Character and control organisation
- Automatically groups controls into categories such as Head, Torso, Arms, Legs and others.
- Supports multiple characters through separate tabs.
- Automatically skips controls based on configurable keywords.
- Controls with all rotation channels locked are ignored automatically.

#### Customisation
- Edit control categories and skip rules directly from the **Edit Controls** window.
- Create custom categories and assign keywords to them.
- Move keywords between categories using drag and drop.
- Assign custom icons to control categories.
- Configuration is stored between Maya sessions.
<img width="800" height="390" alt="22" src="https://github.com/user-attachments/assets/af294b24-280f-4c3a-a9e5-17dbe3b64fdf" />

#### Updates
- Automatically checks GitHub for new rmGimbalMonitor releases on startup.
- Updates can also be checked manually from **Help → Check for Updates**.
- Individual versions can be skipped if the user does not want to be reminded again.
<img width="800" height="390" alt="33" src="https://github.com/user-attachments/assets/929d49c6-c057-4a45-b150-005640e7ff4c" />

### Compatibility

Tested and confirmed working on:
- Maya 2022
- Maya 2023
- Maya 2024 / 2024.2

**Not currently supported: Maya 2016-2020/2025 and newer.**

### Installation
1) Go to [Releases](https://github.com/Drendika/MayaCustomTools/releases).
2) Download the latest release archive (`rmGimbalMonitor_V2.zip`).
3) Extract the files to the desktop.
4) Drag and drop the file `Drug&Drop Install.py` into Maya.
5) A new rmGimbalMonitor icon should appear on the active Maya shelf.
The exact step-by-step process is shown in this video (Link goes here). 

### Known Issues
- Incorrect display of custom icons that are less than 32x32
- An overly long category name does not fit in the column of the tables and Edit Controls.
- After adding a custom icon, it is copied to the `icons` folder, yet the system still uses the icon originally selected by the user from its original location rather than the one in the `icons` folder.

### Roadmap
Development plans are tracked in the [Roadmap](ROADMAP.md).


## Snippets
### Hot reload
#### Features
Code snippet for rapid UI development using PySide. Hot reload deletes all modules from `sys.modules` and closes+deletes Qt window.

#### Compatibility
Hot reload should work on Maya 2016 - 2027
Tested and confirmed working on:
- Maya 2022
- Maya 2023
- Maya 2024
