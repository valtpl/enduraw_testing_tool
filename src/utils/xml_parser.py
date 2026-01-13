"""
XML Parser for MetaLyzer TCP export files (Excel XML format)
"""
import xml.etree.ElementTree as ET
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from config import (
    XML_FILENAME_PATTERN,
    SECTION_PATIENT_DATA,
    SECTION_ADMIN_DATA,
    SECTION_BIO_DATA,
    SECTION_TEST_DATA,
    SECTION_SUMMARY_TABLE,
    SECTION_MEASUREMENT_DATA
)


class TCPXmlParser:
    """Parser for MetaLyzer TCP XML export files"""
    
    # XML namespaces used in Excel XML format
    NAMESPACES = {
        'ss': 'urn:schemas-microsoft-com:office:spreadsheet',
        'o': 'urn:schemas-microsoft-com:office:office',
        'x': 'urn:schemas-microsoft-com:office:excel',
        'html': 'http://www.w3.org/TR/REC-html40'
    }
    
    def __init__(self):
        self.filepath = None
        self.tree = None
        self.root = None
        
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a TCP XML file and extract all relevant data.
        
        Args:
            filepath: Path to the XML file
            
        Returns:
            Dictionary containing parsed data
        """
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        
        # Parse filename for basic info
        filename_data = self._parse_filename(os.path.basename(filepath))
        
        # Find the worksheet
        worksheet = self.root.find('.//ss:Worksheet[@ss:Name="MetasoftStudio"]', self.NAMESPACES)
        if worksheet is None:
            # Try without namespace prefix
            worksheet = self.root.find('.//{urn:schemas-microsoft-com:office:spreadsheet}Worksheet')
        
        if worksheet is None:
            raise ValueError(f"Could not find MetasoftStudio worksheet in {filepath}")
        
        table = worksheet.find('ss:Table', self.NAMESPACES)
        if table is None:
            table = worksheet.find('{urn:schemas-microsoft-com:office:spreadsheet}Table')
            
        rows = table.findall('ss:Row', self.NAMESPACES)
        if not rows:
            rows = table.findall('{urn:schemas-microsoft-com:office:spreadsheet}Row')
        
        # Parse different sections
        patient_data = self._parse_patient_data(rows)
        bio_data = self._parse_bio_data(rows)
        test_metadata = self._parse_test_metadata(rows)
        summary_data = self._parse_summary_table(rows)
        measurements = self._parse_measurement_data(rows)
        
        return {
            'filename_data': filename_data,
            'patient_data': patient_data,
            'bio_data': bio_data,
            'test_metadata': test_metadata,
            'summary_data': summary_data,
            'measurements': measurements
        }
    
    def _parse_filename(self, filename: str) -> Dict[str, str]:
        """Extract athlete name and date from filename"""
        # Pattern: TCP__NOM_Prenom_YYYY.MM.DD_HH.MM.SS_.xml
        pattern = r"TCP__([A-Z]+)_([A-Za-zÀ-ÿ]+)_(\d{4})\.(\d{2})\.(\d{2})_(\d{2})\.(\d{2})\.(\d{2})_\.xml"
        match = re.match(pattern, filename)
        
        if match:
            nom, prenom, year, month, day, hour, minute, second = match.groups()
            return {
                'last_name': nom,
                'first_name': prenom,
                'date': f"{year}-{month}-{day}",
                'time': f"{hour}:{minute}:{second}",
                'datetime': f"{year}-{month}-{day}T{hour}:{minute}:{second}"
            }
        return {
            'last_name': '',
            'first_name': '',
            'date': '',
            'time': '',
            'datetime': ''
        }
    
    def _get_cell_value(self, cell) -> str:
        """Extract text value from a cell element"""
        data = cell.find('ss:Data', self.NAMESPACES)
        if data is None:
            data = cell.find('{urn:schemas-microsoft-com:office:spreadsheet}Data')
        if data is not None and data.text:
            return data.text.strip()
        return ""
    
    def _get_row_cells(self, row) -> List[str]:
        """Get all cell values from a row"""
        cells = row.findall('ss:Cell', self.NAMESPACES)
        if not cells:
            cells = row.findall('{urn:schemas-microsoft-com:office:spreadsheet}Cell')
        return [self._get_cell_value(cell) for cell in cells]
    
    def _find_section_start(self, rows: List, section_name: str) -> int:
        """Find the row index where a section starts"""
        for i, row in enumerate(rows):
            cells = self._get_row_cells(row)
            if cells and section_name in cells[0]:
                return i
        return -1
    
    def _parse_key_value_pairs(self, rows: List, start_idx: int, end_section: str = None) -> Dict[str, str]:
        """Parse key-value pairs from consecutive rows"""
        result = {}
        i = start_idx + 1
        
        while i < len(rows):
            cells = self._get_row_cells(rows[i])
            
            # Check if we've reached the next section
            if cells and end_section and end_section in cells[0]:
                break
                
            # Check for empty row (section boundary)
            if not cells or all(c == "" for c in cells):
                # Multiple empty rows might mean section end
                if i + 1 < len(rows):
                    next_cells = self._get_row_cells(rows[i + 1])
                    if next_cells and any("Données" in c or "Tableau" in c or "Valeur" in c for c in next_cells if c):
                        break
                i += 1
                continue
            
            # Extract key-value if we have at least 2 non-empty cells
            if len(cells) >= 2 and cells[0]:
                key = cells[0]
                # Value is typically in the third cell (after merged header cells)
                value = cells[2] if len(cells) > 2 else cells[1]
                result[key] = value
            
            i += 1
            
        return result
    
    def _parse_patient_data(self, rows: List) -> Dict[str, str]:
        """Parse patient administrative data"""
        idx = self._find_section_start(rows, SECTION_ADMIN_DATA)
        if idx == -1:
            idx = self._find_section_start(rows, SECTION_PATIENT_DATA)
        if idx == -1:
            return {}
        return self._parse_key_value_pairs(rows, idx)
    
    def _parse_bio_data(self, rows: List) -> Dict[str, str]:
        """Parse biological and medical data"""
        idx = self._find_section_start(rows, SECTION_BIO_DATA)
        if idx == -1:
            return {}
        return self._parse_key_value_pairs(rows, idx)
    
    def _parse_test_metadata(self, rows: List) -> Dict[str, str]:
        """Parse test metadata (date, duration, device, etc.)"""
        idx = self._find_section_start(rows, SECTION_TEST_DATA)
        if idx == -1:
            return {}
        return self._parse_key_value_pairs(rows, idx)
    
    def _parse_summary_table(self, rows: List) -> Dict[str, Dict[str, Any]]:
        """Parse the summary table with VT1, VT2, VO2max values"""
        idx = self._find_section_start(rows, SECTION_SUMMARY_TABLE)
        if idx == -1:
            return {}
        
        result = {}
        headers = []
        i = idx + 1
        
        # Find header row (Variable, Unité, Repos, etc.)
        while i < len(rows):
            cells = self._get_row_cells(rows[i])
            if cells and "Variable" in cells[0]:
                headers = cells
                i += 1
                break
            i += 1
        
        # Parse data rows
        while i < len(rows):
            cells = self._get_row_cells(rows[i])
            
            # Stop if we hit a new section or empty rows
            if not cells or all(c == "" for c in cells):
                if i + 1 < len(rows):
                    next_cells = self._get_row_cells(rows[i + 1])
                    if not next_cells or all(c == "" for c in next_cells):
                        break
                i += 1
                continue
            
            # Check for section end
            if cells and any("Valeur de pente" in c or "Measurement Data" in c for c in cells if c):
                break
            
            # Parse row data
            if len(cells) >= 2 and cells[0]:
                variable = cells[0]
                row_data = {}
                for j, header in enumerate(headers):
                    if j < len(cells):
                        row_data[header] = self._convert_value(cells[j])
                result[variable] = row_data
            
            i += 1
            
        return result
    
    def _parse_measurement_data(self, rows: List) -> List[Dict[str, Any]]:
        """Parse the time-series measurement data"""
        idx = self._find_section_start(rows, SECTION_MEASUREMENT_DATA)
        if idx == -1:
            return []
        
        measurements = []
        headers = []
        units = []
        i = idx + 1
        
        # Find headers row (t, Phase, Marqueur, V'O2, etc.)
        while i < len(rows):
            cells = self._get_row_cells(rows[i])
            if cells and cells[0] == "t":
                headers = cells
                i += 1
                # Next row is units
                if i < len(rows):
                    units = self._get_row_cells(rows[i])
                    i += 1
                break
            i += 1
        
        # Parse data rows
        while i < len(rows):
            cells = self._get_row_cells(rows[i])
            
            if not cells or cells[0] == "":
                i += 1
                continue
                
            # Check if this is still measurement data (starts with time format)
            if not re.match(r'\d+:\d+:\d+', cells[0]):
                break
            
            row_data = {}
            for j, header in enumerate(headers):
                if j < len(cells) and header:
                    value = cells[j]
                    # Convert time to seconds for 't' column
                    if header == 't':
                        row_data['t_seconds'] = self._time_to_seconds(value)
                        row_data['t'] = value
                    else:
                        row_data[header] = self._convert_value(value)
            
            measurements.append(row_data)
            i += 1
            
        return measurements
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        if not value or value == "-":
            return None
            
        # Handle French decimal format
        value_clean = value.replace(',', '.').replace(' ', '')
        
        # Try to convert to number
        try:
            if '.' in value_clean:
                return float(value_clean)
            return int(value_clean)
        except ValueError:
            return value
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert time string (h:mm:ss,ms) to seconds"""
        try:
            # Handle format like "0:00:06,200"
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            pass
        return 0.0


def parse_xml_file(filepath: str) -> Dict[str, Any]:
    """Convenience function to parse an XML file"""
    parser = TCPXmlParser()
    return parser.parse_file(filepath)


def get_available_tests(folder_path: str) -> List[Dict[str, str]]:
    """
    Scan a folder for TCP XML files and return basic info about each.
    
    Args:
        folder_path: Path to folder containing XML files
        
    Returns:
        List of dictionaries with file info
    """
    tests = []
    parser = TCPXmlParser()
    
    for filename in os.listdir(folder_path):
        if filename.startswith("TCP__") and filename.endswith(".xml"):
            filepath = os.path.join(folder_path, filename)
            try:
                info = parser._parse_filename(filename)
                info['filepath'] = filepath
                info['filename'] = filename
                tests.append(info)
            except Exception as e:
                print(f"Error parsing {filename}: {e}")
                
    # Sort by date/time
    tests.sort(key=lambda x: x.get('datetime', ''), reverse=True)
    return tests
