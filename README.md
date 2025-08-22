
LinkLoom is a command-line bookmark manager that allows you to save and find your bookmarks using natural language queries. Instead of searching by tags or keywords, you search by meaning.

Forget trying to remember the exact title of an article you saved three months ago. With LinkLoom, you can just ask:

```bash
lloom find "that article about black hole information paradox"
```

and get relevant results instantly.

## How It Works

LinkLoom operates by understanding the semantic meaning of your bookmarks, not just their text.

* **Storage:** Bookmarks (URL, notes) are stored in a local SQLite database.
* **Content Extraction:** The main text content of the webpage is extracted using [trafilatura](https://github.com/adbar/trafilatura).
* **Semantic Embedding:** The text and your note are converted into vector embeddings using a SentenceTransformer model.
* **Vector Storage:** Embeddings are stored in a local [ChromaDB](https://www.trychroma.com/) for efficient similarity search.
* **Semantic Search:** Your queries are also embedded, and LinkLoom returns the most semantically similar bookmarks.


## Installation

LinkLoom can be installed in two ways:

* From **PyPI** (recommended for most users)
* From **source** (recommended for contributors)

### Prerequisites

* Python **3.9+**
* `git` (only for source installation)

### 1. Create and Activate a Virtual Environment

It is strongly recommended to use a virtual environment.

```bash
python3 -m venv .venv
```

Activate it:

* On Linux/macOS:

  ```bash
  source .venv/bin/activate
  ```
* On Windows:

  ```
  .venv\Scripts\activate
  ```

---

### 2. Install from PyPI (Stable)

The easiest way is to install directly from PyPI:

```bash
pip install linkloom
```

---

### 3. Install from Source (Development)

If you want to contribute or run the latest changes:

```bash
git clone https://github.com/neirzhei/LinkLoom.git
cd LinkLoom
```

Install [uv](https://github.com/astral-sh/uv) (fast build tool):

```bash
pip install uv
```

Then install in editable mode:

```bash
uv pip install -e .
```



## Usage

Make sure your virtual environment is active (`source .venv/bin/activate`) before using the CLI.

### Adding a Bookmark

```bash
lloom add "https://neirzhei.github.io/article/art-in-weaponry.html" --note "might check out miyamoto musashi's book"
```

Output:

```bash
Saved: id=1
```

### Finding a Bookmark

```bash
lloom find "miyamoto's view on art"
```

Output:

```bash
https://neirzhei.github.io/article/art-in-weaponry.html
```
---
