import numpy as np
import pandas as pd


def _embedding_matrix(embeddings, row_count):
    matrix = np.asarray(embeddings, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != row_count:
        raise ValueError("embed_texts must return one two-dimensional vector row per input text")
    return matrix


def embed_documents(documents: pd.DataFrame, embed_texts):
    return _embedding_matrix(embed_texts(documents["text"].tolist()), len(documents))


def retrieve_top_k(query, documents: pd.DataFrame, document_embeddings, embed_texts, k=10):
    if k < 0:
        raise ValueError("k must be non-negative")

    matrix = _embedding_matrix(document_embeddings, len(documents))
    query_vector = _embedding_matrix(embed_texts([query]), 1)[0]

    document_norms = np.linalg.norm(matrix, axis=1)
    query_norm = np.linalg.norm(query_vector)
    denominators = document_norms * query_norm
    scores = np.divide(
        matrix @ query_vector,
        denominators,
        out=np.zeros(len(documents), dtype=float),
        where=denominators > 0,
    )
    positions = np.lexsort((np.arange(len(documents)), -scores))[:k]

    result = documents.iloc[positions].copy()
    result["score"] = scores[positions]
    return result.reset_index(drop=True)


def evaluate_retrieval(evaluation_pairs, documents: pd.DataFrame, document_embeddings, embed_texts, k=10):
    if not evaluation_pairs:
        return {"recall_at_k": 0.0, "mrr": 0.0}

    hits = 0
    reciprocal_ranks = []
    for query, relevant_doc_id in evaluation_pairs:
        ranked_rows = retrieve_top_k(query, documents, document_embeddings, embed_texts, k=k)
        ranked_ids = ranked_rows["doc_id"].tolist()
        if relevant_doc_id in ranked_ids:
            hits += 1
            reciprocal_ranks.append(1.0 / (ranked_ids.index(relevant_doc_id) + 1))
        else:
            reciprocal_ranks.append(0.0)

    query_count = len(evaluation_pairs)
    return {
        "recall_at_k": hits / query_count,
        "mrr": sum(reciprocal_ranks) / query_count,
    }
