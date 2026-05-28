# API Auth (Home Assistant Custom Integration)

## Übersicht

`api_auth` ist eine **Custom Component** für Home Assistant, die eine einfache API-basierte Authentifizierung bereitstellt. 

Funktionen:
* Login per Benutzername/Passwort
* Token-basierte Session-Verwaltung
* Token-Prüfung & Logout
* **NEU:** Benutzerverwaltung direkt in der Home Assistant UI
* **NEU:** Speicherung in einer SQLite-Datenbank

---

## Installation

### 1. Dateien kopieren
Kopiere den Ordner `api_auth` in deinen Home Assistant `custom_components` Ordner:
```
/config/custom_components/api_auth/
```

### 2. Integration in Home Assistant hinzufügen
1. Starte Home Assistant neu.
2. Gehe zu **Einstellungen** -> **Geräte & Dienste**.
3. Klicke auf **Integration hinzufügen**.
4. Suche nach **API Auth** und richte sie ein.
   *Hinweis: Es ist kein Eintrag in der `configuration.yaml` mehr nötig.*

---

## Benutzerverwaltung (UI)

Die Verwaltung der Benutzer erfolgt nun vollständig über die Home Assistant Benutzeroberfläche:

1. Gehe zu **Einstellungen** -> **Geräte & Dienste**.
2. Suche die **API Auth** Kachel und klicke auf **KONFIGURIEREN**.
3. Wähle im Menü eine Aktion:
   * **Benutzer hinzufügen**: Erstelle neue Benutzer mit Passwort und Rolle.
   * **Passwort ändern**: Ändere sicher das Passwort eines bestehenden Benutzers.
   * **Benutzer löschen**: Entferne einen Benutzer und alle zugehörigen Tokens.

---

## Datenspeicherung

Alle Daten werden sicher in einer SQLite-Datenbank gespeichert:
* `/config/api_auth.db`

Bestehende Benutzer aus alten `api_users.json` Dateien werden beim ersten Start nach der Umstellung **automatisch migriert** und die JSON-Dateien anschließend gelöscht.

---

## API Endpoints

### 1. Login
`POST /api/auth`
**Body:** `{"username": "demo", "password": "yourpassword"}`
**Response:** `{"success": true, "token": "...", "expires": 1700000000}`

### 2. Token Check
`POST /api/check_token`
**Body:** `{"token": "..."}`
**Response:** `{"success": true, "user_id": 1, "username": "demo", "role": "admin"}`

### 3. Logout
`POST /api/logout`
**Body:** `{"token": "..."}`

---

## Sicherheit
* **Bcrypt**: Passwörter werden sicher mit dem Bcrypt-Algorithmus gehasht.
* **Thread-Sicherheit**: Alle Datenbank-Operationen laufen asynchron im Hintergrund, um Home Assistant nicht zu blockieren.
* **Lokale Verarbeitung**: Keine Cloud-Abhängigkeit, alle Daten bleiben auf deinem Server.
