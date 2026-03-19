
# Optimising Search for 'Map of the World' 
**From PDFs to compact, fast, portable indexes**

---

## Why this matters for children's social care data

Children's social care information is **extensive and often spread very wide** across government and partner websites, (long)PDFs, and research portals. Our approach focuses(in-part) on making that material **accessible and searchable** without moving heavy files around or duplicating storage.

- **Fast, lightweight search:** we extract text once and create a minimised search index (no PDFs, just raw optimised data)
- **Clarity and provenance:** chunk-level search surfaces the **exact clauses** (e.g. thresholds, Section 47, kinship care) with links back to the authoritative source and licence
- **Low overhead, high resilience:** compact Parquet/FAISS artefacts are inexpensive to store (e.g. in R2), simple to mirror, and easy to reuse locally by LAs/sector stakeholders
- **Keeps pace with change:** incremental builds pick up updates. Reprocessing just what changed, so the map stays current as guidance, published reports or sector research evolves
- **Defined scope boundaries:** Defined licensing metadata, and explicit source boundaries ensure ring-fenced sector scope

## Who this is for (and what you’ll get)

- **Product / content folks:** how we take lots of PDFs and turn them into a **tiny, fast** search index that still finds the right things.
- **Engineers / data people:** the design choices, math, and scaling numbers so you can **reuse this pipeline** on your own document sets.

**One‑line summary:** we extract text --> split into semantically sensible chunks --> embed each chunk as a vector --> store compactly in Parquet using **uint8 quantisation** --> build a **FAISS** similarity index (HNSW by default). The public search can then use a **small JSON keyword index** for near-instant client‑side search; deeper semantic search uses the vector index as needed.

---

## Why this approach works

1. **We do heavy lifting once, locally.** PDFs are slow to parse and (comparitively)large to store especially at scale; we extract the text and avoid shipping raw files within the platform. 
2. **We chunk long documents.** Searching against topically coherent chunks(minimised to the most relevant) beats whole‑document matching for retrieval quality. 
3. **We use sentence embeddings.** Similarity in embedding space approximates “is this about the same thing?”
4. **We store vectors compactly.** Quantising embeddings to **uint8** shrinks storage ~4× with negligible impact on retrieval quality for our use case(s). - Although we are still defining/asking about the sector's possible use-cases. 
5. **We separate UX search from deep search.** The site ships a tiny keyword index for instant(or at least faster) results; we're also aiming for external LA workflows being able to use the vector index offline.

---

## Recall loss

Saving embeddings as **uint8** instead of 32‑bit floats means we're using **lossy** compression scheme. That slightly perturbs numbers. If someone later rebuilds a vector index **from those saved numbers**, nearest‑neighbour results may differ *a bit* from athe float32 baseline.

In practice with normalised sentence embeddings:

- Cosine similarity between orig and dequantised vectors usually **≥ 0.995** (to around ~0.999)
- End‑to‑end **recall@10** typically changes by **0-2%** on common text corpora
- MotW live FAISS index is built directly from **float32** in memory, so **website retrieval quality is unaffected** by how we store the vectors in Parquet

### quick math

L2‑normalise each embedding vector `x` (vals lie roughly in [-1, 1]) and map each component to 8 bits:

- **Quantise:** `q = round((x + 1) * 127.5)` --> `q ∈ {0,…,255}`  
- **Dequantise:** `x' = (q / 127.5) - 1.0`  
- **Re‑normalise:** `x'' = x' / ||x'||` (keeps cosine similarity meaningful)

Because most info in sentence embeddings is in **direction** (not exact magnitudes), cos similarity very stable after this process.

---

## pipeline (what and why)

reference for devs and those managing platform/repo back-end stuff, probably not relevant to most stakeholders

1. **Text extraction** (PyMuPDF; pdfminer fallback)  
   - Why: PyMuPDF is 2-5× faster on increasing scale on PDFs  
2. **Chunking** (default ~1,800 chars with ~150 overlap)  
   - Why: balances context and index size; fewer, richer chunks --> faster build and smaller artefacts  
3. **Embedding** (`all-MiniLM-L6-v2`, 384‑dim, normalised)  
   - Why: Small fast quality; normalisation makes cosine = inner product and improves quantisation robustness  
