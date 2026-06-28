import logging
import os
from collections.abc import Iterable

logger = logging.getLogger(__name__)

# Standalone Milvus 通过 URI 连接(docker 模式 docker-compose 注入,
# 本地裸跑用 docker compose up -d milvus 后通过 localhost:19530 连接)
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")
TEXT_COLLECTION = os.getenv("MILVUS_TEXT_COLLECTION", "local_notebook_text_segments_v1")
IMAGE_COLLECTION = os.getenv("MILVUS_IMAGE_COLLECTION", "local_notebook_image_segments_v1")

MILVUS_INDEX_TYPE = os.getenv("MILVUS_INDEX_TYPE", "IVF_PQ").upper()
MILVUS_IVF_NLIST = int(os.getenv("MILVUS_IVF_NLIST", "128"))
MILVUS_IVF_NPROBE = int(os.getenv("MILVUS_IVF_NPROBE", "32"))
MILVUS_PQ_M = int(os.getenv("MILVUS_PQ_M", "128"))
MILVUS_PQ_NBITS = int(os.getenv("MILVUS_PQ_NBITS", "8"))

_client = None


def _get_client():
    global _client
    if _client is None:
        from pymilvus import MilvusClient
        _client = MilvusClient(uri=MILVUS_URI)
    return _client


def _legacy_col(project_id: str) -> str:
    return "p_" + project_id.replace("-", "_")


def _legacy_img_col(project_id: str) -> str:
    return _legacy_col(project_id) + "_images"


def legacy_collection_names(project_id: str) -> tuple[str, str]:
    return _legacy_col(project_id), _legacy_img_col(project_id)


def shared_collection_names() -> tuple[str, str]:
    return TEXT_COLLECTION, IMAGE_COLLECTION


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _in_expr(field_name: str, values: Iterable[str]) -> str:
    values_quoted = ", ".join(_quote(value) for value in values)
    return f"{field_name} in [{values_quoted}]"


def _not_in_expr(field_name: str, values: Iterable[str]) -> str:
    values_quoted = ", ".join(_quote(value) for value in values)
    return f"{field_name} not in [{values_quoted}]"


def _project_filter(project_id: str) -> str:
    return f"project_id == {_quote(project_id)}"


def _project_file_filter(project_id: str, file_id: str) -> str:
    return f"{_project_filter(project_id)} and file_id == {_quote(file_id)}"


def _filter_for_project_files(project_id: str, file_ids: list[str] | None = None) -> str:
    filter_expr = _project_filter(project_id)
    if file_ids:
        filter_expr += f" and {_in_expr('file_id', file_ids)}"
    return filter_expr


def _pq_m(dim: int) -> int:
    preferred = max(1, MILVUS_PQ_M)
    if dim % preferred == 0 and preferred <= dim:
        return preferred

    candidates = [128, 96, 64, 48, 32, 24, 16, 12, 8, 4, 2, 1]
    for candidate in candidates:
        if candidate <= dim and dim % candidate == 0:
            logger.warning(
                "MILVUS_PQ_M=%s is incompatible with vector dim=%s; using m=%s",
                preferred,
                dim,
                candidate,
            )
            return candidate
    return 1


def _add_vector_index(index_params, dim: int) -> None:
    params: dict[str, int] = {"nlist": MILVUS_IVF_NLIST}
    if MILVUS_INDEX_TYPE == "IVF_PQ":
        params.update({"m": _pq_m(dim), "nbits": MILVUS_PQ_NBITS})

    index_params.add_index(
        field_name="embedding",
        index_type=MILVUS_INDEX_TYPE,
        metric_type="L2",
        params=params,
    )


def _add_filter_indexes(index_params) -> None:
    index_params.add_index(field_name="project_id", index_type="INVERTED")
    index_params.add_index(field_name="file_id", index_type="INVERTED")


def ensure_collection(project_id: str, dim: int) -> None:
    client = _get_client()
    name = TEXT_COLLECTION
    if client.has_collection(name):
        return

    from pymilvus import DataType
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id",            DataType.VARCHAR,      max_length=200, is_primary=True)
    schema.add_field("project_id",    DataType.VARCHAR,      max_length=50)
    schema.add_field("file_id",       DataType.VARCHAR,      max_length=50)
    schema.add_field("file_name",     DataType.VARCHAR,      max_length=500)
    schema.add_field("segment_index", DataType.INT64)
    schema.add_field("content",       DataType.VARCHAR,      max_length=4096)
    schema.add_field("summary",       DataType.VARCHAR,      max_length=2048)
    schema.add_field("embedding",     DataType.FLOAT_VECTOR, dim=dim)

    index_params = client.prepare_index_params()
    _add_filter_indexes(index_params)
    _add_vector_index(index_params, dim)

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )
    logger.info(
        "Created Milvus text collection '%s' dim=%s index=%s",
        name,
        dim,
        MILVUS_INDEX_TYPE,
    )


