def main():
    with open("config.yml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    config = Config(**config_data)

    x = MdfToJsonSchema(config)
    x.generate_node_schemas()
    x.generate_main_schema()

    with open("nodes.json", "w") as f:
        json.dump(x.node_schemas, f, indent=2)

    with open("main.json", "w") as f:
        json.dump(x.main_schema, f, indent=2)