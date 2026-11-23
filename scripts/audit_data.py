"""Metadata-only split audit. Never emits sealed test task contents."""

import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "vendor/tau2-bench"
DATA = UP / "data/tau2"
COMMIT = "989d3285ae669e49503324bdb9981bf14fccedeb"


def read(path):
    return json.loads((DATA / path).read_text())


def dump(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    head = subprocess.check_output(
        ["git", "-C", str(UP), "rev-parse", "HEAD"], text=True
    ).strip()
    assert head == COMMIT, head
    tasks = read("domains/retail/tasks.json")
    replacements = read("multilingual/en/retail_tasks_en.json")
    frozen = set(read("task_subsets/retail_50.json")["task_ids"])
    official = read("domains/retail/split_tasks.json")
    assert frozen == {t["id"] for t in replacements}
    # Include both historical and reviewed versions when protecting entities.
    versions = {t["id"]: [t] for t in tasks}
    for t in replacements:
        versions[t["id"]].append(t)
    db = read("domains/retail/db.json")
    identities = {}
    for uid, user in db["users"].items():
        tokens = {uid, user.get("email", "")}
        name = user.get("name", {})
        if isinstance(name, dict):
            tokens.add(
                " ".join(str(name.get(k, "")) for k in ("first_name", "last_name"))
            )
        identities[uid] = {s.casefold() for s in tokens if s.strip()}
    entities, texts = {}, {}
    for tid, vv in versions.items():
        blob = json.dumps(vv, ensure_ascii=False).casefold()
        keys = set()
        for uid, tokens in identities.items():
            if any(tok in blob for tok in tokens):
                keys.add("user:" + uid)
        for oid, order in db["orders"].items():
            # Order IDs are unique digit strings; match with boundaries.
            if re.search(
                r"(?<!\d)" + re.escape(oid.lstrip("#").casefold()) + r"(?!\d)", blob
            ):
                keys.add("order:" + oid)
                keys.add("user:" + order["user_id"])
        entities[tid] = keys
        texts[tid] = []
        for version in vv:
            raw = json.dumps(version["user_scenario"], sort_keys=True).casefold()
            raw = re.sub(r"[\w.+-]+@[\w.-]+", "<email>", raw)
            raw = re.sub(r"\b\w+_\w+_\d+\b|\d+", "<id>", raw)
            texts[tid].append(raw)
    parent = {tid: tid for tid in versions}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    links = []
    ids = sorted(versions, key=int)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            shared = entities[a] & entities[b]
            sim = max(
                difflib.SequenceMatcher(None, x, y, autojunk=False).ratio()
                for x in texts[a]
                for y in texts[b]
            )
            if shared or sim >= 0.80:
                union(a, b)
                links.append(
                    {
                        "a": a,
                        "b": b,
                        "reason": "entity" if shared else "text_similarity",
                        "similarity": round(sim, 4),
                    }
                )
    groups = {}
    for tid in ids:
        groups.setdefault(find(tid), []).append(tid)
    final_groups = {find(t) for t in frozen}
    legacy_holdout = set(official["test"]) - frozen
    held_groups = final_groups | {find(t) for t in legacy_holdout}
    candidates = set(official["train"]) - frozen
    safe_groups = [g for root, g in groups.items() if root not in held_groups]
    safe_groups.sort(
        key=lambda g: hashlib.sha256(
            (",".join(g) + ":retailalign-v1").encode()
        ).hexdigest()
    )
    dev, train = [], []
    for g in safe_groups:
        (dev if len(dev) < 8 else train).extend(g)
    train, dev = sorted(train, key=int), sorted(dev, key=int)
    quarantine = sorted(candidates - set(train) - set(dev), key=int)
    manifest = {
        "version": "retailalign-split-v1",
        "upstream_commit": COMMIT,
        "status": "metadata_frozen_generation_blocked_pending_semantic_audit",
        "final_test": sorted(frozen, key=int),
        "legacy_holdout": sorted(legacy_holdout, key=int),
        "train": train,
        "dev": dev,
        "quarantine": quarantine,
        "groups": sorted(groups.values(), key=lambda g: int(g[0])),
        "rules": {
            "text_similarity_threshold": 0.80,
            "seed": "retailalign-v1",
            "dev_target_min_tasks": 8,
        },
    }
    assert not set(train) & set(dev)
    assert not (set(train) | set(dev)) & (frozen | legacy_holdout)
    assert set(train) | set(dev) <= candidates
    assert not any(entities[a] & entities[b] for a in train + dev for b in frozen)
    dump("manifests/split_v1.json", manifest)
    dump(
        "reports/split_audit.json",
        {
            "official_train": len(official["train"]),
            "official_test": len(official["test"]),
            "frozen": len(frozen),
            "train_frozen_overlap": len(set(official["train"]) & frozen),
            "candidate_train": len(candidates),
            "train": len(train),
            "dev": len(dev),
            "quarantine": len(quarantine),
            "links": links,
            "limits": [
                "Entity scan + normalized textual similarity only; semantic paraphrases require manual review.",
                "Shared product catalogue and policy are environment assets, not independent tasks.",
                "No final-test prose, reference actions or answers were emitted.",
            ],
        },
    )
    # Pin all distributed input assets, excluding old simulation/results outputs.
    hashes = {}
    for p in sorted(DATA.rglob("*")):
        if p.is_file() and not any(
            s in p.relative_to(DATA).parts for s in ("results", "simulations")
        ):
            hashes[str(p.relative_to(UP))] = hashlib.sha256(p.read_bytes()).hexdigest()
    dump(
        "manifests/upstream.json",
        {
            "repository": "https://github.com/sierra-research/tau2-bench",
            "tag": "v2.0.0",
            "tag_object": "acd66c4d8681ce27ef0cbb4839d24f87218b9b9c",
            "commit": head,
            "package_version": "2.0.0",
            "benchmark": "text-v1",
            "revision": read("benchmarks/text.json")["revision"],
            "license": "MIT",
            "python": ">=3.12,<3.14",
            "uv_lock_sha256": hashlib.sha256((UP / "uv.lock").read_bytes()).hexdigest(),
            "data_sha256": hashes,
        },
    )
    print(
        json.dumps(
            {
                k: len(manifest[k])
                for k in ("train", "dev", "final_test", "legacy_holdout", "quarantine")
            }
        )
    )


if __name__ == "__main__":
    main()
