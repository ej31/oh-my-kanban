#!/usr/bin/env python3
"""TypeScript가 생성한 config.toml을 load_config()로 파싱해서 JSON 출력."""
import sys
import json


def main() -> None:
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not config_path:
        print(json.dumps({"error": "config_path argument required"}))
        sys.exit(1)

    # CONFIG_FILE을 임시 경로로 오버라이드
    import oh_my_kanban.config as cfg_module
    from pathlib import Path
    cfg_module.CONFIG_FILE = Path(config_path)

    from oh_my_kanban.config import load_config
    cfg = load_config()
    print(json.dumps({
        "base_url": cfg.base_url,
        "api_key": cfg.api_key,
        "workspace_slug": cfg.workspace_slug,
        "linear_api_key": cfg.linear_api_key,
        "linear_team_id": cfg.linear_team_id,
    }))


if __name__ == "__main__":
    main()
