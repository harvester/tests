from robot.api.deco import keyword


@keyword("Update YAML")
def update_yaml(ctx, path, value):
    *keys, key = path.split("?")
    ptr = ctx
    for k in keys:
        ptr = ptr.setdefault(k, {})
    ptr[key] = value
    return ctx
