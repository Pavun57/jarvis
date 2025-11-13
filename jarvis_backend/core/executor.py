"""System command and app execution."""
import subprocess
import platform
import os
from typing import Optional, Dict, Any
from pathlib import Path


class Executor:
    """Executes system commands and opens applications."""
    
    def __init__(self):
        self.system = platform.system()
        self.app_paths = self._load_app_paths()
    
    def _load_app_paths(self) -> Dict[str, str]:
        """Load common application paths based on OS."""
        paths = {}
        
        if self.system == "Windows":
            # Windows common app paths
            username = os.getenv("USERNAME", "")
            common_paths = {
                "vscode": r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(username),
                "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
                "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
            }
            # Also check alternative Brave paths
            alt_brave_paths = [
                r"C:\Users\{}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe".format(username),
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            ]
            if "brave" not in common_paths or not os.path.exists(common_paths["brave"]):
                for path in alt_brave_paths:
                    if os.path.exists(path):
                        common_paths["brave"] = path
                        break
        elif self.system == "Darwin":  # macOS
            common_paths = {
                "vscode": "/Applications/Visual Studio Code.app/Contents/MacOS/Electron",
                "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                "safari": "/Applications/Safari.app/Contents/MacOS/Safari",
            }
        else:  # Linux
            common_paths = {
                "vscode": "code",
                "chrome": "google-chrome",
                "firefox": "firefox",
                "brave": "brave-browser",
            }
        
        return common_paths
    
    def _normalize_app_name(self, app_name: str) -> str:
        """Normalize app name to standard key."""
        app_name_lower = app_name.lower().strip()
        
        # Map common variations to standard names
        name_mapping = {
            "vs": "vscode",
            "vs code": "vscode",
            "visual studio code": "vscode",
            "code": "vscode",
            "visual studio": "vscode",
        }
        
        # Check if it's a known variation
        if app_name_lower in name_mapping:
            return name_mapping[app_name_lower]
        
        # Remove spaces and special characters for matching
        normalized = app_name_lower.replace(" ", "").replace("-", "").replace("_", "")
        
        # Check if normalized version matches any key
        for key in self.app_paths.keys():
            if normalized == key.replace(" ", "").replace("-", "").replace("_", ""):
                return key
        
        return app_name_lower
    
    def open_app(self, app_name: str) -> Dict[str, Any]:
        """Open an application by name."""
        # Normalize the app name
        normalized_name = self._normalize_app_name(app_name)
        
        # Check if we have a known path
        if normalized_name in self.app_paths:
            app_path = self.app_paths[normalized_name]
            try:
                if self.system == "Windows":
                    # Check if path exists
                    import os
                    if os.path.exists(app_path):
                        subprocess.Popen([app_path], shell=False)
                    else:
                        # Try alternative: use 'code' command if VS Code is in PATH
                        if normalized_name == "vscode":
                            subprocess.Popen(["code"], shell=True)
                        else:
                            subprocess.Popen([app_path], shell=True)
                else:
                    subprocess.Popen([app_path])
                return {"success": True, "message": f"Opened {app_name}"}
            except Exception as e:
                # Fallback: try using the app name directly
                return self._try_open_directly(app_name, str(e))
        
        # Try to find and open the app
        return self._try_open_directly(app_name)
    
    def _try_open_directly(self, app_name: str, previous_error: str = None) -> Dict[str, Any]:
        """Try to open app using system commands."""
        try:
            if self.system == "Windows":
                # For VS Code, try 'code' command first
                if "code" in app_name.lower() or "vs" in app_name.lower():
                    try:
                        subprocess.Popen(["code"], shell=True)
                        return {"success": True, "message": f"Opened {app_name}"}
                    except:
                        pass
                
                # Try common Windows methods
                subprocess.Popen([app_name], shell=True)
            elif self.system == "Darwin":
                # macOS: try open command
                subprocess.Popen(["open", "-a", app_name])
            else:
                # Linux: try as command
                subprocess.Popen([app_name])
            
            return {"success": True, "message": f"Opened {app_name}"}
        except Exception as e:
            error_msg = previous_error if previous_error else str(e)
            return {"success": False, "error": f"Could not open {app_name}: {error_msg}"}
    
    def run_command(self, command: str) -> Dict[str, Any]:
        """Execute a system command."""
        try:
            # Check if command is trying to create a file with echo (common pattern)
            # This is unreliable on Windows, so we'll suggest using write_file skill instead
            if "echo" in command.lower() and (">" in command or ">>" in command):
                # Try to extract file path and content
                if ">" in command:
                    parts = command.split(">", 1)
                    if len(parts) == 2:
                        content_part = parts[0].replace("echo", "").strip().strip('"').strip("'")
                        file_part = parts[1].strip()
                        # If this looks like file creation, suggest using write_file
                        if file_part.endswith((".py", ".java", ".js", ".ts", ".txt", ".md", ".json", ".html", ".css", ".xml", ".yaml", ".yml")):
                            return {
                                "success": False,
                                "error": f"File creation via echo is unreliable. Please use write_file skill with file_path='{file_part}' and content parameters.",
                                "suggestion": "use_write_file_skill"
                            }
            
            if self.system == "Windows":
                # Use PowerShell for better command handling on Windows
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_url(self, url: str) -> Dict[str, Any]:
        """Open a URL in the default browser."""
        try:
            if self.system == "Windows":
                os.startfile(url)
            elif self.system == "Darwin":  # macOS
                subprocess.Popen(["open", url])
            else:  # Linux
                subprocess.Popen(["xdg-open", url])
            
            return {"success": True, "message": f"Opened {url} in browser"}
        except Exception as e:
            return {"success": False, "error": f"Could not open URL: {str(e)}"}
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read contents of a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

