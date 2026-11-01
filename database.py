"""
Module de gestion de la base de données SQLite
pour l'application de notes d'Informatique - Collège Saint Thomas de Manjo
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Chemin de la base de données
_db_local = Path(__file__).parent / "notes_informatique.db"
try:
    # Test d'écriture
    _test = _db_local.parent / ".write_test"
    _test.touch()
    _test.unlink()
    DB_PATH = _db_local
except Exception:
    DB_PATH = Path("/tmp/notes_informatique_manjo.db")

CLASSES = [
    "6e", "5e",
    "4eAll", "4eEsp",
    "3eAll", "3eEsp",
    "2ndeAll", "2ndeEsp", "2ndeC",
    "1ereAll", "1ereEsp", "1ereC", "1ereD",
    "tleAll", "tleEsp", "tleC", "tleD",
]

CLASS_LABELS = {
    "6e": "Sixième",
    "5e": "Cinquième",
    "4eAll": "Quatrième Allemand",
    "4eEsp": "Quatrième Espagnol",
    "3eAll": "Troisième Allemand",
    "3eEsp": "Troisième Espagnol",
    "2ndeAll": "Seconde Allemand",
    "2ndeEsp": "Seconde Espagnol",
    "2ndeC": "Seconde C",
    "1ereAll": "Première Allemand",
    "1ereEsp": "Première Espagnol",
    "1ereC": "Première C",
    "1ereD": "Première D",
    "tleAll": "Terminale A4 Allemand",
    "tleEsp": "Terminale A4 Espagnol",
    "tleC": "Terminale C",
    "tleD": "Terminale D",
}


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crée les tables si elles n'existent pas."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eleves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classe TEXT NOT NULL,
                nom TEXT NOT NULL,
                sexe TEXT CHECK(sexe IN ('F', 'M')) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(classe, nom)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eleve_id INTEGER NOT NULL,
                eval1 REAL,
                eval2 REAL,
                eval3 REAL,
                eval4 REAL,
                eval5 REAL,
                eval6 REAL,
                FOREIGN KEY (eleve_id) REFERENCES eleves(id) ON DELETE CASCADE,
                UNIQUE(eleve_id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eleves_classe ON eleves(classe)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_eleve ON notes(eleve_id)")


def ajouter_eleve(classe: str, nom: str, sexe: str) -> int:
    """Ajoute un élève et retourne son id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO eleves (classe, nom, sexe) VALUES (?, ?, ?)",
            (classe, nom.strip().upper(), sexe)
        )
        eleve_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO notes (eleve_id) VALUES (?)",
            (eleve_id,)
        )
        return eleve_id


def modifier_eleve(eleve_id: int, nom: str, sexe: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE eleves SET nom = ?, sexe = ? WHERE id = ?",
            (nom.strip().upper(), sexe, eleve_id)
        )


