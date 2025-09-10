import time, os, shutil, json, argparse, logging
from pathlib import Path

# ===== PLATFORM-INDEPENDENT PATHS =====
SCRIPT_DIR = Path(__file__).parent.resolve()
if os.name == 'nt':  # Windows
    APP_DATA_DIR = Path(os.getenv('APPDATA')) / "TidyBot"
else:  # Linux, MacOS
    APP_DATA_DIR = Path.home() / ".config" / "tidybot"

CONFIG_FILE = APP_DATA_DIR / "config.json"
LOG_FILE = APP_DATA_DIR / "tidybot.log"

# ===== SET UP LOGGING FIRST =====
def setup_logging():
    """Set up logging before anything else runs."""
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Fatal error: Could not create app data directory: {e}")
        exit(1)
    
    logger = logging.getLogger("TidyBot")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create logger immediately
logger = setup_logging()
logger.info("TidyBot started.")
logger.info(f"Config directory: {APP_DATA_DIR}")
logger.info(f"Config file: {CONFIG_FILE}")

def create_default_config():
    """Creates a default configuration file."""
    default_config = {
  "initialized": True,
  "downloads_path": "~/Downloads",
  "file_categories": {
    "Archives": [
      ".zip",
      ".rar",
      ".7z",
      ".tar",
      ".gz",
      ".bz2",
      ".xz",
      ".iso",
      ".dmg",
      ".pkg"
    ],
    "Documents": [
      ".pdf",
      ".doc",
      ".docx",
      ".txt",
      ".rtf",
      ".odt",
      ".xls",
      ".xlsx",
      ".ppt",
      ".pptx",
      ".csv",
      ".md",
      ".epub",
      ".mobi"
    ],
    "Graphics": [
      ".jpg",
      ".jpeg",
      ".png",
      ".gif",
      ".bmp",
      ".svg",
      ".webp",
      ".tiff",
      ".psd",
      ".raw",
      ".ico",
      ".heic",
      ".mp4",
      ".mov",
      ".avi",
      ".mkv",
      ".wmv",
      ".flv",
      ".webm",
      ".m4v",
      ".mp3",
      ".wav",
      ".flac",
      ".aac",
      ".ogg",
      ".wma",
      ".m4a",
      ".aiff",
      ".mid",
      ".midi"
    ],
    "Others":[],
    "Programs": [
      ".exe",
      ".msi",
      ".deb",
      ".rpm",
      ".appimage",
      ".bat",
      ".sh",
      ".cmd",
      ".apk",
      ".dmg",
      ".pkg"
    ]
  }
}
    return default_config

def load_config():
    """Loads configuration, automatically fixes corrupted files."""
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        if not CONFIG_FILE.exists():
            logger.info("No config file found. Creating default configuration.")
            config = create_default_config()
            config["downloads_path"] = Path(config["downloads_path"]).expanduser()
            return config
        
        # Try to read the existing config file
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                config["downloads_path"] = Path(config["downloads_path"]).expanduser()
                return config
                
        except json.JSONDecodeError as e:
            # CONFIG FILE IS CORRUPTED!
            logger.warning(f"Config file is corrupted: {e}. Creating backup and generating new config.")
            
            # Create a backup of the corrupted file
            backup_path = CONFIG_FILE.with_suffix('.json.bak')
            try:
                shutil.copy2(CONFIG_FILE, backup_path)
                logger.info(f"Backup of corrupted config saved to: {backup_path}")
            except:
                logger.warning("Could not create backup of corrupted config.")
            
            # Create a fresh default config
            config = create_default_config()
            config["downloads_path"] = Path(config["downloads_path"]).expanduser()
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("New default config created.")
            return config
            
    except Exception as E:
        logger.error(f"Unexpected error loading config: {E}", exc_info=True)
        config = create_default_config()
        config["downloads_path"] = Path(config["downloads_path"]).expanduser()
        return config

def get_available_name(destination_path):
    """Generates a unique filename if destination already exists."""
    if not destination_path.exists():
        return destination_path

    stem = destination_path.stem
    suffix = destination_path.suffix
    parent_dir = destination_path.parent

    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        new_path = parent_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def sorter(dry_run=False):
    config = load_config()

    if config is None:
        logger.error("Exiting: Could not load config.")
        return
    
    download_path = config['downloads_path']
    categories = config['file_categories']

    if not download_path.exists():
        logger.error(f"Downloads path does not exist: {download_path}")
        return

    if not config.get("initialized", False):
        logger.info("First run detected. Creating category folders...")
        for folder_name in categories.keys():
            if dry_run:
                logger.info(f"[DRY RUN] Would create '{download_path}/{folder_name}'")
            else:
                (download_path / folder_name).mkdir(exist_ok=True)
                logger.info(f"Created folder: {folder_name}")
        
        config["initialized"] = True
        
        if not dry_run:
            try:
                config_for_save = config.copy()
                config_for_save["downloads_path"] = str(config["downloads_path"])
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config_for_save, f, indent=4)
                logger.info("Config updated: initialized = True")
            except Exception as e:
                logger.error(f"Error saving config: {e}")
        else:
            logger.info("[DRY RUN] Would set config['initialized'] to True")

    for item in download_path.iterdir():
        if item.is_file():
            file_suffix = item.suffix.lower()

            if file_suffix in categories["Archives"]:
                target_dir = download_path / "Archives"
            elif file_suffix in categories["Documents"]:
                target_dir = download_path / "Documents"
            elif file_suffix in categories["Graphics"]:
                target_dir = download_path / "Graphics"
            elif file_suffix in categories["Programs"]:
                target_dir = download_path / "Programs"
            else:
                target_dir = download_path / "Others"

            original_destination = target_dir / item.name
            final_destination = get_available_name(original_destination)

            if dry_run:
                if original_destination == final_destination:
                    logger.info(f"[DRY RUN] Would move '{item.name}' to '{target_dir.name}/'")
                else:
                    logger.info(f"[DRY RUN] Would move '{item.name}' to '{target_dir.name}/' as '{final_destination.name}'")
            else:
                try:
                    shutil.move(str(item), str(final_destination))
                    if original_destination == final_destination:
                        logger.info(f"Moved: {item.name} -> {target_dir.name}/")
                    else:
                        logger.info(f"Moved and renamed: {item.name} -> {target_dir.name}/{final_destination.name}")
                except Exception as e:
                    logger.error(f"Error moving {item.name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Organize your Downloads folder.')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Simulate organization without moving any files.')
    args = parser.parse_args()

    try:
        sorter(dry_run=args.dry_run)
        logger.info("TidyBot finished successfully.")
    except Exception as E:
        logger.error(f"TidyBot encountered an error: {E}", exc_info=True)