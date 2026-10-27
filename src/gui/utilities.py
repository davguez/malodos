#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Qt-based utility helpers (wx-free compatibility layer).

This module keeps the historical API shape used by legacy callers while
implementing it with PySide6 so importing it never pulls wx.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from PySide6.QtCore import QCoreApplication, QEventLoop
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressDialog,
    QVBoxLayout,
    QWidget,
)


NO_VALUE = "?"


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _parent_window(parent: Optional[QWidget] = None) -> Optional[QWidget]:
    if parent is not None:
        return parent
    app = QApplication.instance()
    if app is None:
        return None
    win = app.activeWindow()
    if win is not None:
        return win
    wins = app.topLevelWidgets()
    return wins[0] if wins else None


def show_message(message: str = "", caption: str = "", style: Any = None) -> None:
    del style
    _app()
    QMessageBox.information(_parent_window(), caption or "Malodos", message)


def ask(message: str = "", caption: str = "", default_answer: bool = True) -> bool:
    _app()
    buttons = QMessageBox.Yes | QMessageBox.No
    default_btn = QMessageBox.Yes if default_answer else QMessageBox.No
    answer = QMessageBox.question(
        _parent_window(),
        caption or "Malodos",
        message,
        buttons,
        default_btn,
    )
    return answer == QMessageBox.Yes


class MultipleButtonDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        message: str,
        choices: Sequence[str],
    ) -> None:
        super().__init__(parent)
        self.SetValue = self.set_value
        self._choice: int = -1
        self.setWindowTitle("Malodos")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message, self))

        button_box = QDialogButtonBox(self)
        for idx, label in enumerate(choices):
            btn = QPushButton(label, self)
            btn.clicked.connect(lambda _checked=False, i=idx: self.set_value(i))
            button_box.addButton(btn, QDialogButtonBox.ActionRole)
        layout.addWidget(button_box)

    def set_value(self, value: int) -> None:
        self._choice = value
        self.accept()

    @property
    def answer(self) -> int:
        return self._choice


class _PasswordDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        text: str,
        default: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or "Password")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(text, self))

        row = QHBoxLayout()
        row.addWidget(QLabel("Password:", self))
        self._line = QLineEdit(self)
        self._line.setEchoMode(QLineEdit.Password)
        self._line.setText(default or "")
        row.addWidget(self._line)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self._line.text()


def ask_password(message: str = "", default_answer: str = "") -> str:
    _app()
    dialog = _PasswordDialog(_parent_window(), "Password", message, default_answer)
    return dialog.password() if dialog.exec() == QDialog.Accepted else ""


def multichoice(
    choices: Sequence[str] | str,
    message: str = "Choose",
    caption: str = "Choose",
) -> int:
    del caption
    _app()
    if isinstance(choices, str):
        normalized = [c for c in choices.split("|") if c]
    else:
        normalized = list(choices)
    if not normalized:
        return -1

    dialog = MultipleButtonDialog(_parent_window(), message, normalized)
    return dialog.answer if dialog.exec() == QDialog.Accepted else -1


class ProgressDialog:
    def __init__(self, title: str = "") -> None:
        self._dialog: Optional[QProgressDialog] = None
        self._maximum = 100
        self._value = 0
        self._last_message = title or ""

    def new_sub_step(self, step_size: int, new_message: str = "") -> "ProgressDialog":
        del step_size
        if new_message:
            self._last_message = new_message
        return self

    def add_to_current_step(self, step_progress: int) -> None:
        self._value = min(self._maximum, self._value + int(step_progress))
        if self._dialog is not None:
            self._dialog.setValue(self._value)
            if self._last_message:
                self._dialog.setLabelText(self._last_message)
            QCoreApplication.processEvents(QEventLoop.AllEvents)

    def finish_current_step(self) -> None:
        if self._dialog is not None:
            self._dialog.setValue(self._maximum)
            QCoreApplication.processEvents(QEventLoop.AllEvents)

    def destroy(self) -> None:
        if self._dialog is not None:
            self._dialog.close()
            self._dialog.deleteLater()
            self._dialog = None

    def show(self) -> None:
        _app()
        self._dialog = QProgressDialog(self._last_message or "Working...", "", 0, self._maximum, _parent_window())
        self._dialog.setWindowTitle("Malodos")
        self._dialog.setMinimumDuration(0)
        self._dialog.setAutoClose(False)
        self._dialog.setAutoReset(False)
        self._dialog.setCancelButton(None)
        self._dialog.setValue(self._value)
        self._dialog.show()
        QCoreApplication.processEvents(QEventLoop.AllEvents)


def getGlobalProgressDialog(title: str) -> ProgressDialog:
    pd = ProgressDialog(title)
    pd.show()
    return pd
