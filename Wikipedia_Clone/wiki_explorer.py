from rich import print_json
import bz2
import xml.etree.ElementTree as ET
import re
import csv
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from config import config

class WikiExplorer:
    def __init__(self, config: 'config'):
        self.config = config
        self.file_absolute = self.config.file_absolute
        self.link_pattern = re.compile(r"\[\[([^|:\]]+)(?:\|[^\]]+)?\]\]")
        # Add a blacklist for common non-topical links
        self.blacklist = {"Main Page", "Portal:Contents", "Portal:Featured content"}
        
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
    
    def _clean_links(self, links, current_title):
        """Filters out administrative links and self-references."""
        clean = []
        for link in links:
            # 1. Remove links with colons (Namespaces like Category:, Template:, etc.)
            if ":" in link:
                continue
            # 2. Remove self-references
            if link == current_title:
                continue
            # 3. Remove blacklisted items
            if link in self.blacklist:
                continue
            
            clean.append(link)
        return clean
    
    def get_page_links(self, limit=100):
        count = 0
        with bz2.BZ2File(self.file_absolute, "rb") as f:
            context = ET.iterparse(f, events=("end",))
            
            for event, elem in context:
                tag = elem.tag.split('}')[-1]
                
                if tag == "page":
                    ns_elem = elem.find(".//{*}ns")
                    ns = ns_elem.text if ns_elem is not None else "Unknown"
                    is_redirect = elem.find(".//{*}redirect") is not None
                    
                    if ns == "0" and not is_redirect:
                        title = elem.find(".//{*}title").text
                        text_elem = elem.find(".//{*}text")
                        
                        if text_elem is not None and text_elem.text:
                            raw_links = self.link_pattern.findall(text_elem.text)
                            # Apply the cleaning method
                            clean_links = self._clean_links(list(set(raw_links)), title)
                            
                            yield {
                                "source": title,
                                "targets": clean_links,
                                "out_count": len(clean_links)
                            }
                            count += 1

                    elem.clear()
                    if count >= limit:
                        break

    def process_and_report(self, limit=100):
        """Run with a higher limit to see the cleaned data."""
        for page_data in self.get_page_links(limit=limit):
            if page_data['out_count'] > 0:
                print(f"Page: {page_data['source']} | Clean Links: {page_data['out_count']}")
                print(f"Sample: {page_data['targets'][:3]}")
                print("-" * 20)

    def save_to_csv(self, output_filename="wiki_edges.csv", limit=1000):
        """
        Extracts links and saves them as an Edge List (Source, Target).
        """
        output_path = Path(self.config.path_default) / output_filename
        
        print(f"Starting extraction... Saving to: {output_path}")
        
        with open(output_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow(['source', 'target'])
            
            count = 0
            # Reuse the extraction logic (you can refactor this into a generator)
            with bz2.BZ2File(self.file_absolute, "rb") as f:
                context = ET.iterparse(f, events=("end",))
                for event, elem in context:
                    tag = elem.tag.split('}')[-1]
                    if tag == "page":
                        ns = elem.find(".//{*}ns").text
                        is_redirect = elem.find(".//{*}redirect") is not None
                        
                        if ns == "0" and not is_redirect:
                            title = elem.find(".//{*}title").text
                            text_elem = elem.find(".//{*}text")
                            
                            if text_elem is not None and text_elem.text:
                                raw_links = self.link_pattern.findall(text_elem.text)
                                clean_links = self._clean_links(list(set(raw_links)), title)
                                
                                # Write each connection as a new row
                                for target in clean_links:
                                    writer.writerow([title, target])
                                
                                count += 1
                                if count % 100 == 0:
                                    print(f"Processed {count} pages...")

                        elem.clear()
                        if count >= limit:
                            break
                            
        print(f"Finished! Saved {count} pages of relationships to {output_filename}")