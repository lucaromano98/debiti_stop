# Deploy – Backend Debiti Stop

Istruzioni per mettere in produzione il backend Django (db-backoffice.it).

## Variabili d’ambiente (produzione)

Imposta queste variabili sul server o sul pannello del servizio di hosting:

| Variabile       | Obbligatoria | Esempio / note |
|-----------------|-------------|----------------|
| `SECRET_KEY`    | Sì          | Stringa lunga e casuale (es. generata con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DEBUG`         | No          | `False` in produzione |
| `ALLOWED_HOSTS` | No          | `db-backoffice.it,www.db-backoffice.it` (separati da virgola, senza spazi) |
| `DATABASE_URL`  | Se usi DB remoto | URL tipo `mysql://user:password@host:3306/nome_db` (il nome dopo la barra è il database). |
| `DATABASE_NAME` | No          | Se il database si chiama diversamente dall’URL (es. `defaultdb`), imposta qui il nome reale, es. `defaultdb`. |

Per sviluppo in locale puoi usare un file `.env` nella cartella `back_end` (non committare `.env` se contiene segreti).

## Comandi prima del deploy

Sulla macchina di build o sul server:

```bash
cd back_end
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

## Avvio in produzione

- **Con Procfile** (Heroku, Railway, Render, ecc.): il Procfile avvia già Gunicorn; la piattaforma imposta `PORT`.
- **A mano (VPS / server)**:
  ```bash
  gunicorn debiti_stop.wsgi --bind 0.0.0.0:8000
  ```
  Oppure, se usi un reverse proxy (nginx) che fa proxy a una socket:
  ```bash
  gunicorn debiti_stop.wsgi --bind unix:/run/gunicorn.sock
  ```

## File statici

Con `DEBUG=False` i static vengono serviti da **WhiteNoise**. Esegui sempre `collectstatic` prima del deploy. Se in futuro userai un CDN o S3, potrai cambiare `STATICFILES_STORAGE` nelle settings.

## Checklist rapida

- [ ] `SECRET_KEY` diversa da quella di sviluppo e tenuta segreta
- [ ] `DEBUG=False` in produzione
- [ ] `ALLOWED_HOSTS` con il dominio reale (es. `db-backoffice.it`)
- [ ] `DATABASE_URL` configurata se usi MySQL/PostgreSQL
- [ ] Eseguito `migrate` e `collectstatic`
- [ ] HTTPS configurato sul dominio (es. Let’s Encrypt dietro nginx)
