import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConfigManager:
    """
    Manages configuration settings for the LoadFile Creator.
    Loads settings from JSON file and provides easy access to configuration options.
    """
    
    def __init__(self, config_file: str = "bates_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self._detect_platform()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Configuration file {self.config_file} not found. Using defaults.")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}. Using defaults.")
            return self._get_default_config()
    
    def _detect_platform(self):
        """Detect the current platform and set appropriate font paths."""
        self.platform = platform.system().lower()
        if self.platform == "windows":
            self.font_paths = self.config.get("font_paths", {}).get("windows", [])
        elif self.platform == "linux":
            self.font_paths = self.config.get("font_paths", {}).get("linux", [])
        elif self.platform == "darwin":  # macOS
            self.font_paths = self.config.get("font_paths", {}).get("macos", [])
        else:
            self.font_paths = []
        
        # Add custom fonts
        custom_fonts = self.config.get("font_paths", {}).get("custom", [])
        self.font_paths.extend(custom_fonts)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file is not found."""
        return {
            "bates_stamping": {
                "font_size": 30,
                "margin": 20,
                "text_color_light": [255, 255, 255],
                "text_color_dark": [0, 0, 0],
                "contrast_threshold": 128,
                "add_border": False,
                "border_color": [255, 255, 255],
                "border_width": 2,
                "shadow": False,
                "shadow_offset": [2, 2],
                "shadow_color": [0, 0, 0],
                "supported_formats": ["jpg", "jpeg", "tiff", "tif", "png", "bmp"],
                "quality": 95,
                "dpi": 200
            },
            "font_paths": {
                "windows": ["C:\\Windows\\Fonts\\arial.ttf"],
                "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
                "macos": ["/System/Library/Fonts/Arial.ttf"],
                "custom": []
            },
            "loadfile_settings": {
                "delimiter": "0x14",
                "wrapper": "0xFE",
                "encoding": "utf-8",
                "required_fields": [
                    "BegBates", "EndBates", "NativeLocation", "TextLocation", 
                    "Filename", "FileExtension", "HashValue"
                ]
            },
                    "processing_settings": {
            "timeout": 500,
            "max_file_timeout": 300,
            "max_total_timeout": 3600,
            "max_workers": 4,
            "pdf_dpi": 150,
            "pdf_chunk_size": 5,
            "image_compression": 6,
            "memory_cleanup": True,
            "memory_check_interval": 10,
            "email_family_grouping": True,
            "sequential_bates": True,
            "alphabetical_sort": True
        }
        }
    
    def get_bates_config(self) -> Dict[str, Any]:
        """Get Bates stamping configuration."""
        return self.config.get("bates_stamping", {})
    
    def get_loadfile_config(self) -> Dict[str, Any]:
        """Get loadfile configuration."""
        return self.config.get("loadfile_settings", {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.config.get("processing_settings", {})
    
    def get_font_paths(self) -> List[str]:
        """Get font paths for current platform."""
        return self.font_paths
    
    def find_available_font(self) -> Optional[str]:
        """Find the first available font from configured paths."""
        for font_path in self.font_paths:
            # Handle relative paths
            if not os.path.isabs(font_path):
                # Try relative to current directory
                current_dir = Path.cwd()
                test_path = current_dir / font_path
                if test_path.exists():
                    return str(test_path)
            else:
                # Absolute path
                if os.path.exists(font_path):
                    return font_path
        
        print(f"Warning: No fonts found from configured paths for {self.platform}.")
        return None
    
    def update_config(self, section: str, key: str, value: Any):
        """Update a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_delimiter_chars(self) -> tuple:
        """Get delimiter and wrapper characters for loadfile."""
        loadfile_config = self.get_loadfile_config()
        delim = chr(int(loadfile_config.get("delimiter", "0x14"), 16))
        wrap = chr(int(loadfile_config.get("wrapper", "0xFE"), 16))
        return delim, wrap
    
    def get_required_fields(self) -> List[str]:
        """Get list of required fields for loadfile."""
        loadfile_config = self.get_loadfile_config()
        return loadfile_config.get("required_fields", [])

# Example usage and utility functions
def create_config_template():
    """Create a template configuration file."""
    template = {
        "bates_stamping": {
            "font_size": 30,
            "margin": 20,
            "text_color_light": [255, 255, 255],
            "text_color_dark": [0, 0, 0],
            "contrast_threshold": 128,
            "add_border": False,
            "border_color": [255, 255, 255],
            "border_width": 2,
            "shadow": False,
            "shadow_offset": [2, 2],
            "shadow_color": [0, 0, 0],
            "supported_formats": ["jpg", "jpeg", "tiff", "tif", "png", "bmp"],
            "quality": 95,
            "dpi": 200
        },
        "font_paths": {
            "windows": [
                "C:\\Windows\\Fonts\\arial.ttf",
                "C:\\Windows\\Fonts\\calibri.ttf",
                "C:\\Windows\\Fonts\\verdana.ttf"
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ],
            "macos": [
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ],
            "custom": [
                "fonts/arial.ttf",
                "Supporting_Files/FONTS/08634_ClarendonBT.ttf"
            ]
        },
        "loadfile_settings": {
            "delimiter": "0x14",
            "wrapper": "0xFE",
            "encoding": "utf-8",
            "required_fields": [
                "BegBates", "EndBates", "NativeLocation", "TextLocation", 
                "Filename", "FileExtension", "HashValue"
            ]
        },
        "processing_settings": {
            "timeout": 500,
            "max_file_timeout": 300,
            "max_total_timeout": 3600,
            "max_workers": 4,
            "pdf_dpi": 150,
            "pdf_chunk_size": 5,
            "image_compression": 6,
            "memory_cleanup": True,
            "memory_check_interval": 10,
            "email_family_grouping": True,
            "sequential_bates": True,
            "alphabetical_sort": True
        }
    }
    
    with open("bates_config_template.json", 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=4, ensure_ascii=False)
    print("Configuration template created: bates_config_template.json")

if __name__ == "__main__":
    # Create template if run directly
    create_config_template() 