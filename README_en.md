# Steam Game Accelerator

A network acceleration tool designed specifically for Steam platform games (such as DOTA2, CS2), effectively reducing game latency and enhancing gaming experience through intelligent route optimization and node selection.

## Features

- **Multiple Server Region Support**: Supports multiple game server regions including China, Hong Kong, Southeast Asia, etc.
- **Intelligent Node Selection**: Automatically tests and selects the optimal acceleration node
- **Real-time Latency Monitoring**: Continuously monitors game connection quality and displays optimization effects
- **Automatic Game Detection**: Capable of automatically detecting running Steam games
- **User-friendly Interface**: Clean and intuitive operation interface

## System Requirements

- **Operating System**: Windows 10/11
- **Runtime Environment**: Python 3.8+
- **Permission Requirements**: Administrator privileges (for modifying system routes)
- **Dependencies**: See requirements.txt for details

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/your-username/steam-accelerator.git
cd steam-accelerator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Direct Execution

1. Run as administrator:
```bash
python gui.py
```

2. Select game and server region in the interface
3. Click the "Start Acceleration" button
4. View real-time acceleration status and optimization effects

### Method 2: Using Batch File

Simply double-click the `启动加速器.bat` file (requires administrator privileges)

## Technical Architecture

### Core Components

1. **Accelerator Core**
   - Responsible for route optimization and node management
   - Provides latency testing functionality
   - Manages acceleration sessions

2. **Game Detector**
   - Detects running games
   - Intelligently determines game regions
   - Retrieves game server information

3. **User Interface (UI)**
   - Provides graphical operation interface
   - Displays acceleration status and latency information
   - Supports game and server region selection

### Working Principle

1. **Node Quality Assessment**
   - Tests node-to-local latency
   - Evaluates node connectivity to game servers
   - Comprehensively calculates node scores (0-100)

2. **Route Optimization**
   - Modifies system routing tables
   - Sets optimal paths for game server IPs
   - Periodically updates routes to maintain optimal performance

## Configuration Instructions

In `config.json`, you can configure:

1. **Node Configuration**
   - Acceleration nodes categorized by region and carrier
   - Each node includes IP, location, and ISP information

2. **Game Server Configuration**
   - Server IP lists for different games
   - Server groups categorized by region

## Project Structure

```
steam_accelerator/
├── gui.py              # Main interface entry
├── src/
│   ├── core.py         # Accelerator core
│   ├── game_detector.py # Game detection
│   ├── main.py         # Main program logic
│   └── ui.py           # UI implementation
├── config.json         # Configuration file
└── requirements.txt    # Dependency list
```