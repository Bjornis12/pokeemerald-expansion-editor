import os
import re
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Pokemon:
    nickname: Optional[str] = ""
    species: str = ""
    gender: Optional[str] = ""
    held_item: Optional[str] = ""
    level: int = 100
    ability: Optional[str] = ""
    nature: Optional[str] = ""
    ball: Optional[str] = ""
    tera_type: Optional[str] = ""
    dynamax_level: int = -1
    is_shiny: bool = False
    is_gigantamax: bool = False
    ivs: List[Optional[int]] = field(default_factory=lambda: [None] * 6)
    evs: List[Optional[int]] = field(default_factory=lambda: [None] * 6)
    moves: List[str] = field(default_factory=list)
    happiness: Optional[int] = None

@dataclass
class Trainer:
    id: str = ""
    name: str = ""
    class_: str = ""
    pic: str = ""
    gender: str = ""
    music: str = ""
    double_battle: bool = False
    ai_flags: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)  # 🔧 lagt til denne
    mugshot: Optional[str] = None                  # 🔧 valgfritt hvis du bruker mugshot
    party: List[Pokemon] = field(default_factory=list)

class TrainerParser:
    def __init__(self):
        self.trainers: List[Trainer] = []
        self.ai_flags: List[str] = []
        self.music_tracks: List[str] = []
        self.classes: List[str] = []
        self.pics: List[str] = []

        self.species: List[str] = []
        self.moves: List[str] = []
        self.items: List[str] = []
        self.natures: List[str] = []
        self.abilities: List[str] = []
        self.balls: List[str] = []
        self.tera_types: List[str] = []

    def load_trainers(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError("Could not find trainers.party file")

        with open(path, encoding="utf-8") as f:
            data = f.read()

        blocks = re.split(r"^===\s*", data, flags=re.MULTILINE)
        self.trainers.clear()
        seen_ai, seen_music, seen_class, seen_pic = set(), set(), set(), set()

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().splitlines()
            if not lines:
                continue

            header_match = re.match(r"(TRAINER_[A-Z0-9_]+)\s*===", lines[0])
            if not header_match:
                continue
            trainer_id = header_match.group(1)
            if not trainer_id or trainer_id.startswith("TRAINER_XXXX"):
                continue  # Hopp over ubrukte eller testtrenere

            trainer_id = header_match.group(1)
            if not trainer_id or trainer_id.startswith("TRAINER_NONE"):
                continue  # Hopp over ubrukte eller testtrenere

            trainer = Trainer(id=trainer_id)
            mon: Optional[Pokemon] = None

            for line in lines[1:]:
                line = line.strip()
                if line.startswith("Name:"):
                    trainer.name = line[5:].strip()
                elif line.startswith("Class:"):
                    trainer.class_ = line[6:].strip()
                    seen_class.add(trainer.class_)
                elif line.startswith("Pic:"):
                    trainer.pic = line[4:].strip()
                    seen_pic.add(trainer.pic)
                elif line.startswith("Gender:"):
                    trainer.gender = line[7:].strip()
                elif line.startswith("Music:"):
                    trainer.music = line[6:].strip()
                    seen_music.add(trainer.music)
                elif line.startswith("Double Battle:"):
                    trainer.double_battle = "yes" in line.lower()
                elif line.startswith("AI:"):
                    flags = [f.strip() for f in line[3:].split("/")]
                    trainer.ai_flags = flags
                    seen_ai.update(flags)
                elif line.startswith("Items:"):
                    items = [i.strip() for i in line[6:].split("/") if i.strip()]
                    trainer.items = items
                elif line.startswith("Mugshot:"):
                    trainer.mugshot = line[8:].strip()
                elif re.match(r"^[A-Za-z0-9\- ']", line) and not ":" in line and not line.strip().startswith("- "):
                    if mon:
                        trainer.party.append(mon)
                    mon = Pokemon()

                    # Parse nickname, species, gender og held item
                    mon.nickname, mon.species, mon.gender, mon.held_item = self._parse_mon_line(line)
                elif mon:
                    if line.startswith("Level:"):
                        mon.level = int(line[6:].strip())
                    elif line.startswith("Ability:"):
                        mon.ability = line[8:].strip()
                    elif line.startswith("Nature:"):
                        mon.nature = line[7:].strip()
                    elif line.startswith("Ball:"):
                        mon.ball = line[5:].strip()
                    elif line.startswith("Tera Type:"):
                        mon.tera_type = line[10:].strip()
                    elif line.startswith("Dynamax Level:"):
                        mon.dynamax_level = int(line[15:].strip())
                    elif line.startswith("Shiny:"):
                        mon.is_shiny = "yes" in line.lower()
                    elif line.startswith("Gigantamax:"):
                        mon.is_gigantamax = "yes" in line.lower()
                    elif line.startswith("Happiness:"):
                        mon.happiness = int(line[10:].strip())
                    elif line.startswith("IVs:"):
                        mon.ivs = self._parse_stat_line(line[4:].strip())
                    elif line.startswith("EVs:"):
                        mon.evs = self._parse_stat_line(line[4:].strip())
                    elif line.startswith("- "):
                        move = line[2:].strip()
                        if move:
                            mon.moves.append(move)

            if mon:
                trainer.party.append(mon)
            self.trainers.append(trainer)

        self.ai_flags = sorted(seen_ai)
        self.music_tracks = sorted(seen_music)
        self.classes = sorted(seen_class)
        self.pics = sorted(seen_pic)

    def _parse_mon_line(self, line: str):
        pattern = re.compile(
            r'^(?:(?P<nickname>.*?) \((?P<species1>.*?)\)|(?P<species2>.*?))'
            r'(?: \((?P<gender>[MF])\))?'
            r'(?: @ (?P<item>.+))?$'
        )
        match = pattern.match(line.strip())
        if not match:
            return "", "", "Unknown", None  # fallback

        nickname = match.group('nickname') or ""
        species = match.group('species1') or match.group('species2') or ""
        gender = match.group('gender') or "Unknown"
        item = match.group('item') or None
        return nickname.strip(), species.strip(), gender.strip(), item.strip() if item else None


    def _parse_stat_line(self, text: str) -> List[Optional[int]]:
        result = [None] * 6
        mapping = {"HP": 0, "Atk": 1, "Def": 2, "SpA": 3, "SpD": 4, "Spe": 5}
        stats = re.findall(r"(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)", text)
        for value, name in stats:
            index = mapping.get(name)
            if index is not None:
                result[index] = int(value)
        return result

    def load_species(self, folder_path: str):
        self.species.clear()
        pattern = re.compile(r'\.speciesName\s*=\s*_\("(.+?)"\)')
        for filename in os.listdir(folder_path):
            if filename.startswith("gen_") and filename.endswith("_families.h"):
                with open(os.path.join(folder_path, filename), encoding="utf-8") as f:
                    for line in f:
                        match = pattern.search(line)
                        if match:
                            self.species.append(match.group(1))
        self.species.sort()


    def load_moves(self, filepath: str):
        self.moves.clear()
        if not os.path.exists(filepath):
            print(f"Could not find moves.h: {filepath}")
            return

        move_regex = re.compile(r"#define\s+MOVE_([A-Z0-9_]+)\s+\d+")
        seen = set()

        with open(filepath, encoding="utf-8") as f:
            for line in f:
                match = move_regex.match(line)
                if match:
                    raw_name = match.group(1)

                    if '//' in line or 'MOVE_' in raw_name:
                        continue

                    formatted = re.sub(r"_", " ", raw_name.lower()).title()

                    if formatted not in seen:
                        self.moves.append(formatted)
                        seen.add(formatted)

        self.moves.sort(key=str.lower)
        print(f"Loaded {len(self.moves)} moves.")




    def load_items(self, filepath: str):
        self.items.clear()
        self.balls.clear()
        if not os.path.exists(filepath):
            return
        pattern = re.compile(r"#define\s+ITEM_([A-Z0-9_]+)\s+\d+")
        in_ball_section = False
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if "// Poké Balls" in line:
                    in_ball_section = True
                elif "// Medicine" in line:
                    in_ball_section = False

                match = pattern.match(line)
                if match:
                    name = match.group(1).replace("_", " ").title()
                    self.items.append(name)
                    if in_ball_section:
                        self.balls.append(name)
        self.items.sort()
        self.balls.sort()

    def load_natures(self, filepath: str):
        self.natures.clear()
        if not os.path.exists(filepath):
            return
        pattern = re.compile(r"#define\s+NATURE_([A-Z_]+)\s+\d+")
        inside = False
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if "// Pokémon natures" in line:
                    inside = True
                    continue
                elif "// Pokémon stats" in line:
                    break
                if inside:
                    match = pattern.match(line)
                    if match:
                        raw = match.group(1)
                        name = raw.lower().replace("_", " ").title()
                        self.natures.append(name)
        self.natures.sort()

    def load_abilities(self, filepath: str):
        self.abilities.clear()
        if not os.path.exists(filepath):
            return
        pattern = re.compile(r"#define\s+ABILITY_([A-Z_]+)\s+\d+")
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    name = match.group(1).replace("_", " ").title()
                    self.abilities.append(name)
        self.abilities.sort()

    def load_tera_types(self, filepath: str):
        self.tera_types.clear()
        if not os.path.exists(filepath):
            return
        pattern = re.compile(r"#define\s+TYPE_([A-Z_]+)\s+\d+")
        inside = False
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if "// Pokémon types" in line:
                    inside = True
                    continue
                elif "// Pokémon egg groups" in line:
                    break
                if inside:
                    match = pattern.match(line)
                    if match:
                        raw = match.group(1)
                        if raw == "NONE":
                            continue
                        self.tera_types.append(raw.replace("_", " ").title())
        self.tera_types.sort()
