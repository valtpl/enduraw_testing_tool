"""
TCP Data Processor - Main Application with CustomTkinter GUI
Cross-platform desktop application for processing MetaLyzer XML exports
"""
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional

from xml_parser import TCPXmlParser, get_available_tests
from data_transformer import DataTransformer
from json_exporter import JsonExporter
from config import APP_NAME, APP_VERSION


# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TestListItem(ctk.CTkFrame):
    """Individual test item in the list"""
    
    def __init__(self, master, test_info: Dict, on_select=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.test_info = test_info
        self.on_select = on_select
        self.is_selected = False
        self.has_data = False
        
        self.configure(fg_color="transparent", corner_radius=5)
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        
        # Checkbox and name
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self, 
            text="",
            variable=self.checkbox_var,
            width=20,
            checkbox_width=18,
            checkbox_height=18
        )
        self.checkbox.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        # Name label
        name = f"{test_info.get('last_name', '')} {test_info.get('first_name', '')}"
        self.name_label = ctk.CTkLabel(
            self, 
            text=name,
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        self.name_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Date/time label
        date_time = f"{test_info.get('date', '')} {test_info.get('time', '')}"
        self.date_label = ctk.CTkLabel(
            self, 
            text=date_time,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.date_label.grid(row=1, column=1, padx=5, pady=0, sticky="w")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            self,
            text="○",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=0, column=2, rowspan=2, padx=10)
        
        # Bind click
        self.bind("<Button-1>", self._on_click)
        self.name_label.bind("<Button-1>", self._on_click)
        self.date_label.bind("<Button-1>", self._on_click)
        
    def _on_click(self, event):
        if self.on_select:
            self.on_select(self)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.configure(fg_color=("gray85", "gray25"))
        else:
            self.configure(fg_color="transparent")
    
    def set_has_data(self, has_data: bool):
        self.has_data = has_data
        if has_data:
            self.status_label.configure(text="●", text_color="green")
        else:
            self.status_label.configure(text="○", text_color="gray")


class InputForm(ctk.CTkScrollableFrame):
    """Form for manual data input"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.entries = {}
        self._create_form()
    
    def _create_form(self):
        """Create all form fields in 2-column layout"""
        # Configure grid for 2 columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # ==================== LEFT COLUMN (col=0) ====================
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_columnconfigure(1, weight=1)
        
        left_row = 0
        
        # ----- IDENTIFICATION -----
        left_row = self._add_section_to_frame(left_frame, "🪪 Identification", left_row)
        left_row = self._add_field_to_frame(left_frame, "email", "Email (ID utilisateur) *", left_row)
        left_row = self._add_field_to_frame(left_frame, "last_name", "Nom", left_row)
        left_row = self._add_field_to_frame(left_frame, "first_name", "Prénom", left_row)
        left_row = self._add_field_to_frame(left_frame, "date_of_birth", "Date de naissance", left_row)
        left_row = self._add_field_to_frame(left_frame, "age", "Âge", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "sport_practiced", "Sport pratiqué", left_row)
        left_row = self._add_field_to_frame(left_frame, "specialty", "Spécialité", left_row)
        left_row = self._add_checkbox_to_frame(left_frame, "has_coach", "A un coach", left_row)
        
        # ----- COMPOSITION CORPORELLE -----
        left_row = self._add_section_to_frame(left_frame, "⚖️ Composition Corporelle", left_row)
        left_row = self._add_field_to_frame(left_frame, "height_cm", "Taille (cm)", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "current_weight", "Poids actuel (kg)", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "weight_before_test", "Poids avant test (kg)", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "weight_after_test", "Poids après test (kg)", left_row, field_type="number")
        
        # ----- VIE PROFESSIONNELLE -----
        left_row = self._add_section_to_frame(left_frame, "💼 Vie Professionnelle", left_row)
        left_row = self._add_field_to_frame(left_frame, "job_title", "Métier", left_row)
        left_row = self._add_field_to_frame(left_frame, "working_hours_per_week", "Heures/semaine", left_row, field_type="number")
        
        # ----- ÉQUIPEMENT -----
        left_row = self._add_section_to_frame(left_frame, "⌚ Équipement & Suivi", left_row)
        left_row = self._add_field_to_frame(left_frame, "watch_brand", "Marque de montre", left_row)
        left_row = self._add_field_to_frame(left_frame, "watch_estimated_vo2", "VO2 montre", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "min_hr_before", "FC repos (bpm)", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "max_hr_ever", "FC max connue", left_row, field_type="number")
        left_row = self._add_field_to_frame(left_frame, "average_weekly_volume", "Volume hebdo", left_row)
        
        # Prédictions montre (format HH:MM:SS)
        left_row = self._add_subsection_to_frame(left_frame, "Prédictions montre (HH:MM:SS)", left_row)
        left_row = self._add_time_field_to_frame(left_frame, "prediction_5k", "5K", left_row)
        left_row = self._add_time_field_to_frame(left_frame, "prediction_10k", "10K", left_row)
        left_row = self._add_time_field_to_frame(left_frame, "prediction_half", "Semi", left_row)
        left_row = self._add_time_field_to_frame(left_frame, "prediction_marathon", "Marathon", left_row)
        
        # ==================== RIGHT COLUMN (col=1) ====================
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_frame.grid_columnconfigure(1, weight=1)
        
        right_row = 0
        
        # ----- HISTORIQUE & OBJECTIFS -----
        right_row = self._add_section_to_frame(right_frame, "🎯 Historique & Objectifs", right_row)
        right_row = self._add_subsection_to_frame(right_frame, "Records personnels (HH:MM:SS)", right_row)
        right_row = self._add_time_field_to_frame(right_frame, "record_5k", "5K", right_row)
        right_row = self._add_time_field_to_frame(right_frame, "record_10k", "10K", right_row)
        right_row = self._add_time_field_to_frame(right_frame, "record_half", "Semi", right_row)
        right_row = self._add_time_field_to_frame(right_frame, "record_marathon", "Marathon", right_row)
        right_row = self._add_field_to_frame(right_frame, "utmb_index", "Index UTMB", right_row, field_type="number")
        right_row = self._add_field_to_frame(right_frame, "upcoming_goals", "Objectifs à venir", right_row)
        
        # ----- CONTEXTE SÉANCE -----
        right_row = self._add_section_to_frame(right_frame, "📋 Contexte Séance", right_row)
        right_row = self._add_field_to_frame(right_frame, "seance_veille", "Séance de la veille", right_row)
        right_row = self._add_field_to_frame(right_frame, "observations", "Observations", right_row)
        
        # ----- PROTOCOLE -----
        right_row = self._add_section_to_frame(right_frame, "📊 Protocole", right_row)
        right_row = self._add_textfield_to_frame(right_frame, "protocol_description", "Description du test", right_row)
        right_row = self._add_field_to_frame(right_frame, "first_stage_speed", "Vitesse 1er palier (km/h)", right_row, field_type="number")
        right_row = self._add_field_to_frame(right_frame, "last_stage_speed", "Vitesse dernier palier (km/h)", right_row, field_type="number")
        
        # ----- RÉSULTATS GÉNÉRAUX -----
        right_row = self._add_section_to_frame(right_frame, "📈 Résultats Généraux", right_row)
        right_row = self._add_field_to_frame(right_frame, "measured_vo2max", "VO2max mesuré", right_row, field_type="number")
        right_row = self._add_field_to_frame(right_frame, "max_hr", "FC max atteinte", right_row, field_type="number")
        
        # ----- SEUILS -----
        right_row = self._add_section_to_frame(right_frame, "🎚️ Seuils Ventilatoires", right_row)
        right_row = self._add_thresholds_to_frame(right_frame, right_row)
        
        # ----- LACTATE -----
        right_row = self._add_section_to_frame(right_frame, "🧪 Mesures Lactate", right_row)
        right_row = self._add_lactate_to_frame(right_frame, right_row)
        
        # ----- CONSEILS -----
        right_row = self._add_section_to_frame(right_frame, "� Conseils", right_row)
        right_row = self._add_textfield_to_frame(right_frame, "conseils_entrainements", "Conseils d'entraînement", right_row)
    
    def _add_section_to_frame(self, frame, title: str, row: int) -> int:
        """Add section header to a specific frame"""
        label = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        label.grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        return row + 1
    
    def _add_subsection_to_frame(self, frame, title: str, row: int) -> int:
        """Add subsection header"""
        label = ctk.CTkLabel(frame, text=f"  {title}", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        label.grid(row=row, column=0, columnspan=2, pady=(8, 2), sticky="w")
        return row + 1
    
    def _add_field_to_frame(self, frame, key: str, label: str, row: int, field_type: str = "text") -> int:
        """Add input field to a specific frame"""
        lbl = ctk.CTkLabel(frame, text=label, anchor="w")
        lbl.grid(row=row, column=0, padx=(0, 5), pady=2, sticky="w")
        entry = ctk.CTkEntry(frame, width=150)
        entry.grid(row=row, column=1, pady=2, sticky="ew")
        self.entries[key] = {'widget': entry, 'type': field_type}
        return row + 1
    
    def _add_time_field_to_frame(self, frame, key: str, label: str, row: int) -> int:
        """Add time input field with HH:MM:SS placeholder and auto-formatting"""
        lbl = ctk.CTkLabel(frame, text=label, anchor="w")
        lbl.grid(row=row, column=0, padx=(0, 5), pady=2, sticky="w")
        entry = ctk.CTkEntry(frame, width=100, placeholder_text="HH:MM:SS")
        entry.grid(row=row, column=1, pady=2, sticky="w")
        
        # Bind auto-format on focus out and key release
        entry.bind('<FocusOut>', lambda e, ent=entry: self._format_time_entry(ent))
        entry.bind('<Return>', lambda e, ent=entry: self._format_time_entry(ent))
        
        self.entries[key] = {'widget': entry, 'type': 'time'}
        return row + 1
    
    def _format_time_entry(self, entry):
        """Auto-format time entry: HHMMSS -> HH:MM:SS"""
        value = entry.get().strip()
        if not value:
            return
        
        # Remove existing colons and spaces
        clean = value.replace(':', '').replace(' ', '')
        
        # Only process if it looks like unformatted time (digits only)
        if clean.isdigit():
            # Pad with leading zeros if needed
            clean = clean.zfill(6)
            
            # Format as HH:MM:SS
            if len(clean) >= 6:
                formatted = f"{clean[:2]}:{clean[2:4]}:{clean[4:6]}"
                entry.delete(0, 'end')
                entry.insert(0, formatted)
    
    def _add_checkbox_to_frame(self, frame, key: str, label: str, row: int) -> int:
        """Add checkbox to a specific frame"""
        checkbox = ctk.CTkCheckBox(frame, text=label)
        checkbox.grid(row=row, column=0, columnspan=2, pady=5, sticky="w")
        self.entries[key] = {'widget': checkbox, 'type': 'checkbox'}
        return row + 1
    
    def _add_textfield_to_frame(self, frame, key: str, label: str, row: int) -> int:
        """Add multi-line text field"""
        lbl = ctk.CTkLabel(frame, text=label, anchor="w")
        lbl.grid(row=row, column=0, columnspan=2, pady=(5, 2), sticky="w")
        textbox = ctk.CTkTextbox(frame, height=80)
        textbox.grid(row=row+1, column=0, columnspan=2, pady=2, sticky="ew")
        self.entries[key] = {'widget': textbox, 'type': 'textbox'}
        return row + 2
    
    def _add_thresholds_to_frame(self, frame, row: int) -> int:
        """Add SV1 and SV2 side by side in a frame"""
        threshold_frame = ctk.CTkFrame(frame, fg_color="transparent")
        threshold_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        threshold_frame.grid_columnconfigure(0, weight=1)
        threshold_frame.grid_columnconfigure(1, weight=1)
        
        # SV1
        sv1_frame = ctk.CTkFrame(threshold_frame, corner_radius=8)
        sv1_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        ctk.CTkLabel(sv1_frame, text="🟠 SV1", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        for i, (key, lbl) in enumerate([("sv1_hr", "FC"), ("sv1_speed", "Vitesse (km/h)"), ("sv1_vo2", "VO2")]):
            ctk.CTkLabel(sv1_frame, text=lbl).grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            entry = ctk.CTkEntry(sv1_frame, width=70)
            entry.grid(row=i+1, column=1, padx=5, pady=2)
            self.entries[key] = {'widget': entry, 'type': 'number'}
        ctk.CTkLabel(sv1_frame, text="").grid(row=4, pady=3)
        
        # SV2
        sv2_frame = ctk.CTkFrame(threshold_frame, corner_radius=8)
        sv2_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        ctk.CTkLabel(sv2_frame, text="� SV2", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        for i, (key, lbl) in enumerate([("sv2_hr", "FC"), ("sv2_speed", "Vitesse (km/h)"), ("sv2_vo2", "VO2")]):
            ctk.CTkLabel(sv2_frame, text=lbl).grid(row=i+1, column=0, padx=5, pady=2, sticky="w")
            entry = ctk.CTkEntry(sv2_frame, width=70)
            entry.grid(row=i+1, column=1, padx=5, pady=2)
            self.entries[key] = {'widget': entry, 'type': 'number'}
        ctk.CTkLabel(sv2_frame, text="").grid(row=4, pady=3)
        
        return row + 1
    
    def _add_lactate_to_frame(self, frame, row: int) -> int:
        """Add lactate section to frame"""
        self.lactate_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.lactate_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        self.lactate_entries = []
        add_btn = ctk.CTkButton(self.lactate_frame, text="+ Ajouter mesure", width=130, command=self._add_lactate_entry)
        add_btn.grid(row=0, column=0, pady=3, sticky="w")
        return row + 1
    
    def _add_thresholds_section(self, row: int) -> int:
        """Add SV1 and SV2 side by side"""
        # Container frame for both thresholds
        threshold_frame = ctk.CTkFrame(self, fg_color="transparent")
        threshold_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        threshold_frame.grid_columnconfigure(0, weight=1)
        threshold_frame.grid_columnconfigure(1, weight=1)
        
        # ===== SV1 Column =====
        sv1_frame = ctk.CTkFrame(threshold_frame, corner_radius=10)
        sv1_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        
        sv1_title = ctk.CTkLabel(sv1_frame, text="🟠 SV1 (Seuil 1)", font=ctk.CTkFont(size=13, weight="bold"))
        sv1_title.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10)
        
        # SV1 fields
        sv1_fields = [
            ("sv1_hr", "FC (bpm)", "number"),
            ("sv1_speed", "Allure (km/h)", "number"),
            ("sv1_vo2", "VO2 (ml/kg/min)", "number")
        ]
        for i, (key, label, ftype) in enumerate(sv1_fields):
            lbl = ctk.CTkLabel(sv1_frame, text=label, anchor="w")
            lbl.grid(row=i+1, column=0, padx=10, pady=3, sticky="w")
            entry = ctk.CTkEntry(sv1_frame, width=100)
            entry.grid(row=i+1, column=1, padx=10, pady=3, sticky="e")
            self.entries[key] = {'widget': entry, 'type': ftype}
        
        # Add padding at bottom
        ctk.CTkLabel(sv1_frame, text="").grid(row=4, column=0, pady=5)
        
        # ===== SV2 Column =====
        sv2_frame = ctk.CTkFrame(threshold_frame, corner_radius=10)
        sv2_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nsew")
        
        sv2_title = ctk.CTkLabel(sv2_frame, text="🟣 SV2 (Seuil 2)", font=ctk.CTkFont(size=13, weight="bold"))
        sv2_title.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10)
        
        # SV2 fields
        sv2_fields = [
            ("sv2_hr", "FC (bpm)", "number"),
            ("sv2_speed", "Allure (km/h)", "number"),
            ("sv2_vo2", "VO2 (ml/kg/min)", "number")
        ]
        for i, (key, label, ftype) in enumerate(sv2_fields):
            lbl = ctk.CTkLabel(sv2_frame, text=label, anchor="w")
            lbl.grid(row=i+1, column=0, padx=10, pady=3, sticky="w")
            entry = ctk.CTkEntry(sv2_frame, width=100)
            entry.grid(row=i+1, column=1, padx=10, pady=3, sticky="e")
            self.entries[key] = {'widget': entry, 'type': ftype}
        
        # Add padding at bottom
        ctk.CTkLabel(sv2_frame, text="").grid(row=4, column=0, pady=5)
        
        return row + 1
    
    def _add_subsection(self, title: str, row: int) -> int:
        """Add subsection header"""
        label = ctk.CTkLabel(
            self,
            text=f"  {title}",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        label.grid(row=row, column=0, columnspan=2, pady=(10, 3), sticky="w")
        return row + 1
        
    def _add_section(self, title: str, row: int) -> int:
        """Add section header"""
        label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray10", "gray90")
        )
        label.grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        return row + 1
    
    def _add_field(self, key: str, label: str, row: int, field_type: str = "text") -> int:
        """Add input field"""
        lbl = ctk.CTkLabel(self, text=label, anchor="w")
        lbl.grid(row=row, column=0, padx=(0, 10), pady=3, sticky="w")
        
        entry = ctk.CTkEntry(self, width=200)
        entry.grid(row=row, column=1, pady=3, sticky="ew")
        
        self.entries[key] = {'widget': entry, 'type': field_type}
        return row + 1
    
    def _add_textfield(self, key: str, label: str, row: int) -> int:
        """Add multi-line text field"""
        lbl = ctk.CTkLabel(self, text=label, anchor="w")
        lbl.grid(row=row, column=0, columnspan=2, pady=(5, 2), sticky="w")
        
        textbox = ctk.CTkTextbox(self, height=100)
        textbox.grid(row=row+1, column=0, columnspan=2, pady=3, sticky="ew")
        
        self.entries[key] = {'widget': textbox, 'type': 'textbox'}
        return row + 2
    
    def _add_lactate_section(self, row: int) -> int:
        """Add dynamic lactate measurements section"""
        # Container for lactate entries
        self.lactate_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lactate_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        self.lactate_frame.grid_columnconfigure(1, weight=1)
        
        # List to store lactate entry widgets
        self.lactate_entries = []
        
        # Add button
        add_btn = ctk.CTkButton(
            self.lactate_frame,
            text="+ Ajouter mesure",
            width=140,
            command=self._add_lactate_entry
        )
        add_btn.grid(row=0, column=0, columnspan=3, pady=5, sticky="w")
        
        return row + 1
    
    def _add_lactate_entry(self):
        """Add a new lactate measurement row"""
        row = len(self.lactate_entries) + 1
        
        entry_frame = ctk.CTkFrame(self.lactate_frame, fg_color="transparent")
        entry_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=2)
        entry_frame.grid_columnconfigure(1, weight=1)
        entry_frame.grid_columnconfigure(3, weight=1)
        
        # Speed label and entry
        speed_lbl = ctk.CTkLabel(entry_frame, text="Vitesse (km/h):", width=100)
        speed_lbl.grid(row=0, column=0, padx=(0, 5))
        
        speed_entry = ctk.CTkEntry(entry_frame, width=80)
        speed_entry.grid(row=0, column=1, padx=5)
        
        # Lactate label and entry
        lactate_lbl = ctk.CTkLabel(entry_frame, text="Lactate (mmol/L):", width=110)
        lactate_lbl.grid(row=0, column=2, padx=(15, 5))
        
        lactate_entry = ctk.CTkEntry(entry_frame, width=80)
        lactate_entry.grid(row=0, column=3, padx=5)
        
        # Remove button
        remove_btn = ctk.CTkButton(
            entry_frame,
            text="✕",
            width=30,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self._remove_lactate_entry(entry_frame)
        )
        remove_btn.grid(row=0, column=4, padx=5)
        
        self.lactate_entries.append({
            'frame': entry_frame,
            'speed': speed_entry,
            'lactate': lactate_entry
        })
    
    def _remove_lactate_entry(self, frame):
        """Remove a lactate measurement row"""
        for i, entry in enumerate(self.lactate_entries):
            if entry['frame'] == frame:
                frame.destroy()
                self.lactate_entries.pop(i)
                break
    
    def _get_lactate_data(self) -> List[Dict]:
        """Get all lactate measurements"""
        measurements = []
        for entry in self.lactate_entries:
            try:
                speed_val = entry['speed'].get().replace(',', '.')
                lactate_val = entry['lactate'].get().replace(',', '.')
                
                if speed_val and lactate_val:
                    measurements.append({
                        'speed': float(speed_val),
                        'lactate_mmol_l': float(lactate_val)
                    })
            except ValueError:
                pass
        return measurements
    
    def _set_lactate_data(self, measurements: List[Dict]):
        """Set lactate measurements from data"""
        # Clear existing entries
        for entry in self.lactate_entries[:]:
            entry['frame'].destroy()
        self.lactate_entries.clear()
        
        # Add new entries
        for m in measurements:
            self._add_lactate_entry()
            idx = len(self.lactate_entries) - 1
            if m.get('speed') is not None:
                self.lactate_entries[idx]['speed'].insert(0, str(m['speed']))
            if m.get('lactate_mmol_l') is not None:
                self.lactate_entries[idx]['lactate'].insert(0, str(m['lactate_mmol_l']))
    
    def _clear_lactate(self):
        """Clear all lactate entries"""
        for entry in self.lactate_entries[:]:
            entry['frame'].destroy()
        self.lactate_entries.clear()
    
    def get_data(self) -> Dict[str, Any]:
        """Get all form data as structured dictionary"""
        data = {}
        
        for key, entry_info in self.entries.items():
            widget = entry_info['widget']
            field_type = entry_info['type']
            
            # Get value based on widget type
            if field_type == 'textbox':
                value = widget.get("1.0", "end-1c")
            elif field_type == 'checkbox':
                value = widget.get()  # Returns 1 or 0
            else:
                value = widget.get()
            
            # Convert type
            if field_type == 'number' and value:
                try:
                    value = float(str(value).replace(',', '.'))
                    if value == int(value):
                        value = int(value)
                except ValueError:
                    value = None
            elif field_type == 'checkbox':
                value = bool(value)  # Convert to boolean
            elif not value:
                value = None
            
            data[key] = value
        
        # Structure the data to match expected format
        return self._structure_data(data, self._get_lactate_data())
    
    def _structure_data(self, flat_data: Dict, lactate_data: List[Dict]) -> Dict[str, Any]:
        """Convert flat form data to nested structure"""
        # has_coach is already boolean from checkbox
        has_coach = flat_data.get('has_coach', False)
        if isinstance(has_coach, str):
            has_coach = has_coach.lower() in ('oui', 'yes', 'true', '1')
        
        return {
            'email': flat_data.get('email', ''),
            'identity': {
                'last_name': flat_data.get('last_name', ''),
                'first_name': flat_data.get('first_name', ''),
                'date_of_birth': flat_data.get('date_of_birth', ''),
                'age': flat_data.get('age'),
                'sport_practiced': flat_data.get('sport_practiced', ''),
                'specialty': flat_data.get('specialty', ''),
                'has_coach': has_coach
            },
            'body_composition': {
                'height_cm': flat_data.get('height_cm'),
                'current_weight': flat_data.get('current_weight'),
                'weight_before_test': flat_data.get('weight_before_test'),
                'weight_after_test': flat_data.get('weight_after_test')
            },
            'professional_life': {
                'job_title': flat_data.get('job_title', ''),
                'working_hours_per_week': flat_data.get('working_hours_per_week')
            },
            'equipment_and_tracking': {
                'watch_brand': flat_data.get('watch_brand', ''),
                'watch_estimated_vo2': flat_data.get('watch_estimated_vo2'),
                'min_hr_before': flat_data.get('min_hr_before'),
                'max_hr_ever': flat_data.get('max_hr_ever'),
                'average_weekly_volume': flat_data.get('average_weekly_volume', ''),
                'watch_race_predictions': {
                    '5k': flat_data.get('prediction_5k', ''),
                    '10k': flat_data.get('prediction_10k', ''),
                    'half_marathon': flat_data.get('prediction_half', ''),
                    'marathon': flat_data.get('prediction_marathon', '')
                }
            },
            'history_and_goals': {
                'personal_records': {
                    '5k': flat_data.get('record_5k', ''),
                    '10k': flat_data.get('record_10k', ''),
                    'half_marathon': flat_data.get('record_half', ''),
                    'marathon': flat_data.get('record_marathon', '')
                },
                'utmb_index': flat_data.get('utmb_index'),
                'upcoming_goals': flat_data.get('upcoming_goals', '')
            },
            'seance_veille': flat_data.get('seance_veille', ''),
            'observations': flat_data.get('observations', ''),
            'protocol_description': flat_data.get('protocol_description', ''),
            'stress_test_results': {
                'thresholds': {
                    'sv1': {
                        'hr_bpm': flat_data.get('sv1_hr'),
                        'pace_km_h': flat_data.get('sv1_speed'),
                        'vo2_ml_kg_min': flat_data.get('sv1_vo2')
                    },
                    'sv2': {
                        'hr_bpm': flat_data.get('sv2_hr'),
                        'pace_km_h': flat_data.get('sv2_speed'),
                        'vo2_ml_kg_min': flat_data.get('sv2_vo2')
                    }
                },
                'measured_vo2max': flat_data.get('measured_vo2max'),
                'max_hr': flat_data.get('max_hr'),
                'first_stage_speed': flat_data.get('first_stage_speed'),
                'last_stage_speed': flat_data.get('last_stage_speed'),
                'lactate_profile': lactate_data
            },
            'conseils_entrainements': flat_data.get('conseils_entrainements', '')
        }
    
    def set_data(self, data: Dict[str, Any]):
        """Set form data from dictionary"""
        # Flatten nested structure
        flat = {}
        flat['email'] = data.get('email', '')
        
        identity = data.get('identity', {})
        flat['last_name'] = identity.get('last_name', '')
        flat['first_name'] = identity.get('first_name', '')
        flat['date_of_birth'] = identity.get('date_of_birth', '')
        flat['age'] = identity.get('age', '')
        flat['sport_practiced'] = identity.get('sport_practiced', '')
        flat['specialty'] = identity.get('specialty', '')
        flat['has_coach'] = identity.get('has_coach', False)  # Boolean for checkbox
        
        body = data.get('body_composition', {})
        flat['height_cm'] = body.get('height_cm', '')
        flat['current_weight'] = body.get('current_weight', '')
        flat['weight_before_test'] = body.get('weight_before_test', '')
        flat['weight_after_test'] = body.get('weight_after_test', '')
        
        prof = data.get('professional_life', {})
        flat['job_title'] = prof.get('job_title', '')
        flat['working_hours_per_week'] = prof.get('working_hours_per_week', '')
        
        equip = data.get('equipment_and_tracking', {})
        flat['watch_brand'] = equip.get('watch_brand', '')
        flat['watch_estimated_vo2'] = equip.get('watch_estimated_vo2', '')
        flat['min_hr_before'] = equip.get('min_hr_before', '')
        flat['max_hr_ever'] = equip.get('max_hr_ever', '')
        flat['average_weekly_volume'] = equip.get('average_weekly_volume', '')
        
        predictions = equip.get('watch_race_predictions', {})
        flat['prediction_5k'] = predictions.get('5k', '')
        flat['prediction_10k'] = predictions.get('10k', '')
        flat['prediction_half'] = predictions.get('half_marathon', '')
        flat['prediction_marathon'] = predictions.get('marathon', '')
        
        history = data.get('history_and_goals', {})
        records = history.get('personal_records', {})
        flat['record_5k'] = records.get('5k', '')
        flat['record_10k'] = records.get('10k', '')
        flat['record_half'] = records.get('half_marathon', '')
        flat['record_marathon'] = records.get('marathon', '')
        flat['utmb_index'] = history.get('utmb_index', '')
        flat['upcoming_goals'] = history.get('upcoming_goals', '')
        
        flat['seance_veille'] = data.get('seance_veille', '')
        flat['observations'] = data.get('observations', '')
        flat['protocol_description'] = data.get('protocol_description', '')
        
        stress = data.get('stress_test_results', {})
        thresholds = stress.get('thresholds', {})
        sv1 = thresholds.get('sv1', {})
        sv2 = thresholds.get('sv2', {})
        flat['sv1_hr'] = sv1.get('hr_bpm', '')
        flat['sv1_speed'] = sv1.get('pace_km_h', '')
        flat['sv1_vo2'] = sv1.get('vo2_ml_kg_min', '')
        flat['sv2_hr'] = sv2.get('hr_bpm', '')
        flat['sv2_speed'] = sv2.get('pace_km_h', '')
        flat['sv2_vo2'] = sv2.get('vo2_ml_kg_min', '')
        flat['measured_vo2max'] = stress.get('measured_vo2max', '')
        flat['max_hr'] = stress.get('max_hr', '')
        flat['first_stage_speed'] = stress.get('first_stage_speed', '')
        flat['last_stage_speed'] = stress.get('last_stage_speed', '')
        
        flat['conseils_entrainements'] = data.get('conseils_entrainements', '')
        
        # Set values
        for key, value in flat.items():
            if key in self.entries:
                entry_info = self.entries[key]
                widget = entry_info['widget']
                
                if entry_info['type'] == 'textbox':
                    widget.delete("1.0", "end")
                    if value:
                        widget.insert("1.0", str(value))
                elif entry_info['type'] == 'checkbox':
                    if value:
                        widget.select()
                    else:
                        widget.deselect()
                else:
                    widget.delete(0, "end")
                    if value is not None and value != '':
                        widget.insert(0, str(value))
        
        # Set lactate data
        lactate_data = data.get('stress_test_results', {}).get('lactate_profile', [])
        self._set_lactate_data(lactate_data)
    
    def clear(self):
        """Clear all form fields"""
        for entry_info in self.entries.values():
            widget = entry_info['widget']
            if entry_info['type'] == 'textbox':
                widget.delete("1.0", "end")
            elif entry_info['type'] == 'checkbox':
                widget.deselect()
            else:
                widget.delete(0, "end")
        
        # Clear lactate entries
        self._clear_lactate()


class TCPDataProcessor(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Set window icon
        self._set_icon()
        
        # Data
        self.source_folder = ""
        self.tests: List[Dict] = []
        self.test_items: List[TestListItem] = []
        self.selected_item: Optional[TestListItem] = None
        self.test_manual_data: Dict[str, Dict] = {}  # filename -> manual data
        
        # Components
        self.parser = TCPXmlParser()
        self.transformer = DataTransformer()
        self.exporter = JsonExporter()
        
        self._create_ui()
    
    def _set_icon(self):
        """Set window icon from Enduraw logo"""
        try:
            # Try ico file first (for windows)
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
            else:
                # Try the logo jpg as fallback
                logo_path = Path(__file__).parent.parent / "endurawLogoBlack.jpg"
                if logo_path.exists():
                    from PIL import Image, ImageTk
                    img = Image.open(logo_path)
                    img = img.resize((64, 64))
                    photo = ImageTk.PhotoImage(img)
                    self.iconphoto(True, photo)
                    self._icon_photo = photo  # Keep reference
        except Exception:
            pass  # Silently ignore if icon fails
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Left panel - Test list
        self._create_test_list_panel()
        
        # Right panel - Input form
        self._create_form_panel()
        
        # Footer with actions
        self._create_footer()
    
    def _create_header(self):
        """Create header with folder selection"""
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)
        
        # Label
        label = ctk.CTkLabel(
            header, 
            text="Dossier source:",
            font=ctk.CTkFont(size=13)
        )
        label.grid(row=0, column=0, padx=15, pady=15)
        
        # Path entry
        self.folder_entry = ctk.CTkEntry(header, placeholder_text="Sélectionnez un dossier contenant les fichiers XML...")
        self.folder_entry.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        
        # Browse button
        browse_btn = ctk.CTkButton(
            header,
            text="Parcourir...",
            width=100,
            command=self._browse_folder
        )
        browse_btn.grid(row=0, column=2, padx=15, pady=15)
    
    def _create_test_list_panel(self):
        """Create left panel with test list"""
        panel = ctk.CTkFrame(self, width=300)
        panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_propagate(False)
        
        # Header
        header = ctk.CTkLabel(
            panel,
            text="Tests Trouvés",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Count label
        self.count_label = ctk.CTkLabel(
            panel,
            text="(0)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.count_label.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # Scrollable list
        self.test_list = ctk.CTkScrollableFrame(panel)
        self.test_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.test_list.grid_columnconfigure(0, weight=1)
    
    def _create_form_panel(self):
        """Create right panel with input form"""
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        
        # Header with athlete name
        header_frame = ctk.CTkFrame(panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.athlete_label = ctk.CTkLabel(
            header_frame,
            text="Sélectionnez un test",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.athlete_label.grid(row=0, column=0, sticky="w")
        
        # Apply to all button
        self.apply_all_btn = ctk.CTkButton(
            header_frame,
            text="Appliquer à tous ▼",
            width=140,
            command=self._show_apply_menu,
            state="disabled"
        )
        self.apply_all_btn.grid(row=0, column=1, padx=5)
        
        # Form
        self.form = InputForm(panel)
        self.form.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Save button
        self.save_form_btn = ctk.CTkButton(
            panel,
            text="Enregistrer les données",
            command=self._save_current_form,
            state="disabled"
        )
        self.save_form_btn.grid(row=2, column=0, padx=15, pady=10)
    
    def _create_footer(self):
        """Create footer with export buttons"""
        footer = ctk.CTkFrame(self, height=60, corner_radius=0)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        
        # Button frame (right aligned)
        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=15, pady=10)
        
        # Output folder button
        self.output_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Dossier Output",
            width=130,
            fg_color="gray40",
            hover_color="gray50",
            command=self._open_output_folder
        )
        self.output_btn.grid(row=0, column=0, padx=5)
        
        # Export selected
        self.export_selected_btn = ctk.CTkButton(
            btn_frame,
            text="Exporter Sélectionné",
            width=150,
            command=self._export_selected,
            state="disabled"
        )
        self.export_selected_btn.grid(row=0, column=1, padx=5)
        
        # Export all
        self.export_all_btn = ctk.CTkButton(
            btn_frame,
            text="Exporter Tous",
            width=120,
            fg_color="green",
            hover_color="darkgreen",
            command=self._export_all,
            state="disabled"
        )
        self.export_all_btn.grid(row=0, column=2, padx=5)
    
    def _browse_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier contenant les fichiers XML")
        if folder:
            self.source_folder = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            
            # Set output folder relative to source
            self.exporter.output_dir = os.path.join(folder, "Output")
            
            self._load_tests()
    
    def _load_tests(self):
        """Load tests from selected folder"""
        # Clear existing
        for item in self.test_items:
            item.destroy()
        self.test_items.clear()
        self.tests.clear()
        
        # Load tests
        try:
            self.tests = get_available_tests(self.source_folder)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
            return
        
        # Update count
        self.count_label.configure(text=f"({len(self.tests)})")
        
        # Create list items
        for test_info in self.tests:
            item = TestListItem(
                self.test_list,
                test_info,
                on_select=self._on_test_select
            )
            item.grid(sticky="ew", pady=2)
            self.test_items.append(item)
            
            # Check if we have saved data
            filename = test_info.get('filename', '')
            if filename in self.test_manual_data:
                item.set_has_data(True)
        
        # Enable/disable buttons
        if self.tests:
            self.export_all_btn.configure(state="normal")
    
    def _on_test_select(self, item: TestListItem):
        """Handle test selection"""
        # Deselect previous
        if self.selected_item:
            # Save current form data first
            self._save_current_form(silent=True)
            self.selected_item.set_selected(False)
        
        # Select new
        self.selected_item = item
        item.set_selected(True)
        
        # Update UI
        test_info = item.test_info
        name = f"{test_info.get('last_name', '')} {test_info.get('first_name', '')}"
        date = test_info.get('date', '')
        self.athlete_label.configure(text=f"{name} - {date}")
        
        # Load form data if exists
        filename = test_info.get('filename', '')
        if filename in self.test_manual_data:
            self.form.set_data(self.test_manual_data[filename])
        else:
            self.form.clear()
        
        # Enable buttons
        self.save_form_btn.configure(state="normal")
        self.export_selected_btn.configure(state="normal")
        self.apply_all_btn.configure(state="normal")
    
    def _save_current_form(self, silent: bool = False):
        """Save current form data"""
        if not self.selected_item:
            return
        
        filename = self.selected_item.test_info.get('filename', '')
        data = self.form.get_data()
        self.test_manual_data[filename] = data
        self.selected_item.set_has_data(True)
        
        if not silent:
            # Brief visual feedback
            self.save_form_btn.configure(text="✓ Enregistré")
            self.after(1500, lambda: self.save_form_btn.configure(text="Enregistrer les données"))
    
    def _show_apply_menu(self):
        """Show menu for apply to all options"""
        if not self.selected_item:
            return
        
        menu = ctk.CTkToplevel(self)
        menu.title("Appliquer à tous")
        menu.geometry("350x250")
        menu.transient(self)
        menu.grab_set()
        
        label = ctk.CTkLabel(
            menu,
            text="Sélectionnez les champs à appliquer à tous les tests:",
            font=ctk.CTkFont(weight="bold")
        )
        label.pack(pady=15)
        
        # Only these 3 fields can be applied to all
        fields = [
            ('has_coach', "A un coach"),
            ('watch_brand', "Marque de montre"),
            ('protocol_description', "Description du test")
        ]
        
        field_vars = {}
        for key, label_text in fields:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(menu, text=label_text, variable=var)
            cb.pack(pady=8, padx=30, anchor="w")
            field_vars[key] = var
        
        def apply():
            current_data = self.form.get_data()
            selected_fields = [k for k, v in field_vars.items() if v.get()]
            
            if not selected_fields:
                messagebox.showwarning("Attention", "Sélectionnez au moins un champ")
                return
            
            for item in self.test_items:
                filename = item.test_info.get('filename', '')
                if filename not in self.test_manual_data:
                    self.test_manual_data[filename] = {}
                
                existing = self.test_manual_data[filename]
                
                for field in selected_fields:
                    if field == 'has_coach':
                        if 'identity' not in existing:
                            existing['identity'] = {}
                        existing['identity']['has_coach'] = current_data.get('identity', {}).get('has_coach', False)
                    elif field == 'watch_brand':
                        if 'equipment_and_tracking' not in existing:
                            existing['equipment_and_tracking'] = {}
                        existing['equipment_and_tracking']['watch_brand'] = current_data.get('equipment_and_tracking', {}).get('watch_brand', '')
                    elif field == 'protocol_description':
                        existing['protocol_description'] = current_data.get('protocol_description', '')
                
                item.set_has_data(True)
            
            menu.destroy()
            messagebox.showinfo("Succès", f"Champs appliqués à {len(self.test_items)} tests")
        
        apply_btn = ctk.CTkButton(menu, text="Appliquer", command=apply)
        apply_btn.pack(pady=20)
    
    def _export_selected(self):
        """Export selected test to JSON"""
        if not self.selected_item:
            return
        
        # Save current form first
        self._save_current_form(silent=True)
        
        test_info = self.selected_item.test_info
        filepath = test_info.get('filepath', '')
        filename = test_info.get('filename', '')
        
        try:
            # Parse XML
            xml_data = self.parser.parse_file(filepath)
            
            # Get manual data
            manual_data = self.test_manual_data.get(filename, {})
            
            # Validate email
            if not manual_data.get('email'):
                messagebox.showwarning("Attention", "L'email (ID utilisateur) est requis")
                return
            
            # Transform
            output_data = self.transformer.transform(xml_data, manual_data)
            
            # Validate
            validation = self.exporter.validate_structure(output_data)
            if not validation['valid']:
                messagebox.showerror("Erreur de validation", "\n".join(validation['errors']))
                return
            
            if validation['warnings']:
                print("Avertissements:", validation['warnings'])
            
            # Export
            output_path = self.exporter.export(output_data)
            
            messagebox.showinfo("Succès", f"Fichier exporté:\n{output_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")
    
    def _export_all(self):
        """Export all tests with data"""
        # Save current form first
        if self.selected_item:
            self._save_current_form(silent=True)
        
        # Check which tests have email
        valid_tests = []
        for item in self.test_items:
            filename = item.test_info.get('filename', '')
            manual_data = self.test_manual_data.get(filename, {})
            if manual_data.get('email'):
                valid_tests.append((item.test_info, manual_data))
        
        if not valid_tests:
            messagebox.showwarning(
                "Attention", 
                "Aucun test avec email valide.\nVeuillez renseigner l'email pour au moins un test."
            )
            return
        
        # Confirm
        if not messagebox.askyesno(
            "Confirmation",
            f"Exporter {len(valid_tests)} test(s) ?"
        ):
            return
        
        # Export
        success = 0
        errors = []
        
        for test_info, manual_data in valid_tests:
            try:
                filepath = test_info.get('filepath', '')
                xml_data = self.parser.parse_file(filepath)
                output_data = self.transformer.transform(xml_data, manual_data)
                self.exporter.export(output_data)
                success += 1
            except Exception as e:
                errors.append(f"{test_info.get('filename', 'Unknown')}: {e}")
        
        # Report
        msg = f"Export terminé: {success}/{len(valid_tests)} fichiers"
        if errors:
            msg += f"\n\nErreurs:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... et {len(errors) - 5} autres erreurs"
        
        messagebox.showinfo("Résultat", msg)
    
    def _open_output_folder(self):
        """Open output folder in file explorer"""
        output_dir = self.exporter.output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Open folder
        if sys.platform == 'win32':
            os.startfile(output_dir)
        elif sys.platform == 'darwin':
            os.system(f'open "{output_dir}"')
        else:
            os.system(f'xdg-open "{output_dir}"')


def main():
    """Entry point"""
    app = TCPDataProcessor()
    app.mainloop()


if __name__ == "__main__":
    main()
