#!/usr/bin/env python3
"""
Compute text-scene R-Precision from paired instruction JSON and scene JSON files.

The scene JSON is converted into a compact natural-language description
(room types, object categories, counts, and room-object membership), and both
instructions and scene descriptions are embedded with a SentenceTransformer.

Examples
--------
1) Two JSON files containing aligned lists:
python compute_r_precision.py \
    --instructions instructions.json \
    --scenes scenes.json \
    --output results.json

2) Two directories whose JSON filenames correspond:
python compute_r_precision.py \
    --instructions instruction_dir \
    --scenes scene_dir \
    --output results.json

3) Use the "query" field inside each scene JSON as the paired instruction:
python compute_r_precision.py \
    --scenes scene_dir \
    --instruction-from-scene query \
    --output results.json

Dependencies
------------
pip install torch sentence-transformers tqdm
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


TEXT_KEYS = (
    "instruction",
    "text",
    "query",
    "prompt",
    "caption",
    "description",
    "task",
)

ID_KEYS = (
    "id",
    "scene_id",
    "uid",
    "name",
    "file_name",
    "filename",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_name(name: str) -> str:
    """Normalize object labels while preserving their semantic category."""
    name = str(name).strip().lower()
    name = name.split("|", 1)[0]
    name = re.sub(r"\s*\([^)]*\)\s*$", "", name)
    name = re.sub(r"[-_]\d+$", "", name)
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def natural_join(items: Sequence[str]) -> str:
    items = [x for x in items if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def counted_phrase(counter: Counter[str]) -> str:
    parts = []
    for name, count in sorted(counter.items()):
        parts.append(f"{count} {name}" if count > 1 else name)
    return natural_join(parts)


def object_category(obj: Dict[str, Any]) -> Optional[str]:
    for key in ("object_name", "category", "class", "label", "name", "id"):
        value = obj.get(key)
        if value:
            category = normalize_name(value)
            if category:
                return category
    return None


def room_name(room: Dict[str, Any]) -> Optional[str]:
    for key in ("roomType", "room_type", "type", "name", "id"):
        value = room.get(key)
        if value:
            return normalize_name(value)
    return None


def scene_to_text(
    scene: Dict[str, Any],
    max_categories_per_room: int = 40,
    include_materials: bool = False,
) -> str:
    """
    Convert a structured scene JSON into a semantic textual description.

    This adapter supports the uploaded format containing:
      - rooms: [{id, roomType, ...}]
      - objects: [{object_name/id, roomId, ...}]
      - metadata.roomSpecId
    """
    clauses: List[str] = []

    rooms = scene.get("rooms", [])
    room_ids_to_names: Dict[str, str] = {}
    room_counter: Counter[str] = Counter()

    if isinstance(rooms, list):
        for room in rooms:
            if not isinstance(room, dict):
                continue
            rname = room_name(room)
            rid = str(room.get("id", rname or "unknown"))
            if rname:
                room_ids_to_names[rid] = rname
                # bedroom 1, bedroom 2 -> bedroom for aggregate count
                aggregate_name = re.sub(r"\s+\d+$", "", rname)
                room_counter[aggregate_name] += 1

    if room_counter:
        clauses.append("The scene contains " + counted_phrase(room_counter) + ".")
    else:
        room_spec = (
            scene.get("metadata", {}).get("roomSpecId")
            if isinstance(scene.get("metadata"), dict)
            else None
        )
        if room_spec:
            clauses.append(f"The scene type is {normalize_name(room_spec)}.")

    room_objects: Dict[str, Counter[str]] = defaultdict(Counter)
    all_objects: Counter[str] = Counter()

    objects = scene.get("objects", [])
    if isinstance(objects, list):
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            category = object_category(obj)
            if not category:
                continue
            all_objects[category] += 1

            rid = str(
                obj.get("roomId")
                or obj.get("room_id")
                or obj.get("room")
                or "unspecified room"
            )
            rname = room_ids_to_names.get(rid, normalize_name(rid))
            room_objects[rname][category] += 1

    # Room-specific descriptions are more informative than one global bag.
    for rname in sorted(room_objects):
        counts = room_objects[rname]
        if max_categories_per_room > 0:
            most_common = counts.most_common(max_categories_per_room)
            counts = Counter(dict(most_common))
        clauses.append(f"The {rname} contains {counted_phrase(counts)}.")

    if not room_objects and all_objects:
        clauses.append("The scene contains " + counted_phrase(all_objects) + ".")

    if include_materials and isinstance(rooms, list):
        material_parts = []
        for room in rooms:
            if not isinstance(room, dict):
                continue
            rname = room_name(room)
            floor = room.get("floor_design")
            wall = room.get("wall_design")
            descriptors = []
            if floor:
                descriptors.append(f"a {floor} floor")
            if wall:
                descriptors.append(f"{wall} walls")
            if rname and descriptors:
                material_parts.append(
                    f"the {rname} has " + natural_join(descriptors)
                )
        if material_parts:
            clauses.append("; ".join(material_parts) + ".")

    if not clauses:
        raise ValueError("Could not extract rooms or objects from scene JSON.")

    return " ".join(clauses)


def extract_text(record: Any, preferred_key: Optional[str] = None) -> str:
    if isinstance(record, str):
        return record.strip()

    if not isinstance(record, dict):
        raise ValueError(f"Instruction record must be a string or dict, got {type(record)}")

    keys = (preferred_key,) if preferred_key else TEXT_KEYS
    for key in keys:
        if key and key in record and isinstance(record[key], str):
            return record[key].strip()

    raise ValueError(
        f"Could not find instruction text. Tried keys: {list(keys)}. "
        f"Available keys: {list(record.keys())}"
    )


def extract_id(record: Any, fallback: str) -> str:
    if isinstance(record, dict):
        for key in ID_KEYS:
            if key in record and record[key] is not None:
                return str(record[key])
    return fallback


def records_from_json(data: Any) -> List[Any]:
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("data", "items", "records", "instructions", "scenes"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        # A single JSON object is one record.
        return [data]

    if isinstance(data, str):
        return [data]

    raise ValueError(f"Unsupported JSON root type: {type(data)}")


def load_instruction_source(
    path: Path,
    text_key: Optional[str],
) -> Tuple[List[str], List[str]]:
    if path.is_file():
        records = records_from_json(load_json(path))
        texts = [extract_text(record, text_key) for record in records]
        ids = [extract_id(record, str(i)) for i, record in enumerate(records)]
        return texts, ids

    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise ValueError(f"No .json files found in instruction directory: {path}")
        texts, ids = [], []
        for file in files:
            records = records_from_json(load_json(file))
            if len(records) != 1:
                raise ValueError(
                    f"Directory mode expects one instruction record per file, "
                    f"but {file} contains {len(records)} records."
                )
            texts.append(extract_text(records[0], text_key))
            ids.append(file.stem)
        return texts, ids

    raise FileNotFoundError(path)


def load_scene_source(
    path: Path,
    max_categories_per_room: int,
    include_materials: bool,
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    if path.is_file():
        records = records_from_json(load_json(path))
        if not all(isinstance(x, dict) for x in records):
            raise ValueError("Every scene record must be a JSON object.")
        scenes = list(records)
        ids = [extract_id(record, str(i)) for i, record in enumerate(scenes)]
        texts = [
            scene_to_text(s, max_categories_per_room, include_materials)
            for s in scenes
        ]
        return scenes, texts, ids

    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise ValueError(f"No .json files found in scene directory: {path}")
        scenes, texts, ids = [], [], []
        for file in tqdm(files, desc="Reading scenes"):
            records = records_from_json(load_json(file))
            if len(records) != 1 or not isinstance(records[0], dict):
                raise ValueError(
                    f"Directory mode expects one scene object per file: {file}"
                )
            scene = records[0]
            scenes.append(scene)
            texts.append(
                scene_to_text(scene, max_categories_per_room, include_materials)
            )
            ids.append(file.stem)
        return scenes, texts, ids

    raise FileNotFoundError(path)


def align_by_id(
    instruction_texts: List[str],
    instruction_ids: List[str],
    scene_texts: List[str],
    scene_ids: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    inst_map = dict(zip(instruction_ids, instruction_texts))
    scene_map = dict(zip(scene_ids, scene_texts))
    shared = sorted(set(inst_map) & set(scene_map))
    if not shared:
        raise ValueError(
            "No shared IDs/filenames between instruction and scene inputs. "
            "Use --alignment index if records are already in the same order."
        )
    return [inst_map[x] for x in shared], [scene_map[x] for x in shared], shared


def compute_retrieval(
    instruction_embeddings: torch.Tensor,
    scene_embeddings: torch.Tensor,
    topk: Sequence[int],
    direction: str,
) -> Dict[str, Any]:
    """
    Paired sample i is the positive match for sample i.
    Embeddings must already be L2-normalized.
    """
    similarity = instruction_embeddings @ scene_embeddings.T
    n = similarity.shape[0]
    target = torch.arange(n, device=similarity.device)

    if direction == "text_to_scene":
        scores = similarity
    elif direction == "scene_to_text":
        scores = similarity.T
    else:
        raise ValueError(direction)

    order = torch.argsort(scores, dim=1, descending=True)
    ranks = (order == target[:, None]).nonzero(as_tuple=False)[:, 1] + 1

    metrics: Dict[str, Any] = {
        f"R-Precision@{k}": float((ranks <= k).float().mean().item())
        for k in topk
    }
    metrics["mean_rank"] = float(ranks.float().mean().item())
    metrics["median_rank"] = float(ranks.float().median().item())
    metrics["MRR"] = float((1.0 / ranks.float()).mean().item())
    metrics["ranks"] = ranks.cpu().tolist()
    metrics["top1_indices"] = order[:, 0].cpu().tolist()
    metrics["positive_similarity"] = (
        scores[torch.arange(n, device=scores.device), target].cpu().tolist()
    )
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute text-scene R-Precision from JSON inputs."
    )
    parser.add_argument("--scenes", type=Path, required=True)
    parser.add_argument("--instructions", type=Path)
    parser.add_argument(
        "--instruction-from-scene",
        type=str,
        default=None,
        help="Read paired instructions from this field in each scene JSON, e.g. query.",
    )
    parser.add_argument(
        "--text-key",
        type=str,
        default=None,
        help="Instruction text key for dict records, e.g. instruction or query.",
    )
    parser.add_argument(
        "--alignment",
        choices=("index", "id"),
        default="index",
        help="Pair records by list order or by IDs/filenames.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-mpnet-base-v2",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Examples: cuda, cuda:0, cpu. Default: auto.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        nargs="+",
        default=[1, 2, 3],
    )
    parser.add_argument(
        "--direction",
        choices=("text_to_scene", "scene_to_text", "both"),
        default="both",
    )
    parser.add_argument("--max-categories-per-room", type=int, default=40)
    parser.add_argument("--include-materials", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("r_precision_results.json"))
    parser.add_argument(
        "--save-scene-texts",
        type=Path,
        default=None,
        help="Optionally save extracted scene descriptions for inspection.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    scenes, scene_texts, scene_ids = load_scene_source(
        args.scenes,
        args.max_categories_per_room,
        args.include_materials,
    )

    if args.instruction_from_scene:
        instruction_texts = []
        instruction_ids = list(scene_ids)
        for idx, scene in enumerate(scenes):
            value = scene.get(args.instruction_from_scene)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Scene {scene_ids[idx]} has no non-empty string field "
                    f"{args.instruction_from_scene!r}."
                )
            instruction_texts.append(value.strip())
        pair_ids = scene_ids

    else:
        if args.instructions is None:
            raise ValueError(
                "Provide --instructions or use --instruction-from-scene FIELD."
            )
        instruction_texts, instruction_ids = load_instruction_source(
            args.instructions, args.text_key
        )

        if args.alignment == "id":
            instruction_texts, scene_texts, pair_ids = align_by_id(
                instruction_texts,
                instruction_ids,
                scene_texts,
                scene_ids,
            )
        else:
            if len(instruction_texts) != len(scene_texts):
                raise ValueError(
                    f"Different sample counts: {len(instruction_texts)} instructions "
                    f"vs {len(scene_texts)} scenes."
                )
            pair_ids = scene_ids

    n = len(scene_texts)
    if n < 2:
        raise ValueError(
            "R-Precision requires at least 2 paired samples, because the other "
            "samples serve as retrieval negatives."
        )

    topk = sorted(set(k for k in args.topk if 1 <= k <= n))
    if not topk:
        raise ValueError(f"No valid --topk value for dataset size {n}.")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(args.model, device=device)

    instruction_embeddings = model.encode(
        instruction_texts,
        batch_size=args.batch_size,
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    scene_embeddings = model.encode(
        scene_texts,
        batch_size=args.batch_size,
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    result: Dict[str, Any] = {
        "num_samples": n,
        "model": args.model,
        "device": device,
        "topk": topk,
        "scene_representation": (
            "Natural-language serialization of room types, object categories, "
            "counts, and room-object membership."
        ),
    }

    directions = (
        ["text_to_scene", "scene_to_text"]
        if args.direction == "both"
        else [args.direction]
    )

    for direction in directions:
        metrics = compute_retrieval(
            instruction_embeddings,
            scene_embeddings,
            topk,
            direction,
        )
        ranks = metrics.pop("ranks")
        top1 = metrics.pop("top1_indices")
        positive_similarity = metrics.pop("positive_similarity")
        result[direction] = metrics
        result[f"{direction}_per_sample"] = [
            {
                "id": pair_ids[i],
                "rank": int(ranks[i]),
                "positive_similarity": float(positive_similarity[i]),
                "top1_retrieved_id": pair_ids[top1[i]],
                "correct_at_1": bool(ranks[i] == 1),
            }
            for i in range(n)
        ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if args.save_scene_texts:
        args.save_scene_texts.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"id": pair_ids[i], "scene_text": scene_texts[i]}
            for i in range(n)
        ]
        with args.save_scene_texts.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved results to: {args.output}")


if __name__ == "__main__":
    main()
