from __future__ import annotations

import envyaml


def get_config(path_to_config: str | None = None) -> envyaml.EnvYAML:
    """Get config from yaml file path."""
    if path_to_config is None:
        path_to_config = "config.yml"

    return envyaml.EnvYAML(
        path_to_config,
        env_file=".env",
        include_environment=False,
        flatten=False,
    )
