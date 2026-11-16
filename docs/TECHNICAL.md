# Implementation

The original image stays unchanged. `build.py` checks its exact SHA-256 and appends a private `.ally` section to a derived copy. Its own C/assembly hooks compile with freestanding GCC and GNU binutils; generated files remain local.

The engine keeps its original 640×480 logical layout. CreateDevice gets a 1920×1080 backbuffer. Viewports scale to that surface and the shared projection's X column receives the 4:3 to 16:9 correction. The same matrix feeds CPU culling and shader constants. Pretransformed fixed-function UI vertices scale uniformly by 2.25 with a 240-pixel horizontal inset. Programmable shader handles and world vertices are excluded.

Game-local RDTSC sites and imported QPC/GetTickCount calls subtract pause offsets. The Python controller freezes the process, shows its own SDL window, adds the suspended interval to these offsets and resumes the process. No kernel clock or system clock is changed.

The cheat affects only the current local racing player's remaining nitro charges. OFF restores the stock captured when enabled for that race. It does not change upgrades, physics multipliers or AI inventory.

The native Speed Measurements preference is set to KPH. The PIN is delivered through the game's own keypad queue and kept in a private local state file. Changed profile records request the native save routine from the rendering thread; pause requests a flush before suspension. Game-owned profile data and high-score files are backed up separately. The profile format and all addresses are revision-specific.

The public package contains neither generated machine code nor extracted instruction bytes. Displaced instructions are read from the user's validated executable when building. `docs/widescreen-build.json`, game data, credentials/PIN, screenshots and artwork remain private.

The native Game Difficulty preference at 0x4cff90 is persisted as integer 1 (easiest), at offset 1580 in both preference files.
