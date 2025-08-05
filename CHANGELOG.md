# Changelog

All notable changes to MythicMate will be documented in this file.

## [1.1.2] - 2025-08-04

### Updated
- Added Season 3 dungeons and removed previous seasons dungeons (change made by Rixanne, not the author Beel)

## [1.1.1] - 2025-01-23

### Fixed
- Resolved webhook expiration issues causing reaction failures
  - Changed message creation method to use channel.send instead of interaction responses
  - Improved message update mechanism with proper error handling

### Added
- Improved logging system
  - Added structured logging with timestamps and log levels
  - Better error handling and reconnection logic for Discord gateway issues

### Technical
- Implemented robust reconnection handling for Discord gateway disconnects
- Improved error handling for guild-only commands
- Added checks to prevent DM usage of server-specific commands

## [1.1.0] - 2025-01-22

### Added
- **Run Scheduling System**
  - New schedule parameter in `/lfm` command
  - Support for immediate ("now") or future-scheduled runs
  - Format: "YYYY-MM-DD HH:MM" or "now"

- **DM Reminder System**
  - Automatic DM reminders 15 minutes before scheduled runs
  - Fallback channel notifications if DMs are blocked
  - Reminders only sent to active group members

- **WIP - Statistics System**
  - New `/mystats` command to view personal statistics
  - Track roles played, completed runs, and average key levels
  - Server-specific statistics tracking

- **WIP - Leaderboard System**
  - New `/leaderboard` command with multiple categories
  - Categories: Most Runs, Highest Keys, Role Distribution
  - Timeframe filters: All Time, Monthly, Weekly
  - Server-specific leaderboards

- **Backup System**
  - Automatic backup list for full roles
  - Display backups in group embed
  - Automatic promotion when main role becomes available
  - Notification system for backup promotions

### Changed
- Database structure to support server-specific data
- Docker configuration to properly persist statistics data
- Improved embed formatting to show backup information

### Technical
- Added SQLite database for statistics tracking
- Implemented server-specific data isolation
- Added data persistence through Docker volumes
- Optimized database queries for performance

## [1.0.0] - 2024-08-09

### Initial Release
- Basic group formation functionality
- Role management through reactions
- Dungeon name translation
- Interactive embeds
- Group completion tracking

[1.1.1]: https://github.com/YourUsername/MythicMate/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/YourUsername/MythicMate/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/YourUsername/MythicMate/releases/tag/v1.0.0 
