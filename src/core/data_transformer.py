"""
Data Transformer - Combines XML data with manual input to create MongoDB-ready output
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.models import (
    TestResult, Seuil, VO2Max, VMA, PatientInfo,
    GraphCurve, Graph, ZoneSeuil, LactateMeasure
)
from config import GRAPH_COLORS, GRAPH_INTERVAL_SECONDS


class DataTransformer:
    """Transform and merge XML data with manual input for MongoDB export"""
    
    def transform(self, xml_data: Dict[str, Any], manual_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform parsed XML data and manual input into final output structure.
        
        Args:
            xml_data: Parsed data from XML file
            manual_input: User-entered manual data
            
        Returns:
            Dictionary matching output_to_mongo_example.json structure
        """
        # Build athlete name from XML or manual input
        filename_data = xml_data.get('filename_data', {})
        patient_data = xml_data.get('patient_data', {})
        
        last_name = patient_data.get('Nom', filename_data.get('last_name', ''))
        first_name = patient_data.get('Prénom', filename_data.get('first_name', ''))
        athlete_name = f"{last_name} {first_name}".strip()
        
        # Build result
        result = TestResult()
        result.user_id = manual_input.get('email', '')
        result.athlete_name = athlete_name
        result.test_date = filename_data.get('date', '')
        result.test_type = "VO2max"
        
        # Build seuils
        result.seuils = self._build_seuils(xml_data.get('summary_data', {}), manual_input)
        
        # Build protocole
        result.protocole = self._build_protocole(xml_data, manual_input)
        
        # Build test_lactate
        result.test_lactate = self._build_test_lactate(manual_input)
        result.observations_lactate = manual_input.get('observations_lactate', '')
        
        # Build patient_info
        result.patient_info = self._build_patient_info(xml_data, manual_input)
        
        # Training advice
        result.conseils_entrainements = manual_input.get('conseils_entrainements', '')
        
        # Build graphiques from measurements
        result.graphiques = self._build_graphiques(
            xml_data.get('measurements', []),
            result.seuils
        )
        
        # Logos and partners (placeholders)
        result.logos = {
            "logo_gauche": "assets/logos/logo1.png",
            "logo_droit": "assets/logos/logo1.png"
        }
        result.partenaires = {
            "titre": "Nos Partenaires",
            "logos": []
        }
        
        return result.to_dict()
    
    def _build_seuils(self, summary_data: Dict[str, Any], manual_input: Dict[str, Any]) -> Dict[str, Any]:
        """Build seuils section from MANUAL INPUT ONLY (not XML)"""
        seuils = {}
        
        # Get thresholds from manual input ONLY
        stress_results = manual_input.get('stress_test_results', {})
        thresholds = stress_results.get('thresholds', {})
        sv1_data = thresholds.get('sv1', {})
        sv2_data = thresholds.get('sv2', {})
        
        # Get VMA from XML for percentage calculation
        v_row = summary_data.get("v", {})
        max_speed = self._safe_float(v_row.get('Valeurs Maximales Absolues'))
        
        # SV1 - From manual input ONLY
        sv1 = Seuil()
        sv1.fc = sv1_data.get('hr_bpm')
        sv1.allure = sv1_data.get('pace_km_h')
        sv1.vo2 = None  # User can add if needed
        
        # Calculate pourcentage_vma if we have VMA and allure
        if sv1.allure and max_speed:
            sv1.pourcentage_vma = int((sv1.allure / max_speed) * 100)
        
        seuils['SV1'] = sv1.to_dict()
        
        # SV2 - From manual input ONLY
        sv2 = Seuil()
        sv2.fc = sv2_data.get('hr_bpm')
        sv2.allure = sv2_data.get('pace_km_h')
        sv2.vo2 = None  # User can add if needed
        
        if sv2.allure and max_speed:
            sv2.pourcentage_vma = int((sv2.allure / max_speed) * 100)
        
        seuils['SV2'] = sv2.to_dict()
        
        # VO2max - From manual input ONLY
        vo2max = VO2Max()
        vo2max.valeur = stress_results.get('measured_vo2max')
        vo2max.fc_max = stress_results.get('max_hr')
        seuils['VO2_max'] = vo2max.to_dict()
        
        # VMA from XML (this is calculated, not a threshold)
        vma = VMA()
        vma.valeur = max_speed
        seuils['VMA'] = vma.to_dict()
        
        return seuils
    
    def _build_protocole(self, xml_data: Dict[str, Any], manual_input: Dict[str, Any]) -> Dict[str, Any]:
        """Build protocol section"""
        first_speed = manual_input.get('stress_test_results', {}).get('first_stage_speed')
        description = manual_input.get('protocol_description', '')
        
        return {
            "vitesse_depart_test": first_speed,
            "description": description
        }
    
    def _build_test_lactate(self, manual_input: Dict[str, Any]) -> Dict[str, Any]:
        """Build lactate test section"""
        lactate_profile = manual_input.get('stress_test_results', {}).get('lactate_profile', [])
        
        mesures = []
        for entry in lactate_profile:
            if entry.get('speed') is not None and entry.get('lactate_mmol_l') is not None:
                mesures.append({
                    "vitesse": entry['speed'],
                    "lactate": entry['lactate_mmol_l']
                })
        
        return {
            "actif": len(mesures) > 0,
            "mesures": mesures
        }
    
    def _build_patient_info(self, xml_data: Dict[str, Any], manual_input: Dict[str, Any]) -> Dict[str, Any]:
        """Build patient info section with all manual input fields"""
        bio_data = xml_data.get('bio_data', {})
        
        # Parse weight from XML (format: "68,2 kg")
        weight_str = bio_data.get('Poids', '')
        weight_xml = None
        if weight_str:
            try:
                weight_xml = float(weight_str.replace('kg', '').replace(',', '.').strip())
            except ValueError:
                pass
        
        # Get from manual input
        identity = manual_input.get('identity', {})
        body_comp = manual_input.get('body_composition', {})
        prof_life = manual_input.get('professional_life', {})
        equipment = manual_input.get('equipment_and_tracking', {})
        history = manual_input.get('history_and_goals', {})
        stress = manual_input.get('stress_test_results', {})
        
        patient_info = PatientInfo()
        
        # Identity
        patient_info.nom = identity.get('last_name', '')
        patient_info.prenom = identity.get('first_name', '')
        patient_info.date_naissance = identity.get('date_of_birth', '')
        patient_info.age = identity.get('age')
        patient_info.sport_base = identity.get('sport_practiced', '')
        patient_info.specialty = identity.get('specialty', '')
        patient_info.has_coach = identity.get('has_coach', False)
        
        # Body composition
        patient_info.taille_cm = body_comp.get('height_cm')
        patient_info.poids_actuel = body_comp.get('current_weight')
        patient_info.poids_debut = body_comp.get('weight_before_test') or weight_xml
        patient_info.poids_final = body_comp.get('weight_after_test')
        
        # Professional
        patient_info.metier = prof_life.get('job_title', '')
        patient_info.heures_travail = prof_life.get('working_hours_per_week')
        
        # Equipment & Tracking
        patient_info.marque_montre = equipment.get('watch_brand', '')
        patient_info.vo2_montre = equipment.get('watch_estimated_vo2')
        patient_info.fc_repos = equipment.get('min_hr_before')
        patient_info.fcmax_ever = equipment.get('max_hr_ever')
        patient_info.volume_cap = self._parse_volume(equipment.get('average_weekly_volume', ''))
        
        # Watch predictions
        predictions = equipment.get('watch_race_predictions', {})
        patient_info.prediction_5k = predictions.get('5k', '')
        patient_info.prediction_10k = predictions.get('10k', '')
        patient_info.prediction_semi = predictions.get('half_marathon', '')
        patient_info.prediction_marathon = predictions.get('marathon', '')
        
        # History & Goals
        patient_info.records_officiels = history.get('official_records', '')
        patient_info.trail_runner = history.get('trail_runner', False)
        patient_info.utmb_index = history.get('utmb_index')
        patient_info.objectifs = history.get('upcoming_goals', '')
        
        # Session context
        patient_info.seance_veille = manual_input.get('seance_veille', '')
        patient_info.observations = manual_input.get('observations', '')
        
        # Last stage speed
        patient_info.last_stage_speed = stress.get('last_stage_speed')
        
        return patient_info.to_dict()
    
    def _build_graphiques(self, measurements: List[Dict[str, Any]], seuils: Dict[str, Any]) -> Dict[str, Any]:
        """Build graph data from measurements"""
        if not measurements:
            return {}
        
        # Aggregate measurements by interval
        aggregated = self._aggregate_by_interval(measurements, GRAPH_INTERVAL_SECONDS)
        
        # Extract time values
        time_values = [m['t_seconds'] for m in aggregated if 't_seconds' in m]
        
        # Graph 1: FC, V'O2, V'CO2
        graph1 = Graph(titre="Heart Rate, V'O2 and V'CO2 Evolution")
        
        # FC curve
        fc_values = [m.get('FC') for m in aggregated]
        if any(v is not None for v in fc_values):
            graph1.courbes.append(GraphCurve(
                nom="FC (bpm)",
                couleur=GRAPH_COLORS["FC"],
                temps_secondes=time_values,
                valeurs=[v if v is not None else 0 for v in fc_values]
            ))
        
        # V'O2 curve
        vo2_values = [m.get("V'O2") for m in aggregated]
        if any(v is not None for v in vo2_values):
            graph1.courbes.append(GraphCurve(
                nom="V'O2 (L/min)",
                couleur=GRAPH_COLORS["V'O2"],
                temps_secondes=time_values,
                valeurs=[v if v is not None else 0 for v in vo2_values]
            ))
        
        # V'CO2 curve (if available - need to parse from XML)
        # Note: This might need adjustment based on actual XML column names
        
        # Graph 2: V'E, BF, RER
        graph2 = Graph(titre="V'E, RER and Breathing Frequency Evolution")
        
        # V'E curve
        ve_values = [m.get("V'E") for m in aggregated]
        if any(v is not None for v in ve_values):
            graph2.courbes.append(GraphCurve(
                nom="V'E (L/min)",
                couleur=GRAPH_COLORS["V'E"],
                temps_secondes=time_values,
                valeurs=[v if v is not None else 0 for v in ve_values]
            ))
        
        # BF curve
        bf_values = [m.get("BF") for m in aggregated]
        if any(v is not None for v in bf_values):
            graph2.courbes.append(GraphCurve(
                nom="BF (/min)",
                couleur=GRAPH_COLORS["BF"],
                temps_secondes=time_values,
                valeurs=[v if v is not None else 0 for v in bf_values]
            ))
        
        # RER curve
        rer_values = [m.get("RER") for m in aggregated]
        if any(v is not None for v in rer_values):
            graph2.courbes.append(GraphCurve(
                nom="RER",
                couleur=GRAPH_COLORS["RER"],
                dash="dot",
                temps_secondes=time_values,
                valeurs=[v if v is not None else 0 for v in rer_values]
            ))
        
        # Build zones_seuils
        zones = self._build_zones_seuils(aggregated, seuils)
        
        result = {
            "graphique_1": graph1.to_dict(),
            "graphique_2": graph2.to_dict(),
            "zones_seuils": [z.to_dict() for z in zones]
        }
        
        return result
    
    def _aggregate_by_interval(self, measurements: List[Dict], interval_sec: int = 15) -> List[Dict]:
        """Aggregate measurements into fixed time intervals"""
        if not measurements:
            return []
        
        aggregated = []
        current_interval = 0
        current_values = {}
        count = 0
        
        for m in measurements:
            t = m.get('t_seconds', 0)
            interval = int(t // interval_sec) * interval_sec + interval_sec
            
            if interval != current_interval:
                # Save previous interval if we have data
                if count > 0:
                    avg_values = {'t_seconds': current_interval}
                    for key, values in current_values.items():
                        if values:
                            valid_values = [v for v in values if v is not None]
                            if valid_values:
                                avg_values[key] = round(sum(valid_values) / len(valid_values), 2)
                    aggregated.append(avg_values)
                
                # Start new interval
                current_interval = interval
                current_values = {}
                count = 0
            
            # Accumulate values
            for key, value in m.items():
                if key not in ['t', 't_seconds', 'Phase', 'Marqueur']:
                    if key not in current_values:
                        current_values[key] = []
                    current_values[key].append(value)
            count += 1
        
        # Don't forget last interval
        if count > 0:
            avg_values = {'t_seconds': current_interval}
            for key, values in current_values.items():
                if values:
                    valid_values = [v for v in values if v is not None]
                    if valid_values:
                        avg_values[key] = round(sum(valid_values) / len(valid_values), 2)
            aggregated.append(avg_values)
        
        return aggregated
    
    def _build_zones_seuils(self, aggregated: List[Dict], seuils: Dict[str, Any]) -> List[ZoneSeuil]:
        """Build threshold zones from aggregated data and seuils"""
        zones = []
        
        # SV1 zone
        sv1 = seuils.get('SV1', {})
        if sv1.get('fc'):
            fc_target = sv1['fc']
            zone = self._find_zone_by_fc(aggregated, fc_target, 'SV1', 'orange')
            if zone:
                zones.append(zone)
        
        # SV2 zone
        sv2 = seuils.get('SV2', {})
        if sv2.get('fc'):
            fc_target = sv2['fc']
            zone = self._find_zone_by_fc(aggregated, fc_target, 'SV2', 'purple')
            if zone:
                zones.append(zone)
        
        # VO2max zone
        vo2max = seuils.get('VO2_max', {})
        if vo2max.get('fc_max'):
            fc_max = vo2max['fc_max']
            # Find when FC reaches max
            for m in aggregated:
                if m.get('FC') and m['FC'] >= fc_max * 0.98:  # Within 2% of max
                    zones.append(ZoneSeuil(
                        nom="VO2_max",
                        couleur="red",
                        fc=fc_max,
                        temps_sec=m['t_seconds'],
                        label=f"VO2Max\nFC={fc_max}"
                    ))
                    break
        
        return zones
    
    def _find_zone_by_fc(self, aggregated: List[Dict], fc_target: int, name: str, color: str) -> Optional[ZoneSeuil]:
        """Find time zone where FC matches target (±2%)"""
        tolerance = 0.02
        fc_min = int(fc_target * (1 - tolerance))
        fc_max = int(fc_target * (1 + tolerance))
        
        matching_times = []
        for m in aggregated:
            fc = m.get('FC')
            if fc and fc_min <= fc <= fc_max:
                matching_times.append(m['t_seconds'])
        
        if matching_times:
            return ZoneSeuil(
                nom=name,
                couleur=color,
                fc_min=fc_min,
                fc_max=fc_max,
                temps_debut_sec=min(matching_times),
                temps_fin_sec=max(matching_times),
                label=f"{name}\n[{fc_min}-{fc_max}] bpm"
            )
        return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(',', '.'))
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        try:
            return int(float(str(value).replace(',', '.')))
        except (ValueError, TypeError):
            return None
    
    def _parse_volume(self, volume_str: str) -> Optional[float]:
        """Parse volume string to number"""
        if not volume_str:
            return None
        try:
            # Remove units and convert
            clean = volume_str.replace('km', '').replace('h', '').strip()
            return float(clean.replace(',', '.'))
        except ValueError:
            return None
