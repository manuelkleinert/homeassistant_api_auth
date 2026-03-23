# API Auth (Home Assistant Custom Integration)

## Übersicht

`api_auth` ist eine **Custom Component** für Home Assistant, die eine einfache API-basierte Authentifizierung bereitstellt.

Funktionen:

* Login per Benutzername/Passwort
* Token-basierte Session-Verwaltung
* Token-Prüfung
* Logout

Geeignet für **kleine Benutzerzahlen** (2–3 Benutzer).

---

## Installation via HACS oder manuell

1. Kopiere den Ordner `api_auth` nach:

```
/config/custom_components/api_auth/
```

2. Füge in `configuration.yaml` hinzu:

```yaml
api_auth:
```

3. **Automatisches Anlegen der Config-Dateien:**
   Beim ersten Start prüft die Component, ob die Dateien existieren:

* `/config/api_users.json` → leere Benutzerliste
* `/config/api_tokens.json` → leere Token-Datei

Existierende Dateien werden **nicht überschrieben**, sodass Passwörter sicher bleiben.

---

## Config-Dateien

### api_users.json

Struktur:

```json
[
    {
        "id": 1,
        "username": "demo",
        "password": "<hashed_password>",
        "role": "admin"
    }
]
```

* `id`: eindeutige Benutzer-ID
* `username`: Benutzername
* `password`: **Bcrypt-gehasht**
* `role`: Benutzerrolle (`admin`, `viewer`, etc.)

### api_tokens.json

Struktur:

```json
{
    "<token>": {
        "user_id": 1,
        "expires": 1700000000
    }
}
```

* `<token>`: zufälliger Token (Hex)
* `user_id`: referenziert den Benutzer in `api_users.json`
* `expires`: Ablaufzeit des Tokens (Unix Timestamp)

---

## Benutzer anlegen / Passwort erstellen

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('[PASSWORD]'.encode(), bcrypt.gensalt()).decode())"
```

* Kopiere den Hash in `api_users.json`
* Optional: Beim ersten Start wird ein Demo-Admin angelegt, wenn die Datei leer ist

---

## API Endpoints

### 1. Login

```http
POST /api/auth
```

**Body:**

```json
{
    "username": "demo",
    "password": "[PASSWORD]"
}
```

**Response:**

```json
{
    "success": true,
    "token": "<token>",
    "expires": 1700000000
}
```

---

### 2. Token Check

```http
POST /api/check_token
```

**Body:**

```json
{
    "token": "<token>"
}
```

**Response:**

```json
{
    "success": true,
    "user_id": 1,
    "username": "demo",
    "role": "admin"
}
```

---

### 3. Logout

```http
POST /api/logout
```

**Body:**

```json
{
    "token": "<token>"
}
```

**Response:**

```json
{
    "success": true
}
```

---

## Beispiele

### Benutzer anlegen via API

```bash
curl -X POST http://homeassistant.local:8123/api/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "[PASSWORD]"}'
```

### Token prüfen

```bash
curl -X POST http://homeassistant.local:8123/api/check_token \
  -H "Content-Type: application/json" \
  -d '{"token": "<token>"}'
```

---

## Hinweise

* **Automatisches Anlegen von Config-Dateien:** Beim ersten Laden prüft die Component, ob `api_users.json` und `api_tokens.json` existieren, und erstellt sie bei Bedarf leer.
* **Sicher:** Existierende Dateien werden **nicht überschrieben**.
* **Passwortschutz:** Nur gehashte Passwörter (Bcrypt) verwenden.
* **Nur kleine Benutzerzahlen:** Für größere User-Management-Systeme ist eine echte Datenbank sinnvoll.
