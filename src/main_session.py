"""
TCP Data Processor - Session-Based Main Application
Tab-based UI with Sessions, Profiles, and XML Matching
"""
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.xml_parser import TCPXmlParser
from core.data_transformer import DataTransformer
from utils.json_exporter import JsonExporter
from core.session_manager import SessionManager
from ui.app_tabs import SessionListItem, ProfileListItem, XmlListItem, MatchListItem
from config import APP_NAME, APP_VERSION

# Import InputForm from original main.py
from main import InputForm

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SessionTab(ctk.CTkFrame):
    """Tab for managing sessions"""
    
    def __init__(self, master, session_manager: SessionManager, on_session_loaded=None, **kwargs):
        super().__init__(master, **kwargs)
        self.session_manager = session_manager
        self.on_session_loaded = on_session_loaded
        self.session_items: List[SessionListItem] = []
        self.selected_item: Optional[SessionListItem] = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_ui()
        self._refresh_sessions()
    
    def _create_ui(self):
        # Header with buttons
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(header, text="Sessions", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, sticky="w")
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2)
        
        self.new_btn = ctk.CTkButton(btn_frame, text="+ Nouvelle Session", command=self._new_session)
        self.new_btn.grid(row=0, column=0, padx=5)
        
        self.open_btn = ctk.CTkButton(btn_frame, text="Ouvrir", command=self._open_session, state="disabled")
        self.open_btn.grid(row=0, column=1, padx=5)
        
        self.delete_btn = ctk.CTkButton(btn_frame, text="Supprimer", fg_color="red", 
                                        hover_color="darkred", command=self._delete_session, state="disabled")
        self.delete_btn.grid(row=0, column=2, padx=5)
        
        # Session list
        self.session_list = ctk.CTkScrollableFrame(self)
        self.session_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.session_list.grid_columnconfigure(0, weight=1)
        
        # Current session info
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.session_label = ctk.CTkLabel(self.info_frame, text="Aucune session active",
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.session_label.grid(row=0, column=0, padx=15, pady=10)
    
    def _refresh_sessions(self):
        for item in self.session_items:
            item.destroy()
        self.session_items.clear()
        self.selected_item = None
        
        sessions = self.session_manager.list_sessions()
        for session_info in sessions:
            item = SessionListItem(self.session_list, session_info, on_select=self._on_select)
            item.grid(sticky="ew", pady=2)
            self.session_items.append(item)
        
        self._update_buttons()
        self._update_current_session_info()
    
    def _on_select(self, item: SessionListItem):
        if self.selected_item:
            self.selected_item.set_selected(False)
        self.selected_item = item
        item.set_selected(True)
        self._update_buttons()
    
    def _update_buttons(self):
        state = "normal" if self.selected_item else "disabled"
        self.open_btn.configure(state=state)
        self.delete_btn.configure(state=state)
    
    def _update_current_session_info(self):
        if self.session_manager.current_session:
            s = self.session_manager.current_session
            self.session_label.configure(text=f"Session active: {s.name} ({s.location})")
        else:
            self.session_label.configure(text="Aucune session active")
    
    def _new_session(self):
        dialog = NewSessionDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            try:
                self.session_manager.create_session(
                    date=dialog.result['date'],
                    location=dialog.result['location'],
                    description=dialog.result.get('description', '')
                )
                self._refresh_sessions()
                if self.on_session_loaded:
                    self.on_session_loaded()
                messagebox.showinfo("Succès", "Session créée avec succès!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création: {e}")
    
    def _open_session(self):
        if not self.selected_item:
            return
        try:
            path = self.selected_item.session_info.get('path', '')
            self.session_manager.load_session(path)
            self._update_current_session_info()
            if self.on_session_loaded:
                self.on_session_loaded()
            messagebox.showinfo("Succès", "Session chargée!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")
    
    def _delete_session(self):
        if not self.selected_item:
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cette session et tout son contenu?"):
            return
        try:
            path = self.selected_item.session_info.get('path', '')
            self.session_manager.delete_session(path)
            self._refresh_sessions()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")


class NewSessionDialog(ctk.CTkToplevel):
    """Dialog for creating a new session"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        
        self.title("Nouvelle Session")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()
        
        # Form
        ctk.CTkLabel(self, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.date_entry = ctk.CTkEntry(self, width=200)
        self.date_entry.grid(row=0, column=1, padx=20, pady=10)
        
        from datetime import datetime
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ctk.CTkLabel(self, text="Lieu:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.location_entry = ctk.CTkEntry(self, width=200)
        self.location_entry.grid(row=1, column=1, padx=20, pady=10)
        
        ctk.CTkLabel(self, text="Description:").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.desc_entry = ctk.CTkEntry(self, width=200)
        self.desc_entry.grid(row=2, column=1, padx=20, pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(btn_frame, text="Créer", command=self._create).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Annuler", fg_color="gray", command=self.destroy).grid(row=0, column=1, padx=10)
    
    def _create(self):
        date = self.date_entry.get().strip()
        location = self.location_entry.get().strip()
        
        if not date or not location:
            messagebox.showwarning("Attention", "Date et lieu sont requis")
            return
        
        self.result = {
            'date': date,
            'location': location,
            'description': self.desc_entry.get().strip()
        }
        self.destroy()


class ProfileTab(ctk.CTkFrame):
    """Tab for managing profiles"""
    
    def __init__(self, master, session_manager: SessionManager, **kwargs):
        super().__init__(master, **kwargs)
        self.session_manager = session_manager
        self.profile_items: List[ProfileListItem] = []
        self.selected_item: Optional[ProfileListItem] = None
        self.current_filename: Optional[str] = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_ui()
    
    def _create_ui(self):
        # Left panel - profile list
        left_panel = ctk.CTkFrame(self, width=280)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_propagate(False)
        
        # Header
        header = ctk.CTkFrame(left_panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(header, text="Profils", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0)
        
        self.new_btn = ctk.CTkButton(header, text="+", width=30, command=self._new_profile)
        self.new_btn.grid(row=0, column=1, padx=5)
        
        self.delete_btn = ctk.CTkButton(header, text="🗑", width=30, fg_color="red", 
                                        command=self._delete_profile, state="disabled")
        self.delete_btn.grid(row=0, column=2)
        
        # List
        self.profile_list = ctk.CTkScrollableFrame(left_panel)
        self.profile_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.profile_list.grid_columnconfigure(0, weight=1)
        
        # Right panel - form
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)
        
        # Form header
        form_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        form_header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        form_header.grid_columnconfigure(0, weight=1)
        
        self.form_title = ctk.CTkLabel(form_header, text="Sélectionnez un profil",
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.form_title.grid(row=0, column=0, sticky="w")
        
        self.save_btn = ctk.CTkButton(form_header, text="Sauvegarder", command=self._save_profile, state="disabled")
        self.save_btn.grid(row=0, column=1)
        
        # Form
        self.form = InputForm(right_panel)
        self.form.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    
    def refresh(self):
        """Refresh profile list"""
        for item in self.profile_items:
            item.destroy()
        self.profile_items.clear()
        self.selected_item = None
        self.current_filename = None
        
        if not self.session_manager.current_session:
            self.form_title.configure(text="Aucune session active")
            return
        
        profiles = self.session_manager.list_profiles()
        for profile_info in profiles:
            # Check if matched
            match = self.session_manager.get_match_for_profile(profile_info['filename'])
            item = ProfileListItem(self.profile_list, profile_info, on_select=self._on_select)
            item.set_matched(match is not None)
            item.grid(sticky="ew", pady=2)
            self.profile_items.append(item)
        
        self.form.clear()
        self.form_title.configure(text="Sélectionnez un profil")
        self._update_buttons()
    
    def _on_select(self, item: ProfileListItem):
        # Deselect previous item (only if widget still exists)
        if self.selected_item:
            try:
                if self.selected_item.winfo_exists():
                    self.selected_item.set_selected(False)
            except Exception:
                pass  # Widget was destroyed, ignore
        
        self.selected_item = item
        self.current_filename = item.profile_info.get('filename')
        
        # Check if clicked item still exists
        try:
            if not item.winfo_exists():
                return
            item.set_selected(True)
        except Exception:
            return
        
        # Load profile data
        data = self.session_manager.get_profile(self.current_filename)
        if data:
            self.form.set_data(data)
            # Safely get name (handle None values)
            identity = data.get('identity') or {}
            last_name = (identity.get('last_name') or '').strip()
            first_name = (identity.get('first_name') or '').strip()
            name = f"{last_name} {first_name}".strip()
            self.form_title.configure(text=name or "Nouveau profil")
        else:
            self.form.clear()
            self.form_title.configure(text="Profil non trouvé")
        
        self._update_buttons()
    
    def _update_buttons(self):
        state = "normal" if self.selected_item else "disabled"
        self.save_btn.configure(state=state)
        self.delete_btn.configure(state=state)
    
    def _new_profile(self):
        if not self.session_manager.current_session:
            messagebox.showwarning("Attention", "Veuillez d'abord ouvrir une session")
            return
        
        # Save current first
        if self.current_filename:
            self._save_profile(silent=True)
        
        from core.profile_template import get_empty_profile
        empty = get_empty_profile()
        
        try:
            filename = self.session_manager.add_profile(empty)
            self.refresh()
            
            # Select the new profile
            for item in self.profile_items:
                if item.profile_info.get('filename') == filename:
                    self._on_select(item)
                    break
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")
    
    def _save_profile(self, silent=False):
        if not self.current_filename:
            return
        
        # Check if file still exists (might have been deleted)
        profile_exists = self.session_manager.get_profile(self.current_filename) is not None
        if not profile_exists:
            if not silent:
                messagebox.showwarning("Attention", "Ce profil n'existe plus. Rafraîchissement...")
            self.current_filename = None
            self.refresh()
            return
        
        data = self.form.get_data()
        try:
            # update_profile now returns new filename (may be renamed)
            new_filename = self.session_manager.update_profile(self.current_filename, data)
            if new_filename:
                # Update current filename if it was renamed
                self.current_filename = new_filename
                
                if not silent:
                    self.save_btn.configure(text="Sauvegardé")
                    self.after(1500, lambda: self.save_btn.configure(text="Sauvegarder"))
                    
                    # Update the form title with the new name
                    identity = data.get('identity') or {}
                    last_name = (identity.get('last_name') or '').strip()
                    first_name = (identity.get('first_name') or '').strip()
                    name = f"{last_name} {first_name}".strip()
                    self.form_title.configure(text=name or "Nouveau profil")
                    
                    # Only refresh the profile list on explicit save (not silent)
                    # to avoid destroying widgets during click handlers
                    self._refresh_profile_list()
            elif not silent:
                messagebox.showerror("Erreur", "Impossible de sauvegarder le profil")
        except Exception as e:
            if not silent:
                messagebox.showerror("Erreur", f"Erreur: {e}")
    
    def _refresh_profile_list(self):
        """Refresh profile list while keeping current selection"""
        saved_filename = self.current_filename
        
        # Clear and rebuild list
        for item in self.profile_items:
            item.destroy()
        self.profile_items.clear()
        
        if not self.session_manager.current_session:
            return
        
        profiles = self.session_manager.list_profiles()
        for profile_info in profiles:
            match = self.session_manager.get_match_for_profile(profile_info['filename'])
            item = ProfileListItem(self.profile_list, profile_info, on_select=self._on_select)
            item.set_matched(match is not None)
            item.grid(sticky="ew", pady=2)
            self.profile_items.append(item)
            
            # Re-select the previously selected item
            if profile_info.get('filename') == saved_filename:
                self.selected_item = item
                item.set_selected(True)
    
    def _delete_profile(self):
        if not self.current_filename:
            return
        if not messagebox.askyesno("Confirmer", "Supprimer ce profil?"):
            return
        
        self.session_manager.delete_profile(self.current_filename)
        self.current_filename = None
        self.refresh()


class XmlMatchTab(ctk.CTkFrame):
    """Tab for matching XMLs with profiles"""
    
    def __init__(self, master, session_manager: SessionManager, **kwargs):
        super().__init__(master, **kwargs)
        self.session_manager = session_manager
        self.parser = TCPXmlParser()
        self.transformer = DataTransformer()
        self.exporter = JsonExporter()
        
        self.xml_items: List[XmlListItem] = []
        self.profile_items: List[ProfileListItem] = []
        self.match_items: List[MatchListItem] = []
        
        self.selected_xml: Optional[XmlListItem] = None
        self.selected_profile: Optional[ProfileListItem] = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_ui()
    
    def _create_ui(self):
        # === LEFT: XMLs ===
        xml_panel = ctk.CTkFrame(self)
        xml_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=10)
        xml_panel.grid_rowconfigure(1, weight=1)
        xml_panel.grid_columnconfigure(0, weight=1)
        
        # XML header
        xml_header = ctk.CTkFrame(xml_panel, fg_color="transparent")
        xml_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(xml_header, text="Fichiers XML", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0)
        ctk.CTkButton(xml_header, text="Importer", width=80, command=self._import_xmls).grid(row=0, column=1, padx=5)
        
        self.xml_list = ctk.CTkScrollableFrame(xml_panel)
        self.xml_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.xml_list.grid_columnconfigure(0, weight=1)
        
        # === CENTER: Actions ===
        center_panel = ctk.CTkFrame(self, fg_color="transparent")
        center_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=10)
        center_panel.grid_rowconfigure(0, weight=1)
        
        action_frame = ctk.CTkFrame(center_panel)
        action_frame.place(relx=0.5, rely=0.3, anchor="center")
        
        self.match_btn = ctk.CTkButton(action_frame, text="Matcher", width=120, height=40,
                                       font=ctk.CTkFont(size=14), command=self._create_match, state="disabled")
        self.match_btn.grid(row=0, column=0, pady=10)
        
        ctk.CTkLabel(action_frame, text="Sélectionnez un XML\net un profil", 
                    text_color="gray", justify="center").grid(row=1, column=0)
        
        # === RIGHT: Profiles ===
        profile_panel = ctk.CTkFrame(self)
        profile_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=10)
        profile_panel.grid_rowconfigure(1, weight=1)
        profile_panel.grid_columnconfigure(0, weight=1)
        
        # Profile header
        profile_header = ctk.CTkFrame(profile_panel, fg_color="transparent")
        profile_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(profile_header, text="Profils", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0)
        ctk.CTkButton(profile_header, text="Refresh", width=60, command=self.refresh).grid(row=0, column=1, padx=5)
        
        self.profile_list = ctk.CTkScrollableFrame(profile_panel)
        self.profile_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.profile_list.grid_columnconfigure(0, weight=1)
        
        # === BOTTOM: Matches ===
        match_panel = ctk.CTkFrame(self)
        match_panel.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        match_panel.grid_columnconfigure(0, weight=1)
        match_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(match_panel, text="Associations", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.match_list = ctk.CTkScrollableFrame(match_panel, height=150)
        self.match_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.match_list.grid_columnconfigure(0, weight=1)
    
    def refresh(self):
        """Refresh all lists"""
        self._refresh_xmls()
        self._refresh_profiles()
        self._refresh_matches()
    
    def _refresh_xmls(self):
        for item in self.xml_items:
            item.destroy()
        self.xml_items.clear()
        self.selected_xml = None
        
        if not self.session_manager.current_session:
            return
        
        xmls = self.session_manager.list_xmls()
        for xml_info in xmls:
            match = self.session_manager.get_match_for_xml(xml_info['filename'])
            item = XmlListItem(self.xml_list, xml_info, on_select=self._on_xml_select)
            item.set_matched(match is not None)
            item.grid(sticky="ew", pady=2)
            self.xml_items.append(item)
    
    def _refresh_profiles(self):
        for item in self.profile_items:
            item.destroy()
        self.profile_items.clear()
        self.selected_profile = None
        
        if not self.session_manager.current_session:
            return
        
        profiles = self.session_manager.list_profiles()
        for profile_info in profiles:
            match = self.session_manager.get_match_for_profile(profile_info['filename'])
            item = ProfileListItem(self.profile_list, profile_info, on_select=self._on_profile_select)
            item.set_matched(match is not None)
            item.grid(sticky="ew", pady=2)
            self.profile_items.append(item)
    
    def _refresh_matches(self):
        for item in self.match_items:
            item.destroy()
        self.match_items.clear()
        
        if not self.session_manager.current_session:
            return
        
        for match in self.session_manager.matches:
            item = MatchListItem(self.match_list, match.to_dict(),
                               on_export=self._export_match, on_remove=self._remove_match)
            item.grid(sticky="ew", pady=2)
            self.match_items.append(item)
    
    def _on_xml_select(self, item: XmlListItem):
        if self.selected_xml:
            self.selected_xml.set_selected(False)
        self.selected_xml = item
        item.set_selected(True)
        self._update_match_button()
    
    def _on_profile_select(self, item: ProfileListItem):
        if self.selected_profile:
            self.selected_profile.set_selected(False)
        self.selected_profile = item
        item.set_selected(True)
        self._update_match_button()
    
    def _update_match_button(self):
        if self.selected_xml and self.selected_profile:
            self.match_btn.configure(state="normal")
        else:
            self.match_btn.configure(state="disabled")
    
    def _import_xmls(self):
        if not self.session_manager.current_session:
            messagebox.showwarning("Attention", "Veuillez d'abord ouvrir une session")
            return
        
        # Ask user to choose import method
        choice = messagebox.askyesnocancel(
            "Import XML",
            "Voulez-vous importer un dossier entier ?\n\nOui = Dossier\nNon = Fichiers individuels"
        )
        
        if choice is None:  # Cancel
            return
        
        files_to_import = []
        
        if choice:  # Yes = folder
            folder = filedialog.askdirectory(title="Sélectionner un dossier contenant des XMLs")
            if folder:
                from pathlib import Path
                folder_path = Path(folder)
                files_to_import = list(folder_path.glob("*.xml"))
        else:  # No = individual files
            files = filedialog.askopenfilenames(
                title="Sélectionner des fichiers XML",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
            )
            files_to_import = list(files) if files else []
        
        if not files_to_import:
            return
        
        imported = 0
        for filepath in files_to_import:
            try:
                self.session_manager.import_xml(str(filepath))
                imported += 1
            except Exception as e:
                print(f"Error importing {filepath}: {e}")
        
        self._refresh_xmls()
        messagebox.showinfo("Succès", f"{imported} fichier(s) importé(s)")
    
    def _create_match(self):
        if not self.selected_xml or not self.selected_profile:
            return
        
        xml_filename = self.selected_xml.xml_info.get('filename', '')
        profile_filename = self.selected_profile.profile_info.get('filename', '')
        
        self.session_manager.create_match(profile_filename, xml_filename)
        self.refresh()
    
    def _remove_match(self, match_info: Dict):
        profile_name = match_info.get('profile_name', '')
        self.session_manager.remove_match(profile_name)
        self.refresh()
    
    def _export_match(self, match_info: Dict):
        profile_name = match_info.get('profile_name', '')
        xml_filename = match_info.get('xml_filename', '')
        
        try:
            # Get profile data
            profile_data = self.session_manager.get_profile(profile_name)
            if not profile_data:
                messagebox.showerror("Erreur", "Profil non trouvé")
                return
            
            if not profile_data.get('email'):
                messagebox.showwarning("Attention", "L'email est requis dans le profil")
                return
            
            # Parse XML
            xml_path = self.session_manager.get_xml_path(xml_filename)
            xml_data = self.parser.parse_file(xml_path)
            
            # Transform using existing transformer
            output = self.transformer.transform(xml_data, profile_data)
            
            # Generate output filename
            identity = profile_data.get('identity', {})
            name = f"{identity.get('last_name', 'Unknown')}_{identity.get('first_name', '')}".strip('_')
            date = self.session_manager.current_session.date
            output_filename = f"{name}_{date}.json"
            
            # Save to session output folder
            output_path = self.session_manager.save_output(output_filename, output)
            
            # Mark as exported
            self.session_manager.mark_as_exported(profile_name)
            self._refresh_matches()
            
            messagebox.showinfo("Succès", f"Exporté vers:\n{output_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")


class TCPDataProcessorSession(ctk.CTk):
    """Main application with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        
        self.title(f"{APP_NAME} v{APP_VERSION} - Session Mode")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Get base path (where the app is running)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.session_manager = SessionManager(os.path.dirname(base_path))
        
        self._set_icon()
        self._create_ui()
    
    def _set_icon(self):
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass
    
    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, height=50, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(header, text=f"{APP_NAME}", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=10)
        
        self.session_info = ctk.CTkLabel(header, text="Aucune session active", text_color="gray")
        self.session_info.grid(row=0, column=1, padx=20, pady=10)
        
        # Theme switch
        self.theme_btn = ctk.CTkButton(
            header, text="Light Mode", width=100,
            command=self._toggle_theme
        )
        self.theme_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Tab view
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self.tabview.add("Sessions")
        self.tabview.add("Profils")
        self.tabview.add("XML Matching")
        
        # Session tab
        self.session_tab = SessionTab(
            self.tabview.tab("Sessions"),
            self.session_manager,
            on_session_loaded=self._on_session_loaded
        )
        self.session_tab.pack(fill="both", expand=True)
        
        # Profile tab
        self.profile_tab = ProfileTab(
            self.tabview.tab("Profils"),
            self.session_manager
        )
        self.profile_tab.pack(fill="both", expand=True)
        
        # XML Match tab
        self.match_tab = XmlMatchTab(
            self.tabview.tab("XML Matching"),
            self.session_manager
        )
        self.match_tab.pack(fill="both", expand=True)
    
    def _on_session_loaded(self):
        """Called when a session is loaded or created"""
        if self.session_manager.current_session:
            s = self.session_manager.current_session
            self.session_info.configure(text=f"Session: {s.name}")
            
            # Switch to Profils tab automatically
            self.tabview.set("Profils")
        else:
            self.session_info.configure(text="Aucune session active")
        
        # Refresh other tabs
        self.profile_tab.refresh()
        self.match_tab.refresh()
    
    def _toggle_theme(self):
        """Toggle between dark and light mode"""
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="Light Mode")


def main():
    """Entry point"""
    app = TCPDataProcessorSession()
    app.mainloop()


if __name__ == "__main__":
    main()

