import json
import os
import yaml

def read_config(name):
    if not os.path.isfile(name):
        raise Exception(f"File {name} doesn't exists")
    filename, ext = os.path.splitext(name)
    if 'json' in ext:
        return read_json(name), os.path.getmtime(name)
    elif 'properties' in ext:
        return read_prop(name), os.path.getmtime(name)
    elif 'yaml' in ext or 'yml' in ext:
        return read_yaml(name), os.path.getmtime(name)
    else:
        raise Exception("Wrong file type")

def read_json(name):
    with open(name, 'r') as f:
        j_conf = json.load(f)
        conf = {}
        for key, value in j_conf.items():
            conf[key] = value
        return conf

def read_prop(filepath, sep='=', comment_char='#'):
    conf = {}
    with open(filepath, "rt") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(comment_char):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"')
                conf[key] = value
    return conf

def read_yaml(name):
    conf = {}
    with open(name, 'r') as f:
        y_conf = yaml.safe_load(f)
        for key, value in y_conf.items():
            conf[key] = value
        return conf

def main():
    pass

if __name__ == "__main__":
    main()