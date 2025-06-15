from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import List

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTabWidget,
    QMessageBox,
)


class EventScriptEditor(QWidget):
    """
    Generates Poryscript for Trainer battles, Dialog, and Starter events.

    • After pressing **Generate**, the widget reveals:
      – A short “script-ID” you paste into the Object Event in PoryMap  
      – The full Poryscript snippet (read-only) for copy-&-paste  
    • Every script is logged to **generated_scripts.txt** in the same folder
      as the .py / .exe.
    • NEW: each generated script is automatically appended to the selected
      map’s **scripts.pory** file. If a script with the same ID already
      exists, the user is warned (in English) that overwriting may break the
      build and is advised to use a unique name instead.
    """

    # ------------------------------------------------------------------ #
    #  INIT                                                              #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        project_folder: str = "",
        species_list: List[str] | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.project_folder = project_folder
        self.species_list = species_list or ["Bulbasaur", "Charmander", "Squirtle"]

        # ---------- map selector ----------
        self.setWindowTitle("Event Script Editor")
        self.comboMapName = QComboBox()
        map_box = QVBoxLayout()
        map_box.addWidget(QLabel("Select map:"))
        map_box.addWidget(self.comboMapName)

        # ---------- tabs ----------
        self.tabWidget = QTabWidget()
        self._build_trainer_tab()
        self._build_dialog_tab()
        self._build_starter_tab()

        # ---------- assemble ----------
        outer = QVBoxLayout()
        outer.addLayout(map_box)
        outer.addWidget(self.tabWidget)
        self.setLayout(outer)

        if self.project_folder:
            self.set_project_folder(self.project_folder)

    # ------------------------------------------------------------------ #
    #  TAB BUILDERS                                                      #
    # ------------------------------------------------------------------ #
    # ---- Trainer ------------------------------------------------------ #
    def _build_trainer_tab(self) -> None:
        tab = QWidget()

        self.comboTrainerID = QComboBox()
        self.trainer_script_name = QLineEdit()
        self.trainer_intro = QLineEdit()
        self.trainer_defeat = QLineEdit()
        self.trainer_post = QLineEdit()

        # hidden output widgets
        self.lbl_trainer_hint = QLabel("Use this script in PoryMap:")
        self.trainer_hint = QTextEdit()
        self.trainer_hint.setReadOnly(True)
        self.trainer_hint.setFixedHeight(32)
        self.lbl_trainer_script = QLabel("Generated Poryscript:")
        self.trainer_output = QTextEdit()
        self.trainer_output.setReadOnly(True)
        for w in (
            self.lbl_trainer_hint,
            self.trainer_hint,
            self.lbl_trainer_script,
            self.trainer_output,
        ):
            w.setVisible(False)

        gen_btn = QPushButton("Generate Trainer Script")
        gen_btn.clicked.connect(self.generate_trainer_script)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Select Trainer ID:"))
        lay.addWidget(self.comboTrainerID)
        lay.addWidget(QLabel("Script name (without prefix):"))
        lay.addWidget(self.trainer_script_name)
        lay.addWidget(QLabel("Intro text:"))
        lay.addWidget(self.trainer_intro)
        lay.addWidget(QLabel("Defeat text:"))
        lay.addWidget(self.trainer_defeat)
        lay.addWidget(QLabel("Post-battle text:"))
        lay.addWidget(self.trainer_post)
        lay.addWidget(gen_btn)
        lay.addWidget(self.lbl_trainer_hint)
        lay.addWidget(self.trainer_hint)
        lay.addWidget(self.lbl_trainer_script)
        lay.addWidget(self.trainer_output)
        tab.setLayout(lay)
        self.tabWidget.addTab(tab, "Trainer Battle")

    # ---- Dialog ------------------------------------------------------- #
    def _build_dialog_tab(self) -> None:
        tab = QWidget()

        self.dialog_script_name = QLineEdit()
        self.dialog_text = QTextEdit()

        self.lbl_dialog_hint = QLabel("Use this script in PoryMap:")
        self.dialog_hint = QTextEdit()
        self.dialog_hint.setReadOnly(True)
        self.dialog_hint.setFixedHeight(32)
        self.lbl_dialog_script = QLabel("Generated Poryscript:")
        self.dialog_output = QTextEdit()
        self.dialog_output.setReadOnly(True)
        for w in (
            self.lbl_dialog_hint,
            self.dialog_hint,
            self.lbl_dialog_script,
            self.dialog_output,
        ):
            w.setVisible(False)

        gen_btn = QPushButton("Generate Dialog Script")
        gen_btn.clicked.connect(self.generate_dialog_script)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Script name (without prefix):"))
        lay.addWidget(self.dialog_script_name)
        lay.addWidget(QLabel("Dialog text:"))
        lay.addWidget(self.dialog_text)
        lay.addWidget(gen_btn)
        lay.addWidget(self.lbl_dialog_hint)
        lay.addWidget(self.dialog_hint)
        lay.addWidget(self.lbl_dialog_script)
        lay.addWidget(self.dialog_output)
        tab.setLayout(lay)
        self.tabWidget.addTab(tab, "Dialog")

    # ---- Starter ------------------------------------------------------ #
    def _build_starter_tab(self) -> None:
        tab = QWidget()

        self.starter_script_name = QLineEdit()
        self.starter1, self.starter2, self.starter3 = QComboBox(), QComboBox(), QComboBox()
        for cb in (self.starter1, self.starter2, self.starter3):
            cb.addItems(self.species_list)
        self.starter1.setCurrentText("Bulbasaur")
        self.starter2.setCurrentText("Charmander")
        self.starter3.setCurrentText("Squirtle")

        # four hint boxes
        self.lbl_start_hint = QLabel("Use these scripts in PoryMap:")
        self.st_hint_choose = QTextEdit()
        self.st_hint_b1 = QTextEdit()
        self.st_hint_b2 = QTextEdit()
        self.st_hint_b3 = QTextEdit()
        for t in (self.st_hint_choose, self.st_hint_b1, self.st_hint_b2, self.st_hint_b3):
            t.setReadOnly(True)
            t.setFixedHeight(28)

        self.lbl_start_script = QLabel("Generated Poryscript:")
        self.starter_output = QTextEdit()
        self.starter_output.setReadOnly(True)

        # hide initially
        for w in (
            self.lbl_start_hint,
            self.st_hint_choose,
            self.st_hint_b1,
            self.st_hint_b2,
            self.st_hint_b3,
            self.lbl_start_script,
            self.starter_output,
        ):
            w.setVisible(False)

        gen_btn = QPushButton("Generate Starter Script")
        gen_btn.clicked.connect(self.generate_starter_script)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("Script name (without prefix):"))
        lay.addWidget(self.starter_script_name)
        lay.addWidget(QLabel("Select three starter Pokémon:"))
        row = QHBoxLayout()
        row.addWidget(self.starter1)
        row.addWidget(self.starter2)
        row.addWidget(self.starter3)
        lay.addLayout(row)
        lay.addWidget(gen_btn)
        lay.addWidget(self.lbl_start_hint)
        lay.addWidget(self.st_hint_choose)
        lay.addWidget(self.st_hint_b1)
        lay.addWidget(self.st_hint_b2)
        lay.addWidget(self.st_hint_b3)
        lay.addWidget(self.lbl_start_script)
        lay.addWidget(self.starter_output)
        tab.setLayout(lay)
        self.tabWidget.addTab(tab, "Starter Pokémon")

    # ------------------------------------------------------------------ #
    #  DATA HELPERS                                                      #
    # ------------------------------------------------------------------ #
    def set_species_list(self, species: list[str]) -> None:
        self.species_list = species
        for cb in (self.starter1, self.starter2, self.starter3):
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(species)
            cb.blockSignals(False)

    def set_project_folder(self, folder: str) -> None:
        self.project_folder = folder
        self._populate_map_names()
        self._load_trainer_ids()

    def _populate_map_names(self) -> None:
        self.comboMapName.clear()
        maps_dir = os.path.join(self.project_folder, "data", "maps")
        if not os.path.isdir(maps_dir):
            return
        rels = [
            os.path.relpath(r, maps_dir).replace("\\", "/")
            for r, _, files in os.walk(maps_dir)
            if "scripts.pory" in files
        ]
        self.comboMapName.addItems(sorted(rels))

    def _load_trainer_ids(self) -> None:
        if not hasattr(self, "comboTrainerID"):
            return
        self.comboTrainerID.clear()
        path = os.path.join(self.project_folder, "include", "constants", "opponents.h")
        if not os.path.isfile(path):
            return
        ids, inside = [], False
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "#define TRAINER_COUNT" in line:
                    break
                if "#define TRAINER_NONE" in line:
                    inside = True
                    continue
                if inside and line.startswith("#define TRAINER_"):
                    parts = line.split()
                    if len(parts) >= 2:
                        ids.append(parts[1])
        self.comboTrainerID.addItems(sorted(ids))

    # ------------------------------------------------------------------ #
    #  LOGGING                                                           #
    # ------------------------------------------------------------------ #
    def _base_dir(self) -> str:
        return (
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__))
        )

    def _log(self, typ: str, sid: str, desc: str, content: str) -> None:
        log_path = os.path.join(self._base_dir(), "generated_scripts.txt")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{now}] TYPE: {typ.upper()} | ID: {sid}\n"
            f"DESC: {desc}\n{'-'*40}\n{content.strip()}\n{'='*60}\n\n"
        )
        try:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(entry)
        except Exception as e:
            QMessageBox.critical(self, "Error saving log", str(e))

    # ------------------------------------------------------------------ #
    #  FILE HELPERS                                                      #
    # ------------------------------------------------------------------ #
    def _script_id_exists(self, path: str, sid: str) -> bool:
        """Return True if a script with the given ID already exists in the file."""
        if not os.path.isfile(path):
            return False
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith(f"script {sid} "):
                    return True
        return False

    def _append_to_scripts_pory(self, map_rel: str, script: str, ids: list[str]) -> None:
        """Append script to the map's scripts.pory, checking for duplicates."""
        path = os.path.join(self.project_folder, "data", "maps", map_rel, "scripts.pory")
        if not os.path.isfile(path):
            QMessageBox.critical(self, "Missing File", f"scripts.pory not found:\n{path}")
            return

        # check for duplicate IDs
        for sid in ids:
            if self._script_id_exists(path, sid):
                reply = QMessageBox.question(
                    self,
                    "Script already exists",
                    f"A script named '{sid}' already exists in scripts.pory.\n\n"
                    "Overwriting may break other parts of the pokeemerald-expansion build "
                    "if the script is already referenced. It is recommended to save with a "
                    "unique name instead.\n\nDo you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return  # cancel entire operation
                break  # user answered Yes → proceed

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{script.strip()}\n")
        except Exception as e:
            QMessageBox.critical(self, "Error Writing File", str(e))

    # ------------------------------------------------------------------ #
    #  SCRIPT GENERATORS                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_pascal(txt: str) -> str:
        return "".join(p.capitalize() for p in txt.split("_"))

    # ---- Trainer ------------------------------------------------------ #
    @pyqtSlot()
    def generate_trainer_script(self) -> None:
        map_rel = self.comboMapName.currentText()
        trainer_id = self.comboTrainerID.currentText()
        prefix = self.trainer_script_name.text().strip()
        if not (map_rel and trainer_id and prefix):
            return

        intro = self.trainer_intro.text().strip()
        defeat = self.trainer_defeat.text().strip()
        post = self.trainer_post.text().strip()

        map_name = map_rel.replace("/", "_")
        name = self._to_pascal(prefix)
        sid = f"{map_name}_{name}_Battle"

        script = f'''
script {sid} {{
    trainerbattle_single({trainer_id}, {map_name}_Text_{name}Intro, {map_name}_Text_{name}Defeated)
    msgbox({map_name}_Text_{name}PostBattle)
    waitmessage
    closemessage
    end
}}

text {map_name}_Text_{name}Intro {{
    format("{intro}")
}}

text {map_name}_Text_{name}Defeated {{
    format("{defeat}")
}}

text {map_name}_Text_{name}PostBattle {{
    format("{post}")
}}
'''.strip()

        # reveal & set
        for w in (
            self.lbl_trainer_hint,
            self.trainer_hint,
            self.lbl_trainer_script,
            self.trainer_output,
        ):
            w.setVisible(True)

        self.trainer_hint.setPlainText(sid)
        self.trainer_output.setPlainText(script)
        self._log("trainer", sid, f"Intro: {intro}", script)
        self._append_to_scripts_pory(map_rel, script, [sid])

    # ---- Dialog ------------------------------------------------------- #
    @pyqtSlot()
    def generate_dialog_script(self) -> None:
        map_rel = self.comboMapName.currentText()
        prefix = self.dialog_script_name.text().strip()
        if not (map_rel and prefix):
            return

        dialog = self.dialog_text.toPlainText().strip()
        map_name = map_rel.replace("/", "_")
        name = self._to_pascal(prefix)
        sid = f"{map_name}_{name}_Dialog"

        script = f'''
script {sid} {{
    faceplayer
    msgbox({map_name}_Text_{name}Dialog)
    waitmessage
    closemessage
    end
}}

text {map_name}_Text_{name}Dialog {{
    format("{dialog}")
}}
'''.strip()

        for w in (
            self.lbl_dialog_hint,
            self.dialog_hint,
            self.lbl_dialog_script,
            self.dialog_output,
        ):
            w.setVisible(True)

        self.dialog_hint.setPlainText(sid)
        self.dialog_output.setPlainText(script)
        self._log("dialog", sid, f"Dialog: {dialog}", script)
        self._append_to_scripts_pory(map_rel, script, [sid])

    # ---- Starter ------------------------------------------------------ #
    @pyqtSlot()
    def generate_starter_script(self) -> None:
        map_rel = self.comboMapName.currentText()
        prefix = self.starter_script_name.text().strip()
        if not (map_rel and prefix):
            return

        s1, s2, s3 = (
            self.starter1.currentText(),
            self.starter2.currentText(),
            self.starter3.currentText(),
        )
        map_name = map_rel.replace("/", "_")
        name = self._to_pascal(prefix)

        sid_choose = f"{map_name}_{name}Choose"
        sid_b1 = f"{map_name}_{name}Ball1"
        sid_b2 = f"{map_name}_{name}Ball2"
        sid_b3 = f"{map_name}_{name}Ball3"

        script = f'''
script {sid_choose} {{
    lock
    faceplayer
    msgbox({map_name}_Text_{name}Choose)
    waitmessage
    closemessage
    setvar VAR_RESULT 0
    call {sid_b1}
    call {sid_b2}
    call {sid_b3}
    end
}}

script {sid_b1} {{
    checkflag FLAG_STARTER_CHOSEN_1
    if SET, return
    msgbox("You chose {s1}!")
    givepokemon {s1}, 5
    setflag FLAG_STARTER_CHOSEN_1
    removeobject THIS_EVENT
    return
}}

script {sid_b2} {{
    checkflag FLAG_STARTER_CHOSEN_2
    if SET, return
    msgbox("You chose {s2}!")
    givepokemon {s2}, 5
    setflag FLAG_STARTER_CHOSEN_2
    removeobject THIS_EVENT
    return
}}

script {sid_b3} {{
    checkflag FLAG_STARTER_CHOSEN_3
    if SET, return
    msgbox("You chose {s3}!")
    givepokemon {s3}, 5
    setflag FLAG_STARTER_CHOSEN_3
    removeobject THIS_EVENT
    return
}}

text {map_name}_Text_{name}Choose {{
    format("Choose your starter Pokémon!")
}}
'''.strip()

        for w in (
            self.lbl_start_hint,
            self.st_hint_choose,
            self.st_hint_b1,
            self.st_hint_b2,
            self.st_hint_b3,
            self.lbl_start_script,
            self.starter_output,
        ):
            w.setVisible(True)

        self.st_hint_choose.setPlainText(sid_choose)
        self.st_hint_b1.setPlainText(sid_b1)
        self.st_hint_b2.setPlainText(sid_b2)
        self.st_hint_b3.setPlainText(sid_b3)
        self.starter_output.setPlainText(script)
        self._log(
            "starter",
            sid_choose,
            f"Starters: {s1}, {s2}, {s3}",
            script,
        )
        self._append_to_scripts_pory(map_rel, script, [sid_choose, sid_b1, sid_b2, sid_b3])


# ---------------------------------------------------------------------- #
#  Run directly (optional)                                               #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ed = EventScriptEditor()
    ed.show()
    sys.exit(app.exec())
