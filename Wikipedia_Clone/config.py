from urllib.parse import urljoin
import rich
import requests
from rich.progress import track
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from rich.prompt import Confirm
import posixpath
from urllib.parse import urlparse
import inspect
import os

class config:

    def __init__(self, url, file_absolute=None  ):
        # Keep the FULL url for requests, but extract the path for the filename
        self.url = url 
        parsed_path = urlparse(url).path
        
        self.url_filename = posixpath.basename(parsed_path)
        
        # If the filename is 'data.xml.bz2', this captures '.xml.bz2'
        if self.url_filename.count('.') > 1:
            self.url_extensions = "." + ".".join(self.url_filename.split('.')[1:])
        else:
            self.url_extensions = Path(self.url_filename).suffix

        # Setup paths
        self.path_default = Path(self.caller_script_dir()) / 'data'
        self.make_dir(self.path_default)
        self.file_absolute = None
        

    def procedure(self, file_absolute=None):
        rich.print("[bold magenta]Welcome to the wikipedia cloning and data science tool.[/bold magenta]")
        is_local = Confirm.ask("Do you already have the data downloaded?")
        if is_local:
            rich.print(f'Check the opened window to select the data file ending in "{self.url_extensions}"')
            self.get_file_path()
        else:
            is_download = Confirm.ask("Would you like to download the data now?")
            if is_download:
                msg = '[yellow]The data is about 25GB and could take a long time to download.[/yellow]\n'
                # msg += 'Run this program again after finishing the download from...\n'
                msg += 'Downloading data from...\n'
                msg += f'{self.url}\n'
                rich.print(msg)
                self.download_file()
            else:
                rich.print('[green]Exiting app.[/green]')

    def get_file_path(self):
        # 1. Create a hidden root window (prevents a blank box from staying open)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # 2. Open the 'Open File' dialog
        file_path = filedialog.askopenfilename(
            title="Select your Data File",
            filetypes=[('Compressed XML', '*.xml.bz2'),
                       ("All files", "*.*")]
        )
        if not file_path:
            rich.print("[red]File selection cancelled.[/red]")
            return 
        # 3. Destroy the root window after selection
        root.destroy()
        self.file_absolute = file_path
        rich.print(f'You selected...\n{self.file_absolute}')

    def download_file(self, file_absolute=None):
        # Determine where to save
        if file_absolute is None:
            self.file_absolute = self.get_save_location()
        else:
            self.file_absolute = file_absolute
        
        # If user cancelled the file dialog
        if not self.file_absolute:
            rich.print("[red]Download cancelled: No save location selected.[/red]")
            return
        
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            # FIX 3: Use the FULL URL here
            response = requests.get(self.url, stream=True, headers=headers, allow_redirects=True)
            response.raise_for_status() 

            total_size = int(response.headers.get('content-length', 0))
            
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task_id = progress.add_task("Downloading...", total=total_size)
                
                with open(self.file_absolute, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task_id, advance=len(chunk))
            
            rich.print(f"[bold green]Success![/bold green] File saved to...\n{self.file_absolute}\n")

        except Exception as e:
            rich.print(f"[bold red]Error:[/bold red] {e}")
    
    def get_save_location(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # Keep it on top
        
        # We put the double extension first so it's the default filter
        ftypes = [
            ('Compressed Wikipedia Archive', '*.xml.bz2'),
            ('Bzip2 Compressed', '*.bz2'),
            ('All files', '*.*')
        ]
        
        save_path = filedialog.asksaveasfilename( 
            initialdir=self.path_default,
            initialfile=self.url_filename, # e.g., 'enwiki-latest.xml.bz2'
            title="Save Data As",
            filetypes=ftypes,
            # We set this to the LAST part of the extension to help the OS
            defaultextension=".bz2" 
        )
        
        root.destroy()

        if save_path:
            # If the OS stripped '.bz2' or '.xml.bz2', add it back.
            # We check for the specific double extension you need.
            if not save_path.lower().endswith('.xml.bz2'):
                
                # If it ends in .xml, just add .bz2
                if save_path.lower().endswith('.xml'):
                    save_path += '.bz2'
                # If it has no extension at all, add the whole thing
                elif '.' not in os.path.basename(save_path):
                    save_path += '.xml.bz2'
                # Otherwise, the user likely typed their own extension (like .csv), 
                # so we leave it alone.
                
        rich.print(f'Your file is being saved at...\n{save_path}')
        return save_path
    
    def caller_script_dir(self):
        # walk the stack and find the first frame whose filename is not this file
        this_file = Path(__file__).resolve()
        for frame_info in inspect.stack()[1:]:
            caller_path = Path(frame_info.filename).resolve()
            if caller_path != this_file:
                return caller_path.parent
        return None
    
    def make_dir(self, path):
        path.mkdir(parents=True, exist_ok=True)
        return None