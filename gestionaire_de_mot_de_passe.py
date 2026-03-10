import json
import os
import hashlib
import secrets
import string
import requests
import pyperclip
import customtkinter as ctk
from tkinter import messagebox
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid
import pyotp
import tempfile

# --- CONFIGURATION SÉCURITÉ ---
DATA_FILE = "vault.json"
SALT_FILE = "salt.bin"
PBKDF2_ITERATIONS = 600000

class CryptoEngine:
    def __init__(self, password, salt=None):
        self.salt = salt if salt else os.urandom(16)
        self.key = self._derive_key(password, self.salt)
        self.fernet = Fernet(self.key)

    def _derive_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt(self, data):
        return self.fernet.encrypt(json.dumps(data).encode()).decode()

    def decrypt(self, token):
        return json.loads(self.fernet.decrypt(token.encode()).decode())

# --- Main --- #

class ShieldPassApp(ctk.CTk):
    def __init__(self, crypto_engine, vault_data):
        super().__init__()
        self.crypto = crypto_engine
        self.vault = vault_data
        
        self.title("ShieldPass Premium v4.1 - Ultra Secure")
        self.geometry("1400x800")
        ctk.set_appearance_mode("dark")
        
        self.card_color = "#242731"
        self.accent_color = "#3d5afe"
        self.totp_labels = {} 

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.show_dashboard()
        self.update_totp_codes()

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🛡 SHIELDPASS", font=("Roboto", 24, "bold"), text_color=self.accent_color).pack(pady=40)
        ctk.CTkButton(self.sidebar, text="🏠 Dashboard", command=self.show_dashboard).pack(pady=10, padx=20)
        ctk.CTkButton(self.sidebar, text="➕ Ajouter", fg_color="#2ecc71", hover_color="#27ae60", command=self.add_entry_window).pack(pady=10, padx=20)
        ctk.CTkLabel(self.sidebar, text="").pack(expand=True)
        ctk.CTkButton(self.sidebar, text="⚙️ Sécurité", command=self.change_master_password_ui).pack(pady=20, padx=20)

        self.main_view = ctk.CTkScrollableFrame(self, fg_color="transparent", border_width=0)
        self.main_view.grid(row=0, column=1, padx=30, pady=20, sticky="nsew")

    # --- SÉCURITÉ : GESTION DU PRESSE-PAPIERS ---
    def copy_to_clipboard(self, text):
        """Copie le texte et le supprime après 30 secondes."""
        pyperclip.copy(text)
        self.after(30000, lambda: self.clear_clipboard_if_matching(text))

    def clear_clipboard_if_matching(self, original_text):
        """Efface le presse-papiers seulement s'il contient encore le MDP."""
        try:
            if pyperclip.paste() == original_text:
                pyperclip.copy("")
        except: pass

    # --- SÉCURITÉ : SAUVEGARDE ATOMIQUE ---
    def save_vault(self):
        """Sauvegarde sécurisée : écrit dans un fichier temporaire puis renomme."""
        try:
            # Sauvegarde du sel
            with open(SALT_FILE, "wb") as f:
                f.write(self.crypto.salt)
            
            # Sauvegarde atomique du vault
            encrypted_data = self.crypto.encrypt(self.vault)
            temp_fd, temp_path = tempfile.mkstemp(dir=os.getcwd())
            with os.fdopen(temp_fd, 'w') as f:
                f.write(encrypted_data)
            
            # Remplace le fichier original de façon atomique
            os.replace(temp_path, DATA_FILE)
        except Exception as e:
            messagebox.showerror("Erreur Sauvegarde", f"Erreur critique : {e}")

    def update_totp_codes(self):
        for entry_id, label in self.totp_labels.items():
            try:
                secret = self.vault[entry_id].get('2fa_secret')
                if secret:
                    totp = pyotp.TOTP(secret.replace(" ", ""))
                    code = totp.now()
                    label.configure(text=f"{code[:3]} {code[3:]}")
            except:
                label.configure(text="Séc. Invalide", text_color="#e74c3c")
        self.after(1000, self.update_totp_codes)

    def calculate_health_score(self):
        entries = [v for k, v in self.vault.items() if not k.startswith("_")]
        if not entries: return 100
        scores = [min(len(v.get('pw', '')) * 8.5, 100) for v in entries]
        return int(sum(scores) // len(scores))

    def show_dashboard(self):
        for widget in self.main_view.winfo_children(): widget.destroy()
        self.totp_labels = {}
        
        score = self.calculate_health_score()
        score_color = "#2ecc71" if score > 75 else "#f1c40f" if score > 40 else "#e74c3c"

        health_frame = ctk.CTkFrame(self.main_view, fg_color=self.card_color, corner_radius=15)
        health_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(health_frame, text="SÉCURITÉ DU COFFRE", font=("Roboto", 11, "bold"), text_color="gray").pack(pady=(15, 0))
        ctk.CTkLabel(health_frame, text=f"{score}%", font=("Roboto", 42, "bold"), text_color=score_color).pack(pady=(0, 15))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.refresh_list)
        ctk.CTkEntry(self.main_view, placeholder_text="🔍 Rechercher...", textvariable=self.search_var, width=500, height=45).pack(pady=10)

        self.list_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)
        self.refresh_list()

    def refresh_list(self, *args):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        query = self.search_var.get().lower()
        for entry_id, data in self.vault.items():
            if entry_id.startswith("_"): continue
            if query in data.get('site', '').lower() or query in data.get('user', '').lower():
                self.create_row(entry_id, data)

    def create_row(self, entry_id, data):
        card = ctk.CTkFrame(self.list_frame, fg_color=self.card_color, corner_radius=12)
        card.pack(fill="x", pady=5)

        # Labels et infos
        cat = data.get('cat', 'Perso')
        cat_colors = {"Perso": "#3498db", "Pro": "#2ecc71", "Banque": "#e67e22", "Autre": "#95a5a6"}
        ctk.CTkLabel(card, text=cat.upper(), font=("Roboto", 9, "bold"), fg_color=cat_colors.get(cat, "#95a5a6"), 
                     text_color="white", width=70, height=22, corner_radius=6).pack(side="left", padx=15)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", padx=10)
        ctk.CTkLabel(info_frame, text=data.get('site', 'Inconnu'), font=("Roboto", 14, "bold"), anchor="w", width=200).pack(fill="x")
        ctk.CTkLabel(card, text=f"👤 {data['user']}", text_color="gray", width=180, anchor="w").pack(side="left", padx=5)

        # Actions
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=10)

        ctk.CTkButton(btns, text="🗑", width=35, fg_color="#c0392b", command=lambda i=entry_id: self.delete_entry(i)).pack(side="right", padx=2)
        
        # Bouton Copie avec vidage automatique
        ctk.CTkButton(btns, text="📋", width=35, command=lambda: self.copy_to_clipboard(data['pw'])).pack(side="right", padx=2)
        
        pw_var = ctk.StringVar(value="••••••••")
        def toggle():
            if pw_var.get() == "••••••••":
                pw_var.set(data['pw'])
                self.after(8000, lambda: pw_var.set("••••••••") if card.winfo_exists() else None)
            else: pw_var.set("••••••••")
        ctk.CTkButton(btns, text="👁", width=35, command=toggle).pack(side="right", padx=2)
        ctk.CTkLabel(card, textvariable=pw_var, width=110, anchor="e").pack(side="right", padx=10)

        if data.get('2fa_secret'):
            totp_f = ctk.CTkFrame(card, fg_color="#1a1c23", corner_radius=6)
            totp_f.pack(side="right", padx=10, pady=10)
            lbl_2fa = ctk.CTkLabel(totp_f, text="--- ---", font=("Roboto", 14, "bold"), text_color=self.accent_color)
            lbl_2fa.pack(padx=10, pady=2)
            self.totp_labels[entry_id] = lbl_2fa

    def add_entry_window(self):
        win = ctk.CTkToplevel(self); win.title("Ajouter"); win.geometry("400x650"); win.attributes('-topmost', True)
        ctk.CTkLabel(win, text="NOUVEL ACCÈS", font=("Roboto", 20, "bold")).pack(pady=20)
        e_site = ctk.CTkEntry(win, placeholder_text="Site", width=300, height=40); e_site.pack(pady=10)
        e_user = ctk.CTkEntry(win, placeholder_text="Identifiant", width=300, height=40); e_user.pack(pady=10)
        e_pass = ctk.CTkEntry(win, placeholder_text="Mot de passe", width=300, height=40, show="*"); e_pass.pack(pady=10)
        e_note = ctk.CTkEntry(win, placeholder_text="Note", width=300, height=40); e_note.pack(pady=10)
        e_2fa = ctk.CTkEntry(win, placeholder_text="Clé 2FA (TOTP)", width=300, height=40); e_2fa.pack(pady=10)
        e_cat = ctk.CTkOptionMenu(win, values=["Perso", "Pro", "Banque", "Autre"], width=300, height=40); e_cat.pack(pady=10)

        def save():
            if e_site.get() and e_pass.get():
                new_id = str(uuid.uuid4())
                self.vault[new_id] = {
                    "site": e_site.get(), "user": e_user.get(), "pw": e_pass.get(), 
                    "cat": e_cat.get(), "note": e_note.get(), "2fa_secret": e_2fa.get()
                }
                self.save_vault(); win.destroy(); self.show_dashboard()
        ctk.CTkButton(win, text="Enregistrer", command=save, width=300, height=45, fg_color="#2ecc71").pack(pady=25)

    def delete_entry(self, entry_id):
        if messagebox.askyesno("Suppression", "Supprimer définitivement ?"):
            del self.vault[entry_id]; self.save_vault(); self.show_dashboard()

    def change_master_password_ui(self):
        new = ctk.CTkInputDialog(text="Nouveau MDP Maître:", title="Sécurité").get_input()
        if new:
            self.crypto = CryptoEngine(new, salt=os.urandom(16))
            self.save_vault()
            messagebox.showinfo("OK", "Mot de passe maître mis à jour et coffre ré-encrypté.")

