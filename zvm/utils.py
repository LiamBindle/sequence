
def dereference(d: dict):
    # dereference $ref recursively
    for k, v in d.items():
        if isinstance(v, list):
            for i in range(len(v)):
                if v[i]
    if ref.startswith("#"):
        keys = ref[1:].split("/")
