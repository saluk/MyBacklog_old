import sys,os

EXTRACT_ICONS = sys.platform.startswith("win")


win_steam_paths = ["c://steam","d://steam","e://steam","f://steam","g://steam"]
mac_steam_paths = ["~/Library/Application Support/Steam"]

steam_paths = [os.path.abspath(p) for p in {"mac":mac_steam_paths,"darwin":mac_steam_paths,"win32":win_steam_paths}.get(sys.platform,[])]