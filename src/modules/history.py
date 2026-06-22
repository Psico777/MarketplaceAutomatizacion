"""
Historial de publicaciones + logging.

Guarda cada intento de publicacion (exito o fallo) en un JSON append-only,
para saber que se subio, que fallo, y cuantas publicaciones llevas hoy
(util para respetar el limite diario anti-baneo).
"""
import os
import json
import logging
from datetime import datetime, date


class ListingHistory:
    def __init__(self, history_file='listings_history.json', logs_dir='logs'):
        self.history_file = history_file
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self._records = self._load()
        self.logger = self._setup_logger()

    # ---------- persistencia ----------
    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"No se pudo guardar el historial: {e}")

    def _setup_logger(self):
        logger = logging.getLogger('marketplace')
        if logger.handlers:
            return logger
        logger.setLevel(logging.INFO)
        log_path = os.path.join(self.logs_dir, f"run_{date.today().isoformat()}.log")
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(fh)
        return logger

    # ---------- API ----------
    def record(self, image, title, price, status, attempts=1, error=None):
        """status: 'success' | 'failed'"""
        rec = {
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'image': os.path.basename(image) if image else '',
            'title': title,
            'price': price,
            'status': status,
            'attempts': attempts,
            'error': str(error) if error else None,
        }
        self._records.append(rec)
        self._save()
        if status == 'success':
            self.logger.info(f"PUBLICADO: {title} (S/{price}) [{rec['image']}]")
        else:
            self.logger.error(f"FALLO: {title} [{rec['image']}] -> {error}")
        return rec

    def count_today(self, status='success'):
        """Cuantas publicaciones (por estado) se hicieron hoy."""
        today = date.today().isoformat()
        return sum(
            1 for r in self._records
            if r.get('status') == status and str(r.get('timestamp', '')).startswith(today)
        )

    def remaining_today(self, daily_limit):
        return max(0, daily_limit - self.count_today('success'))

    def summary(self):
        ok = sum(1 for r in self._records if r.get('status') == 'success')
        fail = sum(1 for r in self._records if r.get('status') == 'failed')
        return {'total': len(self._records), 'success': ok, 'failed': fail, 'today': self.count_today('success')}