def ensure_image_collection(project_id: str, dim: int) -> None:
    client = _get_client()
    name = IMAGE_COLLECTION
    if client.has_collection(name):
        return

    from pymilvus import DataType
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id",            DataType.VARCHAR,      max_length=200, is_primary=True)
    schema.add_field("project_id",    DataType.VARCHAR,      max_length=50)
    schema.add_field("file_id",       DataType.VARCHAR,      max_length=50)
    schema.add_field("file_name",     DataType.VARCHAR,      max_length=500)
    schema.add_field("image_index",   DataType.INT64)
    schema.add_field("description",   DataType.VARCHAR,      max_length=4096)
    schema.add_field("embedding",     DataType.FLOAT_VECTOR, dim=dim)

    index_params = client.prepare_index_params()
    _add_filter_indexes(index_params)
    _add_vector_index(index_params, dim)

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )
    logger.info(
        "Created Milvus image collection '%s' dim=%s index=%s",
        name,
        dim,
        MILVUS_INDEX_TYPE,
    )


def upsert_chunks(project_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return
    client = _get_client()
    data = [{**chunk, "project_id": project_id} for chunk in chunks]
    client.upsert(collection_name=TEXT_COLLECTION, data=data)


def upsert_image_chunks(project_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return
    client = _get_client()
    data = [{**chunk, "project_id": project_id} for chunk in chunks]
    client.upsert(collection_name=IMAGE_COLLECTION, data=data)


def delete_by_file(project_id: str, file_id: str) -> None:
    client = _get_client()

    if client.has_collection(TEXT_COLLECTION):
        client.delete(
            collection_name=TEXT_COLLECTION,
            filter=_project_file_filter(project_id, file_id),
        )

    if client.has_collection(IMAGE_COLLECTION):
        client.delete(
            collection_name=IMAGE_COLLECTION,
            filter=_project_file_filter(project_id, file_id),
        )


def delete_project_vectors(project_id: str) -> None:
    client = _get_client()

    for name in shared_collection_names():
        if client.has_collection(name):
            client.delete(collection_name=name, filter=_project_filter(project_id))
            logger.info("Deleted Milvus vectors from '%s' for project %s", name, project_id)

    for name in legacy_collection_names(project_id):
        if client.has_collection(name):
            client.drop_collection(collection_name=name)
            logger.info("Dropped legacy Milvus collection '%s'", name)


def delete_project_collections(project_id: str) -> None:
    delete_project_vectors(project_id)


def delete_projects_vectors(project_ids: Iterable[str]) -> None:
    ids = sorted(set(project_ids))
    if not ids:
        return

    client = _get_client()
    filter_expr = _in_expr("project_id", ids)
    for name in shared_collection_names():
        if client.has_collection(name):
            client.delete(collection_name=name, filter=filter_expr)


def delete_vectors_not_in_projects(active_project_ids: Iterable[str]) -> None:
    ids = sorted(set(active_project_ids))
    client = _get_client()
    filter_expr = (
        _not_in_expr("project_id", ids)
        if ids
        else 'project_id != ""'
    )
    for name in shared_collection_names():
        if client.has_collection(name):
            client.delete(collection_name=name, filter=filter_expr)


def search(
    project_id: str,
    query_vector: list[float],
    file_ids: list[str] | None = None,
    top_k: int = 8,
) -> list[dict]:
    client = _get_client()
    name = TEXT_COLLECTION

    if not client.has_collection(name):
        return []

    results = client.search(
        collection_name=name,
        data=[query_vector],
        limit=top_k,
        filter=_filter_for_project_files(project_id, file_ids),
        output_fields=["file_id", "file_name", "segment_index", "content", "summary"],
        search_params={"metric_type": "L2", "params": {"nprobe": MILVUS_IVF_NPROBE}},
    )

    hits = []
    for hit in results[0]:
        hits.append({
            "segment_id":    hit["id"],
            "file_id":       hit["entity"]["file_id"],
            "file_name":     hit["entity"]["file_name"],
            "segment_index": hit["entity"]["segment_index"],
            "content":       hit["entity"]["content"],
            "summary":       hit["entity"].get("summary") or "",
            "score":         hit["distance"],
        })
    return hits


def search_images(
    project_id: str,
    query_vector: list[float],
    file_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    client = _get_client()
    name = IMAGE_COLLECTION

    if not client.has_collection(name):
        return []

    results = client.search(
        collection_name=name,
        data=[query_vector],
        limit=top_k,
        filter=_filter_for_project_files(project_id, file_ids),
        output_fields=["file_id", "file_name", "image_index", "description"],
        search_params={"metric_type": "L2", "params": {"nprobe": MILVUS_IVF_NPROBE}},
    )

    hits = []
    for hit in results[0]:
        hits.append({
            "image_id":      hit["id"],
            "file_id":       hit["entity"]["file_id"],
            "file_name":     hit["entity"]["file_name"],
            "image_index":   hit["entity"]["image_index"],
            "description":   hit["entity"]["description"],
            "score":         hit["distance"],
        })
    return hits


def get_by_ids(project_id: str, segment_ids: list[str]) -> list[dict]:
    if not segment_ids:
        return []
    client = _get_client()
    name = TEXT_COLLECTION
    if not client.has_collection(name):
        return []

    results = client.query(
        collection_name=name,
        filter=f"{_project_filter(project_id)} and {_in_expr('id', segment_ids)}",
        output_fields=["file_id", "file_name", "segment_index", "content", "summary"],
    )

    return [
        {
            "id":            r["id"],
            "file_id":       r.get("file_id", ""),
            "file_name":     r.get("file_name", ""),
            "segment_index": r.get("segment_index", 0),
            "content":       r.get("content", ""),
            "summary":       r.get("summary") or "",
        }
        for r in (results or [])
    ]