def login_process():
    login = ctk.CTk(); login.title("ShieldPass Login"); login.geometry("450x400")
    login.configure(fg_color="#000000") 
    ctk.CTkLabel(login, text="🛡", font=("Roboto", 60), text_color="#3d5afe").pack(pady=30)
    ctk.CTkLabel(login, text="Authentification", font=("Roboto", 20, "bold")).pack()
    pw_entry = ctk.CTkEntry(login, placeholder_text="Master Password", show="*", width=300, height=45)
    pw_entry.pack(pady=25)

    def attempt():
        pwd = pw_entry.get()
        if not pwd: return
        try:
            if not os.path.exists(DATA_FILE):
                engine = CryptoEngine(pwd); vault = {"_auth_check": "VALID"}
            else:
                with open(SALT_FILE, "rb") as f: salt = f.read()
                engine = CryptoEngine(pwd, salt=salt)
                with open(DATA_FILE, "r") as f: vault = engine.decrypt(f.read())
            login.destroy(); ShieldPassApp(engine, vault).mainloop()
        except Exception:
            messagebox.showerror("Erreur", "Mot de passe incorrect ou coffre corrompu.")

    ctk.CTkButton(login, text="Déverrouiller", command=attempt, width=300, height=45, fg_color="#3d5afe").pack(pady=10)
    pw_entry.bind("<Return>", lambda e: attempt())
    login.mainloop()

if __name__ == "__main__":
    login_process()