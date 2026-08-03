# <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/award.svg" width="32" height="32" align="top"> Non-Ancient Chess of Rome

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Panda3D](https://img.shields.io/badge/Panda3D-1.10-orange)
![LLMs](https://img.shields.io/badge/LLMs-10%20Providers-green)
![Chess Engine](https://img.shields.io/badge/Engine-Negamax%2FAlpha--Beta-red)

A full-stack 3D chess arena where 10 different LLM providers can be matched against each other or a custom negamax engine. The environment is built on Panda3D, featuring real-time animations, hardware-accelerated shadows, match analytics, and a custom DirectGUI interface.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/monitor.svg" width="24" height="24" align="top"> Engine Rendering and Interface

The interface is built completely using Panda3D DirectGUI, bypassing standard HTML/CSS wrappers for a native 3D experience.

### <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/layout.svg" width="20" height="20" align="top"> Main Menu
![Main Menu](screen_shots/Main_Menu.png)

### <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/server.svg" width="20" height="20" align="top"> Provider Selection
The system automatically detects the provider based on the API key prefix.
<p align="center">
  <img src="screen_shots/LLM_Select_Screen.png" width="32%">
  <img src="screen_shots/LLM_Select_Screen1.png" width="32%">
  <img src="screen_shots/LLM_Select_Screen3.png" width="32%">
</p>

### <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/settings.svg" width="20" height="20" align="top"> Settings Configuration
![Settings Screen](screen_shots/Settings_Screen.gif)

### <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/clock.svg" width="20" height="20" align="top"> Match History
Games are serialized and can be analyzed move-by-move.
<p align="center">
  <img src="screen_shots/Match_History_Screen.png" width="100%">
</p>
<p align="center">
  <img src="screen_shots/Match_History_Screen.gif" width="100%">
</p>

### <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/bar-chart-2.svg" width="20" height="20" align="top"> Match Analytics
![Game Over](screen_shots/Game_Over_Screen.png)

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/git-merge.svg" width="24" height="24" align="top"> Architecture

```text
main.py                → game_3d.py (Panda3D ShowBase)
├── src/
│   ├── chess_renderer.py    → 3D board, GLB models, lighting pipeline
│   ├── background_show.py   → Orbital camera logic
│   ├── api_manager.py       → LLM provider integrations
│   ├── config_manager.py    → Persistent configuration state
│   ├── stats_tracker.py     → Move analytics and history serialization
│   └── screens/
│       ├── base_screen.py        → Custom UI toolkit
│       ├── main_menu.py         
│       ├── mode_select_screen.py 
│       ├── settings_screen.py  
│       ├── game_screen.py      
│       ├── history_screen.py   
│       └── replay_screen.py    
├── bot_llm.py              → Network retry logic and validation
├── bot_local.py            → Negamax engine and board evaluation
└── match_history.json      → Serialized match records
```

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/share-2.svg" width="24" height="24" align="top"> Multi-LLM Orchestration

The `api_manager.py` handles communication across 10 different providers through a unified completion interface. API keys are parsed by their prefix to route requests to the correct endpoint.

| Provider | Endpoint | Token Prefix |
|---|---|---|
| OpenAI | `/v1/chat/completions` | `sk-` |
| Anthropic | `/v1/messages` | `sk-ant-` |
| Google Gemini | `/v1beta/openai/chat/completions` | `AIza` |
| DeepSeek | `/chat/completions` | `sk-d-` |
| Groq | `/openai/v1/chat/completions` | `gsk_` |
| Nvidia NIM | `/v1/chat/completions` | `nvapi-` |
| Together | `/v1/chat/completions` | bare token |
| Mistral | `/v1/chat/completions` | bare token |
| OpenRouter | `/api/v1/chat/completions` | `sk-or-` |
| Ollama | `localhost:11434/v1/chat/completions` | — |

Model lists are fetched dynamically and cached. The cache is invalidated if the API signature changes.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/shield.svg" width="24" height="24" align="top"> API Error Handling and Fallbacks

Language models frequently output invalid UCI strings or hallucinate illegal moves. `bot_llm.py` implements a robust retry mechanism.

1. System prompt is constructed with FEN and a list of legal moves.
2. The completion is requested with `temperature=0.1`.
3. The returned string is parsed and validated against `python-chess`.
4. If illegal, the error is appended to the context and the request is retried (up to 3 times).
5. If all retries fail, the system falls back to a random legal move and flags the player for disqualification.

Metrics such as `tokens_in`, `tokens_out`, `delay_ms`, and `illegal_attempts` are logged per move.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/cpu.svg" width="24" height="24" align="top"> Local Negamax Engine

`bot_local.py` contains a custom engine implementing Negamax with Alpha-Beta pruning, running at depth 3.

- **Quiescence Search**: Extends the search horizon for capture sequences to prevent horizon effect blunders.
- **Move Ordering**: Utilizes MVV-LVA (Most Valuable Victim - Least Valuable Attacker) and killer heuristics.
- **Evaluation**: Employs piece-square tables that dynamically switch between middle-game and endgame states.
- **Safety Metrics**: Awards positive evaluation scores for castled positions.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/pen-tool.svg" width="24" height="24" align="top"> Custom DirectGUI Framework

Standard UI libraries are often disjointed from the 3D scene. `base_screen.py` implements a native UI toolkit over DirectGUI.

- **Typography**: Uses `OldeEnglish.ttf` for primary headings and `SegoeUI.ttf` for readability in labels.
- **Components**: Custom button classes with 4-state color transitions (normal, hover, clicked, disabled).
- **Theme**: Adheres to a strict palette of white, gold, dim gray, and panel black.

All interface screens inherit from `BaseScreen` for consistency.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/box.svg" width="24" height="24" align="top"> 3D Scene Pipeline

The renderer (`chess_renderer.py`) manages the visual state of the board independently from the logical state.

- **Materials**: Applies Physical Based Rendering (PBR) approximations. White pieces use silver specular maps, while black pieces use gold.
- **Lighting**: A single directional light casts shadows via a 2048x2048 depth map.
- **Atmosphere**: Exponential fog (density 0.02) is used to obscure the table edges.
- **Geometry**: Custom GLB models are scaled dynamically based on piece type.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/refresh-cw.svg" width="24" height="24" align="top"> Threaded Game Loop

The core match execution (`game_screen.py`) is decoupled from the rendering thread to prevent blocking the UI during network requests or deep engine searches.

- **Concurrency**: The game logic runs in a background thread, dispatching state updates to the main Panda3D thread.
- **Camera Rig**: A smooth ease-in-out rotation transition is applied when perspectives change.
- **HUD Synchronization**: The top bar updates continuously with latency metrics and SAN notations.

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/terminal.svg" width="24" height="24" align="top"> Installation and Execution

### Windows Launcher
Double-click `PLAY.bat`. The script detects the Python environment, resolves missing dependencies via pip, and starts the 3D application.

### Manual Execution
```bash
pip install panda3d chess requests

# Launch 3D application
python main.py

# Launch text-based console mode
python game_manager.py
```

Provide your API keys through the in-game Settings menu, or prefix them directly (e.g., `provider:sk-xx` for providers without standardized prefixes).

---

## <img src="https://cdn.jsdelivr.net/npm/feather-icons/dist/icons/file-text.svg" width="24" height="24" align="top"> License

MIT License.
