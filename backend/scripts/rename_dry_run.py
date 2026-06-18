# -*- coding: utf-8 -*-
"""rename 전 dry-run — 21 collector 의 *현재 등록 상태* + *rename 후 예상* dump.

용도: collection clumi_ prefix 제거 계획 검증 (registry 컨벤션 일관성).
"""
from app.dream_agent.tools.registry import get_registry

reg = get_registry()
reg.load()

print("=== 21 clumi collector — 현재 등록 상태 ===")
collectors = [
    t for t in reg.get_all()
    if t.name.startswith("clumi_") and t.name.endswith("_collector")
]
print(f"총 {len(collectors)} 개")
print()
print(f'{"current name":<48} | {"current class":<35} | executor')
print("-" * 110)
for spec in sorted(collectors, key=lambda t: t.name):
    cls = reg.import_tool(spec.name)
    executor = spec.executor or "(inferred from path)"
    print(f"{spec.name:<48} | {cls.__name__:<35} | {executor}")

print()
print("=== rename 후 예상 (registry 의 _infer_import_path 컨벤션 기반) ===")
print(f'{"new name":<48} | {"new class":<35}')
print("-" * 88)
for spec in sorted(collectors, key=lambda t: t.name):
    new_name = spec.name.replace("clumi_", "", 1)
    new_class = "".join(w.capitalize() for w in new_name.split("_"))
    print(f"{new_name:<48} | {new_class:<35}")

print()
print("=== 검증: PRODUCES_KEY (.py) vs produces (YAML) 일치 확인 ===")
import importlib
from pathlib import Path
import yaml

CATALOG_DIR = Path(__file__).resolve().parents[1] / "app/dream_agent/tools/catalog/collection/clumi"
mismatches = []
for spec in sorted(collectors, key=lambda t: t.name):
    yaml_path = CATALOG_DIR / f"{spec.name}.yaml"
    if not yaml_path.exists():
        continue
    yaml_data = yaml.safe_load(yaml_path.read_text("utf-8"))
    yaml_produces = yaml_data.get("produces", [])
    cls = reg.import_tool(spec.name)
    py_produces_key = cls.PRODUCES_KEY
    if py_produces_key not in yaml_produces:
        mismatches.append((spec.name, py_produces_key, yaml_produces))
        print(f"  ⚠ {spec.name}: .py PRODUCES_KEY={py_produces_key} not in YAML produces={yaml_produces}")
if not mismatches:
    print("  ✓ 모든 21 collector 의 PRODUCES_KEY 가 YAML produces 와 일치")