4. **Storage**  
   - **Per‑doc Parquet** (text + metadata) ---> easy incremental updates  
   - **Vectors in Parquet as `uint8`** ---> ~4× smaller than float32, plus schema metadata describing de/quantisation  
   - **Combined Parquet** (optional) for simple downstream use if LAs have a use for  
5. **Indexing** (FAISS)  
   - **HNSW** default: excellent recall, easier to tune  
   - **IVF‑PQ** optional: order‑of‑magnitude smaller index for very large corpora; small recall trade‑off, tunable with `nprobe`
6. **Incremental builds**  
   - `state.json` records per‑document SHA‑256; unchanged docs are skipped. Rebuilds are proportional to change, not corpus size
7. **Website search index (keyword JSON)**  
   - From Parquet, not PDFs. Cleaned text, remove stop‑words and over‑common terms, derive per‑doc keywords ---> a **very small** JSON file for client‑side search

---

## Real‑world impact for users

- **Fast search:** small on‑site JSON makes type‑ahead and filters (appear) near-instant  
- **Better hits:** chunk‑level indexing can return relevant text blocks from extensive PDFs  
- **Stable URLs:** Not yet in use. But would be backlinks within the motw platform to object specific detail(s)  
- **Scales:** adding thousands of docs has less of impact on site response and repo bloat  

---

## Real‑world impact for devs/engineers/platform

This a reference for devs and those managing  platform/repo back-end stuff, probably not relevant to most stakeholders. 

- **Artefacts, not assets:** Git & Pages store compact Parquet/JSON, not PDFs  
- **Cheap(er) storage:** vectors as `uint8` and HNSW/IVF‑PQ keep Git/R2 costs low(er)  
- **Reproducible builds:** manifest + hashes = deterministic rebuilds  
- **Interoperability:** Parquet + FAISS are standard; others can reuse the corpus locally  

---

## Sizing & scaling (rules of thumb)

This a reference for devs and those managing platform/repo back-end stuff, probably not relevant to most stakeholders. 

Let **C** = number of chunks. With 384‑dim embeddings:

- **Float32 vector size (raw):** `C × 384 × 4` bytes  
- **UInt8 vector size (raw):** `C × 384 × 1` bytes (~4× smaller)  
- **HNSW index size:** typically **~1-2 KB per chunk** (depends on `M`, dataset)  
- **Parquet overhead:** +10-30% over raw, but ZSTD helps especially for text  

### Example projections

Assuming current chunking yields ~**74 chunks/doc** (observed ~1,928 chunks for 26 docs) ---> **3,000 docs ~ 222k chunks**  

| Component | Formula | 222k chunks (est.) |
|---|---|---:|
| Parquet vectors (float32 raw) | `C × 384 × 4` | ~**341 MB** (+overhead) |
| Parquet vectors (uint8 raw) | `C × 384 × 1` | ~**85 MB** (+overhead) |
| HNSW index | ~1-2 KB × C | **~220-440 MB** |
| Parquet text+meta | compressed | **tens of MB** (depends on text volume) |

> If HNSW index starts feeling large to juggle, flip to **IVF‑PQ**: you can expect **tens of MB** with recall@10 often **95-99%**, tunable via `nprobe`.

---

## Keyword index (what’s in tiny JSON)

compact derived per‑doc keyword list from the Parquet text:

- Normalise punctuation/quotes and remove boilerplate (e.g., page headers)  
- Lowercase, keep words of 4+ letters  
- Remove **stop‑words** (scikit‑learn English) and **domain‑common words** (CSC custom list of high freq/low importance words)  
- Filter **too‑common** terms with `max_df` (e.g., drop tokens appearing in >85% of docs) and **too‑rare** with `min_df` (e.g., keep tokens in ≥2 docs)

This makes `docs/search_index.json` **tiny** and fast(er) for lookup/searches.

---

## Why HNSW now, IVF‑PQ later?

- **HNSW** gives near‑exact recall with simple knobs (`M`, `efConstruction`, `efSearch`), great for up to a few hundred thousand vectors on a single machine.
- **IVF‑PQ** compresses vectors and partitions the space. It is useful when you need **smaller indexes** and faster queries at scale. We trade some/a little recall, but can dial it back with `nprobe` and codebook size.

**Switching rule of thumb:** if chunks exceed **~200-250k** or HNSW file becomes problematic (>~300 MB), toggle IVF‑PQ.

