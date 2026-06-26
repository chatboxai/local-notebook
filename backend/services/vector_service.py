import logging
import os

logger = logging.getLogger(__name__)

# Standalone Milvus 通过 URI 连接(docker 模式 docker-compose 注入,
# 本地裸跑用 docker compose up -d milvus 后通过 localhost:19530 连接)
MILVUS_URI = os.getenv("MILVUS_URI", "http://localhost:19530")

_client = None


def _get_client():
    global _client
    if _client is None:
        from pymilvus import MilvusClient
        _client = MilvusClient(uri=MILVUS_URI)
    return _client


def _col(project_id: str) -> str:
    return "p_" + project_id.replace("-", "_")


def _img_col(project_id: str) -> str:
    return "p_" + project_id.replace("-", "_") + "_images"


def ensure_collection(project_id: str, dim: int) -> None:
    client = _get_client()
    name = _col(project_id)
    if client.has_collection(name):
        return

    from pymilvus import DataType
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id",            DataType.VARCHAR,      max_length=200, is_primary=True)
    schema.add_field("file_id",       DataType.VARCHAR,      max_length=50)
    schema.add_field("file_name",     DataType.VARCHAR,      max_length=500)
    schema.add_field("segment_index", DataType.INT64)
    schema.add_field("content",       DataType.VARCHAR,      max_length=4096)
    schema.add_field("summary",       DataType.VARCHAR,      max_length=2048)
    schema.add_field("embedding",     DataType.FLOAT_VECTOR, dim=dim)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="IVF_FLAT",
        metric_type="L2",
        params={"nlist": 128},
    )

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )
    logger.info(f"Created Milvus collection '{name}' dim={dim}")


def ensure_image_collection(project_id: str, dim: int) -> None:
    client = _get_client()
    name = _img_col(project_id)
    if client.has_collection(name):
        return

    from pymilvus import DataType
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id",            DataType.VARCHAR,      max_length=200, is_primary=True)
    schema.add_field("file_id",       DataType.VARCHAR,      max_length=50)
    schema.add_field("file_name",     DataType.VARCHAR,      max_length=500)
    schema.add_field("image_index",   DataType.INT64)
    schema.add_field("description",   DataType.VARCHAR,      max_length=4096)
    schema.add_field("embedding",     DataType.FLOAT_VECTOR, dim=dim)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="IVF_FLAT",
        metric_type="L2",
        params={"nlist": 128},
    )

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )
    logger.info(f"Created Milvus image collection '{name}' dim={dim}")


def upsert_chunks(project_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return
    client = _get_client()
    client.upsert(collection_name=_col(project_id), data=chunks)


def upsert_image_chunks(project_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return
    client = _get_client()
    client.upsert(collection_name=_img_col(project_id), data=chunks)


def delete_by_file(project_id: str, file_id: str) -> None:
    client = _get_client()

    name = _col(project_id)
    if client.has_collection(name):
        client.delete(collection_name=name, filter=f'file_id == "{file_id}"')

    img_name = _img_col(project_id)
    if client.has_collection(img_name):
        client.delete(collection_name=img_name, filter=f'file_id == "{file_id}"')


def delete_project_collections(project_id: str) -> None:
    client = _get_client()

    for name in (_col(project_id), _img_col(project_id)):
        if client.has_collection(name):
            client.drop_collection(collection_name=name)
            logger.info("Dropped Milvus collection '%s'", name)


def search(
    project_id: str,
    query_vector: list[float],
    file_ids: list[str] | None = None,
    top_k: int = 8,
) -> list[dict]:
    client = _get_client()
    name = _col(project_id)

    if not client.has_collection(name):
        return []

    filter_expr = None
    if file_ids:
        ids_quoted = ", ".join(f'"{fid}"' for fid in file_ids)
        filter_expr = f"file_id in [{ids_quoted}]"

    results = client.search(
        collection_name=name,
        data=[query_vector],
        limit=top_k,
        filter=filter_expr,
        output_fields=["file_id", "file_name", "segment_index", "content", "summary"],
        search_params={"metric_type": "L2", "params": {"nprobe": 16}},
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
    name = _img_col(project_id)

    if not client.has_collection(name):
        return []

    filter_expr = None
    if file_ids:
        ids_quoted = ", ".join(f'"{fid}"' for fid in file_ids)
        filter_expr = f"file_id in [{ids_quoted}]"

    results = client.search(
        collection_name=name,
        data=[query_vector],
        limit=top_k,
        filter=filter_expr,
        output_fields=["file_id", "file_name", "image_index", "description"],
        search_params={"metric_type": "L2", "params": {"nprobe": 16}},
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
    name = _col(project_id)
    if not client.has_collection(name):
        return []

    results = client.get(
        collection_name=name,
        ids=segment_ids,
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

