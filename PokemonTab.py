# PokemonTab.py
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QComboBox, QLineEdit, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal


STAT_NAMES = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]


class PokemonTab(QWidget):
    """
    One tab per Pokémon in the trainer’s party
    ----------------------------------------------------
    ┌──────────────┬──────────────────────┐
    │ Basic/Moves  │  Advanced details    │  (side-by-side)
    └──────────────┴──────────────────────┘
    EV row  (6 spin-boxes) ──────────────────────────────
    IV row  (6 spin-boxes) ──────────────────────────────
    Pokémon front sprite (left-aligned)
    """
    species_changed = pyqtSignal(str)  # signal: ny art
    def __init__(
        self,
        pokemon,                   # dataclass instance
        species_list, move_list, item_list,
        nature_list, ability_list, ball_list, tera_types,
        project_root               # root folder of the ROM project
    ):
        super().__init__()
        self.project_root = project_root

        # ========== 1. TOP ROW (two group-boxes) ==========
        top_hbox = QHBoxLayout()

        # -- left: basic info + moves
        left_group = QGroupBox("Basic Info & Moves")
        left_form = QFormLayout()
        self.species = QComboBox()
        unique_species = sorted(set(species_list), key=str.casefold)
        self.species.addItems(unique_species)
        self.species.setCurrentText(pokemon.species)
        left_form.addRow("Species:", self.species)
        self.pokemon = pokemon
        self.nickname = QLineEdit(pokemon.nickname or "")
        left_form.addRow("Nickname:", self.nickname)

        self.level = QSpinBox()
        self.level.setRange(1, 100)
        self.level.setValue(pokemon.level)
        left_form.addRow("Level:", self.level)

        self.gender = QComboBox()
        self.gender.addItems(["None", "M", "F"])
        self.gender.setCurrentText(pokemon.gender or "None")
        left_form.addRow("Gender:", self.gender)

        self.held_item = QComboBox()
        self.held_item.addItems(["None"] + item_list)
        self.held_item.setCurrentText(pokemon.held_item or "None")
        left_form.addRow("Held Item:", self.held_item)

        # Moves
        self.move_inputs = []
        for i in range(4):
            cb = QComboBox()
            cb.addItems(["None"] + move_list)
            cb.setCurrentText(
                pokemon.moves[i] if i < len(pokemon.moves) and pokemon.moves[i] else "None"
            )
            self.move_inputs.append(cb)
            left_form.addRow(f"Move {i+1}:", cb)

        left_group.setLayout(left_form)
        top_hbox.addWidget(left_group)

        # -- right: advanced details
        right_group = QGroupBox("Advanced Details")
        right_form = QFormLayout()

        self.ability = QComboBox()
        self.ability.addItems(["None"] + ability_list)
        self.ability.setCurrentText(pokemon.ability or "None")
        right_form.addRow("Ability:", self.ability)

        self.nature = QComboBox()
        self.nature.addItems(["None"] + nature_list)
        self.nature.setCurrentText(pokemon.nature or "None")
        right_form.addRow("Nature:", self.nature)

        self.ball = QComboBox()
        self.ball.addItems(["None"] + ball_list)
        self.ball.setCurrentText(pokemon.ball or "None")
        right_form.addRow("Ball:", self.ball)

        self.tera_type = QComboBox()
        self.tera_type.addItems(["None"] + tera_types)
        self.era_type = pokemon.tera_type or "None"
        self.tera_type.setCurrentText(self.era_type)
        right_form.addRow("Tera Type:", self.tera_type)

        self.shiny = QCheckBox("Shiny")
        self.shiny.setChecked(pokemon.is_shiny)
        right_form.addRow(self.shiny)

        self.gigantamax = QCheckBox("Gigantamax")
        self.gigantamax.setChecked(pokemon.is_gigantamax)
        right_form.addRow(self.gigantamax)

        self.dynamax_level = QSpinBox()
        self.dynamax_level.setRange(0, 10)
        self.dynamax_level.setValue(max(0, pokemon.dynamax_level))
        right_form.addRow("Dynamax Level:", self.dynamax_level)

        self.happiness = QSpinBox()
        self.happiness.setRange(0, 255)
        self.happiness.setValue(pokemon.happiness or 0)
        right_form.addRow("Happiness:", self.happiness)

        right_group.setLayout(right_form)
        right_group.setFixedWidth(300)
        top_hbox.addWidget(right_group)

        # ========== 2. EV / IV ROWS ==========
        bottom_form = QFormLayout()

        def stat_row(values, maximum):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            spins = []
            for v in values:
                sb = QSpinBox()
                sb.setRange(0, maximum)
                sb.setFixedWidth(45)
                sb.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
                sb.setValue(v if v is not None else 0)
                spins.append(sb)
                row_layout.addWidget(sb)
            row_layout.addStretch()
            return row_widget, spins

        ev_container, self.ev_spins = stat_row(pokemon.evs, 252)
        for sb in self.ev_spins:
            sb.valueChanged.connect(self.limit_total_evs)
        bottom_form.addRow("EVs   HP/Atk/Def/SpA/SpD/Spe:", ev_container)

        iv_container, self.iv_spins = stat_row(pokemon.ivs, 31)
        bottom_form.addRow("IVs   HP/Atk/Def/SpA/SpD/Spe:", iv_container)

        # ========== 3. IMAGE ==========
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.update_image(pokemon.species)
        # Oppdater bilde når species endres
        self.species.currentTextChanged.connect(self.on_species_changed)

        # ========== 4. MAIN V-BOX ==========
        main_vbox = QVBoxLayout()
        main_vbox.addLayout(top_hbox)
        main_vbox.addLayout(bottom_form)
        main_vbox.addWidget(self.image_label)
        main_vbox.addStretch()

        self.setLayout(main_vbox)

    # ----------------- HELPERS -----------------
    def limit_total_evs(self):
        total = sum(sb.value() for sb in self.ev_spins)
        if total > 510:
            sender = self.sender()
            sender.blockSignals(True)
            sender.setValue(sender.value() - (total - 510))
            sender.blockSignals(False)

    def apply_changes(self):
        self.pokemon.nickname        = self.nickname.text().strip()
        self.pokemon.species         = self.species.currentText().strip()
        self.pokemon.level           = self.level.value()
        self.pokemon.gender          = self.gender.currentText().strip() if self.gender.currentText() != "None" else ""
        self.pokemon.held_item       = self.held_item.currentText().strip() if self.held_item.currentText() != "None" else ""
        self.pokemon.ability         = self.ability.currentText().strip() if self.ability.currentText() != "None" else ""
        self.pokemon.nature          = self.nature.currentText().strip() if self.nature.currentText() != "None" else ""
        self.pokemon.ball            = self.ball.currentText().strip() if self.ball.currentText() != "None" else ""
        self.pokemon.tera_type       = self.tera_type.currentText().strip() if self.tera_type.currentText() != "None" else ""
        self.pokemon.dynamax_level   = self.dynamax_level.value()
        self.pokemon.happiness = self.happiness.value() if self.happiness.value() > 0 else None
        self.pokemon.is_shiny        = self.shiny.isChecked()
        self.pokemon.is_gigantamax   = self.gigantamax.isChecked()

        # Moves
        self.pokemon.moves = [
            cb.currentText().strip()
            for cb in self.move_inputs
            if cb.currentText().strip() and cb.currentText() != "None"
        ]

        # IVs / EVs – hent fra spinnere hvis de finnes
        if hasattr(self, "iv_spins"):
            self.pokemon.ivs = [s.value() if s.value() >= 0 else None for s in self.iv_spins]
        if hasattr(self, "ev_spins"):
            self.pokemon.evs = [s.value() if s.value() > 0 else None for s in self.ev_spins]




    def update_image(self, species_name):
        base_path = os.path.join(self.project_root, "graphics", "pokemon")
        species_folder = species_name.lower().replace(" ", "_")
        target_folder = os.path.join(base_path, species_folder)

        anim_path = os.path.join(target_folder, "anim_front.png")
        front_path = os.path.join(target_folder, "front.png")

        chosen_path = anim_path if os.path.exists(anim_path) else (
            front_path if os.path.exists(front_path) else None
        )

        if chosen_path:
            pixmap = QPixmap(chosen_path)
            if chosen_path.endswith("anim_front.png"):
                # Vis kun øverste halvdel
                cropped = pixmap.copy(0, 0, pixmap.width(), pixmap.height() // 2)
                pixmap = cropped
            scaled = pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("(No image found)")

    def on_species_changed(self, new_species):
        self.update_image(new_species)
        self.species_changed.emit(new_species)

