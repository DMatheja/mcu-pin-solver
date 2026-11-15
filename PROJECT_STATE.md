# Project Context & State: MCU-Validator (LLM-Modulo Framework)

## 1. Projektziel & Problemstellung
Im Rahmen einer wissenschaftlichen Studienarbeit wird ein **Neuro-Symbolisches Verifikations-Framework (LLM-Modulo)** für KI-generierten Mikrocontroller-Code (C/C++, Arduino/PlatformIO) entwickelt.

* **Das Problem:** Large Language Models (LLMs) halluzinieren bei der Code-Generierung für Embedded-Systeme häufig ungültige Hardware-Konfigurationen (z. B. Nutzung von internen SPI-Flash-Pins, Boot-/Strapping-Pins, Doppelbelegungen oder Peripherie-Konflikte wie gleichzeitige Nutzung von `ADC2` und `Wi-Fi` auf einem ESP32-C3).
* **Die Lösung:** Ein deterministischer Prüf- und Reparatur-Regelkreis:
  1. **Statische Code-Analyse (Parser):** Extrahiert Pin-Zuweisungen, genutzte Pin-Fähigkeiten (`gpio`, `adc`, `pwm`, `i2c`) und global aktive Peripherie (`wifi`, `usb_serial`) aus dem C/C++-Code.
  2. **Formale Verifikation (Microsoft Z3 SMT-Solver):** Prüft die extrahierten Anforderungen gegen eine deklarative JSON-Hardware-Datenbank (aktuell `esp32-c3.json`).
  3. **Minimal-invasive Reparatur (Z3 Optimize / MaxSMT):**
     * **SAT (Valide):** Der Code verletzt keine Hardware-Constraints und darf kompiliert werden.
     * **UNSAT (Konflikt):** Z3 berechnet über Hard- und Soft-Constraints eine minimal-invasive Alternativbelegung (fehlerfreie Original-Pins werden mit hohem Gewicht beibehalten, Strapping-Pins mit mittlerem Gewicht gemieden).
  4. **Automatischer Korrektur-Prompt (Feedback):** Aus der Diagnose und dem Z3-Modell wird ein präziser Reprompting-Text generiert, der das LLM anweist, exakt die fehlerhaften Pins auszutauschen.

---

## 2. Architektur-Prinzipien & Arbeitsweise für den Agenten
1. **100 % Datengetrieben (Kein MCU-Hardcoding):** Die Python-Z3-Engine enthält keinerlei spezifisches Wissen über den ESP32-C3. Alle Pin-Eigenschaften, Aliase und Konfliktregeln werden dynamisch aus JSON-Dateien geladen. Neue Mikrocontroller (z. B. ESP32-S3, STM32, RP2040) werden ausschließlich über neue JSON-Dateien ergänzt.
2. **Zweistufiges Vorgehen (WICHTIG für die Zusammenarbeit):**
   * **Aktueller Stand (Flaches 3-Dateien-MVP):** Um die Komplexität für den Einstieg gering zu halten, läuft das System aktuell als kompaktes 3-Dateien-Setup (`esp32-c3.json`, `validator.py`, `test_sketch.cpp`) in einem einzelnen Ordner.
   * **Ziel-Architektur (Clean Architecture Package):** Erst wenn das flache MVP vollständig verstanden und mit PlatformIO getestet ist, wird der Code schrittweise in das modulare `src`-Package-Layout überführt.
3. **Pacing-Regel für KI-Agenten:** Der Entwickler ist Programmier-Einsteiger. Erkläre Änderungen kleinschrittig, liefere pro Interaktion maximal 1–2 Dateien und gib immer an, wie der Schritt sofort im Terminal getestet werden kann.

---

## 6. Nächste offene Aufgaben (Roadmap für den Agenten)

1. **Aufgabe 1 (Sofort-Ziel heute): Lokalen Testlauf verifizieren**
   * Sicherstellen, dass `python validator.py` fehlerfrei durchläuft und das erwartete `UNSAT`-Ergebnis mit dem Korrektur-Prompt im Terminal ausgibt.
2. **Aufgabe 2 (Heute): Einfache PlatformIO-Anbindung des Minimal-MVPs**
   * Ein kurzes Pre-Build-Skript (`pio_check.py` bzw. `extra_scripts = pre:...` in der `platformio.ini`) schreiben, das genau diese `validator.py` vor dem Kompilieren in PlatformIO aufruft und den Build bei Konflikten stoppt.
3. **Aufgabe 3 (Späterer Ausbau für die Studienarbeit): Modulare Aufteilung (Clean Architecture)**
   * Sobald das MVP mit PlatformIO läuft, schrittweise Aufteilung der `validator.py` in `models.py`, `solver.py`, `parser.py`, `feedback.py` und `pyproject.toml`.
4. **Aufgabe 4 (Späterer Ausbau): Parser- & JSON-Erweiterung**
   * Umstieg von Regex auf `tree-sitter` für komplexe C/C++-Strukturen.
   * Erweiterung der JSON- und Z3-Logik um geteilte Bus-Pins (I2C SDA/SCL dürfen von mehreren Sensoren gemeinsam genutzt werden) und geteilte PWM-/Timer-Kanäle.