def supprimer_eleve(eleve_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE eleve_id = ?", (eleve_id,))
        cursor.execute("DELETE FROM eleves WHERE id = ?", (eleve_id,))


def get_eleves(classe: str) -> List[Dict[str, Any]]:
    """Retourne la liste des élèves d'une classe avec leurs notes."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.nom, e.sexe,
                   n.eval1, n.eval2, n.eval3, n.eval4, n.eval5, n.eval6
            FROM eleves e
            LEFT JOIN notes n ON e.id = n.eleve_id
            WHERE e.classe = ?
            ORDER BY e.nom
        """, (classe,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_notes(eleve_id: int, notes: Dict[str, Optional[float]]):
    """Met à jour les notes d'un élève. notes = {'eval1': 12.5, ...}"""
    with get_connection() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        for key in ["eval1", "eval2", "eval3", "eval4", "eval5", "eval6"]:
            if key in notes:
                fields.append(f"{key} = ?")
                values.append(notes[key])
        if not fields:
            return
        values.append(eleve_id)
        sql = f"UPDATE notes SET {', '.join(fields)} WHERE eleve_id = ?"
        cursor.execute(sql, values)


def get_statistiques(classe: str) -> Dict[str, Any]:
    """Calcule toutes les statistiques pour une classe."""
    eleves = get_eleves(classe)
    if not eleves:
        return {"effectif": 0}

    def safe_avg(values):
        vals = [v for v in values if v is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    def safe_max(values):
        vals = [v for v in values if v is not None]
        return max(vals) if vals else None

    def safe_min(values):
        vals = [v for v in values if v is not None]
        return min(vals) if vals else None

    def count_success(values, sexe=None):
        count = 0
        for e in eleves:
            if sexe and e["sexe"] != sexe:
                continue
            for v in values:
                if e.get(v) is not None and e[v] >= 10:
                    count += 1
                    break  # on compte l'élève une fois si on regarde une moyenne
        return count

    # Préparer les listes de notes
    evals = {
        "eval1": [e["eval1"] for e in eleves],
        "eval2": [e["eval2"] for e in eleves],
        "eval3": [e["eval3"] for e in eleves],
        "eval4": [e["eval4"] for e in eleves],
        "eval5": [e["eval5"] for e in eleves],
        "eval6": [e["eval6"] for e in eleves],
    }

    # Moyennes par trimestre
    moy1_list = []
    moy2_list = []
    moy3_list = []
    for e in eleves:
        m1 = safe_avg([e["eval1"], e["eval2"]])
        m2 = safe_avg([e["eval3"], e["eval4"]])
        m3 = safe_avg([e["eval5"], e["eval6"]])
        moy1_list.append(m1)
        moy2_list.append(m2)
        moy3_list.append(m3)

    filles = [e for e in eleves if e["sexe"] == "F"]
    garcons = [e for e in eleves if e["sexe"] == "M"]

    def success_rate(note_list, sexe_filter=None):
        total = 0
        success = 0
        for i, e in enumerate(eleves):
            if sexe_filter and e["sexe"] != sexe_filter:
                continue
            val = note_list[i]
            if val is not None:
                total += 1
                if val >= 10:
                    success += 1
        return round(100 * success / total, 1) if total > 0 else 0

    stats = {
        "effectif": len(eleves),
        "filles": len(filles),
        "garcons": len(garcons),
        "max": {k: safe_max(v) for k, v in evals.items()},
        "min": {k: safe_min(v) for k, v in evals.items()},
        "moy_classe": {k: safe_avg(v) for k, v in evals.items()},
        "moy1_classe": safe_avg(moy1_list),
        "moy2_classe": safe_avg(moy2_list),
        "moy3_classe": safe_avg(moy3_list),
        "taux_reussite": {},
    }

    for key in ["eval1", "eval2", "eval3", "eval4", "eval5", "eval6"]:
        stats["taux_reussite"][key] = {
            "filles": success_rate(evals[key], "F"),
            "garcons": success_rate(evals[key], "M"),
            "total": success_rate(evals[key]),
        }

    # Taux sur les moyennes trimestrielles
    stats["taux_reussite"]["moy1"] = {
        "filles": success_rate(moy1_list, "F"),
        "garcons": success_rate(moy1_list, "M"),
        "total": success_rate(moy1_list),
    }
    stats["taux_reussite"]["moy2"] = {
        "filles": success_rate(moy2_list, "F"),
        "garcons": success_rate(moy2_list, "M"),
        "total": success_rate(moy2_list),
    }
    stats["taux_reussite"]["moy3"] = {
        "filles": success_rate(moy3_list, "F"),
        "garcons": success_rate(moy3_list, "M"),
        "total": success_rate(moy3_list),
    }

    return stats


def calculer_moyennes_et_rangs(eleves: List[Dict]) -> List[Dict]:
    """Ajoute moy1/2/3 et rang1/2/3 à chaque élève."""
    def avg(a, b):
        vals = [v for v in (a, b) if v is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    for e in eleves:
        e["moy1"] = avg(e.get("eval1"), e.get("eval2"))
        e["moy2"] = avg(e.get("eval3"), e.get("eval4"))
        e["moy3"] = avg(e.get("eval5"), e.get("eval6"))

    def assign_ranks(key_moy, key_rang):
        # Trier les élèves qui ont une moyenne
        sorted_eleves = sorted(
            [e for e in eleves if e[key_moy] is not None],
            key=lambda x: x[key_moy],
            reverse=True
        )
        for rank, e in enumerate(sorted_eleves, 1):
            e[key_rang] = rank
        for e in eleves:
            if key_rang not in e:
                e[key_rang] = None

    assign_ranks("moy1", "rang1")
    assign_ranks("moy2", "rang2")
    assign_ranks("moy3", "rang3")
    return eleves


def importer_depuis_excel(filepath: str, classe: str) -> int:
    """Importe des élèves depuis un fichier Excel (optionnel)."""
    try:
        import pandas as pd
        df = pd.read_excel(filepath)
        count = 0
        for _, row in df.iterrows():
            nom = str(row.get("NOMS ET PRENOMS", row.get("nom", ""))).strip()
            sexe = str(row.get("SEXE", row.get("sexe", "M"))).strip().upper()
            if not nom or nom == "nan":
                continue
            if sexe not in ("F", "M"):
                sexe = "M"
            try:
                ajouter_eleve(classe, nom, sexe)
                count += 1
            except sqlite3.IntegrityError:
                pass  # déjà existant
        return count
    except Exception as e:
        raise RuntimeError(f"Erreur d'import : {e}")


# Initialisation au chargement du module
init_db()
