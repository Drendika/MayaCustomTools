# rmGimbalMonitor Roadmap

This roadmap outlines the planned development of rmGimbalMonitor.
Features and release targets may change during development.

## Status
- Planned
- In Progress
- Completed
- Experimental

## v2.0.0 [In Progress]
Taget date: 13 - 14 October 2026
- [x] Review and refactor the existing codebase
- [ ] Create a tool showcase video
- [ ] Release

## v2.1.0 [Planned]
- [ ] Migrate to PySide6
- [ ] Add validation for duplicate character selection
- [ ] Rework `closeEvent` so the monitor hides instead of being destroyed
- [ ] Detect whether the user selected the main control or the rig root group
- [ ] Add optional detection of controls driven through Parent Constraints
- [ ] Add automatic character type detection
- [ ] Add automatic update download and installation
- [ ] Add changelogs

## v2.2.0 [Planned]
- [ ] Allow removing entries from the initialization stage
- [ ] Add model/table refresh without restarting the monitor
- [ ] Add sorting by control type
  - [ ] Show/hide invisible controls
  - [ ] IK/FK filtering based on the currently active system
- [ ] Add a preset for robots/mechanical characters

## v2.3.0 [Planned]
- [ ] Add Maya docking support
- [ ] Allow character tabs to be detached
- [ ] Restore the tool automatically between Maya sessions
- [ ] Remember window position
- [ ] Create documentation

## v2.4.0  [Planned]
- [ ] First major UI redesign
- [ ] Add separators between table categories
- [ ] Improve table interactivity
- [ ] Add Ukrainian localization

## v2.5.0 [Planned]
- [ ] Add rotation order changing and baking to a new rotation order
- [ ] Add rotation order recommendations for controls
- [ ] Add circular gimbal-lock progress indicator option
- [ ] Optimize `updateGimbalData()` to calculate only actively rotating controls

## v2.6.0 [Planned]
- [ ] Add characters through a dedicated setup window
- [ ] [Experimental] Explore displaying gimbal-lock information directly on Maya controls