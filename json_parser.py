# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 01:33:31 2022

@author: Asterisk
"""
import xml.etree.ElementTree as ET
import json
from pathlib import Path

npc_overloads = {}


def load_npc_names(path):
    npcNames = load_text_file(path)
    remapping = {}
    for ids in npcNames:
        if str(ids)[0] == "1":
            remapping[int(str(ids)[1:-1])] = npcNames[ids]
    for key in npc_overloads:
        remapping[key] = npc_overloads[key]
    return remapping


def parse_npc_dialogue(path):
    dialogues = {}

    def get_dialogue(npc_id, section_id):
        if not npc_id in dialogues:
            dialogues[npc_id] = {}
        sections = dialogues[npc_id]
        if section_id not in sections:
            sections[section_id] = []
        return sections[section_id]

    data = load_text_file(path)
    for identifier, line in data.items():
        line = line.strip()
        if not line:
            continue
        # step = identifier % 1000
        section = (identifier // 1000) % 100
        npc = identifier // 100000
        get_dialogue(npc, section).append(line)
    return dialogues


def load_text_file(path):
    tree = ET.parse(path)
    root = tree.getroot()
    text_elements = list(list(root)[3])
    elements = {}
    for element in text_elements:
        identifier = int(element.items()[0][1])
        text = element.text
        if "%null%" not in text:
            elements[identifier] = text
    return elements


def pairedTextFiles(path0, path1):
    merged = {}
    l, r = map(load_text_file, [path0, path1])
    for key in l:
        if key in r:
            merged[key] = (l[key], r[key])
        else:
            merged[key] = (l[key], "")
    for key in r:
        if key not in merged:
            merged[key] = ("", r[key])
    return merged


def prepare_json(**kwargs):
    texts = {key: load_text_file(path) for key, path in kwargs.items()}
    merged = {}

    def get_dict(id):
        if id not in merged:
            merged[id] = {}
        return merged[id]

    for key, loaded in texts.items():
        for id, text in loaded.items():
            info = get_dict(id)
            info[key] = text

    return merged


def singleTextFiles(path):
    l = load_text_file(path)
    m = {}
    for key in l:
        m[key] = ("", l[key])
    return m


root = Path(r"./GameText/GR/data/INTERROOT_win64/msg/engUS")
dump_folder = Path(__file__).resolve().parent / "json"
dump_folder.mkdir(exist_ok=True)


def dump_json(entity_type, *args):
    files = {
        att: root / (entity_type.title() + att.title() + ".fmg.xml") for att in args
    }
    dump = prepare_json(**files)
    with open(dump_folder / f"{entity_type}.json", "w") as f:
        json.dump(dump, f)


for entity_type in ("accessory", "arts", "gem", "goods", "protector", "weapon"):
    dump_json(entity_type, "name", "caption")

npc_map = load_npc_names(root / "NpcName.fmg.xml")
dialogues = parse_npc_dialogue(root / "TalkMsg.fmg.xml")
for key in dialogues:
    if key in npc_map:
        dialogues[key]["name"] = npc_map[key]

with open(dump_folder / "npc_dialogues.json", "w") as f:
    json.dump(dialogues, f)
