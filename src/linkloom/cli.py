import os
import typer
import trafilatura
import httpx
import sqlite3
import chromadb
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Optional

app = typer.Typer(help="LinkLoom - Handsome Bookmark Manager")
DB_PATH = "bookmark.db"
CHROMA_DIR = "chromadb"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
NOTE_WEIGHT = float(os.getenv("LLOOM_NOTE_WEIGHT", "0.7"))

#-----------------(SQLite Database)
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookmark(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        note TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    con.close()

#-----------------(Sentence Transformer and ChromaDB)
model = SentenceTransformer(MODEL_NAME)

client = PersistentClient(path=CHROMA_DIR)
try:
    coll = client.get_collection("bookmark")
except Exception:
    coll = client.create_collection(name="bookmark")

#-----------------(Scrapping)
USER_AGENT = "LinkLoom (+url)"

def fetch_content(url: str) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT}
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=20) as httpc:
            r = httpc.get(url)
            r.raise_for_status()
            html = r.text
    except Exception:
        return None
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text:
        return None
    words = text.strip().split()
    intro_para = " ".join(words[:130])
    return intro_para

#-----------------(Embedding)
def embed(text: str) -> Optional[np.ndarray]:
    if not text:
        return None
    arr = model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
    return np.asarray(arr, dtype=float)

def l2_normalize(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec)
    return vec / n if n and n != 0 else vec

#-----------------(CLI Commands)
@app.callback()
def main():
    init_db()

@app.command("add")
def add(url: str, note: str = typer.Option("", "--note")):
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO bookmark(url, note) VALUES (?, ?)", (url, note))
            bid = cur.lastrowid

            content = fetch_content(url)
            content_emb = embed(content) if content else None
            note_emb = embed(note) if note else None

            if content_emb is not None and note_emb is not None:
                combined = l2_normalize((1 - NOTE_WEIGHT) * content_emb + NOTE_WEIGHT * note_emb)
            elif content_emb is not None:
                combined = l2_normalize(content_emb)
            elif note_emb is not None:
                combined = l2_normalize(note_emb)
            else:
                combined = None

            if combined is None:
                typer.echo("Failed to generate embedding. Aborting.")
                raise typer.Exit(code=1)
            coll.add(
                ids=[str(bid)],
                embeddings=[combined.tolist()],
                metadatas=[{"url": url, "note": note}],
            )
            cur.execute("UPDATE bookmark SET status=? WHERE id=?", ("processed", bid))
            typer.echo(f"Saved: id={bid}")

    except sqlite3.IntegrityError:
        typer.echo("URL already exists!")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"failed: {e}")
        raise typer.Exit(code=1)

@app.command("find")
def find(query: str, k: int = 3):
    q_emb = embed(query)
    if q_emb is None:
        typer.echo("Failed to embed query.")
        raise typer.Exit(code=1)
    q_emb = l2_normalize(q_emb)
    try:
        res = coll.query(query_embeddings=[q_emb.tolist()], n_results=k)
    except Exception:
        typer.echo("No result")
        raise typer.Exit(code=0)

    ids = res.get("ids", [[]])[0]

    if not ids:
        typer.echo("No result")
        raise typer.Exit(code=0)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for idx in ids:
        try:
            cur.execute("SELECT url FROM bookmark WHERE id=?", (int(idx),))
            row = cur.fetchone()
        except Exception:
            row = None
        if row:
            url = row[0]
            typer.echo(f"{url}")
    con.close()