"""
JSON Exporter - Exports transformed data to JSON files
"""
import json
import os
from typing import Dict, Any
from datetime import datetime


class JsonExporter:
    """Export transformed test data to JSON files"""
    
    def __init__(self, output_dir: str = "Output"):
        self.output_dir = output_dir
        
    def export(self, data: Dict[str, Any], output_path: str = None) -> str:
        """
        Export data to a JSON file.
        
        Args:
            data: Dictionary to export
            output_path: Optional full path. If not provided, generates from data.
            
        Returns:
            Path to the created file
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        if output_path is None:
            output_path = self._generate_filename(data)
        
        # Ensure full path
        if not os.path.isabs(output_path):
            output_path = os.path.join(self.output_dir, output_path)
        
        # Write JSON with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def _generate_filename(self, data: Dict[str, Any]) -> str:
        """Generate output filename from data"""
        athlete_name = data.get('athlete_name', 'Unknown')
        test_date = data.get('test_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Clean filename
        safe_name = "".join(c if c.isalnum() or c in ' _-' else '_' for c in athlete_name)
        safe_name = safe_name.replace(' ', '_')
        
        filename = f"{safe_name}_{test_date}_vo2max.json"
        return filename
    
    def validate_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that data has required fields for MongoDB.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Dictionary with validation results
        """
        required_fields = [
            'user_id',
            'athlete_name',
            'test_date',
            'test_type',
            'seuils',
            'patient_info'
        ]
        
        seuil_fields = ['SV1', 'SV2', 'VO2_max', 'VMA']
        
        errors = []
        warnings = []
        
        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
            elif field == 'user_id' and not data[field]:
                errors.append("user_id (email) is empty")
        
        # Check seuils
        seuils = data.get('seuils', {})
        for seuil_name in seuil_fields:
            if seuil_name not in seuils:
                warnings.append(f"Missing seuil: {seuil_name}")
        
        # Check graphiques
        if 'graphiques' not in data or not data['graphiques']:
            warnings.append("No graph data available")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def export_batch(self, data_list: list, progress_callback=None) -> Dict[str, Any]:
        """
        Export multiple test results.
        
        Args:
            data_list: List of data dictionaries to export
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Summary of export operation
        """
        results = {
            'success': [],
            'failed': [],
            'total': len(data_list)
        }
        
        for i, data in enumerate(data_list):
            try:
                filepath = self.export(data)
                results['success'].append({
                    'athlete': data.get('athlete_name', 'Unknown'),
                    'path': filepath
                })
                
                if progress_callback:
                    progress_callback(i + 1, len(data_list), filepath)
                    
            except Exception as e:
                results['failed'].append({
                    'athlete': data.get('athlete_name', 'Unknown'),
                    'error': str(e)
                })
        
        return results
