import bz2
import xml.etree.ElementTree as ET
from rich import print_json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from config import config

class WikiExplorer:
    def __init__(self, config: 'config'):
        self.config = config
        self.file_absolute = self.config.file_absolute

    def peek(self, limit=1, only_articles=True, exclude_redirects=True, trunc_size=300):
        """
        Explores the Wikipedia dump with toggleable filters.
        
        Args:
            limit (int): How many matches to find before stopping.
            only_articles (bool): If True, only shows Namespace 0.
            exclude_redirects (bool): If True, hides pages that redirect to others.
        """
        count = 0
        # Step 1: Open the compressed stream
        with bz2.BZ2File(self.file_absolute, "rb") as f:
            # We use 'end' events to ensure the element is fully populated
            context = ET.iterparse(f, events=("end",))
            
            for event, elem in context:
                tag = elem.tag.split('}')[-1] # Strip the XML namespace URL
                
                if tag == "page":
                    # --- PARAMETER EXTRACTION ---
                    # Find the Namespace (ns)
                    ns_elem = elem.find(".//{*}ns")
                    ns = ns_elem.text if ns_elem is not None else "Unknown"
                    
                    # Check for the existence of a <redirect> tag
                    # .find() returns the Element if it exists, or None if it doesn't
                    is_redirect = elem.find(".//{*}redirect") is not None
                    
                    # --- TUPLE MATCH CASE ---
                    # We create a tuple (Namespace, IsRedirect) to match against
                    match (ns, is_redirect):
                        # Case: It is an article (0) and NOT a redirect (False)
                        case ("0", False):
                            self._process_and_print(elem, trunc_size)
                            count += 1
                        
                        # Case: It is an article (0) but IS a redirect (True)
                        case ("0", True):
                            if not exclude_redirects:
                                self._process_and_print(elem, trunc_size)
                                count += 1
                                
                        # Case: Any other Namespace (1, 14, etc.)
                        case _:
                            if not only_articles:
                                self._process_and_print(elem, trunc_size)
                                count += 1

                    # Step 2: Memory Management
                    elem.clear()
                    
                    # Stop if we hit the user's requested limit
                    if count >= limit:
                        break

    def _process_and_print(self, elem, trunc_size):
        """Helper to convert the XML element to a dict and print it."""
        data = self._xml_to_dict(elem, trunc_size)
        print_json(data=data)

    def _xml_to_dict(self, element, trunc_size):
        """Recursively converts XML to a nested dictionary for exploration."""
        tag_name = element.tag.split('}')[-1]
        data = {tag_name: {}}
        
        for child in element:
            child_tag = child.tag.split('}')[-1]
            if len(child) > 0:
                child_data = self._xml_to_dict(child, trunc_size)
                data[tag_name][child_tag] = child_data[child_tag]
            else:
                # Capture text but keep it readable in the terminal
                text = child.text if child.text else ""
                data[tag_name][child_tag] = text[:trunc_size] + "..." if len(text) > trunc_size else text
        return data