---

## Interoperability & reuse

- **Parquet** is easy to read from Python, R, Spark, DuckDB, Polars, etc.
- **FAISS** is a standard ANN engine; the index can be loaded locally or by a lightweight service.
- The corpus is **self‑describing**: Parquet schema metadata indicates whether embeddings are `float32` or quantised (`uint8` with dequant rule).

---

## Frequently asked "but will it…?"

- **…find the right stuff in compressed vectors?**  
  Yes-for docs and model, differences are tiny. We've normalised vectors, which preserves cosine structure.

- **…scale to thousands of PDFs?**  
  Yes. The heavier corpus build, is seperate and done externally, size via incremental hashing, hence only compact artefacts. 

- **…lock me into specific, or paid 3rd-party|software?**  
  No. We've aimed for an entirely open/Git-centric approach on this + open formats (Parquet, FAISS) + standard Python libs

- **…support OCR/scanned PDFs?**  
  No. But it could. WE just dont see the immeadiate need for this within the sector. Could later add Tesseract or cloud OCR  if needed. Can add later if any colleagues are aware of such docs. 

---

## Key libraries and why we chose them

- **PyMuPDF (`pymupdf`)**: fast, robust PDF text extraction  
- **Sentence‑Transformers**: high‑quality sentence embeddings + easy APIs  
- **FAISS**: full vector search (HNSW, IVF‑PQ) with scalable performance  
- **PyArrow/Parquet**: portable column based storage; perfect for text + vectors + metadata  
- **scikit‑learn**: light‑weight keyword vocab building with stop‑word & frequency filters

---

## Takeaways

- By **separating heavy preprocessing** from what's hosted in the main/mkdocs site here, plus by **quantising vectors**, we massively cut the needed storage and bandwidth without compromising colleagues' experience in the search etc
- The site’s search is able to be **near-instant with smaller footprint**, and an underlying corpus remains **portable and reusable** for future or onward data projects - although we're not yet sure of the use-cases on this.

---


# FAISS and Parquet artefacts: structure and reference

A bit about how derived files are organised within the project, what's inside Parquet tables, and what the FAISS index stores. 

---

## Repo layout (derived artefacts)

```
artifacts/
  state.json                        # per-document hashes, build config, last_built
  chunks/                           # per-document Parquet (text + metadata)
    1a2b3c4d5e6f7a8b.parquet
    9c0d1e2f3a4b5c6d.parquet
    ...
  vectors/                          # per-document Parquet (text + vectors)
    1a2b3c4d5e6f7a8b.parquet
    9c0d1e2f3a4b5c6d.parquet
    ...
  motw_chunks.parquet               # combined (optional)
  motw_vectors.parquet              # combined (optional)
  motw_index.faiss                  # FAISS HNSW index (default)
  motw_index_ivfpq.faiss            # FAISS IVF-PQ index (optional)
```

- `doc_id` is the first 16 hex of the SHA-256 of the raw file content.
- Per-document Parquet files enable incremental builds and quick reloads.
- Combined Parquet files are optional and exist for convenience.

---

## Parquet schemas

### Per-document **chunks** Parquet (`artifacts/chunks/<doc_id>.parquet`)

Schema:

```
doc_id:      string          # 16-char hex id (content address)
chunk_id:    int32           # 0..N-1 per document
source_path: string          # original path on disk
source_name: string          # original filename (for example My_File.pdf)
text:        string          # chunked, cleaned text
```

Example row:

| doc_id           | chunk_id | source_name              | text (truncated)            |
|------------------|---------:|--------------------------|-----------------------------|
| 1a2b3c4d5e6f7a8b | 0        | ADCS_Safeguarding_...pdf | Local authorities should... |

### Per-document **vectors** Parquet (`artifacts/vectors/<doc_id>.parquet`)

Same columns as **chunks**, plus one embedding column:

- If stored as float32:
  ```
  embedding: list<float32>    # length 384
  ```
- If stored as uint8 (space-saving default):
  ```
  embedding_q: list<uint8>    # length 384, quantised
  ```

Parquet schema metadata (present on the vectors file) indicates storage:

```
motw.embedding.storage = "float32"      # or "uint8_sym"
motw.embedding.dequant  = "x = (q / 127.5) - 1.0"
```

