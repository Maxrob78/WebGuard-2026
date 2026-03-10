
***

# 🛡️ ShieldPass Premium v4.1 - Ultra Secure Vault

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Cryptography](https://img.shields.io/badge/Security-AES--128%20%7C%20PBKDF2-brightgreen)
![GUI](https://img.shields.io/badge/UI-CustomTkinter-blueviolet)

**ShieldPass** est un gestionnaire de mots de passe de bureau ultra-sécurisé, conçu en Python. Fonctionnant entièrement hors-ligne, il garantit la souveraineté totale de vos données. L'application combine une interface moderne et réactive avec des standards cryptographiques industriels pour protéger vos identifiants contre les cybermenaces.

---

## ✨ Fonctionnalités Principales

* **🔒 Chiffrement de Qualité Militaire :** Les données sont chiffrées en AES-128 via le module `Fernet`.
* **🔑 Dérivation de Clé Sécurisée :** Le mot de passe maître n'est jamais stocké. La clé de chiffrement est dérivée à la volée en utilisant **PBKDF2HMAC** (SHA-256) avec un sel aléatoire et 600 000 itérations (résistance avancée aux attaques par force brute).
* **📱 Authentification à Double Facteur (2FA / TOTP) :** Génération intégrée en temps réel des codes TOTP à 6 chiffres pour les sites compatibles.
* **🛡️ Protection de la Mémoire :** Les mots de passe copiés dans le presse-papiers sont automatiquement effacés après 30 secondes.
* **💾 Résilience des Données :** Système de sauvegarde atomique pour prévenir la corruption du coffre-fort en cas de plantage.
* **📊 Tableau de Bord Intuitif :** Interface sombre (Dark Mode) avec CustomTkinter, intégrant une barre de recherche en temps réel et un tri par catégories.

---

## 🛠️ Technologies Utilisées

* **Langage :** Python 3
* **UI :** `customtkinter`
* **Cryptographie :** `cryptography` (Fernet, PBKDF2HMAC, SHA256)
* **Génération 2FA :** `pyotp`
* **Système :** `pyperclip`, `uuid`, `tempfile`

---

## 🚀 Installation & Exécution

### 1. Prérequis
Assurez-vous d'avoir Python 3.8 ou une version supérieure installée sur votre machine.

### 2. Cloner le dépôt
```bash
git clone [https://github.com/Maxrob78/ShieldPass.git](https://github.com/Maxrob78/ShieldPass.git)
cd ShieldPass
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```
exécutez : `pip install customtkinter cryptography pyotp pyperclip requests`

### 4. Lancer l'application
```bash
python main.py