- For `embedding_q`, clients can reconstruct an approximate float vector as:
  - `x = (q / 127.5) - 1.0`, then L2-normalise `x` before cosine similarity.
- Vectors were normalised during embedding, which keeps cosine behaviour stable after dequantisation.

### Combined Parquet files (optional)

`artifacts/motw_chunks.parquet` and `artifacts/motw_vectors.parquet` have the same schemas as above, but hold all docs together. They are convenient for one-shot analysis and for users/LA colleagues that do not want to iterate per-doc files.

---

## FAISS index files

The pipeline can build either:

### HNSW index (default) - `artifacts/motw_index.faiss`

Stored properties inside the binary:

- `d` ---> 384 (embedding dimension)
- `metric` ---> inner product (cosine when vectors are normalised)
- `ntotal` ---> number of vectors (equals total chunks)
- Graph parameters saved with the index:
  - `M` ---> graph degree used at build time (for example 32)
  - `efConstruction` ---> build breadth (for example 80)
- Query-time parameter you set after loading:
  - `efSearch` ---> search breadth (for example 64 or 128). Higher ---> better recall, slower

Notes:
- Excellent recall and speed up to a few hundred thousand vectors  
- File size typically ~1-2 KB per vector, depending on `M` and data

### IVF-PQ index (optional) - `artifacts/motw_index_ivfpq.faiss`

Stored properties:

- `d` ---> 384
- `metric` ---> inner product
- `ntotal` ---> number of vectors
- Coarse quantiser and codebooks:
  - `nlist` ---> number of coarse centroids (for example 1024)
  - `m` ---> number of subquantisers (for example 16)
  - `nbits` ---> bits per subvector (for example 8)
  - Trained centroids and PQ codebooks included in the file
- Query-time parameter (set after loading):
  - `nprobe` --> how many coarse lists to search (for example 16, 32, 64). Higher --> better recall, slower.

Notes:
- Much smaller on disk than HNSW (often tens of MB), with a small recall trade-off - tune via `nprobe`.

---

## Minimal load examples (for ref)

```python
# Load FAISS index
import faiss
index = faiss.read_index("artifacts/motw_index.faiss")  # or motw_index_ivfpq.faiss
# For HNSW, can increase recall at query time:
try:
    index.hnsw.efSearch = 64
except AttributeError:
    pass
# For IVF-PQ:
try:
    index.nprobe = 32
except AttributeError:
    pass
```

```python
# Load vectors from Parquet (handles float32 or uint8 storage)
import pyarrow.parquet as pq
import numpy as np

t = pq.read_table("artifacts/motw_vectors.parquet")  # or per-document under artifacts/vectors/
cols = set(t.schema.names)

if "embedding" in cols:  # float32
    embs = np.array([np.array(x) for x in t.column("embedding").to_pylist()], dtype="float32")
elif "embedding_q" in cols:  # uint8
    q = np.array([np.array(x, dtype="uint8") for x in t.column("embedding_q").to_pylist()], dtype="uint8")
    x = (q.astype("float32") / 127.5) - 1.0
    # re-normalise to unit length
    n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-6
    embs = x / n
else:
    raise ValueError("No embedding column found")
```

---

## How these pieces fit the platform

- **Parquet** carries all chunk text and metadata for analytics, auditing, and lightweight keyword indexing.
- **FAISS** provides high-quality semantic retrieval over the same chunks.
- Storing Parquet embeddings as **uint8** keeps long-term storage small while preserving near-identical search behaviour when vectors are dequantised and normalised.
- HNSW is the default for accuracy and simplicity. IVF-PQ is available when a much smaller index is needed, with tunable recall.

---

## Glossary  

- **Parquet**: a columnar file format for tables. Efficient to store and quick to scan. Works well with Pandas, DuckDB, Spark and friends.
- **FAISS**: Facebook AI Similarity Search - a library for fast similarity search over vectors (numerical representations of text). Lets you find "things like this" quickly. 
- **HNSW**: Hierarchical Navigable Small World graph. A very fast index structure used by FAISS for high‑quality approximate nearest‑neighbour search.
- **Artefacts**: the files we produce from processing (e.g. Parquet tables and FAISS indexes) that you can store, publish, or reuse.
- **L2‑normalise**: scale a vector so its length is 1. This keeps cosine similarity meaningful and makes quantisation behave well.
