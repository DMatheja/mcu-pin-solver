# Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT

## Deckblatt

**Duale Hochschule Baden-Württemberg (DHBW) Mannheim**  
Studienakademie: Mannheim (Coblitzallee)  
Studienbereich Technik – Studiengang: Angewandte Informatik

**STUDIENARBEIT**  
Modul `T3_3100` (Studienarbeit)

**Thema:**  
**Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT**  
*Konzeption, Implementierung und Evaluation einer Pre-Build-Pin-Prüfung für PlatformIO (`mcu-pin-solver`)*

| Angabe | Eintrag |
| :--- | :--- |
| Verfasser | David Matheja |
| Matrikelnummer | 9809395 |
| Kurs | TINF24AI1 |
| Dualer Partner | Freudenberg Technology Innovation (FTI) |
| Bearbeitungszeitraum | 01.10.2026 – 12.04.2027 |
| Betreuer/in bzw. Gutachter/in | `[eintragen]` |
| Softwarestand | Version `0.2.0` (PlatformIO Registry: `dmatheja/mcu-pin-solver@^0.2.0`) |
| Quellcode (Bestandteil der Abgabe) | https://github.com/DMatheja/mcu-pin-solver |

---

## Kurzfassung

Große Sprachmodelle (*Large Language Models*, LLMs) erzeugen in wenigen Sekunden C++-Code für Mikrocontroller, der syntaktisch einwandfrei wirkt und sich fehlerfrei kompilieren lässt. Bei der Wahl der Anschluss-Pins (GPIOs) unterlaufen ihnen jedoch gravierende Hardware-Fehler, die kein Compiler bemerkt: Sie verwenden Pins des internen Programmspeichers, messen analoge Sensoren über Wandler, die durch aktives WLAN gesperrt sind, legen zwei Signale eines Busses auf denselben Pin oder belegen Anschlüsse doppelt. Im industriellen Embedded-Prototyping verursachen solche erst auf der Hardware entdeckten Fehler vermeidbare Fehlersuche, Umlötarbeiten oder kostspielige Leiterplatten-Neuanfertigungen.

Diese Studienarbeit konzipiert, implementiert und evaluiert `mcu-pin-solver` (Version `0.2.0`), eine Open-Source-Bibliothek und Kommandozeilenanwendung zur statischen Hardware-Pin-Prüfung *vor* dem Kompilieren. Ein Syntaxbaum-Parser auf Basis von Tree-Sitter (`tree-sitter-cpp`) analysiert ein- und mehrdateiige C/C++-Projekte ohne Ziel-Toolchain und extrahiert Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Fähigkeiten, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripherie (`wifi`, `usb_serial`). Die Prüfung erfolgt gegen schema-validierte, austauschbare JSON-Hardware-Profile, sodass neue Mikrocontroller ohne Änderung am Python-Code ergänzt werden können. Bei Konflikten löst der SMT-Solver Z3 ein dreistufig gewichtetes MaxSMT-Optimierungsproblem, das gültige Originalpins bewahrt (`1000`), Strapping-Pins meidet (`20`) und knappe ADC-/USB-Pins schont (`5`). Das Ergebnis wird mit Dateizeilen-Verweis als kopierbarer LLM-Modulo-Reparatur-Prompt ausgegeben; ein PlatformIO-Pre-Build-Hook bricht fehlerhafte Builds vor dem Compilerstart ab.

Die Evaluation stützt sich auf 42 automatisierte Tests (inklusive neun End-to-End-Szenarien und plattformübergreifender CI unter Windows und Linux mit `ruff` und `mypy`), dreizehn Grenzfallexperimente im Vergleich zwischen Prototyp `v0.1.0` und Stand `v0.2.0`, Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, einen realen End-to-End-Test über die PlatformIO Registry sowie eine Wirtschaftlichkeits- und Break-even-Betrachtung. Typische CLI-Prüfläufe dauern im Median 172 bis 211 ms; fehlerhafte PlatformIO-Builds werden in 1,21 s gestoppt, während ein gültiges 20-Pin-Projekt in 7,59 ms (In-Process) geprüft wird. Grenzen bei `#ifdef`-Zweigen, `gpio_num_t`-Typen, Drittbibliotheks-Konstruktoren, quadratischem MaxSMT-Wachstum ab ca. 20 konfliktbehafteten Pins sowie die noch ausstehende großskalige LLM-Benchmark-Studie werden kritisch reflektiert.

## Abstract

Large Language Models (LLMs) generate syntactically valid embedded C++ firmware within seconds, yet they frequently introduce hardware pin faults invisible to compilers—such as assigning internal flash memory pins, reading analog channels blocked by an active Wi-Fi radio, overlapping bus lines, or duplicating GPIOs. In industrial embedded prototyping, detecting such defects only after hardware assembly leads to costly debugging cycles or board respins.

This thesis designs, implements, and evaluates `mcu-pin-solver` (version `0.2.0`), an open-source pre-build hardware pin validator for PlatformIO and standalone CLI workflows. Using Tree-Sitter (`tree-sitter-cpp`), the tool parses single- and multi-file C/C++ projects without requiring a target cross-compiler, extracting pin constants, direct numeric pin calls, required capability sets, bus-line identities (`Wire:sda`, `SPI:mosi`, etc.), and active peripherals (`wifi`, `usb_serial`). Pin requests are checked against schema-validated, declarative JSON board profiles so new microcontrollers can be supported without modifying Python code. Whenever conflicts arise, Z3 solves a three-tier weighted MaxSMT optimization problem that preserves valid original pins (`1000`), avoids strapping pins (`20`), and spares scarce ADC/USB pins (`5`), emitting a copy-paste LLM-Modulo repair prompt with `file:line` locations while halting invalid PlatformIO builds before compilation.

The evaluation covers 42 automated tests (including nine end-to-end scenarios and cross-platform Windows/Linux CI with `ruff` and `mypy`), thirteen edge-case experiments comparing prototype `v0.1.0` against `v0.2.0`, runtime and scaling benchmarks up to 20 pins and 21 files, a live PlatformIO Registry end-to-end build test, and a total-cost-of-ownership and break-even analysis. Median CLI checks take 172–211 ms, invalid PlatformIO builds abort in 1.21 s prior to compilation, and valid 20-pin projects pass in-process validation in 7.59 ms. Remaining limitations—including `#ifdef` preprocessor branches, ESP-IDF `gpio_num_t` enums, third-party constructors, quadratic MaxSMT scaling around 20 conflicting pins, and the absence of a large-scale benchmark on live LLM-generated firmware—are transparently discussed.

---

## Inhaltsverzeichnis

- [Kurzfassung](#kurzfassung)
- [Abstract](#abstract)
- [Abkürzungsverzeichnis](#abkürzungsverzeichnis)
- [Symbolverzeichnis](#symbolverzeichnis)
- [Abbildungsverzeichnis](#abbildungsverzeichnis)
- [Tabellenverzeichnis](#tabellenverzeichnis)
- [Listingverzeichnis](#listingverzeichnis)
- [1 Einleitung](#1-einleitung)
  - [1.1 Ausgangssituation](#11-ausgangssituation)
  - [1.2 Problemstellung und wirtschaftliche Relevanz](#12-problemstellung-und-wirtschaftliche-relevanz)
  - [1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen](#13-fünf-fehlerklassen-und-ihre-elektronischen-ursachen)
  - [1.4 Zielsetzung und Forschungsfragen](#14-zielsetzung-und-forschungsfragen)
  - [1.5 Methodisches Vorgehen und Aufbau der Arbeit](#15-methodisches-vorgehen-und-aufbau-der-arbeit)
- [2 Grundlagen](#2-grundlagen)
  - [2.1 Große Sprachmodelle](#21-große-sprachmodelle)
  - [2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip](#22-neuro-symbolische-ki-und-das-llm-modulo-prinzip)
  - [2.3 Quelltextanalyse: vom Text zum Syntaxbaum](#23-quelltextanalyse-vom-text-zum-syntaxbaum)
  - [2.4 Tree-Sitter](#24-tree-sitter)
  - [2.5 SAT, SMT und der Solver Z3](#25-sat-smt-und-der-solver-z3)
  - [2.6 Optimierung mit MaxSMT](#26-optimierung-mit-maxsmt)
  - [2.7 PlatformIO und der Build-Prozess](#27-platformio-und-der-build-prozess)
- [3 Verwandte Arbeiten und Stand der Technik](#3-verwandte-arbeiten-und-stand-der-technik)
  - [3.1 Neuro-symbolische Kopplung von LLMs mit formalen Solvern](#31-neuro-symbolische-kopplung-von-llms-mit-formalen-solvern)
  - [3.2 Sprachmodelle in der Embedded-, IoT- und Automatisierungsentwicklung](#32-sprachmodelle-in-der-embedded--iot--und-automatisierungsentwicklung)
  - [3.3 Klassische Werkzeuge der Embedded-Praxis](#33-klassische-werkzeuge-der-embedded-praxis)
  - [3.4 Kritische Synthese und Forschungslücke](#34-kritische-synthese-und-forschungslücke)
- [4 Anforderungsanalyse](#4-anforderungsanalyse)
  - [4.1 Akteure und Anwendungsfälle](#41-akteure-und-anwendungsfälle)
  - [4.2 Funktionale Anforderungen](#42-funktionale-anforderungen)
  - [4.3 Nicht-funktionale Anforderungen (ISO/IEC 25010:2023)](#43-nicht-funktionale-anforderungen-isoiec-250102023)
  - [4.4 Architektur-Invarianten und Systemgrenzen](#44-architektur-invarianten-und-systemgrenzen)
- [5 Konzeption und Entwurfsentscheidungen](#5-konzeption-und-entwurfsentscheidungen)
  - [5.1 Entscheidung 1: Verfahren zur Quelltextanalyse](#51-entscheidung-1-verfahren-zur-quelltextanalyse)
  - [5.2 Entscheidung 2: Verfahren zur Konfliktlösung](#52-entscheidung-2-verfahren-zur-konfliktlösung)
  - [5.3 Entscheidung 3: Zweistufiger Ablauf](#53-entscheidung-3-zweistufiger-ablauf)
  - [5.4 Entscheidung 4: Hardware-Wissen als validierte Daten](#54-entscheidung-4-hardware-wissen-als-validierte-daten)
  - [5.5 Gesamtarchitektur](#55-gesamtarchitektur)
  - [5.6 Durchgängiges Beispiel](#56-durchgängiges-beispiel)
- [6 Implementierung](#6-implementierung)
  - [6.1 Repository und Softwareumgebung](#61-repository-und-softwareumgebung)
  - [6.2 Hardware-Profile und Schema-Validierung (`board.py`)](#62-hardware-profile-und-schema-validierung-boardpy)
  - [6.3 AST-Parser (`parser.py`)](#63-ast-parser-parserpy)
  - [6.4 Regelprüfer und MaxSMT-Solver (`solver.py`)](#64-regelprüfer-und-maxsmt-solver-solverpy)
  - [6.5 Wer darf bleiben? Prioritäten bei gegenseitiger Pin-Blockade](#65-wer-darf-bleiben-prioritäten-bei-gegenseitiger-pin-blockade)
  - [6.6 Bericht, CLI und Reparatur-Prompt (`cli.py`)](#66-bericht-cli-und-reparatur-prompt-clipy)
  - [6.7 Integration in PlatformIO und Paketierung (`pio_hook.py`, `library.json`, `pyproject.toml`)](#67-integration-in-platformio-und-paketierung-pio_hookpy-libraryjson-pyprojecttoml)
- [7 Evaluation](#7-evaluation)
  - [7.1 Evaluationsdesign und Messumgebung](#71-evaluationsdesign-und-messumgebung)
  - [7.2 Automatisierte Testsuite und Regressionsszenarien](#72-automatisierte-testsuite-und-regressionsszenarien)
  - [7.3 Ausgewählte Szenarien im Detail](#73-ausgewählte-szenarien-im-detail)
  - [7.4 Grenzfallexperimente und Entwicklung von v0.1.0 zu v0.2.0](#74-grenzfallexperimente-und-entwicklung-von-v010-zu-v020)
  - [7.5 Laufzeit-, Skalierungsmessung und PlatformIO-End-to-End-Prüfung](#75-laufzeit--skalierungsmessung-und-platformio-end-to-end-prüfung)
  - [7.6 Wirtschaftliche Bewertung](#76-wirtschaftliche-bewertung)
  - [7.7 Soll-Ist-Abgleich](#77-soll-ist-abgleich)
  - [7.8 Gültigkeit der Ergebnisse (Threats to Validity)](#78-gültigkeit-der-ergebnisse-threats-to-validity)
- [8 Diskussion, Grenzen und Ausblick](#8-diskussion-grenzen-und-ausblick)
  - [8.1 Diskussion der Ergebnisse](#81-diskussion-der-ergebnisse)
  - [8.2 Verbleibende Grenzen des Systems](#82-verbleibende-grenzen-des-systems)
  - [8.3 Reflexion der KI-gestützten Entstehung](#83-reflexion-der-ki-gestützten-entstehung)
  - [8.4 Ausblick](#84-ausblick)
- [9 Fazit](#9-fazit)
- [Literaturverzeichnis](#literaturverzeichnis)
- [Anhang](#anhang)
- [Verzeichnis der verwendeten KI-Hilfsmittel](#verzeichnis-der-verwendeten-ki-hilfsmittel)
- [Ehrenwörtliche Erklärung](#ehrenwörtliche-erklärung)

---

## Abkürzungsverzeichnis

| Abkürzung | Bedeutung |
| :--- | :--- |
| ADC | *Analog-to-Digital Converter*, Analog-Digital-Wandler |
| AST | *Abstract Syntax Tree*, abstrakter Syntaxbaum |
| CDCL | *Conflict-Driven Clause Learning*, Suchverfahren in SAT-Solvern |
| CI | *Continuous Integration*, automatisierte Tests bei jeder Änderung |
| CLI | *Command Line Interface*, Kommandozeilenschnittstelle |
| CS | *Chip Select*, Auswahlleitung eines SPI-Geräts |
| CST | *Concrete Syntax Tree*, konkreter Syntaxbaum |
| GPIO | *General-Purpose Input/Output*, frei verwendbarer Anschluss |
| HIL | *Hardware-in-the-Loop*, automatisierter Test auf realer Zielhardware |
| I2C | *Inter-Integrated Circuit*, serieller Zweidrahtbus (SDA, SCL) |
| JSON | *JavaScript Object Notation*, textbasiertes Datenformat |
| LLM | *Large Language Model*, großes Sprachmodell |
| MaxSMT | *Maximum Satisfiability Modulo Theories*, Optimierungsvariante von SMT |
| MCP | *Model Context Protocol*, standardisierte Werkzeugschnittstelle für KI-Agenten |
| MILP | *Mixed-Integer Linear Programming*, gemischt-ganzzahlige lineare Optimierung |
| MCU | *Microcontroller Unit*, Mikrocontroller |
| PSRAM | *Pseudo-Static RAM*, zusätzlicher Arbeitsspeicher |
| PWM | *Pulse-Width Modulation*, Pulsweitenmodulation |
| ROI | *Return on Investment*, Kapitalrendite / Wirtschaftlichkeitskennzahl |
| SAT | *Satisfiability*, Erfüllbarkeit; auch Ergebnis „erfüllbar“ |
| SMT | *Satisfiability Modulo Theories*, Erfüllbarkeit modulo Theorien |
| SPI | *Serial Peripheral Interface*, schneller serieller Bus |
| TCO | *Total Cost of Ownership*, Gesamtkosten über den Lebenszyklus |
| UART | *Universal Asynchronous Receiver Transmitter*, serielle Schnittstelle |
| UNSAT | *Unsatisfiable*, Ergebnis „nicht erfüllbar“ |
| USB-CDC | *USB Communications Device Class*, serielle Konsole über USB |

## Symbolverzeichnis

| Symbol | Bedeutung |
| :--- | :--- |
| $\mathcal{P}$ | Menge aller im Hardware-Profil eingetragenen GPIO-Nummern eines Chips |
| $r_i$ | $i$-te aus dem Quelltext extrahierte Pin-Anforderung (`PinRequest`), $i = 1, \dots, n$ |
| $p_i^0$ | im Quelltext notierte (ursprüngliche) Pin-Nummer von $r_i$ |
| $C_i$ | Menge der von $r_i$ benötigten Fähigkeiten, z. B. $\{\texttt{adc}\}$ oder $\{\texttt{adc}, \texttt{i2c}\}$ |
| $b_i$ | optionale Bus-Leitungsrolle (`bus_group`) von $r_i$, z. B. `Wire:sda`, `SPI:mosi` oder $\bot$ (`None`) |
| $A(c)$ | über `capability_aliases` aufgelöste Menge konkreter Fähigkeiten, z. B. $A(\texttt{adc}) = \{\texttt{adc1}, \texttt{adc2}\}$ |
| $v_i$ | ganzzahlige Entscheidungsvariable in Z3 (`pin_i`): neuer Pin für $r_i$ |
| $P_i$ | Menge der für $r_i$ zulässigen Pins (Kandidatenmenge) |
| $S$ | Menge der Strapping-Pins des Chips |
| $K_i$ | Menge der Pins in $P_i$, die knappe Spezialfunktionen (`adc`/`usb`) tragen, die $r_i$ selbst nicht anfordert |
| $\mathbb{I}[\cdot]$ | Indikatorfunktion: 1, wenn die Bedingung gilt, sonst 0 |

## Abbildungsverzeichnis

- Abbildung 1.1: Pin-Multiplexing als „Rangierbahnhof“ (ESP32-C3, vereinfacht)
- Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver`
- Abbildung 2.2: Konkreter und abstrakter Syntaxbaum (schematisch)
- Abbildung 2.3: Von Tree-Sitter erzeugter Syntaxbaum eines Beispielprogramms
- Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen in MaxSMT
- Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess (`v0.2.0`)
- Abbildung 6.1: Zweistufiger Ablauf in `validate()` (`mcu_validator/solver.py`)

## Tabellenverzeichnis

- Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung
- Tabelle 3.1: Einordnung verwandter Ansätze und Forschungslücke
- Tabelle 4.1: Funktionale Anforderungen
- Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023
- Tabelle 4.3: Architektur-Invarianten
- Tabelle 5.1: Nutzwertanalyse Quelltextanalyse
- Tabelle 5.2: Nutzwertanalyse Konfliktlösung
- Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`)
- Tabelle 6.1: Dateien des Repositories (`v0.2.0`)
- Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`)
- Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen
- Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`)
- Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`)
- Tabelle 7.1: Messumgebung (`v0.2.0`)
- Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien
- Tabelle 7.3: Ergebnisse der Grenzfallexperimente (`v0.1.0` im Vergleich zu `v0.2.0`)
- Tabelle 7.4: Gemessene Laufzeiten der Regressionsszenarien (`v0.2.0`)
- Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`)
- Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung
- Tabelle 7.7: Soll-Ist-Abgleich (`v0.2.0`)
- Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`

## Listingverzeichnis

- Listing 1.1: Kompilierbares, aber auf dem ESP32-C3 fehlerhaftes Programm
- Listing 5.1: Szenario 0 (`00_flash_and_wifi_conflict.cpp`)
- Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (`v0.2.0`)
- Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (`v0.2.0`)
- Listing 6.1: Auszug aus `mcu_validator/boards/esp32-c3.json`
- Listing 6.2: Laden des Hardware-Profils (`load_board`, `mcu_validator/board.py`)
- Listing 6.3: Kollisionssichere Schlüsselvergabe (`_record_definition`, `mcu_validator/parser.py`)
- Listing 6.4: Positionsgenaue Extraktion von Fähigkeiten und Bus-Rollen (`_pin_args_for_call`)
- Listing 6.5: Aufbau der harten und weichen Z3-Bedingungen (`_add_pin_constraints`)
- Listing 6.6: Kern des PlatformIO-Hooks (`pio_hook.py`) und der Paketkonfiguration (`library.json`)
- Listing 7.1: CLI-Ausgabe für Szenario 02 (`v0.2.0`)
- Listing 7.2: CLI-Ausgabe für Szenario 03 (`v0.2.0`)
- Listing 7.3: CLI-Ausgabe für Szenario 04 (`v0.2.0`)
- Listing 7.4: CLI-Ausgabe für Szenario 05 (`v0.2.0`)
- Listing 7.5: CLI-Ausgabe für Szenario 06 (`v0.2.0`)
- Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, `v0.2.0`)

---

# Hauptteil

## 1 Einleitung

### 1.1 Ausgangssituation

Ein Programm auf einem gewöhnlichen PC muss nicht wissen, an welcher Leiterbahn welches Bauteil hängt – Betriebssystem und Treiber verbergen diese Details. Bei einem **Mikrocontroller** (*Microcontroller Unit*, MCU) wie dem ESP32-C3 oder ESP32-S3 von Espressif ist das anders. Ein Mikrocontroller ist ein vollständiger kleiner Computer auf einem einzigen Chip, und sein Programm steuert direkt elektrische Anschlüsse. Diese Anschlüsse heißen **GPIOs** (*General-Purpose Input/Output*). Jede GPIO-Nummer bezeichnet einen bestimmten Kontakt des Chips, der auf einem Entwicklungsboard wie dem `esp32-c3-devkitm-1` auf eine Stiftleiste geführt ist.

Äußerlich sehen alle Pins gleich aus. Intern sind sie aber mit unterschiedlichen Baugruppen verbunden:

- **Digitale Ein- und Ausgänge** (`gpio`) schalten zwischen 0 V und 3,3 V, etwa für LEDs, Relais oder Taster.
- **Analog-Digital-Wandler** (`adc`) messen Spannungen von Sensoren und liefern Zahlenwerte. Die ESP32-Chips besitzen zwei Wandler-Gruppen, `ADC1` und `ADC2`.
- **Pulsweitenmodulation** (`pwm`) schaltet einen Ausgang sehr schnell ein und aus, etwa zum Dimmen einer LED oder zum Ansteuern eines Motors.
- **Serielle Busse** (`i2c`, `spi`, `uart`) übertragen Daten zu Displays, Speicherkarten oder Sensoren.
- **Systemfunktionen** wie der interne Programmspeicher (SPI-Flash) oder die USB-Schnittstelle belegen ebenfalls Pins.

Weil ein Chip nicht für jede interne Funktion einen eigenen Anschluss hat, werden Funktionen über elektronische Weichen auf Pins verteilt (**Pin-Multiplexing**). Man kann sich das wie einen Rangierbahnhof vorstellen (Abbildung 1.1): Viele interne Züge teilen sich wenige Ausfahrtsgleise, und manche Gleise sind fest für bestimmte Züge reserviert.

```text
  Interne Baugruppen                 Weichen               Äußere Pins (ESP32-C3)
  ------------------                 -------               ----------------------
  Digitale Ein-/Ausgänge  ───┐                        ┌──► GPIO 0–4   (auch ADC1)
  Analog-Wandler ADC1/ADC2 ──┼──►  Pin-Multiplexing  ─┼──► GPIO 5     (ADC2)
  I2C-/SPI-/UART-Controller ─┘                        └──► GPIO 6–10, 20–21 (frei wählbar)
  Interner SPI-Flash  ────────────── fest verdrahtet ────► GPIO 11–17 (nicht nutzbar)
  USB-Schnittstelle   ────────────── fest verdrahtet ────► GPIO 18, 19 (bei USB belegt)
```
*Abbildung 1.1: Pin-Multiplexing als „Rangierbahnhof“ (ESP32-C3, vereinfacht; Pin-Angaben nach [[9]](#ref-9)).*

Mit großen Sprachmodellen (LLMs) lässt sich Firmware heute in natürlicher Sprache beschreiben, etwa: „Schreibe eine ESP32-C3-Firmware mit Status-LED, Bodenfeuchtesensor, Relais, WLAN und serieller Ausgabe über USB.“ Das Modell liefert in Sekunden strukturierten C++-Code. Empirische Untersuchungen zeigen, dass LLMs für typische Embedded-Aufgaben häufig lauffähigen Code erzeugen, jedoch nicht verlässlich beim ersten Versuch [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26). Gerade bei der Pin-Belegung ist diese Unzuverlässigkeit kritisch: Ein falsch gewählter Pin fällt beim Kompilieren nicht auf, sondern erst auf der physischen Schaltung.

### 1.2 Problemstellung und wirtschaftliche Relevanz

Listing 1.1 zeigt ein Programm, wie es ein Sprachmodell erzeugen könnte. Es lässt sich fehlerfrei übersetzen, ist auf einem ESP32-C3 aber in zwei Punkten falsch.

```cpp
#include <Arduino.h>
#include <WiFi.h>

#define STATUS_LED 12        // Fehler: GPIO 12 gehört zum internen SPI-Flash
const int SOIL_SENSOR = 5;   // Fehler: GPIO 5 ist ADC2, bei aktivem WLAN gesperrt
const int RELAY_PIN = 4;     // korrekt

void setup() {
    Serial.begin(115200);
    WiFi.begin("MyWiFi", "Password123");
    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int reading = analogRead(SOIL_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
}
```
*Listing 1.1: Kompilierbares, aber auf dem ESP32-C3 fehlerhaftes Programm.*

Dass der Compiler diese Fehler nicht findet, hat drei technische Gründe:

1. **Pins sind nur Zahlen.** Funktionen wie `pinMode(uint8_t pin, uint8_t mode)` akzeptieren jede Zahl von 0 bis 255. Für den Compiler ist `pinMode(12, OUTPUT)` genauso gültig wie `pinMode(4, OUTPUT)`.
2. **Der Compiler kennt das Platinen- und Chip-Layout nicht.** Er kennt den Befehlssatz des Prozessors, aber nicht, welche Pins intern mit dem Flash-Speicher verdrahtet sind oder auf dem Chip gar nicht existieren.
3. **Konflikte entstehen erst durch Kombination.** `analogRead(5)` ist für sich genommen zulässig. Unzulässig wird es erst, weil an anderer Stelle – möglicherweise in einer anderen Datei – `WiFi.begin(...)` aufgerufen wird. Der Compiler übersetzt jede Übersetzungseinheit einzeln und prüft solche projektweiten Wechselwirkungen nicht.

Über das rein technische Problem hinaus besitzt diese Lücke unmittelbare **wirtschaftliche Relevanz**: Bereits Boehm zeigte in seiner klassischen Untersuchung zur Software-Ökonomie, dass die Kosten zur Behebung eines Fehlers über die Phasen des Lebenszyklus stark ansteigen [[4]](#ref-4); Boehm und Basili bestätigten dieses Prinzip später auch für kleinere, iterativ arbeitende Entwicklungsteams (mit typischen Kostenfaktoren von 5:1 bis über 100:1 zwischen früher und später Entdeckung) [[5]](#ref-5). Im Embedded-Prototyping – etwa in industriellen F&E-Abteilungen wie bei Freudenberg Technology Innovation (FTI) – verstärkt sich dieser Effekt zusätzlich durch physische Hardware: Wird ein Pin-Konflikt erst nach dem Verdrahten eines Prüfstands oder nach Fertigung einer Prototyp-Leiterplatte entdeckt, entstehen nicht nur Stunden manueller Fehlersuche am Oszilloskop, sondern im ungünstigsten Fall Kosten und Lieferverzögerungen für einen Platinen-Respin. Eine automatische *Shift-Left*-Prüfung vor dem Kompilieren adressiert genau diesen Kostenhebel (vgl. Abschnitt 7.6).

### 1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen

Die technischen Handbücher der ESP32-Chips [[9]](#ref-9), [[10]](#ref-10) unterscheiden zwei Arten der Pin-Verschaltung. Die **GPIO-Matrix** ist ein flexibles digitales Koppelfeld: Digitale Signale wie I2C, SPI, UART oder PWM lassen sich über interne Multiplexer auf nahezu jeden freien Pin legen (mit minimaler zusätzlicher Signallaufzeit gegenüber Direktverbindungen). Analoge Signale (ADC), der interne Speicher und USB sind dagegen über den **IO_MUX** bzw. direkte Leiterbahnen **fest mit bestimmten Pins verbunden**. Diese physikalische Asymmetrie erklärt, warum digitale Signale meist frei verschoben werden können, während analoge Sensoren an feste Pin-Gruppen gebunden sind.

Für diese Arbeit werden fünf Fehlerklassen unterschieden. Die Einteilung stammt vom Verfasser; sie deckt die Fehler ab, gegen die das Werkzeug prüft, erhebt aber keinen Anspruch auf Vollständigkeit.

1. **Reservierte und nicht vorhandene Pins.** Beim ESP32-C3 sind GPIO 11–17 mit der Flash-Versorgung (`VDD_SPI`) bzw. dem internen SPI-Flash verbunden [[9]](#ref-9), beim ESP32-S3 GPIO 26–37 mit Flash bzw. PSRAM [[10]](#ref-10). Wer diese Pins umkonfiguriert, stört das Laden von Programmbefehlen. Hinzu kommen Nummern, die auf dem Chip gar nicht existieren – etwa GPIO 32, das vom älteren ESP32 bekannt ist, beim ESP32-C3 aber fehlt. Solche Nummern werden hier **Geister-Pins** genannt.
2. **Konflikte durch aktive Peripherie.** Bei aktivem WLAN können Anwendungen den Wandler `ADC2` nicht zuverlässig nutzen [[11]](#ref-11). Betroffen sind beim ESP32-C3 GPIO 5, beim ESP32-S3 GPIO 11–20. Entsprechend belegt die native USB-Schnittstelle die Pins GPIO 18/19 (C3) bzw. 19/20 (S3).
3. **Fehlende Fähigkeit.** Nicht jeder Pin kann alles. GPIO 6 des ESP32-C3 besitzt beispielsweise keinen Analog-Wandler; `analogRead(6)` liefert dort keine gültigen Messwerte.
4. **Doppelbelegung – und die erlaubte Ausnahme.** Zwei unabhängige Verbraucher auf demselben Pin stören sich gegenseitig. Bei Bussen wie I2C oder SPI ist das Teilen bestimmter Leitungen dagegen ausdrücklich vorgesehen: Mehrere I2C-Sensoren hängen gemeinsam an derselben `SDA`- und derselben `SCL`-Leitung. Umgekehrt dürfen `SDA` und `SCL` selbst, zwei getrennte Bus-Controller (`Wire` und `Wire1`) oder zwei SPI-Chip-Select-Leitungen (`CS`) *nicht* denselben Pin belegen.
5. **Strapping-Pins.** Beim Einschalten liest der Chip einige Pins aus, um den Boot-Modus zu bestimmen (ESP32-C3: GPIO 2, 8, 9; ESP32-S3: GPIO 0, 3, 45, 46) [[9]](#ref-9), [[10]](#ref-10). Diese Pins dürfen nach dem Start genutzt werden, eine äußere Beschaltung kann aber das Booten verhindern. Anders als die Klassen 1 bis 4 ist Klasse 5 kein harter Fehler, sondern ein Risiko, das bei automatischen Korrekturen gemieden werden sollte.

| Fehlerklasse | Beispiel (ESP32-C3) | Folge auf der Hardware |
| :--- | :--- | :--- |
| 1 Reservierte/fehlende Pins | `STATUS_LED = 12`, `PIR_SENSOR = 32` | Absturz bzw. wirkungsloser Code |
| 2 Aktive Peripherie | `SOIL_SENSOR = 5` (ADC2) und `WiFi.begin` | Analogmessung schlägt fehl |
| 3 Fehlende Fähigkeit | `analogRead(6)` | keine gültigen Messwerte |
| 4 Doppelbelegung | `BUZZER_PIN = 7` und `SERVO_PIN = 7`; `SDA = 6` und `SCL = 6` | Signale stören sich / Bus blockiert |
| 5 Strapping-Pins | externe Last an GPIO 2, 8 oder 9 | Chip startet ggf. nicht |

*Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung.*

### 1.4 Zielsetzung und Forschungsfragen

Ziel der Arbeit ist ein stabiles, für Entwickler und Einsteiger leicht nachvollziehbares Werkzeug, das die fünf Fehlerklassen in PlatformIO-Projekten vor dem Kompilieren erkennt, mit Dateizeilen-Verweis meldet und eine optimierte Ersatzbelegung vorschlägt, die ein Sprachmodell direkt übernehmen kann. Das Hardware-Wissen soll als schema-validierte Datendatei so vom Programmcode getrennt sein, dass sich weitere Mikrocontroller allein über eine neue JSON-Datei ergänzen lassen.

Daraus ergeben sich drei Forschungsfragen:

- **FF1 – Extraktion:** Wie lassen sich Pin-Definitionen, direkte Pin-Literale, benötigte Pin-Fähigkeiten, Bus-Leitungsrollen und aktive Peripherie über mehrere C++-Dateien hinweg zuverlässig aus dem Quelltext gewinnen, ohne die Compiler-Werkzeugkette des Zielchips vorauszusetzen?
- **FF2 – Prüfung und Reparatur:** Wie lässt sich chipspezifisches Wissen als validierbare Datenschicht vom Prüfcode trennen und so in ein Optimierungsproblem übersetzen, dass im Konfliktfall eine Ersatzbelegung entsteht, die möglichst wenig ändert, geteilte Bus-Leitungen erhält, Strapping-Pins meidet und knappe Spezialpins schont?
- **FF3 – Integration und Praxistauglichkeit:** Wie lässt sich die Prüfung so als Python- und PlatformIO-Paket einbinden, dass fehlerhafte Builds gestoppt werden, ein direkt verwertbarer Reparatur-Prompt entsteht und der Einsatz im Embedded-Prototyping wirtschaftlich sinnvoll bleibt?

**Zum Begriff „Verifikation“.** Im Titel ist von Verifikation die Rede. Gemeint ist eine formale Prüfung des *aus dem Quelltext extrahierten Pin-Modells* gegen ein *Modell der Hardware*. Es wird also nicht bewiesen, dass das gesamte Programm fehlerfrei ist. Ob die Prüfung tatsächlich alle Pin-Fehler findet, hängt davon ab, wie vollständig der Parser den Quelltext erfasst und wie genau das Hardware-Profil den Chip beschreibt (vgl. Kapitel 7 und 8).

### 1.5 Methodisches Vorgehen und Aufbau der Arbeit

Die Entwicklung folgte einem iterativen, testgetriebenen Vorgehen in zwei klar getrennten Ausbaustufen:

1. **Prototyp (`v0.1.0`):** Aufbau einer minimalen vertikalen Pipeline aus Tree-Sitter-Parser, Z3-MaxSMT-Solver, zwei Chip-Profilen (`esp32-c3`, `esp32-s3`), neun Regressionsszenarien und einem PlatformIO-Hook. Anschließend wurden gezielte Grenzfallexperimente (*Fault Injection*) durchgeführt, um systematische Schwachstellen aufzudecken.
2. **Produktionsreife Überarbeitung (`v0.2.0`):** Auf Basis dieser empirischen Befunde wurde die Architektur vollständig überarbeitet – mit eigenem, schema-validierendem Board-Modul (`board.py`), typisierten Datenklassen, Bus-Leitungsrollen (`bus_group`), dreistufiger MaxSMT-Gewichtung, korrigierter `pip`- und PlatformIO-Paketierung sowie 42 modularen Unit- und Integrationstests unter GitHub Actions CI (`ruff`, `mypy`, Windows & Linux).

Die vorliegende Ausarbeitung dokumentiert den finalen Stand **`0.2.0`** und belegt den Qualitätszuwachs gegenüber `v0.1.0` in Abschnitt 7.4 anhand identischer Experimente.

Aufbau der Arbeit: Kapitel 2 vermittelt alle theoretischen Grundlagen (LLMs, ASTs, Tree-Sitter, SAT/SMT/MaxSMT, PlatformIO) ohne Vorkenntnisse. Kapitel 3 ordnet die Arbeit kritisch in die aktuelle Literatur (u. a. Logic-LM, SatLM, LLM4PLC, AutoIOT, EmbedGenius) sowie klassische Embedded-Werkzeuge ein. Kapitel 4 formuliert Anforderungen nach ISO/IEC 25010:2023 und Architektur-Invarianten. Kapitel 5 begründet die vier zentralen Entwurfsentscheidungen mit Nutzwert- und Sensitivitätsanalysen und verfolgt ein durchgängiges Beispiel. Kapitel 6 erläutert die Implementierung aller Module top-down. Kapitel 7 evaluiert das System empirisch anhand von 42 Tests, 13 Grenzfällen, Laufzeit- und Skalierungsmessungen bis 20 Pins, einem Live-PlatformIO-Registry-Test sowie einer Wirtschaftlichkeitsbetrachtung. Kapitel 8 diskutiert Ergebnisse, verbleibende Grenzen und den KI-gestützten Entstehungsprozess; Kapitel 9 beantwortet die Forschungsfragen.

---

## 2 Grundlagen

Dieses Kapitel erklärt die drei technischen Säulen des Systems: Sprachmodelle und neuro-symbolische KI (2.1–2.2), Quelltextanalyse mit Syntaxbäumen (2.3–2.4) sowie logische Prüfung und Optimierung mit Z3 (2.5–2.6). Abschnitt 2.7 beschreibt PlatformIO.

### 2.1 Große Sprachmodelle

Ein großes Sprachmodell ist ein tiefes neuronales Netz auf Basis der *Transformer*-Architektur [[24]](#ref-24), das auf sehr großen Text- und Quellcodekorpora trainiert wurde. Es erzeugt Text schrittweise Token für Token: Aus allen bisherigen Tokens $t_1, \dots, t_{k-1}$ schätzt es die bedingte Wahrscheinlichkeit des nächsten Bausteins,

$$P(t_k \mid t_1, \dots, t_{k-1}),$$

und wählt daraus einen Baustein aus (*Next-Token-Prediction*).

> **Kurz erklärt:** Ein Sprachmodell „rechnet“ nicht nach, ob ein Pin auf dem konkreten Chip frei ist. Es schreibt die Zahl, die in statistisch ähnlichen Beispielen häufig folgt.

Für die Hardware-Pin-Belegung ergeben sich daraus drei strukturelle Schwächen:

1. **Verzerrung durch Trainingsdaten.** Im Internet existieren deutlich mehr Codebeispiele für den klassischen ESP32 (auf dem GPIO 12 oder GPIO 32 verbreitet sind) als für neuere Varianten wie den ESP32-C3. Es ist plausibel, dass Modelle solche häufigen Muster auch auf inkompatible Nachfolgechips übertragen.
2. **Fehlende globale Konsistenzprüfung.** Da Text sequenziell erzeugt wird, prüft das Modell beim Generieren von `WiFi.begin(...)` in Zeile 10 nicht rückwirkend mit formaler Garantie, ob `SOIL_SENSOR = 5` aus Zeile 5 dadurch unzulässig geworden ist.
3. **Unzuverlässige intrinsische Selbstkorrektur.** Huang et al. zeigen empirisch, dass Sprachmodelle ihre eigenen Reasoning-Fehler ohne verlässliches externes Feedback nicht konsistent korrigieren können – teilweise verschlechtern wiederholte Selbstprüfungen das Ergebnis sogar [[15]](#ref-15).

### 2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip

Garcez und Lamb beschreiben die Entwicklung der KI in drei Wellen [[13]](#ref-13): Die erste Welle war **symbolisch** – explizite Regeln und Logik, die exakt und prüfbar sind, sich aber schwer auf offene Aufgaben übertragen lassen. Die zweite Welle ist **neuronal** – statistisch lernende Netze wie LLMs, die flexibel generieren, aber keine Korrektheitsgarantien geben. Die dritte Welle, die **neuro-symbolische KI**, verbindet die Stärken beider Paradigmen.

Kambhampati et al. konkretisieren diesen Ansatz mit dem **LLM-Modulo-Framework** [[17]](#ref-17): Ein Sprachmodell erzeugt Kandidatenlösungen, während deterministische externe Prüfer (*Critics*) diese gegen formale Regeln validieren und gezieltes Korrekturfeedback liefern, bis alle Prüfungen bestanden sind. Harte Prüfer überwachen unverhandelbare Bedingungen, weiche Prüfer bewerten Qualitätskriterien.

Bildlich gesprochen ist das Sprachmodell der Architekt, der in Sekunden einen Entwurf skizziert, und `mcu-pin-solver` der Statiker, der die Tragfähigkeit nachrechnet und bei einem Mangel konkrete Ersatzwerte zurückmeldet. Abbildung 2.1 zeigt diesen Kreislauf.

```text
  ┌────────────────────────────────────────────────────────────┐
  │ 1. Generieren (LLM): Nutzerwunsch → C++-Code               │
  └──────────────────────────────┬─────────────────────────────┘
                                 ▼
  ┌────────────────────────────────────────────────────────────┐
  │ 2. Extrahieren (Tree-Sitter): Pins, Fähigkeiten, Bus-Rollen│
  └──────────────────────────────┬─────────────────────────────┘
                                 ▼
  ┌────────────────────────────────────────────────────────────┐
  │ 3. Prüfen und Reparieren (Regeln + Z3 gegen JSON-Profil)   │
  └───────────────┬──────────────────────────────┬─────────────┘
          UNSAT   ▼                              ▼   SAT
  ┌───────────────────────────────┐  ┌────────────────────────┐
  │ 4. Build stoppen, Reparatur-  │  │ Compiler startet       │
  │    Prompt ausgeben            │  └────────────────────────┘
  └───────────────┬───────────────┘
                  └──────► zurück zu 1 (LLM korrigiert Pins)
```
*Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver` (nach dem Prinzip aus [[17]](#ref-17)).*

Wichtig für die Einordnung: Das Werkzeug selbst enthält kein neuronales Netz. Es bildet die symbolische Prüf- und Reparaturkomponente im Kreislauf; „neuro-symbolisch“ ist das *Gesamtsystem* aus Sprachmodell und Verifikator.

### 2.3 Quelltextanalyse: vom Text zum Syntaxbaum

Um Pin-Zuweisungen zuverlässig zu erkennen, genügt keine einfache Textsuche mit **regulären Ausdrücken** (*Regex*). Reguläre Ausdrücke erfassen in der Chomsky-Hierarchie lediglich Typ-3-Sprachen (reguläre Sprachen) [[14]](#ref-14). Sie können weder beliebig geschachtelte Klammerstrukturen noch syntaktische Kontexte von C++ (Typ-2-/kontextsensitiv) sicher unterscheiden. Eine Regex-Suche scheitert daher an typischen Alltagsfällen:

1. Kommentare: `// WiFi.begin("Test");` würde fälschlich als aktiver WLAN-Aufruf gewertet.
2. Zeichenketten: `Serial.println("Bitte nicht WiFi.begin() aufrufen");` ebenso.
3. Lokale Variablen: `for (int i = 0; ...)` oder `int retries = 12;` ähneln äußerlich globalen Pin-Deklarationen.
4. Formatierung: In C++ sind beliebige Leerzeichen wie `WiFi . begin()` erlaubt.

Ein **Parser** arbeitet stattdessen wie das Frontend eines Compilers [[1]](#ref-1): Zuerst zerlegt die *lexikalische Analyse* den Quelltext in Tokens (`const`, `int`, `LED`, `=`, `12`, `;`), anschließend baut die *syntaktische Analyse* daraus einen Baum auf. Man unterscheidet den **konkreten Syntaxbaum** (CST), der jedes Satzzeichen enthält, vom **abstrakten Syntaxbaum** (AST), der nur die semantisch tragende Struktur darstellt (Abbildung 2.2).

```text
Quelltext:  const int LED = 12;

Konkreter Syntaxbaum (CST)                Abstrakter Syntaxbaum (AST)
declaration                               declaration
 ├── const                                 ├── Typ:  int
 ├── int                                   └── Name: LED, Wert: 12
 ├── init_declarator
 │    ├── LED
 │    ├── =
 │    └── 12
 └── ;
```
*Abbildung 2.2: Konkreter und abstrakter Syntaxbaum (schematisch).*

> **Kurz erklärt:** Im Syntaxbaum ist ein Kommentar ein Knoten vom Typ `comment` und eine Zeichenkette ein Knoten vom Typ `string_literal`. Wer gezielt nach `call_expression`-Knoten sucht, kann von Kommentaren und Strings prinzipiell nicht getäuscht werden.

### 2.4 Tree-Sitter

**Tree-Sitter** ist ein inkrementeller Parser-Generator mit fertigen Grammatiken für zahlreiche Programmiersprachen, darunter C++ (`tree-sitter-cpp`) [[6]](#ref-6). Für diese Arbeit sind drei Eigenschaften ausschlaggebend:

1. **Fehlertoleranz.** Tree-Sitter liefert auch bei unvollständigem Code oder fehlenden System-Headern (`Arduino.h`, ESP-IDF) einen nutzbaren Baum und markiert unklare Abschnitte lokal als Fehlerknoten.
2. **Kein Ziel-Compiler erforderlich.** Es genügt eine leichte Python-Bibliothek ohne installierte Cross-Compiler-Toolchain.
3. **Benannte Felder und exakte Positionen.** Obwohl Tree-Sitter intern einen konkreten Baum erzeugt, bieten benannte Felder (`name`, `value`, `function`, `arguments`) sowie Zeilenkoordinaten (`start_point.row`) eine komfortable abstrakte Sicht.

Eine grundsätzliche Grenze bleibt zu beachten: Tree-Sitter führt **keinen C-Präprozessor** aus und betreibt **keine Typauflösung**. Makros werden nicht expandiert, und sämtliche Zweige einer `#ifdef`-Weiche erscheinen gleichzeitig im Baum. Abbildung 2.3 zeigt den realen Baum eines Beispielprogramms.

```cpp
// WiFi.begin()
#define STATUS_LED 12 // Board-LED
const int SOIL_SENSOR = 5;
void setup() {
    WiFi.begin("MyWiFi");
    analogRead(SOIL_SENSOR);
}
```

```text
translation_unit
  comment                              '// WiFi.begin()'
  preproc_def
    name: identifier                   'STATUS_LED'
    value: preproc_arg                 '12 // Board-LED'
  declaration
    type_qualifier                     'const'
    type: primitive_type               'int'
    declarator: init_declarator
      declarator: identifier           'SOIL_SENSOR'
      value: number_literal            '5'
  function_definition
    ...
    body: compound_statement
      expression_statement
        call_expression
          function: field_expression   'WiFi' . 'begin'
          arguments: argument_list
            string_literal             '"MyWiFi"'
      expression_statement
        call_expression
          function: identifier         'analogRead'
          arguments: argument_list
            identifier                 'SOIL_SENSOR'
```
*Abbildung 2.3: Von Tree-Sitter erzeugter Syntaxbaum eines Beispielprogramms (gekürzte Ausgabe des Versuchsskripts, siehe Anhang G).*

Für die Implementierung sind drei Details unmittelbar entscheidend: Auskommentierte Aufrufe erscheinen als `comment`, Zeichenketten als `string_literal` innerhalb der Argumente, und der Wert eines `#define` (`preproc_arg`) enthält den gesamten Rest der Zeile **einschließlich eines nachfolgenden Kommentars** (`'12 // Board-LED'`), der lokal entfernt werden muss.

### 2.5 SAT, SMT und der Solver Z3

Zur Prüfung und Neuberechnung von Pin-Belegungen verwendet `mcu-pin-solver` den SMT-Solver **Z3** von Microsoft Research [[7]](#ref-7). Drei Konzepte bauen dabei aufeinander auf [[2]](#ref-2):

- **SAT (Erfüllbarkeit):** Ein SAT-Solver entscheidet, ob eine aussagenlogische Formel durch Belegung boolescher Variablen erfüllbar (`SAT`) oder unerfüllbar (`UNSAT`) ist. Moderne SAT-Solver nutzen *Conflict-Driven Clause Learning* (CDCL), um aus jedem Widerspruch neue Klauseln zu lernen und ganze Teilbäume des Suchraums sofort auszuschließen.
- **SMT (Erfüllbarkeit modulo Theorien):** Da GPIO-Nummern ganze Zahlen sind, erweitert SMT das SAT-Problem um mathematische Hintergrundtheorien. Für Pin-Zuweisungen genügt die quantorenfreie lineare Ganzzahlarithmetik (**`QF_LIA`**), die entscheidbar ist [[2]](#ref-2): Jedes Signal entspricht einer ganzzahligen Entscheidungsvariablen $v_i$, für die Bedingungen wie $v_{\text{LED}} \in \{0, 1, \dots\}$ und $v_{\text{LED}} \neq v_{\text{Relais}}$ direkt formuliert werden.
- **DPLL($T$):** Intern koppelt Z3 einen CDCL-SAT-Kern mit einem spezialisierten Theorie-Solver für Ganzzahlvergleiche, sodass auch kombinatorisch gekoppelte Pin-Konflikte exakt entschieden werden.

### 2.6 Optimierung mit MaxSMT

Ein gewöhnlicher SMT-Solver liefert *irgendeine* gültige Lösung und dürfte dabei auch bereits korrekte Pins verschieben. Auf einer realen Schaltung wäre das unpraktisch, weil unnötig viele Leitungen umverdrahtet werden müssten. Gesucht ist daher eine **minimal-invasive** Reparatur, die zusätzlich hardwarefreundliche Pins bevorzugt.

Dafür nutzt das Werkzeug die Z3-Optimierungserweiterung $\nu Z$ (`z3.Optimize`) [[3]](#ref-3), die zwischen **harten Bedingungen** (`opt.add`, physikalisch unverhandelbar) und **weichen Bedingungen** (`opt.add_soft`, gewichtete Wünsche) unterscheidet (Abbildung 2.4).

```text
  HARTE BEDINGUNGEN (müssen gelten)
  • jeder Pin existiert, ist nicht reserviert und besitzt alle benötigten Fähigkeiten
  • keine Sperre durch aktive Peripherie (z. B. ADC2 bei WLAN, USB-Pins bei Serial)
  • verschiedene Signale auf verschiedenen Pins –
    außer Signale derselben geteilten Bus-Leitung (z. B. Wire:sda), die zusammenbleiben
                              │
                              ▼  unter allen gültigen Lösungen:
  WEICHE BEDINGUNGEN (dreistufige Punkte-Rangfolge)
  • +1000 Punkte (Stufe 1): Signal behält seinen gültigen Originalpin
  •   +20 Punkte (Stufe 2): Signal belegt keinen Strapping-Pin
  •    +5 Punkte (Stufe 3): Signal schont knappe Spezialpins (ADC/USB), wenn nicht benötigt
```
*Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen in MaxSMT.*

Intern löst Z3 solche gewichteten MaxSMT-Probleme standardmäßig mit dem kernbasierten Verfahren *MaxRes* [[18]](#ref-18): Es identifiziert wiederholt sich gegenseitig ausschließende Wunschgruppen (*unerfüllbare Kerne*) und lockert jeweils die Gruppe mit dem kleinsten Gewicht. Gewichtetes MaxSMT ist im allgemeinen Fall NP-schwer; die konkrete Skalierungsgrenze für Embedded-Pin-Probleme bis 20 Signale wird in Abschnitt 7.5 empirisch vermessen.

### 2.7 PlatformIO und der Build-Prozess

**PlatformIO** ist eine weit verbreitete Entwicklungsumgebung für Mikrocontroller [[20]](#ref-20). Ein Projekt wird über `platformio.ini` konfiguriert (`board`, `lib_deps`, `extra_scripts`). Ein Zusatzskript mit Präfix `pre:` – ebenso das in einer Bibliothek über `library.json` deklarierte `extraScript` – läuft im Build-System SCons **vor** dem Start des C++-Compilers und kann den Build mit `env.Exit(1)` abbrechen. `mcu-pin-solver` nutzt diesen Mechanismus als automatische Qualitäts-Schranke.

> **Zwischenfazit Kapitel 2:** Tree-Sitter erschließt die *Quelltextstruktur* ohne Cross-Compiler, Z3 garantiert *formale Korrektheit und Optimalität* relativ zum Hardware-Modell, und PlatformIO stellt den *frühestmöglichen Eingriffspunkt* vor dem Kompilieren bereit.

---

## 3 Verwandte Arbeiten und Stand der Technik

Dieses Kapitel ordnet `mcu-pin-solver` in drei Forschungs- und Praxisbereiche ein: (1) neuro-symbolische Kopplung von LLMs mit formalen Solvern, (2) LLM-gestützte Embedded- und Automatisierungsentwicklung sowie (3) etablierte Werkzeuge der Embedded-Praxis. Ziel ist nicht nur eine Aufzählung, sondern eine kritische Herausarbeitung der jeweiligen Stärken, Grenzen und der daraus abgeleiteten Forschungslücke.

### 3.1 Neuro-symbolische Kopplung von LLMs mit formalen Solvern

Die Erkenntnis, dass Sprachmodelle bei kombinatorischer Suche und logischer Konsistenz systematisch halluzinieren und sich ohne externes Korrektiv nicht verlässlich selbst korrigieren können [[15]](#ref-15), hat ab 2023 eine Welle neuro-symbolischer Architekturen ausgelöst [[13]](#ref-13). Drei richtungsweisende Arbeiten bilden das theoretische Fundament dieser Studienarbeit:

- **Logic-LM** (Pan et al., Findings of EMNLP 2023) [[19]](#ref-19) übersetzt natürlichsprachliche Logikprobleme mithilfe eines LLMs in formale Repräsentationen (u. a. Prädikatenlogik erster Stufe), übergibt diese an deterministische Solver und nutzt deren Fehlermeldungen in einer *Self-Refinement*-Schleife zur Korrektur fehlerhafter Formalisierungen.
- **SatLM** (Ye et al., NeurIPS 2023) [[27]](#ref-27) überträgt dieses Prinzip explizit auf **SAT/SMT-Solver**: Statt das LLM schrittweise imperative Lösungsprogramme schreiben zu lassen, generiert es eine deklarative Constraint-Spezifikation, während ein automatischer Theorembeweiser die kombinatorische Suche vollständig übernimmt. Die Autoren zeigen überzeugend, dass dadurch Planungs- und Suchfehler drastisch sinken.
- **LLM-Modulo** (Kambhampati et al., ICML 2024) [[17]](#ref-17) verallgemeinert diesen Gedanken zu einer Architektur aus Generator (LLM) und heterogenen externen Prüfern (*Critics*), die harte Korrektheits- und weiche Qualitätskriterien trennen.

**Kritische Reflexion und eigene Abgrenzung.** Sowohl *Logic-LM* [[19]](#ref-19) als auch *SatLM* [[27]](#ref-27) weisen für die Embedded-Softwareentwicklung eine entscheidende Schwachstelle auf: Das **LLM selbst** muss die formale Logikspezifikation erzeugen. Halluziniert das Modell bereits bei der Übersetzung in die SMT-Formel (z. B. indem es vergisst, den `ADC2`/WLAN-Konflikt als Klausel zu notieren), liefert selbst ein perfekter SMT-Solver eine falsche Antwort. `mcu-pin-solver` dreht diese Verantwortung bewusst um: Das Sprachmodell schreibt gewöhnlichen, idiomatischen **Arduino-C++-Code**, während ein **deterministischer AST-Parser** (`tree-sitter-cpp`) zusammen mit einer **kuratierten, schema-validierten JSON-Wissensbasis** die Z3-Formel konstruiert. Übersetzungs-Halluzinationen beim Aufstellen der Hardware-Constraints sind damit strukturell ausgeschlossen; die Korrektheit hängt nur noch von der deterministischen Abdeckung des Parsers und der Datenblatt-Treue der JSON-Datei ab.

### 3.2 Sprachmodelle in der Embedded-, IoT- und Automatisierungsentwicklung

Auch im Bereich eingebetteter Systeme und der Automatisierungstechnik entstanden zwischen 2024 und 2025 mehrere bedeutende Studien und Frameworks:

- **Empirische Hardware-in-the-Loop-Studie (Englhardt et al., CHI EA 2024)** [[8]](#ref-8): Die Autoren evaluierten GPT-3.5, GPT-4 und PaLM 2 auf realer Mikrocontroller-Hardware mit Sensoren und Aktoren. Zwar erzeugte insbesondere GPT-4 für viele Aufgaben funktionierenden Code und nützliche Debugging-Hinweise, scheiterte aber wiederholt an hardware-nahen Details und benötigte menschliche Rückkopplung. Hardware-in-the-Loop-Tests (HIL) decken Fehler zuverlässig auf, setzen jedoch physisch aufgebaute Prüfstände voraus und greifen zeitlich zu spät.
- **LLM4PLC (Fakih et al., ICSE-SEIP 2024)** [[12]](#ref-12): Für speicherprogrammierbare Steuerungen (SPS) koppeln die Autoren ein Sprachmodell in einer iterativen Schleife mit Syntaxprüfer, Compiler und einem formalen Modellprüfer (NuSMV), dessen Gegenbeispiele an das LLM zurückgeführt werden. Inhaltlich ist LLM4PLC der engste konzeptionelle Verwandte zu `mcu-pin-solver`. Der wesentliche Unterschied: LLM4PLC prüft funktionales Steuerungsverhalten von SPS-Code und überlässt die eigentliche Reparatur vollständig dem Sprachmodell, während `mcu-pin-solver` auf Mikrocontroller-Pin-Constraints spezialisiert ist und die **optimierte Ersatzbelegung selbst per MaxSMT berechnet**, sodass das LLM nur noch konkrete Zahlenwerte ersetzen muss.
- **EmbedGenius (Yang et al., 2024)** [[26]](#ref-26) und **AutoIOT (Shen et al., ACM MobiCom 2025)** [[22]](#ref-22): Beide jüngeren Frameworks automatisieren die Erstellung vollständiger IoT-/Embedded-Anwendungen (u. a. für ESP32 und Arduino) mittels LLM-Agenten, Wissensabruf über Hardware-Dokumentation und iterativem Testen. Gerade diese aktuellen Arbeiten belegen eindrücklich die Relevanz des Problemfelds – sie zeigen aber ebenso, dass rein prompt- oder dokumentationsgetriebene Agenten bei komplexen Pin-Multiplexing-Konflikten ohne formalen Solver weiterhin probabilistisch raten müssen. Eine deterministische Pre-Build-Komponente wie `mcu-pin-solver` lässt sich daher komplementär als leichter „Hardware-Critic“ in solche Agenten-Pipelines integrieren.

### 3.3 Klassische Werkzeuge der Embedded-Praxis

Abseits der KI-Forschung existieren in der industriellen Embedded-Praxis vier etablierte Werkzeugklassen, die jedoch ein anderes Problem lösen:

- **Statische C++-Linter (`clang-tidy`, `cppcheck`):** Finden klassische Softwarefehler (Speicherlecks, uninitialisierte Variablen, Typkonvertierungen), besitzen aber keinerlei Modell über das Pin-Multiplexing oder die Peripherie-Wechselwirkungen eines konkreten Mikrocontrollers.
- **Grafische Hersteller-Konfiguratoren (`STM32CubeMX`)** [[23]](#ref-23): Modellieren Pin-Multiplexing und Peripheriekonflikte sehr präzise, arbeiten jedoch **top-down** – der Entwickler klickt Pins manuell in einer GUI zusammen und generiert daraus Initialisierungscode. Vorhandenen oder von einem LLM erzeugten Arduino-C++-Code können sie nicht nachträglich analysieren und reparieren.
- **Deklarative Hardware-Beschreibungen in Betriebssystemen (`Zephyr Devicetree`)** [[28]](#ref-28): Trennen Pin-Zuweisungen sauber in `.dts`-Dateien vom C-Code und prüfen sie beim Build. Im weit verbreiteten Arduino-/PlatformIO-Prototyping, auf das LLMs primär trainiert sind, stehen Pin-Definitionen jedoch direkt im C++-Quelltext.
- **Typsichere Hardware-Abstraktionen in Rust (`embedded-hal`)** [[21]](#ref-21): Nutzen das Ownership-Typsystem von Rust, um Pins als eindeutige Ressourcen abzubilden – eine Doppelbelegung scheitert bereits beim Kompilieren. Dieses elegante Prinzip steht für das riesige Ökosystem aus bestehendem Arduino-C++-Code jedoch nicht zur Verfügung und berechnet zudem keine optimierte Ausweichbelegung.

### 3.4 Kritische Synthese und Forschungslücke

Tabelle 3.1 verdichtet den Literaturvergleich entlang von fünf für die Forschungsfragen entscheidenden Kriterien.

| Ansatz / Referenz | Prüft vorhandenen Arduino-C++-Code | Deterministisches Chip-Pin-Modell | Berechnet optimierte Ersatzbelegung | Kein physischer Prüfstand / Ziel-Compiler nötig | Einbindung in LLM-Rückkopplung |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logic-LM [[19]](#ref-19) / SatLM [[27]](#ref-27) | nein (NL $\rightarrow$ Logik) | nein (LLM formalisiert selbst) | ja (Solver) | ja | ja |
| Englhardt et al. [[8]](#ref-8) | ja | indirekt über Hardware | nein | nein (HIL-Aufbau) | ja (Mensch-in-Schleife) |
| LLM4PLC [[12]](#ref-12) | nein (SPS-Code) | formaler Modellprüfer | nein (LLM repariert) | teilweise (SPS-Toolchain) | ja |
| EmbedGenius [[26]](#ref-26) / AutoIOT [[22]](#ref-22) | ja (generierter Code) | nein (RAG / Heuristik) | nein (LLM-Iteration) | nein / teilweise | ja (Agenten-Loop) |
| C++-Linter (`clang-tidy`) | ja | nein | nein | teilweise | nein |
| STM32CubeMX [[23]](#ref-23) | nein (GUI $\rightarrow$ Code) | ja | nein (nur Konfliktanzeige) | ja | nein |
| Zephyr Devicetree [[28]](#ref-28) | nein (`.dts`) | ja | nein | nein (Zephyr-Build) | nein |
| Rust `embedded-hal` [[21]](#ref-21) | nein (Rust) | teilweise (Ownership) | nein | nein (Rust-Compiler) | nein |
| **`mcu-pin-solver` (diese Arbeit)** | **ja (Teilmenge, vgl. 8.2)** | **ja (validiertes JSON)** | **ja (Z3 MaxSMT)** | **ja** | **ja (Reparatur-Prompt)** |

*Tabelle 3.1: Einordnung verwandter Ansätze und Forschungslücke.*

**Forschungslücke.** Die Literatur zeigt eine klare Lücke an der Schnittstelle zweier Welten: Neuere LLM-Embedded-Frameworks [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26) verlassen sich bei der Pin-Wahl noch auf probabilistische Selbstkorrektur oder teure Hardware-Tests, während klassische Embedded-Werkzeuge [[21]](#ref-21), [[23]](#ref-23), [[28]](#ref-28) keinen bestehenden Arduino-C++-Code ohne Ziel-Toolchain rückwärts analysieren und reparieren. Gleichzeitig zeigen Logic-LM [[19]](#ref-19), SatLM [[27]](#ref-27) und LLM-Modulo [[17]](#ref-17) das Potenzial externer SMT-Solver, überlassen aber oft die Formalisierung dem LLM selbst. Genau hier setzt `mcu-pin-solver` an: deterministische AST-Extraktion + schema-validiertes Chip-Profil + Z3-MaxSMT-Reparatur direkt als Pre-Build-Schranke in PlatformIO.

---

## 4 Anforderungsanalyse

### 4.1 Akteure und Anwendungsfälle

Das System bedient drei Nutzergruppen:

1. **Embedded-Entwicklerinnen und -Entwickler** bauen ein Projekt in PlatformIO oder rufen `mcu-validate` auf der Kommandozeile auf. Sie erwarten, dass Pin-Konflikte vor dem Kompilieren mit Dateiname und Zeilennummer klar gemeldet werden.
2. **Das Sprachmodell** erzeugt den C++-Entwurf und erhält im Konfliktfall einen kompakten, unmissverständlichen Prompt, um ausschließlich die fehlerhaften Pin-Zuweisungen zu korrigieren.
3. **Maintainer** ergänzen Unterstützung für neue Mikrocontroller über eine deklarative JSON-Datei (oder übergeben ein eigenes Profil per CLI) – ohne Python-Code zu ändern.

### 4.2 Funktionale Anforderungen

| ID | Anforderung | Beschreibung |
| :--- | :--- | :--- |
| FA-01 | Hardware-Profil laden und validieren | Aus einer Board-Kennung (z. B. `esp32-c3-devkitm-1`) oder einem direkten `.json`-Dateipfad wird das passende Profil (längstes Präfix zuerst) geladen und gegen das erwartete Schema geprüft. |
| FA-02 | Mehrere Dateien & Include-Ordner | Bei Angabe von `src/` werden alle `.h`, `.hpp`, `.c`, `.cpp`, `.ino` in `src/` und dem Nachbarordner `include/` (sowie optional per `--include-dir` übergebenen Ordnern) gelesen; Build- und Testordner (`.pio/`, `test/`, `tests/`) werden ausgelassen. |
| FA-03 | Fehlalarmfreie Extraktion | Top-Level-Pin-Konstanten (`#define`, globale `int`/`uint8_t`-Deklarationen) und direkte Pin-Literale (z. B. `pinMode(12, OUTPUT)`) werden über den Syntaxbaum gelesen; Kommentare, Zeichenketten, lokale Variablen und fachfremde Konstanten (`BAUD_RATE`, `DELAY_MS`) erzeugen keine Fehlalarme. |
| FA-04 | Eindeutige Behandlung von Widersprüchen | Gleiche Definitionen in mehreren Dateien werden zusammengefasst; widersprüchliche Definitionen desselben Namens bleiben unter eindeutig getrennten Schlüsseln sichtbar. |
| FA-05 | Fähigkeiten, Bus-Rollen und Module | Aus Funktionsaufrufen (mit genauer Positionsauswertung der Argumente) und einer Namens-Fallback-Heuristik werden Mengen benötigter Fähigkeiten (`gpio`, `adc`, `pwm`, `i2c`, `spi`, `uart`), Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) und aktive Module (`wifi`, `usb_serial`) abgeleitet. |
| FA-06 | Präzise Diagnose | Jeder Verstoß (Pin fehlt, Kollision, reserviert, Fähigkeit fehlt, Sperre durch Modul) wird einzeln mit Dateizeilen-Verweis und der konkreten Regelbegründung im Klartext gemeldet. |
| FA-07 | Kollision vs. geteilte Bus-Leitung | Unabhängige Signale, unterschiedliche Bus-Leitungen (`SDA` vs. `SCL`, `SCK` vs. `MOSI`), getrennte Bus-Instanzen (`Wire` vs. `Wire1`) und SPI-`CS`-Leitungen dürfen keinen Pin teilen; Signale derselben Bus-Leitung (z. B. zwei Geräte an `Wire:sda`) dürfen teilen und bleiben bei einer Reparatur gekoppelt. |
| FA-08 | Minimale Reparatur & Kapazitätsmeldung | Bei Konflikten wird eine gültige Belegung berechnet, die Originalpins bewahrt, Strapping-Pins meidet und knappe ADC-/USB-Pins schont. Existiert keine gültige Belegung, wird dies klar ohne `GPIO None` gemeldet. |
| FA-09 | Transparenter Bericht & Reparatur-Prompt | Die Ausgabe zeigt die Anzahl geprüfter Pins (inkl. Warnung bei 0 erkannten Pins) sowie im `UNSAT`-Fall alle Fehler und eine vollständige `Keep`/`Change`-Anweisung. |
| FA-10 | Build-Schranke und CLI | Als PlatformIO-Bibliothek (`dmatheja/mcu-pin-solver@^0.2.0`) stoppt das Werkzeug fehlerhafte Builds vor dem Kompilieren; per `pip install .` steht der CLI-Befehl `mcu-validate` eigenständig bereit. |

*Tabelle 4.1: Funktionale Anforderungen.*

### 4.3 Nicht-funktionale Anforderungen (ISO/IEC 25010:2023)

Die Qualitätsanforderungen orientieren sich an der aktuellen Ausgabe des internationalen Produktqualitätsmodells **ISO/IEC 25010:2023** (*SQuaRE*) [[16]](#ref-16), das gegenüber der Ausgabe von 2011 insbesondere die Merkmale *Flexibilität* (zuvor *Übertragbarkeit*) und *Funktionale Sicherheit (Safety)* schärft.

| ID | Merkmal (ISO/IEC 25010:2023) | Abnahmekriterium |
| :--- | :--- | :--- |
| NFA-01 | Erweiterbarkeit (Wartbarkeit – Modifizierbarkeit) | Der Python-Code enthält keine chipspezifischen Pin-Nummern oder Chipnamen; ein neuer Chip erfordert nur eine JSON-Datei. |
| NFA-02 | Zeitverhalten (Leistungseffizienz) | Ein Prüflauf für ein typisches Embedded-Projekt (bis ca. 15–20 Dateien/Pins) bleibt unter 1 s (bzw. im `SAT`-Fall deutlich darunter); Skalierungsgrenzen werden transparent vermessen. |
| NFA-03 | Plattformunabhängigkeit (Flexibilität – Anpassbarkeit) | Lauffähig unter Windows und Linux ohne installierte Compiler-Werkzeugkette des Zielchips. |
| NFA-04 | Korrektheit der Vorschläge (Funktionale Eignung & Safety) | Jeder ausgegebene Z3-Vorschlag besteht eine sofortige erneute Prüfung gegen alle harten Regeln des Hardware-Profils und verhindert hardwaregefährdende Pin-Belegungen. |
| NFA-05 | Paket-Hygiene (Flexibilität – Installierbarkeit) | Sowohl `pip install .` (inkl. gebündelter Board-JSONs) als auch die Einbindung über die PlatformIO Registry funktionieren eigenständig; Beispielcode wird nicht mitkompiliert; der CLI-Aufruf erzeugt keine Python-Warnungen. |
| NFA-06 | Testbarkeit & Codequalität (Wartbarkeit) | Eine modulare Testsuite deckt alle Kernmodule und Fehlerklassen ab und läuft in der CI zusammen mit statischer Typprüfung (`mypy`) und Linting (`ruff`). |
| NFA-07 | Lesbarkeit & Analysierbarkeit (Wartbarkeit) | Klare, top-down lesbare Gliederung in vier getrennte Kernmodule (`board.py`, `parser.py`, `solver.py`, `cli.py`) mit typisierten Datenklassen und minimalen Laufzeitabhängigkeiten (nur Z3 und Tree-Sitter). |

*Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023 [[16]](#ref-16).*

### 4.4 Architektur-Invarianten und Systemgrenzen

Sechs verbindliche Architektur-Invarianten (Tabelle 4.3) sichern die Trennung von Daten, Parsing und Solver ab und werden durch die modulare Testsuite sowie die CI automatisch überprüft.

| ID | Invariante | Regel |
| :--- | :--- | :--- |
| INV-01 | Keine Chip-Logik in Python | GPIO-Nummern, reservierte Bereiche, Strapping-Pins, Auslöser und Konfliktregeln stehen ausschließlich in `mcu_validator/boards/*.json` (oder vom Nutzer übergebenen JSON-Dateien). |
| INV-02 | Syntaxbaum zuerst | C++-Strukturen werden nur über Tree-Sitter gewonnen; reguläre Ausdrücke dienen nur zum Bereinigen kurzer, bereits aus dem Baum isolierter Bezeichner oder Funktionsnamen. |
| INV-03 | Eindeutige Schlüsselvergabe | Widersprüchliche Definitionen oder direkte Literale erhalten stets global eindeutige Namen (`_reserve_unique_key`), damit im Solver keine Variablenkollision entsteht. |
| INV-04 | Paarweise Bus-Leitungskopplung | Zwei Signale werden genau dann gekoppelt ($v_i = v_j$), wenn sie dieselbe einzelne teilbare Bus-Fähigkeit, dieselbe `bus_group` und denselben Ausgangspin besitzen; sonst gilt strikt $v_i \neq v_j$. |
| INV-05 | Strikte Gewichtsrangfolge | Originalpin behalten (`1000`) dominiert Strapping-Meidung (`20`), diese dominiert das Schonen knapper Spezialpins (`5`); harte Hardware-Regeln werden niemals abgeschwächt. |
| INV-06 | Paket-Hygiene | `package-data` in `pyproject.toml`, `srcFilter` und `export` in `library.json`; kein Import von `.cli` in `__init__.py` (vermeidet `runpy`-`RuntimeWarning`). |

*Tabelle 4.3: Architektur-Invarianten.*

**Im Umfang enthalten** sind die statische Analyse von Pin-Deklarationen, direkten Pin-Aufrufen und Peripherie-Auslösern, die Schema-Validierung und Prüfung gegen JSON-Profile, die Z3-Reparatur und die Einbindung in PlatformIO. **Nicht enthalten** sind elektrische Simulation (z. B. Strombelastbarkeit oder Pull-up-Dimensionierung), die Auswertung von Werten, die erst zur Laufzeit entstehen, sowie das automatische Überschreiben von C++-Dateien.

---

## 5 Konzeption und Entwurfsentscheidungen

Dieses Kapitel begründet die vier zentralen Entwurfsentscheidungen und verfolgt anschließend ein vollständiges Beispiel durch alle Systemschichten. Für die Verfahrensauswahl kommen Nutzwertanalysen zum Einsatz. Dabei wird offen benannt, dass Gewichte und Punkte vom Verfasser in Kenntnis der Lösung festgelegt wurden – Nutzwertanalysen machen Abwägungen transparent, ersetzen aber keinen mathematischen Beweis. Deshalb ergänzt jeweils eine Sensitivitätsanalyse, ab welcher Gewichtsänderung eine andere Option gewinnen würde.

### 5.1 Entscheidung 1: Verfahren zur Quelltextanalyse

Zur Wahl standen drei Optionen: **A – Reguläre Ausdrücke** direkt auf dem Quelltext, **B – `libclang`** (Compiler-API mit voller Präprozessor- und Typauflösung) und **C – Tree-Sitter** (`tree-sitter-cpp`). Bewertet wurde von 1 (ungenügend) bis 5 (sehr gut):

| Kriterium | Gewicht | A Regex | B `libclang` | C Tree-Sitter |
| :--- | :---: | :---: | :---: | :---: |
| K1 Robust gegen Kommentare, Zeichenketten, Schleifen (FA-03) | 25 % | 1 | 5 | 5 |
| K2 Betrieb ohne Werkzeugkette und Header des Zielchips (NFA-03) | 25 % | 5 | 2 | 5 |
| K3 Toleranz gegenüber unvollständigem Code | 15 % | 4 | 2 | 4 |
| K4 Semantische Tiefe (Makros, `#ifdef`, Typen) | 20 % | 1 | 5 | 2 |
| K5 Installations- und Integrationsaufwand | 15 % | 5 | 3 | 5 |
| **Nutzwert** | 100 % | **3,05** | **3,50** | **4,25** |

*Tabelle 5.1: Nutzwertanalyse Quelltextanalyse.*

**Begründung.** Reguläre Ausdrücke scheitern an K1 (Abschnitt 2.3). `libclang` bietet zwar maximale semantische Tiefe (Makroexpansion, `#ifdef`), setzt aber eine vollständige Cross-Compiler-Konfiguration samt Ziel-Headern (`Arduino.h`, ESP-IDF) voraus und bricht bei fehlenden Pfaden ab. Tree-Sitter benötigt lediglich ein kleines Python-Paket und läuft plattformübergreifend ohne Ziel-Toolchain.

**Sensitivität.** `libclang` überholt Tree-Sitter erst, wenn K4 auf mindestens ~36 % hochgewichtet wird. Solange Portabilität und fehlertoleranter Betrieb ohne Ziel-Toolchain dominieren, ist Tree-Sitter die stabil beste Wahl; die bewussten Grenzen dieser Entscheidung (v. a. `#ifdef`) dokumentiert Kapitel 8.

### 5.2 Entscheidung 2: Verfahren zur Konfliktlösung

Für die Berechnung einer Ersatzbelegung wurden vier Verfahren verglichen: **1 – Eigene Heuristik**, **2 – SMT ohne Optimierung** (`z3.Solver`), **3 – Gemischt-ganzzahlige lineare Optimierung** (MILP, z. B. PuLP) und **4 – MaxSMT** (`z3.Optimize`).

| Kriterium | Gewicht | 1 Heuristik | 2 SMT | 3 MILP | 4 MaxSMT |
| :--- | :---: | :---: | :---: | :---: | :---: |
| K1 Garantiert optimale Lösung bzgl. der Zielfunktion (FA-08) | 30 % | 1 | 1 | 5 | 5 |
| K2 Natürliche Formulierung von „verschieden“ und „gekoppelt“ (FA-07) | 25 % | 2 | 5 | 2 | 5 |
| K3 Abhängigkeiten und Installation | 15 % | 5 | 4 | 4 | 4 |
| K4 Laufzeit bei typischen Pin-Zahlen (bis ca. 15–20 Signale) | 15 % | 5 | 5 | 4 | 4 |
| K5 Nachvollziehbarkeit des Ergebnisses | 15 % | 4 | 2 | 3 | 3 |
| **Nutzwert** | 100 % | **2,90** | **3,20** | **3,65** | **4,40** |

*Tabelle 5.2: Nutzwertanalyse Konfliktlösung.*

**Begründung.** Eine gierige Heuristik versagt bei gekoppelten Engpässen: Kollidieren eine LED und ein Analogsensor auf dem vorletzten freien ADC1-Pin, kann eine falsche Reihenfolge den Sensor auf einen Strapping-Pin verdrängen oder gar keine Lösung finden, obwohl ein Ausweichen der LED das Problem löst (Abschnitt 6.5, Fall 3). Reines SMT ohne Optimierung verschiebt unnötig viele korrekte Pins. MILP erreicht dieselbe Optimalität wie MaxSMT, benötigt aber binäre Indikatorvariablen $x_{i,p} \in \{0, 1\}$ für jede Signal-Pin-Kombination und lineare Ungleichungen für Bus-Kopplungen. In Z3 MaxSMT genügen eine einzelne Ganzzahlvariable $v_i$ je Signal sowie direkt lesbare Ausdrücke $v_a = v_b$ und $v_a \neq v_b$ – ein klarer Vorteil für Wartbarkeit und Verständlichkeit (NFA-07).

**Sensitivität.** Der Vorsprung von MaxSMT gegenüber MILP beruht vor allem auf K2 (Modellierungsfreundlichkeit). Erst für sehr große Boards (> 30 konfliktbehaftete Signale) könnte eine boolesche/MILP-Formulierung Laufzeitvorteile bieten (vgl. Skalierungsmessung in Abschnitt 7.5 und Ausblick 8.4).

### 5.3 Entscheidung 3: Zweistufiger Ablauf

Übergäbe man alle Originalpins direkt als harte Bedingungen an Z3, erhielte der Entwickler im Fehlerfall nur ein pauschales `UNSAT` ohne Erklärung. Daher trennt das System zwei Stufen:

1. **Stufe 1 – Deterministische Diagnose:** Ein einfacher Python-Durchlauf prüft jedes Signal einzeln gegen das Hardware-Profil und sammelt sämtliche Klartextfehler mit Dateizeile. Besteht kein Konflikt, endet die Prüfung sofort mit `SAT` – Z3 wird gar nicht erst gestartet.
2. **Stufe 2 – MaxSMT-Reparatur:** Nur bei mindestens einem Konflikt berechnet Z3 die optimale Ersatzbelegung.

So werden alle Fehler eines Projekts in einem Durchlauf gemeldet, und gültige Builds bleiben praktisch latenzfrei (`0,01–0,06 ms` Prüfzeit selbst bei 20 Pins, Abschnitt 7.5).

### 5.4 Entscheidung 4: Hardware-Wissen als validierte Daten

Alle Chip-Eigenschaften liegen in deklarativen JSON-Dateien statt im Python-Code (INV-01). Diese Trennung ist nicht nur architektonisch sauber, sondern auch **wirtschaftlich entscheidend**: Das Hinzufügen eines weiteren Mikrocontrollers reduziert sich auf das Anlegen einer geprüften JSON-Datei (~1–2 Stunden Datenblatt-Arbeit, vgl. Anhang F und Abschnitt 7.6), statt eine komplette Prüflogik neu zu entwickeln.

Da JSON-Profile in der Praxis auch mit Unterstützung von Sprachmodellen erstellt werden, validiert `BoardSpec.from_dict()` in Version `0.2.0` jede geladene Datei streng gegen das erwartete Schema (Abschnitt 6.2). Typische Schema-Fehler wie `"capabilities": "gpio"` (Zeichenkette statt Liste), `"forbidden_pins": ["18"]` (Text statt Ganzzahl) oder Tippfehler in `when_resource_active` werden sofort mit klarem Hinweis abgefangen, statt stillschweigend wirkungslos zu bleiben.

### 5.5 Gesamtarchitektur

Abbildung 5.1 zeigt die modulare Vierschicht-Architektur von Version `0.2.0` vom Build-Start bis zur Entscheidung.

```text
  platformio.ini + Projektdateien (include/, src/)
          │   "pio run" startet das Pre-Build-Skript vor dem Compiler
          ▼
  pio_hook.py
    ├─ läuft nur einmal pro Build (Merker _MCU_VALIDATOR_RAN)
    ├─ prüft / installiert Python-Pakete (mit Versionsgrenzen & Fehlerhilfe)
    └─ ruft auf: python -m mcu_validator.cli <src> <board> [--include-dir <include>]
          ▼
  mcu_validator/cli.py  (Einstiegspunkt: mcu-validate / validate_path)
    ├─ 1. board.py  : load_board(board)      → BoardSpec (validiert aus boards/*.json)
    ├─ 2. parser.py : parse_cpp(pfad, board) → ParsedProject (PinRequests + aktive Module)
    ├─ 3. solver.py : validate(proj, board)  → ValidationResult (Diagnose + ggf. Z3 MaxSMT)
    └─ 4. cli.py    : format_report(...)     → Bericht + kopierbarer Reparatur-Prompt
          │
          ├── SAT   (Exit-Code 0) → Compiler startet
          ├── UNSAT (Exit-Code 1) → env.Exit(1), Reparatur-Prompt ausgeben
          └── ERROR (Exit-Code 2) → Konfigurations- / Eingabefehler melden
```
*Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess (`v0.2.0`).*

### 5.6 Durchgängiges Beispiel

Das folgende Beispiel verfolgt Szenario 0 aus der Testsuite (Listing 5.1) durch alle Schritte auf einem ESP32-C3. Es entspricht inhaltlich Listing 1.1.

```cpp
#include <Arduino.h>
#include <WiFi.h>

// SCENARIO 0: Reserved SPI flash pin + ADC2/Wi-Fi conflict on ESP32-C3 (valid on ESP32-S3)
#define STATUS_LED 12        // ESP32-C3 error: internal SPI flash (valid GPIO on ESP32-S3)
const int SOIL_SENSOR = 5;   // ESP32-C3 error: ADC2 conflicts with Wi-Fi (ADC1 on ESP32-S3)
const int RELAY_PIN = 4;     // Valid standard GPIO on both MCUs

void setup() {
    Serial.begin(115200);
    WiFi.begin("MyWiFi", "Password123");

    pinMode(STATUS_LED, OUTPUT);
    pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
    int reading = analogRead(SOIL_SENSOR);
    digitalWrite(STATUS_LED, HIGH);
    digitalWrite(RELAY_PIN, LOW);
}
```
*Listing 5.1: Szenario 0 (`tests/scenarios/00_flash_and_wifi_conflict.cpp`).*

**Schritt 1 – Profil laden und validieren (`board.py`).** Aus `mcu_validator/boards/esp32-c3.json` ergibt sich als typisiertes `BoardSpec`-Objekt: GPIO 11–17 sind reserviert, GPIO 5 besitzt nur `adc2`, `ADC1` liegt auf GPIO 0–4, Strapping-Pins sind 2, 8 und 9, aktives `wifi` sperrt `adc2` und aktives `usb_serial` sperrt GPIO 18 und 19.

**Schritt 2 – Quelltext analysieren (`parser.py`).** Der Parser findet auf oberster Ebene `STATUS_LED = 12` (Zeile 5; der Zeilenkommentar wird lokal entfernt), `SOIL_SENSOR = 5` (Zeile 6) und `RELAY_PIN = 4` (Zeile 7). Lokale Variablen innerhalb von `setup()` oder `loop()` werden ignoriert. Weil `SOIL_SENSOR` an `analogRead` übergeben wird, erhält es `capabilities = frozenset({"adc"})`; `STATUS_LED` und `RELAY_PIN` erhalten `frozenset({"gpio"})`. `WiFi.begin` und `Serial.begin` aktivieren `wifi` und `usb_serial`. Ergebnis als `ParsedProject`:

```python
ParsedProject(
    requests=(
        PinRequest(name="STATUS_LED",  pin=12, capabilities=frozenset({"gpio"}), location="00_flash_and_wifi_conflict.cpp:5"),
        PinRequest(name="SOIL_SENSOR", pin=5,  capabilities=frozenset({"adc"}),  location="00_flash_and_wifi_conflict.cpp:6"),
        PinRequest(name="RELAY_PIN",   pin=4,  capabilities=frozenset({"gpio"}), location="00_flash_and_wifi_conflict.cpp:7"),
    ),
    active_resources=("wifi", "usb_serial"),
)
```

**Schritt 3 – Diagnose (Stufe 1 in `solver.py`).** `STATUS_LED` liegt auf dem reservierten Flash-Pin GPIO 12. `SOIL_SENSOR` fordert `adc` an, also `adc1` oder `adc2`; GPIO 5 bietet nur `adc2`, und genau diese Fähigkeit wird durch die aktive Regel `WIFI_BLOCKS_ADC2` gesperrt. Die Fehlermeldung gibt direkt den hinterlegten `reason`-Text dieser Regel aus. `RELAY_PIN` (GPIO 4) ist gültig. Da zwei Fehler vorliegen, folgt Stufe 2.

**Schritt 4 – Reparatur (Stufe 2 in `solver.py`).** Für jedes Signal wird die Menge der zulässigen Pins bestimmt. Weil `usb_serial` aktiv ist, fallen GPIO 18 und 19 weg:

$$P_{\text{LED}} = P_{\text{RELAY}} = \{0, 1, \dots, 10, 20, 21\}, \qquad P_{\text{SOIL}} = \{0, 1, 2, 3, 4\}$$

Hart gefordert ist, dass alle drei Signale paarweise verschiedene Pins erhalten. Die weichen Bedingungen bewerten jede gültige Lösung dreistufig:

- **+1000 Punkte** für jedes Signal, das seinen gültigen Originalpin behält (erreichbar für `RELAY_PIN` auf GPIO 4).
- **+20 Punkte** für jedes Signal, das keinen Strapping-Pin ($\{2, 8, 9\}$) belegt.
- **+5 Punkte** für jedes Signal, das keinen unnötigen Spezialpin (`adc`/`usb`) verbraucht. Für `STATUS_LED` und `RELAY_PIN` (nur `gpio`) sind die Pins $\{0, 1, 2, 3, 4, 5\}$ knappe ADC-Pins; freie Nicht-Spezialpins sind $\{6, 7, 10, 20, 21\}$. Für `SOIL_SENSOR` entfällt diese Bedingung, da es selbst `adc` anfordert.

| Belegung (LED, Sensor, Relais) | Relais behalten | Strapping-Meidung | Knappe Pins geschont | Summe | Bewertung |
| :--- | :---: | :---: | :---: | :---: | :--- |
| (12, 5, 4) – Original | – | – | – | ungültig | verletzt harte Regeln |
| (6, 3, 10) | 0 | 20 + 20 + 20 = 60 | 5 + 0 + 5 = 10 | 70 | Relais unnötig verschoben |
| (6, 2, 4) | 1000 | 20 + 0 + 20 = 40 | 5 + 0 + 0 = 5 | 1045 | Sensor auf Strapping-Pin 2 |
| (1, 3, 4) | 1000 | 20 + 20 + 20 = 60 | 0 + 0 + 0 = 0 | 1060 | LED belegt knappen ADC1-Pin 1 |
| (6, 3, 4) – Ausgabe von Z3 | 1000 | 20 + 20 + 20 = 60 | 5 + 0 + 0 = 5 | **1065** | **optimal** |

*Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`).*

Die drei Gewichts-Stufen greifen sauber ineinander: `RELAY_PIN` bleibt auf GPIO 4 (obwohl GPIO 4 ein ADC1-Pin ist, wiegen `1000` Punkte weit schwerer als `5`), `SOIL_SENSOR` weicht auf den strapping-freien ADC1-Pin GPIO 3 aus, und `STATUS_LED` erhält mit GPIO 6 einen gewöhnlichen GPIO, statt einen weiteren wertvollen ADC1-Pin zu belegen.

**Schritt 5 – Ausgabe (`cli.py`).** Listing 5.2 zeigt die reale CLI-Ausgabe in Version `0.2.0`. Dieselbe Datei ist auf einem ESP32-S3 fehlerfrei (Listing 5.3), denn dort ist GPIO 12 ein normaler Pin und GPIO 5 gehört zu `ADC1`. Allein der Austausch des Hardware-Profils ändert also das Ergebnis – genau die Trennung aus Entscheidung 4.

```text
=================================================================
 Target         : tests/scenarios/00_flash_and_wifi_conflict.cpp (ESP32-C3)
 Active Modules : wifi, usb_serial
 Checked Pins   : 3 (STATUS_LED=12, SOIL_SENSOR=5, RELAY_PIN=4)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 12, 00_flash_and_wifi_conflict.cpp:5): Reserved pin (Internal SPI flash (SPIHD)).
  - SOIL_SENSOR (GPIO 5, 00_flash_and_wifi_conflict.cpp:6): ADC2 cannot be used while Wi-Fi is active on ESP32-C3.

Please regenerate the code using this exact Z3-verified pin assignment:
  - STATUS_LED: Change GPIO 12 -> GPIO 6
  - SOIL_SENSOR: Change GPIO 5 -> GPIO 3
  - RELAY_PIN: Keep GPIO 4 (unchanged)

-----------------------------------------------------
```
*Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (`v0.2.0`, Rückgabewert 1).*

```text
=================================================================
 Target         : tests/scenarios/00_flash_and_wifi_conflict.cpp (ESP32-S3)
 Active Modules : wifi, usb_serial
 Checked Pins   : 3 (STATUS_LED=12, SOIL_SENSOR=5, RELAY_PIN=4)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (`v0.2.0`, Rückgabewert 0).*

---

## 6 Implementierung

Dieses Kapitel beschreibt die Umsetzung von `mcu-pin-solver` in Version `0.2.0` anhand der realen Projektdateien. Alle vier Kernmodule sind nach dem Top-down-Prinzip aufgebaut: Ganz oben steht jeweils die Einstiegsfunktion (`load_board`, `parse_cpp`, `validate`, `validate_path`), darunter folgen die Hilfsfunktionen in Ausführungsreihenfolge. Der Hauptteil zeigt die wesentlichen Auszüge; die vollständigen Quelltexte und Hardware-Profile finden sich in den Anhängen A bis E.

### 6.1 Repository und Softwareumgebung

Das System gliedert sich in vier Schichten: die Integration (`pio_hook.py`, `library.json`, `pyproject.toml`), die Orchestrierung und Ausgabe (`cli.py`, `__init__.py`), den Prüfkern (`board.py`, `parser.py`, `solver.py`) und die gebündelten deklarativen Hardware-Daten (`mcu_validator/boards/*.json`). Tabelle 6.1 gibt eine Übersicht über alle Projektdateien.

| Datei / Ordner | Umfang | Aufgabe |
| :--- | :--- | :--- |
| `mcu_validator/boards/esp32-c3.json` | 50 Zeilen JSON | Hardware-Profil für den ESP32-C3 (Anhang A) |
| `mcu_validator/boards/esp32-s3.json` | 73 Zeilen JSON | Hardware-Profil für den ESP32-S3 (Anhang B) |
| `mcu_validator/board.py` | 284 Zeilen Python | Typisierte Datenklassen, Profil-Auflösung und JSON-Schema-Validierung (Anhang C) |
| `mcu_validator/parser.py` | 541 Zeilen Python | Dateiauflösung, Tree-Sitter-AST-Analyse, Bus-Rollen, Namens-Fallback (Anhang D) |
| `mcu_validator/solver.py` | 284 Zeilen Python | Stufe-1-Diagnose und dreistufige Z3-MaxSMT-Optimierung (Anhang E) |
| `mcu_validator/cli.py` | 178 Zeilen Python | Argument-Parser (`mcu-validate`), Berichtsformatierung, Exit-Codes `0`/`1`/`2` (Anhang E) |
| `mcu_validator/__init__.py` | 21 Zeilen Python | Öffentliche Python-API & `__version__ = "0.2.0"` ohne Vorab-Import von `.cli` (Anhang E) |
| `pio_hook.py` | 92 Zeilen Python | PlatformIO-Pre-Build-Hook inkl. Paketprüfung und `--include-dir`-Übergabe (Anhang E) |
| `library.json` | 33 Zeilen JSON | PlatformIO-Manifest (`0.2.0`) mit `extraScript`, `srcFilter` und `export` (Anhang E) |
| `pyproject.toml` | 42 Zeilen TOML | Python-Paketmetadaten (`package-data` für `boards/*.json`), `ruff`- und `mypy`-Konfiguration |
| `src/main.cpp` und `platformio.ini` | 56 + 11 Zeilen | ESP32-C3-Demo-Projekt für lokale `pio run`-Tests |
| `tests/test_*.py` und `tests/run_tests.py` | 766 Zeilen (42 Tests) + 7 Szenarien | Modulare Unit- und End-to-End-Testsuite (`test_board`, `test_parser`, `test_solver`, `test_cli`, `test_scenarios`) |
| `.github/workflows/ci.yml` | 35 Zeilen YAML | CI-Matrix (Ubuntu & Windows, Python `3.10`/`3.12`) + `ruff` & `mypy` |
| `README.md` und `.gitattributes` | 139 + 1 Zeile | Leseführer für Einsteiger, Setup-Anleitung, Prompt-Vorlage, LF-Zeilenenden |

*Tabelle 6.1: Dateien des Repositories (`v0.2.0`).*

Das Python-Paket `mcu_validator` umfasst insgesamt 1308 Zeilen (mit `pio_hook.py` 1400 Zeilen, einschließlich Docstrings, Typannotationen, Schema-Validierung und Leerzeilen). Gegenüber dem minimalen Prototyp `0.1.0` (379 Zeilen) wurde der Code gezielt in kleine, top-down lesbare Funktionen und typisierte Datenklassen zerlegt, sodass auch ein Einsteiger den Datenfluss ohne Vorwissen nachvollziehen kann. Sämtliche fünf Quellmodule bestehen `ruff` und `mypy` ohne Warnung oder Fehler; bewusst wurde auf `unittest` aus der Python-Standardbibliothek gesetzt, um keine zusätzlichen Test-Abhängigkeiten zu verlangen.

### 6.2 Hardware-Profile und Schema-Validierung (`board.py`)

Gemäß INV-01 liegen sämtliche GPIO-Nummern, Fähigkeiten und Sperrregeln in JSON-Dateien im Paketordner `mcu_validator/boards/`. Die Ablage *innerhalb* des Python-Pakets (in Verbindung mit `package-data` in `pyproject.toml`) stellt sicher, dass die Profile auch nach einem regulären `pip install .` oder aus einem Wheel heraus ohne Pfadbrüche geladen werden.

Jedes Profil besteht neben `mcu` und `description` aus fünf Abschnitten (Listing 6.1):

1. **`pins`:** Bildet physisch vorhandene Pin-Nummern (als Zeichenketten) auf `capabilities`, `strapping`, `reserved` und optional `note` ab. Nicht existierende Pins (wie GPIO 22–25 beim ESP32-S3) fehlen als Schlüssel; reservierte Pins (wie GPIO 11–17 beim ESP32-C3) tragen `"reserved": true` und `"capabilities": []`.
2. **`capability_aliases`:** Löst allgemeine Fähigkeiten (`"adc"`) in chipspezifische Wandlergruppen (`["adc1", "adc2"]`) auf.
3. **`shared_capabilities`:** Nennt Bus-Fähigkeiten (`["i2c", "spi"]`), deren Signalleitungen mehrere Geräte teilen dürfen.
4. **`resource_triggers`:** Ordnet Peripherienamen (`"wifi"`, `"usb_serial"`) den auslösenden C++-Aufrufen zu (`["WiFi.begin", "WiFi.softAP"]`, `["Serial.begin"]`).
5. **`conflict_rules`:** Formuliert kontextabhängige Verbote über `when_resource_active` in Kombination mit `forbidden_capability` oder `forbidden_pins` sowie einer klaren Begründung (`reason`).

```json
{
  "mcu": "ESP32-C3",
  "description": "Espressif ESP32-C3 (RISC-V, Single-Core, Wi-Fi/BLE)",
  "pins": {
    "0":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "2":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (boot mode)" },
    "5":  { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "11": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal flash power supply (VDD_SPI)" },
    "12": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIHD)" },
    "18": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "usb"], "strapping": false, "reserved": false, "note": "USB D-" },
    "20": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "Default UART0 RX" }
  },
  "capability_aliases": { "adc": ["adc1", "adc2"] },
  "shared_capabilities": ["i2c", "spi"],
  "resource_triggers": {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"]
  },
  "conflict_rules": [
    {
      "id": "WIFI_BLOCKS_ADC2",
      "when_resource_active": "wifi",
      "forbidden_capability": "adc2",
      "reason": "ADC2 cannot be used while Wi-Fi is active on ESP32-C3."
    },
    {
      "id": "USB_BLOCKS_GPIO18_19",
      "when_resource_active": "usb_serial",
      "forbidden_pins": [18, 19],
      "reason": "GPIO 18 and 19 are occupied by the internal USB-Serial/JTAG interface."
    }
  ]
}
```
*Listing 6.1: Auszug aus `mcu_validator/boards/esp32-c3.json` (vollständig in Anhang A).*

Listing 6.2 zeigt die Auflösung in `mcu_validator/board.py`. Gegenüber `v0.1.0` wurden drei Stabilitätslücken geschlossen: (1) `load_board` normalisiert sowohl `board_id` als auch die Dateinamen (`_` $\rightarrow$ `-`) und sortiert absteigend nach Namenslänge, sodass `esp32-c3.json` stets vor einem generischen `esp32.json` greift. (2) Direkte `.json`-Dateipfade (z. B. `mcu-validate src ./mein_board.json`) werden unmittelbar geladen. (3) `BoardSpec.from_dict()` validiert jeden Schlüssel und Datentyp streng (Ablehnung von Zeichenketten statt Listen bei `capabilities`, Zeichenketten oder Booleans in `forbidden_pins`, unbekannten Auslösern in `when_resource_active` sowie wirkungslosen Regeln ohne Ziel).

```python
BOARDS_DIR = Path(__file__).resolve().parent / "boards"

def load_board(board_id: str = "esp32-c3", boards_dir: Path = BOARDS_DIR) -> BoardSpec:
    direct_path = Path(board_id)
    if direct_path.suffix.lower() == ".json" and direct_path.is_file():
        return _load_board_file(direct_path)

    normalized = _normalize_name(board_id)
    candidates = sorted(
        boards_dir.glob("*.json") if boards_dir.is_dir() else (),
        key=lambda p: (-len(_normalize_name(p.stem)), _normalize_name(p.stem)),
    )
    for json_file in candidates:
        if _normalize_name(json_file.stem) in normalized:
            return _load_board_file(json_file)

    available = ", ".join(list_boards(boards_dir)) or "none"
    raise FileNotFoundError(
        f"No board profile matching '{board_id}' in {boards_dir} (available: {available})."
    )
```
*Listing 6.2: Laden des Hardware-Profils (`load_board`, `mcu_validator/board.py`).*

Tabelle 6.2 vergleicht beide mitgelieferten Hardware-Profile anhand der Hersteller-Datenblätter [[9]](#ref-9), [[10]](#ref-10). Anders als in `v0.1.0` bilden beide Profile nun die Flexibilität der ESP32-GPIO-Matrix ab: Sämtliche freien GPIOs unterstützen `pwm`, `i2c`, `spi` und `uart`, und beim ESP32-C3 ist zusätzlich GPIO 11 explizit als reservierte Flash-Versorgung (`VDD_SPI`) eingetragen.

| Merkmal | `mcu_validator/boards/esp32-c3.json` | `mcu_validator/boards/esp32-s3.json` |
| :--- | :--- | :--- |
| Architektur | RISC-V Single-Core | Xtensa LX7 Dual-Core |
| Eingetragene GPIOs | `0–21` (22 Einträge) | `0–21`, `26–48` (45 Einträge; `22–25` fehlen) |
| Reservierter Flash / PSRAM | `11–17` (`VDD_SPI` + interner SPI-Flash) | `26–37` (interner SPI-/Octal-SPI-Flash / PSRAM) |
| Strapping-Pins | `2, 8, 9` | `0, 3, 45, 46` |
| `ADC1` (mit WLAN nutzbar) | `0–4` | `1–10` |
| `ADC2` (bei WLAN gesperrt) | `5` | `11–20` |
| Native USB-Pins | `18` (D-), `19` (D+) | `19` (D-), `20` (D+) |
| GPIO-Matrix (`pwm`, `i2c`, `spi`, `uart`) | auf allen freien GPIOs (`0–10`, `18–21`) | auf allen freien GPIOs (`0–21`, `38–48`) |
| Standard-UART0 | `20` (RX), `21` (TX) | `43` (TX), `44` (RX) |

*Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`, Angaben nach [[9]](#ref-9), [[10]](#ref-10)).*

### 6.3 AST-Parser (`parser.py`)

Der Parser in `mcu_validator/parser.py` arbeitet in vier Schritten, die in `parse_cpp()` direkt untereinander stehen: Dateiauflösung, AST-Durchlauf, Aufbau der `PinRequest`-Objekte und Erkennung aktiver Peripherie.

**1. Dateiauflösung (`_resolve_source_files`).** Einzeldateien werden direkt geparst; bei einem Verzeichnis `src/` bindet `_project_search_dirs` automatisch einen Nachbarordner `include/` ein (über `path.resolve()`, sodass auch `.` innerhalb von `src/` funktioniert). Zusätzliche Header-Ordner lassen sich über `include_dirs` (CLI: `--include-dir`) einbinden. Header (`.h`, `.hpp`) werden vor `.c`/`.cpp`/`.ino`-Dateien einsortiert; Build- und Testordner (`.git`, `.pio`, `build`, `test`, `tests`, `.venv`) werden über den *relativen* Pfad ausgeschlossen.

**2. Kollisionssichere Schlüsselvergabe (`_record_definition`).** Jeder gefundene Top-Level-Pin wird als `_PinDefinition` samt Dateipfad und 1-basierter Zeilennummer gespeichert (Listing 6.3). Identische Werte desselben Symbols werden dedupliziert; abweichende Werte erhalten über `_reserve_unique_key` garantiert global eindeutige Schlüssel (`NAME (datei.cpp)`, bei Mehrfachkonflikten `NAME (datei.cpp) #2` usw.). Selbst dreifache `#ifdef`/`#elif`/`#else`-Zweige oder ein Nutzer-Bezeichner `GPIO_12` neben `pinMode(12, OUTPUT)` können dadurch im Solver niemals kollidieren (INV-03).

```python
def _record_definition(
    scan: _SourceScan, name: str, pin: int, file_path: Path, line: int
) -> None:
    seen_pins = scan.seen_values.get(name)
    if seen_pins is None:
        scan.seen_values[name] = {pin}
        key = _reserve_unique_key(name, scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))
    elif pin not in seen_pins:
        seen_pins.add(pin)
        key = _reserve_unique_key(f"{name} ({file_path.name})", scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))
```
*Listing 6.3: Kollisionssichere Schlüsselvergabe (`_record_definition`, `mcu_validator/parser.py`).*

**3. AST-Durchlauf und positionsgenaue Argumentauswertung (`_scan_files`, `_pin_args_for_call`).** Jeder Prüflauf erzeugt eine eigene `Parser(CPP_LANGUAGE)`-Instanz (thread-sicher); `_text()` dekodiert mit `errors="replace"`, sodass Nicht-UTF-8-Kommentare (etwa Windows-1252-Umlaute) keinen Absturz verursachen. Konstanten werden nur außerhalb von Funktionskörpern extrahiert (`skip_functions=True`), sodass lokale Zähler (`int blinkCount = 0;`) ausgeschlossen bleiben. `_parse_uint()` bereinigt Kommentare, einfache Klammern (`#define LED (12)`) und ganzzahlige Suffixe (`12u`).

Bei Funktionsaufrufen wertet `_pin_args_for_call()` die exakten Argumentpositionen bekannter Arduino-/ESP32-APIs aus (Listing 6.4, Tabelle 6.3). Dadurch werden Nicht-Pin-Argumente wie Baudraten (`Serial.begin(115200)`), 1-Argument-I2C-Adressen (`Wire.begin(0x42)`) oder PWM-Werte (`analogWrite(pin, 128)`) ausgeschlossen. Zugleich erhält jede Bus-Leitung eine eindeutige **`bus_group`** (`Wire:sda`, `Wire:scl`, `Wire1:sda`, `SPI:sck`, `SPI:miso`, `SPI:mosi`), während das vierte `SPI.begin`-Argument (Chip-Select `CS`/`SS`) als exklusives `gpio` ohne `bus_group` klassifiziert wird.

```python
def _pin_args_for_call(
    fn_name: str, args: list[Node]
) -> Iterator[tuple[str, str | None, Node]]:
    if not args:
        return
    if fn_name in ARG0_CAPABILITIES:
        yield (ARG0_CAPABILITIES[fn_name], None, args[0])
        return

    wire_match = WIRE_CALL_RE.match(fn_name)
    if wire_match and len(args) >= 2:
        bus = wire_match.group(1)
        yield ("i2c", f"{bus}:sda", args[0])
        yield ("i2c", f"{bus}:scl", args[1])
        return

    spi_match = SPI_CALL_RE.match(fn_name)
    if spi_match:
        bus = spi_match.group(1)
        for role, arg in zip(("sck", "miso", "mosi"), args[:3]):
            yield ("spi", f"{bus}:{role}", arg)
        if len(args) >= 4:
            yield ("gpio", None, args[3])
        return

    if SERIAL_CALL_RE.match(fn_name) and len(args) >= 3:
        for arg in args[2:4]:
            yield ("uart", None, arg)
```
*Listing 6.4: Positionsgenaue Extraktion von Fähigkeiten und Bus-Rollen (`_pin_args_for_call`, `mcu_validator/parser.py`).*

| Funktionsmuster im AST | Ausgewertete Argumente | Fähigkeit | `bus_group` |
| :--- | :--- | :---: | :---: |
| `pinMode`, `digitalWrite`, `digitalRead`, `digitalPinToInterrupt`, `pulseIn`, `tone`, `noTone` | `args[0]` | `gpio` | `None` |
| `analogRead`, `analogReadMilliVolts` | `args[0]` | `adc` | `None` |
| `analogWrite`, `ledcAttach`, `ledcAttachPin` | `args[0]` | `pwm` | `None` |
| `Wire*.begin`, `Wire*.setPins` (ab 2 Arg.) | `args[0]`, `args[1]` | `i2c` | `<Bus>:sda`, `<Bus>:scl` |
| `SPI*.begin` | `args[0..2]` / `args[3]` | `spi` / `gpio` | `<Bus>:sck/miso/mosi` / `None` |
| `Serial*.begin` (ab 3 Arg.) | `args[2..3]` | `uart` | `None` |

*Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen.*

**4. Fähigkeitsmengen, Namens-Fallback und direkte Pin-Literale (`_build_pin_requests`).** Für jede Konstante werden *alle* im AST beobachteten Fähigkeiten als Menge (`frozenset[str]`) gesammelt. Konstanten ohne beobachteten Pin-Aufruf und ohne Pin-Namensmuster (z. B. `BAUD_RATE`, `DELAY_MS`, `I2C_ADDR`, `LED_COUNT`) werden übersprungen. `_infer_from_name()` zerlegt Bezeichner in `SNAKE_CASE` und `camelCase` (`OLED_SDA_PIN`, `oledSdaPin`), verwirft Nicht-Pin-Endungen (`NON_PIN_SUFFIXES`) und blickt vor einer nachgestellten Silbe `PIN`/`GPIO` auf das eigentliche Rollenwort (`SDA`, `SCL`, `MOSI`, `MISO`, `SCK`, `RX`, `TX`, `CS`).

Direkte Zahlenliterale (`pinMode(12, OUTPUT)`, `analogRead(5)`, `Wire.begin(6, 6)`) verarbeitet `_merge_or_append_literal_uses()`: Gehört ein Pin mit derselben `bus_group` bereits einer benannten Konstante (z. B. `const int STATUS_LED = 6; analogRead(6);`), werden zusätzliche Fähigkeiten auf diesen Pin gemergt, damit fehlende Fähigkeiten erkannt werden. Andernfalls entsteht ein eindeutig benannter Eintrag (`GPIO_12`, bei Bus-Konflikt `GPIO_6 (Wire:scl)`).

Gemäß INV-02 durchsucht kein regulärer Ausdruck den C++-Rohtext; alle fünf Muster in `parser.py` arbeiten ausschließlich auf zuvor aus dem AST isolierten Kurzstrings (Tabelle 6.4).

| Muster in `parser.py` | Isolierte AST-Eingabe | Zweck |
| :--- | :--- | :--- |
| `WIRE_CALL_RE`: `^(Wire\d*)\.(?:begin\|setPins)$` | Funktionsname `fn_name` | erkennt `Wire`, `Wire1`, … und extrahiert den Busnamen |
| `SPI_CALL_RE`: `^(SPI\d*)\.begin$` | Funktionsname `fn_name` | erkennt `SPI`, `SPI1`, … und extrahiert den Busnamen |
| `SERIAL_CALL_RE`: `^Serial\d*\.begin$` | Funktionsname `fn_name` | erkennt Hardware-UART-Aufrufe mit `rxPin`/`txPin` |
| `COMMENT_RE`: `//.*\|/\*.*?\*/` | `preproc_arg` eines `#define` | entfernt Zeilen- und Blockkommentare hinter Zahlenwerten |
| `WORD_RE`: `[A-Z]+(?=[A-Z][a-z]\|_|\d\|$)\|[A-Z]?[a-z]+\|\d+` | Bezeichner `name` | zerlegt `SNAKE_CASE` und `camelCase` für `_infer_from_name()` |

*Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`).*

### 6.4 Regelprüfer und MaxSMT-Solver (`solver.py`)

Die Funktion `validate(project, board)` in `mcu_validator/solver.py` prüft nach einer Eindeutigkeitskontrolle der Signalnamen in zwei Stufen (Abbildung 6.1).

```text
  Eingabe: (ParsedProject, BoardSpec)
                        │
                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Stufe 1: Deterministische Diagnose (ohne Z3)                        │
  │ 1. _active_restrictions(): Sperren aus conflict_rules ableiten      │
  │ 2. _find_conflicts(): Für jedes Signal r_i auf Originalpin p_i^0:   │
  │    • Existiert p_i^0 im Profil?                                     │
  │    • Kollision mit früherem Signal (Ausnahme: _can_share_bus True)? │
  │    • Ist p_i^0 als reserved markiert oder in forbidden_pins?        │
  │    • Unterstützt p_i^0 JEDE Fähigkeit c ∈ C_i ohne Komplettsperre?  │
  └─────────────────────┬─────────────────────────────┬─────────────────┘
          conflicts==[] ▼                             ▼ conflicts != []
  ┌───────────────────────────┐     ┌───────────────────────────────────┐
  │ ValidationResult(SAT)     │     │ Stufe 2: Z3 Optimize (MaxSMT)     │
  │ (Z3 wird nicht gestartet) │     │ berechnet minimale Ersatzbelegung │
  └───────────────────────────┘     └─────────────────┬─────────────────┘
                                                      ▼
                                    ValidationResult(UNSAT, repair_possible)
```
*Abbildung 6.1: Zweistufiger Ablauf in `validate()` (`mcu_validator/solver.py`).*

In Stufe 1 prüft `_check_capabilities` jede geforderte Fähigkeit $c \in C_i$ einzeln über Mengenoperationen (`matching = board.expand_capability(c) & pin_caps`). Sind alle passenden Wandlerbanken gesperrt (`matching <= forbidden_caps.keys()`), wird direkt der `reason`-Text der sperrenden Regel gemeldet.

Findet Stufe 1 mindestens einen Konflikt, baut `_solve_reassignment()` das MaxSMT-Modell auf (Listing 6.5). Jede Anforderung $r_i$ erhält eine über ihren Index erzeugte Z3-Variable `Int(f"pin_{idx}")` (Typ `z3.ArithRef`). Ist die Kandidatenmenge $P_i$ für ein Signal leer, gibt der Solver sofort `None` (`repair_possible=False`) zurück – der fehleranfällige Notbehelf `var == -1` aus `v0.1.0` existiert nicht mehr.

```python
KEEP_ORIGINAL_WEIGHT = 1000     # 1st priority: keep already-valid pins unchanged
AVOID_STRAPPING_WEIGHT = 20     # 2nd priority: avoid boot/strapping pins on reassignment
SAVE_SPECIAL_PIN_WEIGHT = 5     # 3rd priority: save scarce ADC/USB pins when plain GPIO suffices
SCARCE_CAPABILITIES = frozenset({"adc", "adc1", "adc2", "usb"})

def _add_pin_constraints(opt, var, req, allowed, board) -> None:
    opt.add(Or([var == p for p in allowed]))

    if req.pin in allowed:
        opt.add_soft(var == req.pin, weight=KEEP_ORIGINAL_WEIGHT)

    strapping_pins = [p for p in allowed if board.pins[p].strapping]
    if strapping_pins and len(strapping_pins) < len(allowed):
        opt.add_soft(And([var != p for p in strapping_pins]), weight=AVOID_STRAPPING_WEIGHT)

    needed_caps = set().union(*(board.expand_capability(cap) for cap in req.capabilities))
    avoid_caps = SCARCE_CAPABILITIES - needed_caps
    scarce_pins = [p for p in allowed if board.pins[p].capabilities & avoid_caps]
    if scarce_pins and len(scarce_pins) < len(allowed):
        opt.add_soft(And([var != p for p in scarce_pins]), weight=SAVE_SPECIAL_PIN_WEIGHT)
```
*Listing 6.5: Aufbau der harten und weichen Z3-Bedingungen (`_add_pin_constraints`, `mcu_validator/solver.py`).*

Mathematisch lautet das Modell für $n$ Anforderungen $r_i$ ($i \in \{1, \dots, n\}$) mit Fähigkeitsmenge $C_i$ und Bus-Gruppe $b_i$:

$$P_i = \Big\{\, p \in \mathcal{P} \;\Big|\; \neg\text{reserved}(p) \;\land\; p \notin \text{ForbiddenPins} \;\land\; \forall c \in C_i:\; \big(\text{caps}(p) \cap (A(c) \setminus \text{ForbiddenCaps})\big) \neq \emptyset \,\Big\}$$

1. **Domänenbindung (hart):** Existiert ein $i$ mit $P_i = \emptyset$, ist keine Reparatur möglich (`repair_possible=False`). Andernfalls gilt $\bigvee_{p \in P_i} (v_i = p)$.
2. **Paarweise Bus-Leitungskopplung (hart, INV-04):** Zwei Signale dürfen genau dann einen Pin teilen (`_can_share_bus`), wenn sie dieselbe einzelne, teilbare Bus-Fähigkeit *und* dieselbe Bus-Leitungsrolle tragen:
   $$\text{share}(r_i, r_j) \iff C_i = C_j \land |C_i| = 1 \land C_i \subseteq \text{shared\_capabilities} \land b_i = b_j$$
   Für alle $\binom{n}{2}$ Paare $1 \le i < j \le n$ gilt damit:
   $$v_i = v_j \quad \text{falls } \text{share}(r_i, r_j) \land p_i^0 = p_j^0, \qquad \text{sonst } v_i \neq v_j.$$
3. **Dreistufige Zielfunktion (weich, INV-05):** Sei $S_i = P_i \cap S$ die Menge der Strapping-Pins in $P_i$ und $K_i \subseteq P_i$ die Menge der Pins mit knappen, von $r_i$ nicht benötigten Spezialfähigkeiten (`adc`/`usb`). Z3 maximiert:
   $$\max \sum_{i=1}^{n} \Big( 1000 \cdot \mathbb{I}[p_i^0 \in P_i \land v_i = p_i^0] \;+\; 20 \cdot \mathbb{I}[\emptyset \subset S_i \subset P_i \land v_i \notin S_i] \;+\; 5 \cdot \mathbb{I}[\emptyset \subset K_i \subset P_i \land v_i \notin K_i] \Big)$$

Durch die Bündelung zu je *einer* weichen Klausel pro Signal und Prioritätsstufe bleibt die Zielfunktion übersichtlich und vermeidet unnötige unerfüllbare Teilklauseln (wenn z. B. alle erlaubten Pins Strapping- oder Spezialpins sind).

### 6.5 Wer darf bleiben? Prioritäten bei gegenseitiger Pin-Blockade

Bei konkurrierenden Signalen auf demselben Pin entscheidet ausschließlich die Zielfunktion (3), ohne fest codierte Namensprioritäten:

1. **Fall 1 – Gleichwertige Einzelsignale (Gleichstand).** Liegen `BUZZER_PIN = 7` und `SERVO_PIN = 7` (beide `gpio`) auf demselben Pin, erreichen beide Lösungen dieselbe Punktzahl ($1000 + 40 + 10 = 1050$). Die Experimente `c` und `c2` (Abschnitt 7.4) zeigen, dass nicht die Deklarationsreihenfolge, sondern die interne Suchheuristik von Z3 den Gleichstand auflöst (in beiden Reihenfolgen blieb `SERVO_PIN` auf GPIO 7, während `BUZZER_PIN` auf GPIO 20 bzw. GPIO 6 auswich). Für identische Eingaben und eine feste Z3-Version bleibt das Ergebnis reproduzierbar.
2. **Fall 2 – Geteilter Bus gegen einzelnes Störsignal („Bus-Trägheit“).** In Szenario 04 sind `OLED_SDA = 6` und `BME280_SDA = 6` über `Wire:sda` gekoppelt ($2 \times 1000 = 2000$ Haltepunkte) gegenüber nur `1000` Punkten für `STATUS_LED = 6`. Tabelle 6.5 belegt die rechnerische Bus-Trägheit: Alle vier I2C-Signale bleiben auf GPIO 6/7, und nur die LED wechselt auf den freien Standard-GPIO 20.

| Variante in Szenario 04 (`v0.2.0`) | Haltepunkte | Strapping-Meidung | Knappe Pins geschont | Summe | Ergebnis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **A (Z3-Lösung):** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 20 | $4 \times 1000 = 4000$ | $5 \times 20 = 100$ | $5 \times 5 = 25$ | **4125** | **optimal** |
| **B:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 1 (ADC1) | $4000$ | $100$ | $4 \times 5 + 0 = 20$ | 4120 | verworfen |
| **C:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 2 (Strapping + ADC1) | $4000$ | $4 \times 20 = 80$ | $20$ | 4100 | verworfen |
| **D:** `STATUS_LED` bleibt auf 6, SDA-Paar $\rightarrow$ 20 | $3 \times 1000 = 3000$ | $100$ | $25$ | 3125 | verworfen |

*Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`).*

3. **Fall 3 – Spezialist gegen Allrounder.** Kollidieren bei aktivem WLAN ein Analogsensor (`SOIL_SENSOR = 1`, braucht `adc1`) und eine LED (`STATUS_LED = 1`, `gpio`) bei bereits belegten ADC1-Pins 0, 3 und 4, bliebe dem Sensor nur noch Strapping-Pin 2. Weicht stattdessen die LED auf GPIO 7 aus, gewinnt diese Variante genau **25 Punkte** (`+20` Strapping-Meidung für den Sensor, `+5` Schonung des ADC1-Pins für die LED). Die Experimente `f` und `f2` bestätigen dies unabhängig von der Deklarationsreihenfolge.

### 6.6 Bericht, CLI und Reparatur-Prompt (`cli.py`)

Das Modul `mcu_validator/cli.py` implementiert über `argparse` den CLI-Befehl `mcu-validate` (sowie `python -m mcu_validator.cli`) mit definierten Exit-Codes: `0` (`SAT`), `1` (`UNSAT`) und `2` (Eingabe- oder Konfigurationsfehler wie fehlender Pfad, unbekanntes Board oder fehlerhafte JSON-Datei – abgefangen ohne Python-Stacktrace).

Über `--list-boards`, `--boards-dir`, `--include-dir` (wiederholbar) und `--version` lässt sich das Werkzeug flexibel in eigene Workflows einbinden. Der Berichtskopf nennt stets `Checked Pins : N (...)` und warnt explizit, wenn `0` Pins erkannt wurden, um trügerische Sicherheit bei nicht abgedeckter C++-Syntax auszuschließen. Im `UNSAT`-Fall folgen alle Einzelkonflikte mit `datei:zeile`-Verweis sowie die vollständige `Keep`/`Change`-Liste (oder ein klarer Kapazitätshinweis bei `repair_possible=False`). Gemäß INV-06 importiert `mcu_validator/__init__.py` nicht `.cli`, sodass `python -W error -m mcu_validator.cli` ohne jede Warnung läuft.

### 6.7 Integration in PlatformIO und Paketierung (`pio_hook.py`, `library.json`, `pyproject.toml`)

`mcu-pin-solver` steht sowohl als Python-Paket (`pip install .`) als auch in der PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) bereit. Listing 6.6 zeigt die Kernlogik von `pio_hook.py` und `library.json`.

```python
# --- Auszug aus pio_hook.py ---
REQUIRED_PACKAGES = (
    "z3-solver>=4.12.0",
    "tree-sitter>=0.23.0",
    "tree-sitter-cpp>=0.23.0",
)

if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True
    hook_dir = _resolve_hook_dir()
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))
    include_dir = Path(env.subst("$PROJECT_INCLUDE_DIR"))

    python_cmd = shutil.which("py") or sys.executable
    if not _ensure_dependencies(python_cmd):
        env.Exit(1)

    cmd = [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id]
    if include_dir.is_dir():
        cmd.extend(["--include-dir", str(include_dir)])
    result = subprocess.run(cmd, env=run_env)

    if result.returncode == 1:
        print("\n>>> BUILD STOPPED: Fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)
    elif result.returncode != 0:
        print(f"\n>>> BUILD STOPPED: MCU-Validator configuration/input error (exit code {result.returncode}).\n")
        env.Exit(1)
```
```json
  // --- Auszug aus library.json (Version 0.2.0) ---
  "export": {
    "include": [
      "mcu_validator/*.py",
      "mcu_validator/boards/*.json",
      "pio_hook.py",
      "library.json",
      "README.md",
      "LICENSE"
    ]
  },
  "build": {
    "extraScript": "pio_hook.py",
    "srcFilter": ["-<*>"]
  }
```
*Listing 6.6: Kern des PlatformIO-Hooks (`pio_hook.py`) und der Paketkonfiguration (`library.json`).*

Fünf Härtungen sichern den produktiven Einsatz: (1) Übergabe von `$PROJECT_INCLUDE_DIR` per `--include-dir`, (2) versionsbeschränkte Paketprüfung mit verständlicher Fehlerhilfe bei Offline-Betrieb oder geschützten System-Pythons (PEP 668), (3) klare Unterscheidung von Exit-Code `1` (Pin-Konflikt) und `2` (Konfigurationsfehler), (4) Schutz gegen Doppelausführung in SCons (`_MCU_VALIDATOR_RAN`) sowie (5) saubere Isolation des Demo-Codes (`"srcFilter": ["-<*>"]`) und Bündelung der Board-Profile via `package-data` in `pyproject.toml`.

> **Zwischenfazit Kapitel 6:** Version `0.2.0` verbindet eine klare, top-down lesbare Vierschicht-Architektur mit strikter Schema-Validierung, präziser Bus-Leitungskopplung und gehärteter Paketierung für Python und PlatformIO.

---

## 7 Evaluation

Dieses Kapitel evaluiert `mcu-pin-solver` (`v0.2.0`) entlang von fünf Säulen: (1) der 42 Tests umfassenden Testsuite samt CI-Matrix, (2) 13 Grenzfallexperimenten im direkten Vergleich zu `v0.1.0`, (3) Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, (4) einem realen End-to-End-Build-Test über die PlatformIO Registry sowie (5) einer Wirtschaftlichkeits- und Break-even-Betrachtung.

### 7.1 Evaluationsdesign und Messumgebung

Die Testsuite gliedert sich in fünf modulare Dateien (`tests/test_board.py`, `test_parser.py`, `test_solver.py`, `test_cli.py`, `test_scenarios.py`). In allen `UNSAT`-End-to-End-Szenarien wendet der Test zusätzlich Z3s vorgeschlagene Pin-Nummern auf das `ParsedProject` an und validiert dieses erneut – damit ist die Korrektheit jeder Reparatur (NFA-04) automatisiert abgesichert.

Alle Laufzeiten wurden auf der in Tabelle 7.1 genannten Umgebung gemessen (Mediane über $N = 10$ Subprozess-Läufe bzw. $M = 30$ In-Process-Läufe; Skalierungstest $M = 15$).

| Komponente | Spezifikation |
| :--- | :--- |
| Prozessor / Betriebssystem (lokal) | AMD Ryzen 9 3900X 12-Core Processor, Microsoft Windows 10 Pro |
| Python-Version (lokal) | Python `3.14.7` |
| Solver und Parser | `z3-solver` `5.4.1.0`, `tree-sitter` `0.26.1`, `tree-sitter-cpp` `0.23.4` |
| PlatformIO Core (lokal) | PlatformIO Core `6.2.0` (Espressif32 `6.12.0`, Arduino-Framework) |
| CI-Umgebung (GitHub Actions) | `ubuntu-latest` & `windows-latest`, Python `3.10` & `3.12`, plus `ruff` & `mypy` |

*Tabelle 7.1: Messumgebung (`v0.2.0`).*

### 7.2 Automatisierte Testsuite und Regressionsszenarien

Die Ausführung von `python -m unittest discover -s tests -v` bestand alle **42 Tests** lokal in ca. 3,4 s sowie in sämtlichen fünf Jobs der GitHub-Actions-CI (`lint`, `ubuntu-latest` 3.10/3.12, `windows-latest` 3.10/3.12):

- **`test_board.py` (12 Tests):** Konsistenz aller mitgelieferten Board-JSONs, Präfix-Sortierung, Unterstrich-Normalisierung, direkte `.json`-Pfade sowie sieben Schema-Negativtests.
- **`test_parser.py` (11 Tests):** Nicht-Pin-Konstanten & lokale Variablen, `(12)` & `12u`, Latin-1-Kommentare, direkte Pin-Literale inkl. Fähigkeits-Merge, 3-Wege-`#ifdef`-Schlüssel, `GPIO_12`-Kollisionsschutz, Namens-Fallback (`OLED_SDA_PIN`, `oledSdaPin`, `SPI_MOSI_PIN`), `Serial1`, dateiübergreifende Konflikte und `--include-dir`.
- **`test_solver.py` (8 Tests):** `SDA == SCL` (benannt und literal), `Wire` vs. `Wire1`, SPI-`CS` & `SCK == MOSI`, Schonung knapper ADC-Pins, Überbuchung (`repair_possible=False`), leeres Projekt und Schutz gegen doppelte Signalnamen.
- **`test_cli.py` (7 Tests):** `--list-boards`, `--version`, `--boards-dir`, Warnungsfreiheit (`python -W error`), Exit-Code `2` ohne Stacktrace bei unbekanntem Board / kaputter JSON sowie 0-Pin-Warnung.
- **`test_scenarios.py` (4 Testmethoden über 9 Konstellationen):** Alle neun Regressionsszenarien (Tabelle 7.2) inklusive automatischer Re-Validierung der Z3-Vorschläge.

| Nr. | Zielpfad | Board | Erwartet & Gemessen | Geprüfter Sachverhalt |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `src/main.cpp` | `esp32-c3` | SAT | Demo-Sketch (`STATUS_LED=8`, `SOIL_SENSOR=1`, `RELAY_PIN=4`, `WiFi.softAP`, `Serial.begin`) |
| 2 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1 & 2: Flash-Pin 12 und `ADC2` (Pin 5) bei aktivem WLAN |
| 3 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | Identischer Code auf ESP32-S3 gültig (Pin 12 normal, Pin 5 in `ADC1`) |
| 4 | `tests/scenarios/01_valid_sketch.cpp` | `esp32-c3` | SAT | Positivkontrolle: fehlerfreier Sketch mit WLAN und USB-Serial |
| 5 | `tests/scenarios/02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 2: `Serial.begin` sperrt USB-Pins 18 und 19 |
| 6 | `tests/scenarios/03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1, 3, 4: Doppelbelegung (7), Geister-Pin (32), fehlendes ADC (6) |
| 7 | `tests/scenarios/04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 4: I2C-Bus auf 6/7 bleibt gekoppelt erhalten, LED weicht aus |
| 8 | `tests/scenarios/05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | AST ignoriert `WiFi.begin(...)` in Kommentar und Zeichenkette |
| 9 | `tests/scenarios/06_multi_file_project/src` | `esp32-c3` | UNSAT | Mehrere Dateien: `include/pins.h` + `src/main.cpp` + `src/sensors.cpp` |

*Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien.*

### 7.3 Ausgewählte Szenarien im Detail

Szenario 0 wurde bereits in Abschnitt 5.6 vorgestellt. Die Listings 7.1 bis 7.5 dokumentieren die tatsächlichen CLI-Ausgaben von Version `0.2.0` für die Szenarien 02 bis 06.

In **Szenario 02** (Listing 7.1) sperrt `Serial.begin(115200)` die USB-Pins 18 und 19. `ENABLE_PIN` (GPIO 6) bleibt unverändert; dank der dritten Prioritätsstufe landen `STEP_PIN` und `DIR_PIN` auf den Standard-GPIOs 21 und 10, statt knappe ADC1-Pins zu belegen.

```text
=================================================================
 Target         : tests/scenarios/02_usb_serial_conflict.cpp (ESP32-C3)
 Active Modules : usb_serial
 Checked Pins   : 3 (STEP_PIN=18, DIR_PIN=19, ENABLE_PIN=6)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STEP_PIN (GPIO 18, 02_usb_serial_conflict.cpp:4): GPIO 18 and 19 are occupied by the internal USB-Serial/JTAG interface.
  - DIR_PIN (GPIO 19, 02_usb_serial_conflict.cpp:5): GPIO 18 and 19 are occupied by the internal USB-Serial/JTAG interface.

Please regenerate the code using this exact Z3-verified pin assignment:
  - STEP_PIN: Change GPIO 18 -> GPIO 21
  - DIR_PIN: Change GPIO 19 -> GPIO 10
  - ENABLE_PIN: Keep GPIO 6 (unchanged)

-----------------------------------------------------
```
*Listing 7.1: CLI-Ausgabe für Szenario 02 (`v0.2.0`, Rückgabewert 1).*

In **Szenario 03** (Listing 7.2) erkennt Stufe 1 alle drei Fehler gleichzeitig samt Dateizeilen-Verweis. `POTI_PIN` wechselt auf `ADC1` (GPIO 0), `PIR_SENSOR` auf GPIO 10 und `BUZZER_PIN` auf den frei gewordenen GPIO 6.

```text
=================================================================
 Target         : tests/scenarios/03_duplicate_and_invalid_pin.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 4 (BUZZER_PIN=7, SERVO_PIN=7, PIR_SENSOR=32, POTI_PIN=6)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - SERVO_PIN (GPIO 7, 03_duplicate_and_invalid_pin.cpp:5): Collides with BUZZER_PIN (not a shared bus line).
  - PIR_SENSOR (GPIO 32, 03_duplicate_and_invalid_pin.cpp:6): Pin does not exist on ESP32-C3.
  - POTI_PIN (GPIO 6, 03_duplicate_and_invalid_pin.cpp:7): Does not support capability 'adc'.

Please regenerate the code using this exact Z3-verified pin assignment:
  - BUZZER_PIN: Change GPIO 7 -> GPIO 6
  - SERVO_PIN: Keep GPIO 7 (unchanged)
  - PIR_SENSOR: Change GPIO 32 -> GPIO 10
  - POTI_PIN: Change GPIO 6 -> GPIO 0

-----------------------------------------------------
```
*Listing 7.2: CLI-Ausgabe für Szenario 03 (`v0.2.0`, Rückgabewert 1).*

**Szenario 04** (Listing 7.3) zeigt die Bus-Trägheit aus Abschnitt 6.5: Alle vier gekoppelten I2C-Signale bleiben unverändert auf GPIO 6/7; nur `STATUS_LED` wechselt auf GPIO 20.

```text
=================================================================
 Target         : tests/scenarios/04_shared_i2c_bus.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 5 (OLED_SDA=6, OLED_SCL=7, BME280_SDA=6, BME280_SCL=7, STATUS_LED=6)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 6, 04_shared_i2c_bus.cpp:9): Collides with OLED_SDA (not a shared bus line).

Please regenerate the code using this exact Z3-verified pin assignment:
  - OLED_SDA: Keep GPIO 6 (unchanged)
  - OLED_SCL: Keep GPIO 7 (unchanged)
  - BME280_SDA: Keep GPIO 6 (unchanged)
  - BME280_SCL: Keep GPIO 7 (unchanged)
  - STATUS_LED: Change GPIO 6 -> GPIO 20

-----------------------------------------------------
```
*Listing 7.3: CLI-Ausgabe für Szenario 04 (`v0.2.0`, Rückgabewert 1).*

**Szenario 05** (Listing 7.4) bestätigt den Schutz gegen falsche Modul-Erkennung aus Kommentaren und Zeichenketten (`Active Modules : none`, `SAT`).

```text
=================================================================
 Target         : tests/scenarios/05_ast_ignores_strings_and_comments.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 1 (SOIL_SENSOR=5)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 7.4: CLI-Ausgabe für Szenario 05 (`v0.2.0`, Rückgabewert 0).*

**Szenario 06** (Listing 7.5) kombiniert `include/pins.h`, `src/main.cpp` und `src/sensors.cpp`, meldet beide Konflikte präzise mit `pins.h:4` und `pins.h:5` und verlegt `STATUS_LED` auf den freien Standard-GPIO 10 (ohne den USB-Pin GPIO 18 zu beanspruchen).

```text
=================================================================
 Target         : tests/scenarios/06_multi_file_project/src (ESP32-C3)
 Active Modules : wifi
 Checked Pins   : 2 (STATUS_LED=12, SOIL_SENSOR=5)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 12, pins.h:4): Reserved pin (Internal SPI flash (SPIHD)).
  - SOIL_SENSOR (GPIO 5, pins.h:5): ADC2 cannot be used while Wi-Fi is active on ESP32-C3.

Please regenerate the code using this exact Z3-verified pin assignment:
  - STATUS_LED: Change GPIO 12 -> GPIO 10
  - SOIL_SENSOR: Change GPIO 5 -> GPIO 3

-----------------------------------------------------
```
*Listing 7.5: CLI-Ausgabe für Szenario 06 (`v0.2.0`, Rückgabewert 1).*

### 7.4 Grenzfallexperimente und Entwicklung von v0.1.0 zu v0.2.0

Tabelle 7.3 dokumentiert 13 gezielte Grenzfallexperimente auf `esp32-c3` und vergleicht den ersten Prototyp `v0.1.0` direkt mit dem finalen Stand `v0.2.0`. Neun in `v0.1.0` aufgedeckte Schwachstellen wurden vollständig behoben; die beiden bewusst verbleibenden Grenzen (`i` bei `gpio_num_t` und `j` bei `#ifdef`) werden in Abschnitt 8.2 eingeordnet.

| ID | Getesteter Fall | Verhalten in `v0.1.0` | Gemessenes Verhalten in `v0.2.0` | Bewertung (`v0.2.0`) |
| :---: | :--- | :--- | :--- | :--- |
| `a` | Direkte Zahlen (`pinMode(12, OUTPUT); analogRead(5);`) + `WiFi` | `SAT` (**False Negative**) | `UNSAT`: `GPIO_12 -> 10`, `GPIO_5 -> 0` | **behoben** |
| `b` | Lokale Zähler (`blinkCount`, `retries`) & `BAUD_RATE 115200` | `UNSAT` (**False Positive**) | Nur `STATUS_LED = 3` geprüft $\rightarrow$ `SAT` | **behoben** |
| `c`, `c2` | Gleichstand `BUZZER_PIN = 7` / `SERVO_PIN = 7`, beide Reihenfolgen | `BUZZER_PIN` blieb (Z3-Heuristik) | `SERVO_PIN` bleibt in beiden Fällen (`BUZZER -> 20` bzw. `6`) | Gleichstand weiterhin solverabhängig |
| `d` | 6 Analogsensoren `S0..S5` + WLAN (nur 5 `ADC1`-Pins vorhanden) | `GPIO None` für alle 6 Signale | `repair_possible=False`, klare Kapazitätsmeldung (Listing 7.6) | **behoben** |
| `e` | Synthetische Fähigkeit `'can'` ($P_i = \emptyset$, 1 bzw. 2 Signale) | `CAN_TX: -1` bzw. `-1 != -1`-Bruch | Sofort und konsistent `repair_possible=False`, `suggested={}` | **behoben** |
| `f`, `f2` | `SOIL_SENSOR = 1` (`adc`) vs. `STATUS_LED = 1` (`gpio`), beide Reihenfolgen | `SOIL_SENSOR = 1`, `LED -> 7` | In beiden Fällen `SOIL_SENSOR = 1`, `STATUS_LED -> 7` (+25 Pkt.) | Spezialist-Priorität bestätigt |
| `h` | Doppelrolle: `Wire.begin(MY_PIN, MY_SCL)` + `analogRead(MY_PIN)` | Nur `'adc'`; Vorschlag ohne I2C | `capabilities={'adc', 'i2c'}` $\rightarrow$ `MY_PIN -> 0` (ADC1 & I2C) | **behoben** |
| `i` | `constexpr int LED_A = 12;`, `static const uint8_t LED_B = 13;`, `const gpio_num_t LED_C = GPIO_NUM_14;` | `LED_A`, `LED_B` erkannt; `LED_C` ignoriert | `LED_A -> 7`, `LED_B -> 6`; `gpio_num_t` weiterhin ignoriert | **verbleibende Grenze** |
| `j` | `#ifdef USE_EXTERNAL_LED` (Pin 2) / `#else` (Pin 12) | Beide Zweige $\rightarrow$ `UNSAT` | Beide Zweige mit eindeutigen Schlüsseln $\rightarrow$ `UNSAT` (kein Absturz bei 3 Zweigen) | **verbleibende Grenze** (False Positive) |
| `k` | `Wire.begin(SDA_A, SCL_A)` & `Wire1.begin(SDA_B, SCL_B)` auf 6/7 | `SAT` (**False Negative**) | `UNSAT` (`Wire` $\neq$ `Wire1`), 4 getrennte Pins (`6, 20, 10, 7`) | **behoben** |
| `l` | Zwei `SPI.begin`-Aufrufe mit `MISO_P = 7`, `CS_A = 7`, `CS_B = 7` | `SAT` (**False Negative**) | `UNSAT` (`CS` als `gpio`), alle 5 Signale getrennt (`6, 21, 10, 7, 20`) | **behoben** |
| `m` | `OLED_SDA = 6` und `OLED_SCL = 6` in `Wire.begin(OLED_SDA, OLED_SCL)` | `SAT` (**False Negative**) | `UNSAT` (`Wire:sda` $\neq$ `Wire:scl`), `OLED_SDA=6`, `OLED_SCL -> 10` | **behoben** (neu geprüft) |

*Tabelle 7.3: Ergebnisse der Grenzfallexperimente auf `esp32-c3` (`v0.1.0` im Vergleich zu `v0.2.0`).*

Listing 7.6 zeigt die bereinigte Ausgabe im Überbuchungsfall `d`: Statt `GPIO None` meldet `v0.2.0` unmissverständlich die ausgeschöpfte Hardware-Kapazität.

```text
=================================================================
 Target         : pigeonhole.cpp (ESP32-C3)
 Active Modules : wifi
 Checked Pins   : 6 (S0=0, S1=1, S2=3, S3=4, S4=2, S5=5)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - S5 (GPIO 5, d_pigeonhole_6_adc_wifi.cpp:2): ADC2 cannot be used while Wi-Fi is active on ESP32-C3.

No valid pin assignment exists on ESP32-C3: the requested pins exceed available hardware capabilities.

-----------------------------------------------------
```
*Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, `v0.2.0`, Rückgabewert 1).*

### 7.5 Laufzeit-, Skalierungsmessung und PlatformIO-End-to-End-Prüfung

**Regressionsszenarien.** Tabelle 7.4 dokumentiert die gemessenen Medianlaufzeiten für alle neun Standardszenarien. Als Basislinie dauerte allein der Python-Start samt Import von `z3`, `tree_sitter` und `tree_sitter_cpp` im Median **139 ms**.

| Szenario | Board | Ergebnis | E2E Median ($N=10$) | Laden ($M=30$) | Parsen ($M=30$) | Lösen ($M=30$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `src/main.cpp` | `esp32-c3` | SAT | 173 ms | 0,36 ms | 0,84 ms | 0,02 ms |
| `00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | 209 ms | 0,55 ms | 0,50 ms | 16,17 ms |
| `00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | 181 ms | 0,45 ms | 0,42 ms | 0,02 ms |
| `01_valid_sketch.cpp` | `esp32-c3` | SAT | 182 ms | 0,37 ms | 0,42 ms | 0,02 ms |
| `02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | 211 ms | 0,57 ms | 0,44 ms | 18,62 ms |
| `03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | 208 ms | 0,56 ms | 0,47 ms | 25,97 ms |
| `04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | 205 ms | 0,55 ms | 0,42 ms | 24,24 ms |
| `05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | 172 ms | 0,36 ms | 0,28 ms | 0,01 ms |
| `06_multi_file_project/src` | `esp32-c3` | UNSAT | 211 ms | 0,53 ms | 1,84 ms | 10,01 ms |

*Tabelle 7.4: Gemessene Laufzeiten der Regressionsszenarien (`v0.2.0`).*

**Skalierung bis 20 Pins und 21 Dateien.** Da die Standardszenarien nur 1 bis 5 Pins umfassen, prüfte ein eigener Skalierungsbenchmark (Anhang G) synthetische Multi-Datei-Projekte auf dem größeren **ESP32-S3** (45 Pins) von 3 bis 20 Signalen – einmal im `UNSAT`-Fall (2 Konflikte: Flash-Pin 26 und `ADC2`-Pin 11 bei aktivem WLAN) sowie im konfliktfreien 20-Pin-`SAT`-Fall (Tabelle 7.5).

| Signale ($n$) | Dateien | Fall | Paarweise Ungleichungen $\binom{n}{2}$ | Parsen ($M=15$) | Lösen ($M=15$) | Summe In-Process |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 3 | 3 | UNSAT (2 Konflikte) | 3 | 1,86 ms | 47,46 ms | 49,32 ms |
| 6 | 6 | UNSAT (2 Konflikte) | 15 | 2,81 ms | 125,42 ms | 128,23 ms |
| 10 | 10 | UNSAT (2 Konflikte) | 45 | 4,12 ms | 299,31 ms | 303,43 ms |
| 15 | 15 | UNSAT (2 Konflikte) | 105 | 5,80 ms | 650,44 ms | 656,25 ms |
| 20 | 20 | UNSAT (2 Konflikte) | 190 | 7,34 ms | 1132,81 ms | 1140,15 ms |
| **20** | **21** | **SAT (konfliktfrei)** | **– (Stufe 1)** | **7,53 ms** | **0,06 ms** | **7,59 ms** |

*Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`).*

Die Messung liefert zwei wesentliche Erkenntnisse: Erstens skaliert das Tree-Sitter-Parsing strikt linear (~0,35 ms je Datei), und dank des zweistufigen Ablaufs (Entscheidung 3) dauert selbst ein konfliktfreies 20-Pin-/21-Datei-Projekt In-Process nur **7,59 ms** (~150 ms E2E) – ein Faktor von über **18.000** gegenüber dem Z3-Durchlauf. Zweitens wächst die Z3-MaxSMT-Laufzeit wegen der $\binom{n}{2}$ paarweisen Ungleichungen über quadratisch mehr Klauseln (190 Ungleichungen und bis zu 60 weiche Klauseln bei $n = 20$): Bis 15 konfliktbehaftete Signale bleibt auch die End-to-End-Zeit deutlich unter 1 s (~0,80 s), während bei 20 konfliktbehafteten Signalen auf einem 45-Pin-Chip rund 1,14 s In-Process (~1,28 s E2E) erreicht werden. Dieser empirisch bestimmte Übergangspunkt wird in Abschnitt 8.4 durch konkrete Optimierungsansätze adressiert.

**Realer End-to-End-Test über die PlatformIO Registry.** Um die Praxistauglichkeit aus Sicht eines fremden Anwenders zu prüfen, wurde `mcu-pin-solver@0.2.0` in einem separaten, leeren Projektordner vollständig neu installiert:

1. `pio pkg install` bezog **`dmatheja/mcu-pin-solver@0.2.0`** (20,71 KB) direkt aus der öffentlichen PlatformIO Registry.
2. Ein `pio run` mit fehlerhaftem ESP32-C3-Code (`STATUS_LED = 12`, `SOIL_SENSOR = 5`, `WiFi.begin`) stoppte den Build über `pio_hook.py` in **1,21 s** (`UNSAT`, Exit-Code `1`) *vor* dem Compilerstart und gab die Diagnose (`main.cpp:3`, `main.cpp:4`) samt Z3-Reparaturvorschlag aus.
3. Nach Übernahme der reparierten Pins lief `pio run` durch den Validator (`SAT`), kompilierte das Projekt mit der RISC-V-Toolchain und erzeugte `firmware.elf` und `firmware.bin` fehlerfrei in **17,76 s** (Exit-Code `0`).
4. Ein separater `git clone` von GitHub in ein leeres Verzeichnis bestand `pip install .`, `mcu-validate --list-boards` und alle 42 Tests ohne manuelle Anpassung.

### 7.6 Wirtschaftliche Bewertung

Um nicht nur die technische Machbarkeit, sondern auch den wirtschaftlichen Nutzen im Embedded-Prototyping – etwa im F&E-Umfeld eines Technologieunternehmens wie Freudenberg Technology Innovation (FTI) – fundiert zu bewerten, werden Gesamtkosten (*Total Cost of Ownership*, TCO), Einsparpotenziale und Break-even anhand transparenter, konservativer Modellannahmen gegenübergestellt.

**1. Kostenseite (TCO).**

- **Lizenz- und laufende Betriebskosten:** Der gesamte Stack (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`, PlatformIO, GitHub Actions) ist Open Source (MIT-/BSD-kompatibel). Es entstehen **0 € Lizenzkosten** und **keine laufenden API- oder Token-Gebühren** für die Prüfung selbst. Gegenüber einem alternativen „LLM-as-a-Judge“-Ansatz, bei dem ein zweites Sprachmodell den Code prüft, entfallen sowohl laufende Cloud-Kosten als auch Datenschutzrisiken durch den Upload proprietärer Firmware in externe APIs – `mcu-pin-solver` läuft zu 100 % lokal.
- **Einmaliger Entwicklungsaufwand:** Der Erstellungsaufwand im Rahmen dieser Studienarbeit liegt im Umfang eines 5-ECTS-Moduls bei ca. **150 Stunden** (bei einem kalkulatorischen internen Entwicklungs-Vollkostensatz von 80–120 €/h entspricht dies kalkulatorisch 12.000–18.000 €; bei Nutzung der frei veröffentlichten Open-Source-Bibliothek fällt dieser Initialaufwand für Anwenderteams jedoch vollständig weg).
- **Inkrementeller Integrations- und Pflegeaufwand:** Die Einbindung in ein bestehendes PlatformIO-Projekt erfordert zwei Zeilen in `platformio.ini` (< 10 Minuten). Die Erstellung und Datenblatt-Prüfung eines neuen Chip-Profils (`boards/<chip>.json`) dauert dank Schema-Validierung und Prompt-Vorlage ca. **1–2 Stunden** (~100–240 €); für laufende Abhängigkeits- und Profilpflege eines Teams werden konservativ ca. **4 Stunden pro Jahr** (~400 €) angesetzt.

**2. Nutzenseite (Fehlervermeidung und Zeitersparnis).**
Nach der *Cost-of-Change*-Kurve von Boehm [[4]](#ref-4) und Boehm/Basili [[5]](#ref-5) steigen Fehlerbehebungskosten steil an, sobald ein Defekt die Kodierungsphase verlässt:

- **Vermiedene Hardware-Fehlersuche (Labor/Prüfstand):** Ein unentdeckter `ADC2`/WLAN- oder Flash-Pin-Konflikt äußert sich auf der Platine meist durch unspezifische Boot-Loops oder scheinbar verrauschte Messwerte. Eine realistische Fehlersuche mit Oszilloskop, Logikanalysator und Datenblattstudium bindet rasch **2 bis 4 Entwicklerstunden** (kalkulatorisch **160–480 €** pro Vorfall).
- **Vermiedene Leiterplatten-Iterationen (PCB-Respin):** Fließt ein fehlerhafter LLM-Pin-Entwurf in eine kundenspezifische Prototyp-Platine ein, entstehen direkte Fertigungs- und Bestückungskosten von typischerweise **300–1.000 €** zuzüglich **1–2 Wochen Projektverzögerung**.
- **Schnellerer Build- und LLM-Iterationszyklus:** Der Pre-Build-Abbruch in **1,21 s** spart gegenüber einem vollen Kompilier- und Flash-Durchlauf (~20–30 s) unmittelbar Wartezeit; zugleich ersetzt der deterministische Z3-Vorschlag oft 2–4 erfolglose LLM-Selbstkorrektur-Runden [[15]](#ref-15) samt zugehörigem Token- und Zeitaufwand.

**3. Modellhafte Break-even-Betrachtung.**
Tabelle 7.6 fasst zwei konservative Einsatzszenarien bei einem mittleren kalkulatorischen Stundensatz von **100 €/h** zusammen (ohne Anrechnung möglicher PCB-Respin-Kosten als zusätzliche Sicherheitsmarge).

| Szenario (Annahme: 100 €/h, 3 h gespart je verhindertem Pin-Fehler) | Laufender Aufwand (Jahr 1) | Einsparung je Vorfall | Break-even | Jährlicher Netto-Nutzen (konservativ) |
| :--- | :---: | :---: | :--- | :--- |
| **A: Nutzung fertiger Profile** (ESP32-C3/-S3 in 1 Team, 5 Entwickler) | ~1 h Setup + 4 h Pflege = **500 €** | **300 €** (3 h Debug) | ab **2** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.500 €/Jahr** |
| **B: Ergänzung eines neuen Chips** (z. B. RP2040/STM32, 2 h JSON + Prüfung) | ~2 h Profil + 5 h Setup/Pflege = **700 €** | **300 €** (3 h Debug) | ab **3** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.300 €/Jahr** |
| **C: Vollkosten-Betrachtung inkl. Eigenentwicklung** (150 h = 15.000 €, 1 Team) | **15.000 €** einmalig + **400 €/Jahr** | **300 €** Debug (bzw. **1.000 €** inkl. Respin) | ~50 Debug-Fehler oder ~15 verhinderte Respins | langfristig positiv bei mehrjähriger Team- oder Open-Source-Nutzung |

*Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung (Annahmen explizit im Text dokumentiert).*

**4. Wirtschaftliche Risiken und Grenzen.**
Dem positiven Nutzen stehen drei wirtschaftliche Risiken gegenüber: (1) Neue Chip-Revisionen oder Framework-Änderungen (wie der ESP-IDF-`adc_oneshot`-Treiber [[11]](#ref-11)) erfordern Pflege der JSON-Profile. (2) Breaking Changes in Drittpaketen (`tree-sitter`, `z3-solver`) verursachen Wartungsaufwand, der durch Versionsgrenzen und automatisierte CI begrenzt wird. (3) Durch verbleibende False Negatives (Abschnitt 8.2) darf das Werkzeug ein physisches Schaltplan-Review vor einer teuren Leiterplatten-Fertigung **nicht ersetzen**, sondern fungiert wirtschaftlich optimal als nahezu kostenlose automatische Frühstufe vor dem ersten Hardware-Aufbau.

### 7.7 Soll-Ist-Abgleich

Tabelle 7.7 überprüft alle Anforderungen und Invarianten aus Kapitel 4 am Stand `v0.2.0`.

| ID | Anforderung / Invariante | Status | Begründung / Einschränkung |
| :--- | :--- | :---: | :--- |
| FA-01 | Hardware-Profil laden & validieren | erfüllt | `load_board` (längstes Präfix, `_`/`-`, direkter `.json`-Pfad) + strenge Schema-Validierung (`test_board.py`) |
| FA-02 | Mehrere Dateien & `--include-dir` | erfüllt | Liest `include/` + `src/` sowie `--include-dir`; schließt `.pio/`, `test/`, `tests/` aus |
| FA-03 | Fehlalarmfreie Extraktion | weitgehend erfüllt | Erfasst Makros (inkl. `(12)`), Deklarationen (`12u`) und Literale; ignoriert Kommentare, Strings, lokale Variablen und Nicht-Pin-Konstanten; offene Grenzen bei `#ifdef` (`j`) und `gpio_num_t` (`i`) |
| FA-04 | Eindeutige Behandlung von Widersprüchen | erfüllt | `_reserve_unique_key` trennt alle abweichenden Definitionen und Literale eindeutig (auch bei 3 `#ifdef`-Zweigen) |
| FA-05 | Fähigkeiten, Bus-Rollen & Module | erfüllt | Mehrfachfähigkeiten als Menge (`h`), positionsgenaue `Wire`/`SPI`/`Serial`-Auswertung inkl. `bus_group` und Namens-Fallback (`OLED_SDA_PIN`) |
| FA-06 | Präzise Diagnose | erfüllt | Meldet alle Fehler einzeln mit `datei:zeile`-Verweis und konkreter Regelbegründung (`reason`) |
| FA-07 | Kollision vs. geteilte Bus-Leitung | erfüllt | Schützt geteilte Bus-Leitungen (`Wire:sda`), lehnt `SDA == SCL` (`m`), `Wire` vs. `Wire1` (`k`), `SCK == MOSI` und doppelte SPI-`CS` (`l`) ab |
| FA-08 | Minimale Reparatur & Kapazitätsmeldung | erfüllt | Dreistufige MaxSMT-Prioritäten (`1000`/`20`/`5`) + klare Meldung bei `repair_possible=False` (`d`, `e`) |
| FA-09 | Transparenter Bericht & Prompt | erfüllt | Zeigt `Checked Pins`, warnt bei 0 Pins und erzeugt kopierbare `Keep`/`Change`-Anweisungen |
| FA-10 | Build-Schranke & CLI | erfüllt | Verifiziert über `pip install .`, `mcu-validate` und realen PlatformIO-Registry-End-to-End-Lauf (`0.2.0`) |
| NFA-01–NFA-07 | Qualitätsanforderungen (ISO/IEC 25010:2023) | weitgehend erfüllt | 0 chip-spezifische Regeln in Python, 42 Tests, 5/5 grüne CI-Jobs (`ruff`, `mypy`); Zeitverhalten `< 1 s` erfüllt für alle `SAT`-Fälle bis 20 Pins (`7,59 ms` In-Process) und `UNSAT` bis 15 Pins (`0,80 s` E2E), bei 20 Pins `UNSAT` ~1,28 s E2E |
| INV-01–INV-06 | Architektur-Invarianten | erfüllt | Alle sechs Invarianten im Codebestand und durch automatisierte Tests abgesichert |

*Tabelle 7.7: Soll-Ist-Abgleich (`v0.2.0`).*

### 7.8 Gültigkeit der Ergebnisse (Threats to Validity)

In Anlehnung an die empirische Software-Engineering-Methodik von Wohlin et al. [[25]](#ref-25) werden drei Validitätsdimensionen kritisch eingeordnet:

- **Interne Gültigkeit** *(Stören zufällige Einflüsse die Messungen?)*: Prozess-Startzeiten unter Windows schwanken durch Hintergrundprozesse und Dateisystem-Caches. Durch 10 bis 30 Wiederholungen, Auswertung des Medians sowie strikte Trennung von Subprozess- und In-Process-Zeiten ist dieser Einfluss methodisch kontrolliert.
- **Externe Gültigkeit** *(Wie weit lassen sich die Befunde auf reale Industrieprojekte und diverse LLMs übertragen?)*: Sämtliche 42 Tests, neun Szenarien, dreizehn Grenzfälle und die synthetischen Skalierungsprojekte wurden im Rahmen dieser Arbeit konstruiert. Es liegt bislang **kein** großskaliger empirischer Benchmark über eine Stichprobe real von verschiedenen Sprachmodellen erzeugter Embedded-Projekte vor (im Unterschied etwa zu den Evaluationen in [[8]](#ref-8) oder [[22]](#ref-22)). Zudem umfassen die mitgelieferten Profile bislang nur ESP32-C3 und ESP32-S3; weitere Architekturen (RP2040, STM32) sind über das offene Schema vorbereitet, aber noch nicht eingepflegt.
- **Konstruktgültigkeit** *(Misst `SAT` tatsächlich vollständige Freiheit von Hardware-Fehlern?)*: Das Ergebnis `SAT` garantiert ausschließlich Konsistenz des *vom Parser extrahierten Pin-Modells* gegen das *hinterlegte JSON-Profil*. Elektrische Eigenschaften (Strombelastbarkeit, Spannungspegel) und syntaktisch nicht erfasste C++-Konstrukte (Abschnitt 8.2) liegen außerhalb des geprüften Konstrukts.

---

## 8 Diskussion, Grenzen und Ausblick

### 8.1 Diskussion der Ergebnisse

Die Evaluation belegt zweierlei: Zum einen lässt sich die in Kapitel 3 identifizierte Forschungslücke – deterministische AST-Extraktion ohne LLM-Formalisierungsfehler, gekoppelt mit validiertem Chip-Wissen und MaxSMT-Reparatur – in einem kompakten, gut wartbaren Werkzeug praxistauglich schließen. Der reale PlatformIO-Registry-Test bestätigt den Nutzen im Alltag unmittelbar: Ein fehlerhafter Build bricht nach 1,21 s ab und liefert Dateiname, Zeilennummer sowie eine Z3-geprüfte Ersatzbelegung, die sowohl gültige Originalpins als auch knappe ADC-Kanäle bewahrt.

Zum anderen zeigt der Vergleich zwischen Prototyp `v0.1.0` und Version `v0.2.0` den Wert systematischer Grenzfallexperimente: Erst die gezielte Suche nach Fehlerszenarien (Abschnitt 7.4) und der 20-Pin-Skalierungstest (Abschnitt 7.5) machten neun konkrete Schwächen in `v0.1.0` sowie die quadratische MaxSMT-Wachstumsgrenze bei rund 20 konfliktbehafteten Pins sichtbar.

### 8.2 Verbleibende Grenzen des Systems

Auch in Version `0.2.0` bestehen sechs klar benennbare Systemgrenzen, die unmittelbar aus den bewussten Architekturentscheidungen folgen (Tabelle 8.1):

1. **Präprozessor-Verzweigungen (`#ifdef` / `#else`).** Tree-Sitter wertet keine bedingte Kompilierung aus und besucht alle Zweige gleichzeitig. Enthält ein inaktiver Zweig einen für ein anderes Board gedachten Pin (Experiment `j`), entsteht weiterhin ein False Positive – wenngleich eindeutige Schlüssel selbst bei dreifachen Verzweigungen nun jeden Solver-Absturz verhindern.
2. **Spezielle C++-Typen und Ausdrücke.** ESP-IDF-Aufzählungen (`const gpio_num_t LED = GPIO_NUM_14;`, Experiment `i`), Pin-Arrays (`int pins[] = {...}`), `enum`-Definitionen und berechnete Makros (`#define LED (BASE + 2)`) werden nicht ausgewertet.
3. **Drittbibliotheks-Konstruktoren und -Methoden.** Wird ein Pin ausschließlich an eine Drittbibliothek übergeben (z. B. `myServo.attach(OUT_1)` oder `OneWire bus(DATA_LINE)`) und trägt keinen Pin-Bezeichner (`PIN`, `GPIO`, `SDA`, …), bleibt er unentdeckt; Konstruktoren wie `DHT dht(DHT_PIN, DHT22);` greifen nur auf den generischen `gpio`-Fallback zurück.
4. **USB-Serial-Annahme bei externem UART-Wandler.** In den ESP32-Profilen aktiviert `Serial.begin(...)` stets `usb_serial` und sperrt GPIO 18/19 (C3) bzw. 19/20 (S3). Auf Boards mit externem USB-UART-Wandlerchip (`ARDUINO_USB_CDC_ON_BOOT=0`) kann diese Regel zu konservativ sein.
5. **Chip-Abdeckung, Schema-Details und Skalierung.** Bisher liegen Profile für ESP32-C3 und ESP32-S3 vor; optionale Schema-Felder für reine Eingangs-Pins (`input_only`, etwa GPIO 34–39 beim klassischen ESP32), PWM-Kanalbudgets oder siliziumspezifische Treiber-Errata (z. B. `CONFIG_ADC_ONESHOT_FORCE_USE_ADC2_ON_C3` [[11]](#ref-11)) sind noch nicht modelliert. Zudem steigt die Z3-Laufzeit bei 20 konfliktbehafteten Pins auf ~1,14 s (Tabelle 7.5).
6. **Manueller Rückkopplungskreis und fehlender LLM-Benchmark.** Der Prompt wird noch manuell in den LLM-Chat kopiert, und die Fehlerrate realer Sprachmodelle vor vs. nach Einsatz von `mcu-pin-solver` steht als empirische Folgestudie noch aus.

| Nr. | Verbleibende Grenze (`v0.2.0`) | Ort | Auswirkung | Möglicher Ausbau |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `#ifdef` / `#else`-Zweige | `parser.py` | False Positive bei Alternativ-Konfigs (`j`) | Makro-Filter über `-D`-Build-Flags aus `platformio.ini` |
| 2 | `gpio_num_t`, Arrays, `enum`, Rechen-Makros | `parser.py` | False Negative (`i`) | Erweiterung der AST-Regeln um `GPIO_NUM_<n>` und `enumerator` |
| 3 | Drittbibliotheks-Aufrufe / Konstruktoren | `parser.py` | False Negative ohne `PIN`-Namensmuster | Konfigurierbare API-Muster im Profil oder Konfigurationsdatei |
| 4 | `Serial.begin` bei externem UART-Bridge-Chip | `boards/*.json` / `pio_hook.py` | Ggf. zu strenge Sperre auf USB-Pins | Auswertung von `-DARDUINO_USB_CDC_ON_BOOT` aus PlatformIO |
| 5 | Chip-Katalog, Schema-Details & 20-Pin-MaxSMT | `boards/*.json` / `solver.py` | Nur C3/S3; ~1,14 s bei 20 Konflikt-Pins | Optionale Felder (`input_only`), weitere MCUs, boolesche / `Distinct`-Kodierung |
| 6 | Manueller Prompt & kein LLM-Benchmark | Workflow / Evaluation | Kopierschritt nötig; externe Validität offen | MCP-Tool / `--json` + systematische LLM-Vergleichsstudie |

*Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`.*

### 8.3 Reflexion der KI-gestützten Entstehung

Sowohl die Entwicklung von `v0.1.0` und `v0.2.0` als auch Entwürfe dieser Ausarbeitung entstanden unter Mitwirkung großer Sprachmodelle (vgl. Verzeichnis der verwendeten KI-Hilfsmittel). Dabei zeigte sich das Kernthema dieser Arbeit gleich zweifach im eigenen Entwicklungsprozess:

1. **Empirische Gegenprüfung plausibler Behauptungen:** Ein früher Entwurf behauptete, Z3 löse Gleichstände zwischen identischen Pins deterministisch nach ihrer Deklarationsreihenfolge auf – erst die Experimente `c` und `c2` widerlegten dies direkt am Code.
2. **Subtile Fehler erst durch Tests und CI sichtbar:** Beim Ausbau der Namensheuristik in `v0.2.0` übersah der reguläre Ausdruck `WORD_RE` zunächst Großbuchstaben-Wörter vor Unterstrichen (`OLED_SDA_PIN`), weil der Lookahead Unterstriche nicht berücksichtigte; erst der neu geschriebene Unit-Test deckte den Defekt sofort auf. Ebenso offenbarte erst die reale GitHub-Actions-CI-Matrix, dass `ubuntu-latest` keine vorinstallierten Python-3.9-Binaries mehr bereitstellt, während erst der Skalierungstest (Tabelle 7.5) die 1-Sekunden-Grenze bei 20 konfliktbehafteten Pins offenlegte.

Automatisierte Tests, statische Prüfungen (`ruff`, `mypy`) und reale End-to-End-Messungen erwiesen sich damit als unverzichtbares Korrektiv gegenüber plausibel wirkendem KI-Code.

### 8.4 Ausblick

Aus dem erreichten Stand `0.2.0` ergeben sich vier lohnende nächste Ausbaustufen:

1. **Übergabe von PlatformIO-Build-Flags:** Über aktive `-D`-Definitionen aus `platformio.ini` ließen sich sowohl `#ifdef`-Zweige präzise filtern als auch native USB-CDC-Boards von Boards mit externem USB-UART-Wandler unterscheiden.
2. **Automatisierter Agenten-Kreislauf (MCP / `--json`):** Durch eine maschinenlesbare `--json`-Ausgabe oder eine MCP-Werkzeugschnittstelle kann ein KI-Coding-Agent (analog zu AutoIOT [[22]](#ref-22) oder EmbedGenius [[26]](#ref-26)) `mcu-validate` direkt als deterministischen Hardware-Critic aufrufen und Konflikte mit begrenzter Iterationszahl automatisch beheben.
3. **Solver-Beschleunigung für große Mikrocontroller (> 20 Pins):** Durch Gruppierung nicht geteilter Signale in ein globales `z3.Distinct(...)` oder eine optionale boolesche One-Hot-Kodierung (`PbEq` / `AtMost`) lässt sich das quadratische Wachstum aus Tabelle 7.5 für große MCUs (z. B. STM32 mit > 60 Pins) deutlich reduzieren.
4. **Katalog-Ausbau und empirische LLM-Studie:** Ergänzung verifizierter Profile für den klassischen ESP32 (mit `input_only`), ESP32-C6, RP2040 und STM32 sowie eine systematische empirische Studie über mehrere Sprachmodelle (Messung der Hardware-Korrektheitsrate mit vs. ohne `mcu-pin-solver`).

---

## 9 Fazit

Die vorliegende Studienarbeit hat mit `mcu-pin-solver` (Version `0.2.0`) ein datengetriebenes Pre-Build-Werkzeug zur statischen Prüfung und MaxSMT-Reparatur von GPIO-Pin-Belegungen in Embedded-C++-Projekten konzipiert, iterativ gehärtet, auf GitHub sowie der PlatformIO Registry veröffentlicht und empirisch evaluiert. Die drei Forschungsfragen lassen sich abschließend wie folgt beantworten:

- **Zu FF1 (Extraktion ohne Ziel-Toolchain):** Mit `tree-sitter-cpp` werden Top-Level-Pin-Konstanten, direkte Pin-Literale, Fähigkeitsmengen, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) und aktive Peripherie über verteilte `include/`- und `src/`-Dateien hinweg ohne Ziel-Compiler in wenigen Millisekunden (unter 2 ms für 3 Dateien, 7,53 ms für 21 Dateien) extrahiert. Kommentare, Zeichenketten, lokale Variablen und Nicht-Pin-Konstanten erzeugen keine Fehlalarme; bewusste Grenzen bleiben `#ifdef`-Alternativen, `gpio_num_t`-Typen und unbekannte Drittbibliotheks-APIs.
- **Zu FF2 (Validierte Datentrennung und MaxSMT-Reparatur):** Durch die Trennung in schema-validierte JSON-Profile (`mcu_validator/boards/*.json`) ist der Prüfcode vollständig chip-agnostisch, wie der direkte Vergleich desselben Programms auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`) belegt. Die zweistufige Pipeline kombiniert eine nahezu verzögerungsfreie Diagnose mit Dateizeilen-Verweis in Stufe 1 (`0,01–0,06 ms` bei `SAT` selbst für 20 Pins) mit einer dreistufig gewichteten MaxSMT-Reparatur in Z3 (`1000` / `20` / `5`), die gültige Pins bewahrt, geteilte Bus-Leitungen zusammenhält, Strapping-Pins meidet, knappe ADC-/USB-Pins schont und Überbuchungen sauber meldet.
- **Zu FF3 (Integration, Praxistauglichkeit und Wirtschaftlichkeit):** Über `pio_hook.py`, `library.json` (`"srcFilter": ["-<*>"]`) und gebündelte Paketdaten in `pyproject.toml` ist das Werkzeug per `pip install .` (`mcu-validate`) und über die PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) unmittelbar einsetzbar. Der Live-Registry-Test bestätigte den Build-Abbruch nach 1,21 s vor dem Kompilieren und den fehlerfreien Durchlauf nach Reparatur; alle 42 Tests sowie `ruff` und `mypy` bestehen unter Windows und Linux. Dank 0 € Lizenz- und API-Kosten amortisiert sich der Einsatz in einem Embedded-Team bereits nach wenigen verhinderten Hardware-Fehlersuchen.

Insgesamt belegt `mcu-pin-solver` am produktiven System, dass die Verbindung aus generativem Sprachmodell, deterministischem AST-Parser und formalem Z3-Solver eine schnelle, transparente und wirtschaftlich sinnvolle Schutzschicht für das Embedded-Prototyping bildet.

---

## Literaturverzeichnis

- <a id="ref-1"></a>**[1] Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006):** *Compilers: Principles, Techniques, and Tools* (2. Aufl.). Addison-Wesley, Boston.
- <a id="ref-2"></a>**[2] Barrett, C., Sebastiani, R., Seshia, S. A., & Tinelli, C. (2021):** *Satisfiability Modulo Theories.* In: Biere, A., Heule, M., van Maaren, H., & Walsh, T. (Hrsg.): *Handbook of Satisfiability* (2. Aufl.), Frontiers in Artificial Intelligence and Applications, Bd. 336, S. 1267–1329, IOS Press.
- <a id="ref-3"></a>**[3] Bjørner, N., Phan, A.-D., & Fleckenstein, L. (2015):** *$\nu Z$ – An Optimizing SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2015)*, Lecture Notes in Computer Science, Bd. 9035, S. 194–199, Springer. DOI: `10.1007/978-3-662-46681-0_14`.
- <a id="ref-4"></a>**[4] Boehm, B. W. (1981):** *Software Engineering Economics.* Prentice-Hall, Englewood Cliffs, NJ.
- <a id="ref-5"></a>**[5] Boehm, B., & Basili, V. R. (2001):** *Software Defect Reduction Top 10 List.* IEEE Computer, Bd. 34, Nr. 1, S. 135–137. DOI: `10.1109/2.962984`.
- <a id="ref-6"></a>**[6] Brunsfeld, M. (2018):** *Tree-sitter – An incremental parsing system for programming tools.* Online-Dokumentation: `https://tree-sitter.github.io/tree-sitter/`.
- <a id="ref-7"></a>**[7] De Moura, L., & Bjørner, N. (2008):** *Z3: An Efficient SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2008)*, Lecture Notes in Computer Science, Bd. 4963, S. 337–340, Springer. DOI: `10.1007/978-3-540-78800-3_24`.
- <a id="ref-8"></a>**[8] Englhardt, Z., Li, R., Nissanka, D., Zhang, Z., Narayanswamy, G., Breda, J., Liu, X., Patel, S., & Iyer, V. (2024):** *Exploring and Characterizing Large Language Models for Embedded System Development and Debugging.* In: *Extended Abstracts of the CHI Conference on Human Factors in Computing Systems (CHI EA '24)* (Preprint: `arXiv:2307.03817`).
- <a id="ref-9"></a>**[9] Espressif Systems (2024):** *ESP32-C3 Series Datasheet* & *ESP32-C3 Technical Reference Manual.* Espressif Systems, Shanghai.
- <a id="ref-10"></a>**[10] Espressif Systems (2024):** *ESP32-S3 Series Datasheet* & *ESP32-S3 Technical Reference Manual.* Espressif Systems, Shanghai.
- <a id="ref-11"></a>**[11] Espressif Systems (2024):** *ESP-IDF Programming Guide – Analog to Digital Converter (ADC) Oneshot Mode Driver & Hardware Limitations (ESP32-C3 / ESP32-S3).* Online-Dokumentation: `https://docs.espressif.com/projects/esp-idf/`.
- <a id="ref-12"></a>**[12] Fakih, M., Dharmaji, R., Moghaddas, Y., Quiros Araya, G., Ogundare, O., & Al Faruque, M. A. (2024):** *LLM4PLC: Harnessing Large Language Models for Verifiable Programming of PLCs in Industrial Control Systems.* In: *IEEE/ACM 46th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP 2024)*, S. 192–203.
- <a id="ref-13"></a>**[13] Garcez, A. d'Avila, & Lamb, L. C. (2023):** *Neurosymbolic AI: The 3rd Wave.* Artificial Intelligence Review, Bd. 56, Nr. 11, S. 12387–12406, Springer. DOI: `10.1007/s10462-023-10448-w`.
- <a id="ref-14"></a>**[14] Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006):** *Introduction to Automata Theory, Languages, and Computation* (3. Aufl.). Addison-Wesley, Boston.
- <a id="ref-15"></a>**[15] Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X., & Zhou, D. (2024):** *Large Language Models Cannot Self-Correct Reasoning Yet.* In: *Twelfth International Conference on Learning Representations (ICLR 2024)*.
- <a id="ref-16"></a>**[16] ISO/IEC (2023):** *ISO/IEC 25010:2023 – Systems and software engineering – Systems and software Quality Requirements and Evaluation (SQuaRE) – Product quality model.* International Organization for Standardization, Genf.
- <a id="ref-17"></a>**[17] Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L., & Murthy, A. (2024):** *LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* In: *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*, PMLR Bd. 235, S. 22895–22907.
- <a id="ref-18"></a>**[18] Narodytska, N., & Bacchus, F. (2014):** *Maximum Satisfiability Using Core-Guided MaxSAT Resolution.* In: *Proceedings of the Twenty-Eighth AAAI Conference on Artificial Intelligence (AAAI 2014)*, S. 2717–2723.
- <a id="ref-19"></a>**[19] Pan, L., Albalak, A., Wang, X., & Wang, W. Y. (2023):** *Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning.* In: *Findings of the Association for Computational Linguistics: EMNLP 2023*, S. 3806–3824. DOI: `10.18653/v1/2023.findings-emnlp.248`.
- <a id="ref-20"></a>**[20] PlatformIO (2024):** *PlatformIO Core Documentation – Project Configuration (`platformio.ini`), Library Manifest (`library.json`) and Advanced Scripting.* Online-Dokumentation: `https://docs.platformio.org/`.
- <a id="ref-21"></a>**[21] Rust Embedded Working Group (2024):** *embedded-hal: A Hardware Abstraction Layer (HAL) for embedded systems.* Online-Dokumentation: `https://docs.rs/embedded-hal/`.
- <a id="ref-22"></a>**[22] Shen, L., Yang, Q., Zheng, Y., & Li, M. (2025):** *AutoIOT: LLM-Driven Automated Natural Language Programming for AIoT Applications.* In: *Proceedings of the 31st Annual International Conference on Mobile Computing and Networking (ACM MobiCom 2025)*. DOI: `10.1145/3680207.3723486` (Preprint: `arXiv:2503.05346`).
- <a id="ref-23"></a>**[23] STMicroelectronics (2024):** *STM32CubeMX: STM32Cube initialization code generator.* Online-Dokumentation: `https://www.st.com/en/development-tools/stm32cubemx.html`.
- <a id="ref-24"></a>**[24] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017):** *Attention Is All You Need.* In: *Advances in Neural Information Processing Systems (NeurIPS 2017)*, Bd. 30.
- <a id="ref-25"></a>**[25] Wohlin, C., Runeson, P., Höst, M., Ohlsson, M. C., Regnell, B., & Wesslén, A. (2024):** *Experimentation in Software Engineering* (2. Aufl.). Springer, Berlin/Heidelberg. DOI: `10.1007/978-3-662-69306-3`.
- <a id="ref-26"></a>**[26] Yang, H., Li, M., Han, M., Li, Z., & Xu, W. (2024):** *EmbedGenius: Towards Automated Software Development for Generic Embedded IoT Systems.* Preprint: `arXiv:2412.09058`.
- <a id="ref-27"></a>**[27] Ye, X., Chen, Q., Dillig, I., & Durrett, G. (2023):** *SatLM: Satisfiability-Aided Language Models Using Declarative Prompting.* In: *Advances in Neural Information Processing Systems (NeurIPS 2023)*, Bd. 36, S. 45548–45580 (Preprint: `arXiv:2305.09656`).
- <a id="ref-28"></a>**[28] Zephyr Project (2024):** *Zephyr Project Documentation – Devicetree Guide.* Online-Dokumentation: `https://docs.zephyrproject.org/latest/build/dts/index.html`.

---

## Anhang

### Anhang A: Hardware-Profil `mcu_validator/boards/esp32-c3.json`

```json
{
  "mcu": "ESP32-C3",
  "description": "Espressif ESP32-C3 (RISC-V, Single-Core, Wi-Fi/BLE)",
  "pins": {
    "0":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "1":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "2":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (boot mode)" },
    "3":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "4":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false },
    "5":  { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "6":  { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false },
    "7":  { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false },
    "8":  { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (ROM log / boot)" },
    "9":  { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (BOOT button)" },
    "10": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "11": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal flash power supply (VDD_SPI)" },
    "12": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIHD)" },
    "13": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIWP)" },
    "14": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPICS0)" },
    "15": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPICLK)" },
    "16": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPID)" },
    "17": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIQ)" },
    "18": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "usb"], "strapping": false, "reserved": false, "note": "USB D-" },
    "19": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "usb"], "strapping": false, "reserved": false, "note": "USB D+" },
    "20": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "Default UART0 RX" },
    "21": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "Default UART0 TX" }
  },
  "capability_aliases": {
    "adc": ["adc1", "adc2"]
  },
  "shared_capabilities": ["i2c", "spi"],
  "resource_triggers": {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"]
  },
  "conflict_rules": [
    {
      "id": "WIFI_BLOCKS_ADC2",
      "when_resource_active": "wifi",
      "forbidden_capability": "adc2",
      "reason": "ADC2 cannot be used while Wi-Fi is active on ESP32-C3."
    },
    {
      "id": "USB_BLOCKS_GPIO18_19",
      "when_resource_active": "usb_serial",
      "forbidden_pins": [18, 19],
      "reason": "GPIO 18 and 19 are occupied by the internal USB-Serial/JTAG interface."
    }
  ]
}
```

### Anhang B: Hardware-Profil `mcu_validator/boards/esp32-s3.json`

```json
{
  "mcu": "ESP32-S3",
  "description": "Espressif ESP32-S3 (Dual-Core Xtensa LX7, Wi-Fi/BLE)",
  "pins": {
    "0":  { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (boot mode)" },
    "1":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "2":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "3":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (JTAG signal source)" },
    "4":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "5":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "6":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "7":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "8":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "9":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "10": { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "11": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "12": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "13": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "14": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "15": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "16": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "17": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "18": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "19": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart", "usb"], "strapping": false, "reserved": false, "note": "USB D- & ADC2" },
    "20": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi", "uart", "usb"], "strapping": false, "reserved": false, "note": "USB D+ & ADC2" },
    "21": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "26": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "27": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "28": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "29": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "30": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "31": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "32": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash / PSRAM" },
    "33": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal Octal-SPI flash / PSRAM" },
    "34": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal Octal-SPI flash / PSRAM" },
    "35": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal Octal-SPI flash / PSRAM" },
    "36": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal Octal-SPI flash / PSRAM" },
    "37": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal Octal-SPI flash / PSRAM" },
    "38": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "39": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "JTAG (MTCK)" },
    "40": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "JTAG (MTDO)" },
    "41": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "JTAG (MTDI)" },
    "42": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart", "jtag"], "strapping": false, "reserved": false, "note": "JTAG (MTMS)" },
    "43": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "Default UART0 TX" },
    "44": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false, "note": "Default UART0 RX" },
    "45": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (VDD_SPI voltage)" },
    "46": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": true,  "reserved": false, "note": "Strapping pin (ROM log / boot)" },
    "47": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false },
    "48": { "capabilities": ["gpio", "pwm", "i2c", "spi", "uart"], "strapping": false, "reserved": false }
  },
  "capability_aliases": {
    "adc": ["adc1", "adc2"]
  },
  "shared_capabilities": ["i2c", "spi"],
  "resource_triggers": {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"]
  },
  "conflict_rules": [
    {
      "id": "WIFI_BLOCKS_ADC2",
      "when_resource_active": "wifi",
      "forbidden_capability": "adc2",
      "reason": "ADC2 cannot be used reliably while Wi-Fi is active on ESP32-S3."
    },
    {
      "id": "USB_BLOCKS_GPIO19_20",
      "when_resource_active": "usb_serial",
      "forbidden_pins": [19, 20],
      "reason": "GPIO 19 and 20 are occupied by the internal USB-Serial/JTAG interface on ESP32-S3."
    }
  ]
}
```

### Anhang C: Quelltext `mcu_validator/board.py`

```python
"""Board hardware profiles loaded and validated from declarative JSON files.

Every microcontroller's physical rules (exposed GPIOs, reserved flash pins,
capabilities, active-peripheral conflicts) live in `mcu_validator/boards/*.json`.
This module parses and validates one JSON file into typed dataclasses so the
rest of the codebase never works with untyped dictionaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Bundled board profiles shipped inside the `mcu_validator` package.
BOARDS_DIR = Path(__file__).resolve().parent / "boards"


@dataclass(frozen=True)
class PinSpec:
    """Hardware properties of one physical GPIO pin on the microcontroller.

    Example:
        PinSpec(number=5, capabilities=frozenset({"gpio", "adc2"}), note="ADC2 + Wi-Fi conflict")
    """

    number: int
    capabilities: frozenset[str]  # Supported features (e.g. {"gpio", "adc1", "pwm"})
    strapping: bool = False       # Boot/strapping pin (prefer avoiding during repair)
    reserved: bool = False        # Internal system pin like SPI flash (must never be used)
    note: str = ""                # Optional short explanation shown in conflict messages


@dataclass(frozen=True)
class ConflictRule:
    """Rule blocking a capability or specific pins whenever a peripheral is active.

    Example:
        When "wifi" is active -> forbid capability "adc2".
        When "usb_serial" is active -> forbid pins {18, 19}.
    """

    id: str
    when_resource_active: str
    reason: str
    forbidden_capability: str | None = None
    forbidden_pins: frozenset[int] = frozenset()


@dataclass(frozen=True)
class BoardSpec:
    """Complete hardware rulebook for one microcontroller (loaded from a board JSON)."""

    mcu: str
    description: str
    pins: dict[int, PinSpec]
    capability_aliases: dict[str, frozenset[str]]
    shared_capabilities: frozenset[str]
    resource_triggers: dict[str, tuple[str, ...]]
    conflict_rules: tuple[ConflictRule, ...]

    def expand_capability(self, cap: str) -> frozenset[str]:
        """Expand a generic capability alias (e.g. 'adc' -> {'adc1', 'adc2'})."""
        return self.capability_aliases.get(cap, frozenset({cap}))

    @classmethod
    def from_dict(cls, data: object) -> BoardSpec:
        """Validate a raw JSON dictionary and build a typed `BoardSpec`.

        Raises:
            ValueError: If required fields are missing or have invalid types.
        """
        if not isinstance(data, dict):
            raise ValueError("Board profile JSON must be an object at the top level.")

        mcu = data.get("mcu")
        if not isinstance(mcu, str) or not mcu.strip():
            raise ValueError("Board profile must define a non-empty string 'mcu'.")

        description = data.get("description", "")
        if not isinstance(description, str):
            raise ValueError(f"Board '{mcu}': 'description' must be a string.")

        pins = _parse_pins(data.get("pins"), mcu)
        aliases = _parse_string_list_map(
            data.get("capability_aliases", {}), "capability_aliases", mcu
        )
        shared = frozenset(
            _parse_string_list(data.get("shared_capabilities", []), "shared_capabilities", mcu)
        )
        triggers = _parse_string_list_map(
            data.get("resource_triggers", {}), "resource_triggers", mcu
        )
        rules = _parse_conflict_rules(data.get("conflict_rules", []), triggers, mcu)

        return cls(
            mcu=mcu,
            description=description,
            pins=pins,
            capability_aliases={k: frozenset(v) for k, v in aliases.items()},
            shared_capabilities=shared,
            resource_triggers={k: tuple(v) for k, v in triggers.items()},
            conflict_rules=rules,
        )


def list_boards(boards_dir: Path = BOARDS_DIR) -> tuple[str, ...]:
    """Return sorted board profile names available in `boards_dir`."""
    if not boards_dir.is_dir():
        return ()
    return tuple(sorted(p.stem for p in boards_dir.glob("*.json")))


def load_board(board_id: str = "esp32-c3", boards_dir: Path = BOARDS_DIR) -> BoardSpec:
    """Find, load, and validate the JSON hardware profile matching `board_id`.

    `board_id` may be either:
      - A PlatformIO/MCU name such as `"esp32-c3-devkitm-1"` or `"ESP32_S3"` (matched
        against `*.json` stems in `boards_dir`, longest match first), or
      - A direct path to a `.json` board profile file.

    Raises:
        FileNotFoundError: If no matching board JSON exists.
        ValueError: If the JSON syntax or board schema is invalid.
    """
    direct_path = Path(board_id)
    if direct_path.suffix.lower() == ".json" and direct_path.is_file():
        return _load_board_file(direct_path)

    normalized = _normalize_name(board_id)
    candidates = sorted(
        boards_dir.glob("*.json") if boards_dir.is_dir() else (),
        key=lambda p: (-len(_normalize_name(p.stem)), _normalize_name(p.stem)),
    )
    for json_file in candidates:
        if _normalize_name(json_file.stem) in normalized:
            return _load_board_file(json_file)

    available = ", ".join(list_boards(boards_dir)) or "none"
    raise FileNotFoundError(
        f"No board profile matching '{board_id}' in {boards_dir} (available: {available})."
    )


# ---------------------------------------------------------------------------
# Internal schema validation helpers
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    """Normalize board names and file stems so 'ESP32_C3' matches 'esp32-c3'."""
    return name.strip().lower().replace("_", "-")


def _load_board_file(json_file: Path) -> BoardSpec:
    """Read a JSON board file and convert JSON/schema errors into clear ValueErrors."""
    try:
        raw_data = json.loads(json_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in board profile '{json_file}': {exc}") from exc
    return BoardSpec.from_dict(raw_data)


def _parse_pins(raw_pins: object, mcu: str) -> dict[int, PinSpec]:
    """Validate the 'pins' mapping and convert string keys to integer GPIO numbers."""
    if not isinstance(raw_pins, dict):
        raise ValueError(f"Board '{mcu}': 'pins' must be an object mapping pin numbers to specs.")

    pins: dict[int, PinSpec] = {}
    for raw_num, info in raw_pins.items():
        if not isinstance(raw_num, str) or not raw_num.isdigit():
            raise ValueError(
                f"Board '{mcu}': pin key '{raw_num}' must be a non-negative integer string."
            )
        if not isinstance(info, dict):
            raise ValueError(f"Board '{mcu}': pin '{raw_num}' entry must be an object.")

        num = int(raw_num)
        caps = _parse_string_list(info.get("capabilities", []), f"pins.{raw_num}.capabilities", mcu)
        strapping = _parse_bool(info.get("strapping", False), f"pins.{raw_num}.strapping", mcu)
        reserved = _parse_bool(info.get("reserved", False), f"pins.{raw_num}.reserved", mcu)
        note = info.get("note", "")
        if not isinstance(note, str):
            raise ValueError(f"Board '{mcu}': 'pins.{raw_num}.note' must be a string.")

        pins[num] = PinSpec(
            number=num,
            capabilities=frozenset(caps),
            strapping=strapping,
            reserved=reserved,
            note=note,
        )
    return pins


def _parse_conflict_rules(
    raw_rules: object,
    triggers: dict[str, list[str]],
    mcu: str,
) -> tuple[ConflictRule, ...]:
    """Validate 'conflict_rules' entries and check that their trigger modules exist."""
    if not isinstance(raw_rules, list):
        raise ValueError(f"Board '{mcu}': 'conflict_rules' must be a list.")

    rules: list[ConflictRule] = []
    for idx, rule in enumerate(raw_rules):
        if not isinstance(rule, dict):
            raise ValueError(f"Board '{mcu}': conflict_rules[{idx}] must be an object.")

        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError(f"Board '{mcu}': conflict_rules[{idx}] needs a non-empty string 'id'.")

        resource = rule.get("when_resource_active")
        if not isinstance(resource, str) or not resource.strip():
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' needs a string 'when_resource_active'."
            )
        if resource not in triggers:
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' references unknown resource '{resource}' "
                f"(not defined in 'resource_triggers')."
            )

        forbidden_cap = rule.get("forbidden_capability")
        if forbidden_cap is not None and not isinstance(forbidden_cap, str):
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' 'forbidden_capability' must be a string."
            )

        raw_forbidden_pins = rule.get("forbidden_pins", [])
        if not isinstance(raw_forbidden_pins, list) or not all(
            isinstance(p, int) and not isinstance(p, bool) and p >= 0 for p in raw_forbidden_pins
        ):
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' 'forbidden_pins' must be "
                "a list of non-negative integers."
            )

        if forbidden_cap is None and not raw_forbidden_pins:
            raise ValueError(
                f"Board '{mcu}': rule '{rule_id}' must specify "
                "'forbidden_capability' or 'forbidden_pins'."
            )

        reason = rule.get("reason", f"Blocked by active '{resource}'.")
        if not isinstance(reason, str):
            raise ValueError(f"Board '{mcu}': rule '{rule_id}' 'reason' must be a string.")

        rules.append(
            ConflictRule(
                id=rule_id,
                when_resource_active=resource,
                reason=reason,
                forbidden_capability=forbidden_cap,
                forbidden_pins=frozenset(raw_forbidden_pins),
            )
        )
    return tuple(rules)


def _parse_string_list(value: object, field_name: str, mcu: str) -> list[str]:
    """Ensure a JSON value is a list of strings (rejecting bare strings like 'gpio')."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be a list of strings.")
    return value


def _parse_string_list_map(value: object, field_name: str, mcu: str) -> dict[str, list[str]]:
    """Ensure a JSON value is a dict mapping string keys to lists of strings."""
    if not isinstance(value, dict):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be an object.")
    result: dict[str, list[str]] = {}
    for key, items in value.items():
        if not isinstance(key, str):
            raise ValueError(f"Board '{mcu}': keys in '{field_name}' must be strings.")
        result[key] = _parse_string_list(items, f"{field_name}.{key}", mcu)
    return result


def _parse_bool(value: object, field_name: str, mcu: str) -> bool:
    """Ensure a JSON value is strictly a boolean."""
    if not isinstance(value, bool):
        raise ValueError(f"Board '{mcu}': '{field_name}' must be a boolean.")
    return value
```

### Anhang D: Quelltext `mcu_validator/parser.py`

```python
"""Tree-Sitter C++ AST analyzer that extracts pin requests and active peripherals.

Start reading at `parse_cpp()` — it shows the full 4-step pipeline from top to bottom.
Each helper section below implements one step in execution order.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Node, Parser

from .board import BoardSpec

# Compiled Tree-Sitter C++ grammar (immutable; each scan creates its own Parser instance).
CPP_LANGUAGE = Language(tscpp.language())

HEADER_EXTS = frozenset({".h", ".hpp"})
CPP_EXTS = HEADER_EXTS | {".c", ".cpp", ".ino"}
IGNORED_DIRS = frozenset({".git", ".pio", ".venv", "__pycache__", "build", "test", "tests", "venv"})
PIN_VAR_TYPES = frozenset({"int", "unsigned int", "uint8_t", "int8_t", "byte"})

# Arduino / ESP32 functions where argument #0 is a hardware pin.
ARG0_CAPABILITIES: dict[str, str] = {
    "pinMode": "gpio",
    "digitalWrite": "gpio",
    "digitalRead": "gpio",
    "digitalPinToInterrupt": "gpio",
    "pulseIn": "gpio",
    "tone": "gpio",
    "noTone": "gpio",
    "analogRead": "adc",
    "analogReadMilliVolts": "adc",
    "analogWrite": "pwm",
    "ledcAttach": "pwm",
    "ledcAttachPin": "pwm",
}

# Suffixes that indicate a non-pin setting (e.g. BAUD_RATE, DELAY_MS, I2C_ADDR, LED_COUNT).
NON_PIN_SUFFIXES = frozenset({
    "ADDR", "BAUD", "CH", "CHANNEL", "COUNT", "DELAY", "FREQ", "HZ", "ID",
    "INTERVAL", "LEN", "LIMIT", "MASK", "MAX", "MIN", "MODE", "MS", "NUM",
    "OFFSET", "PERIOD", "PORT", "RATE", "SIZE", "SPEED", "TIMEOUT", "TYPE", "US",
})

WIRE_CALL_RE = re.compile(r"^(Wire\d*)\.(?:begin|setPins)$")
SPI_CALL_RE = re.compile(r"^(SPI\d*)\.begin$")
SERIAL_CALL_RE = re.compile(r"^Serial\d*\.begin$")
COMMENT_RE = re.compile(r"//.*|/\*.*?\*/", re.DOTALL)
WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|_|\d|$)|[A-Z]?[a-z]+|\d+")


@dataclass(frozen=True)
class PinRequest:
    """One hardware pin assignment extracted from C/C++ code.

    Example:
        PinRequest(name="SOIL_SENSOR", pin=5, capabilities=frozenset({"adc"}), location="pins.h:5")
    """

    name: str                      # Unique signal key (e.g. "SOIL_SENSOR" or "GPIO_12")
    pin: int                       # Assigned GPIO number from the C++ code
    capabilities: frozenset[str]   # Required features (e.g. {"adc"}, {"i2c"})
    bus_group: str | None = None   # Shared bus line identity (e.g. "Wire:sda", "SPI:mosi")
    location: str = ""             # Source file:line like "pins.h:4" (empty if created manually)


@dataclass(frozen=True)
class ParsedProject:
    """Complete parser output handed to the solver."""

    requests: tuple[PinRequest, ...]
    active_resources: tuple[str, ...]


@dataclass(frozen=True)
class _PinDefinition:
    """One top-level integer constant discovered during AST scanning."""

    key: str           # Globally unique signal name
    raw_name: str      # Original C++ identifier
    pin: int
    source_file: Path
    line: int          # 1-based line number


@dataclass(frozen=True)
class _LiteralPinUse:
    """One direct numeric pin argument (e.g. `pinMode(12, OUTPUT)` or `Wire.begin(6, 7)`)."""

    pin: int
    capability: str
    bus_group: str | None
    location: str


@dataclass
class _SourceScan:
    """Mutable working notebook filled while walking all C/C++ files in Step 2."""

    definitions: list[_PinDefinition] = field(default_factory=list)
    used_keys: set[str] = field(default_factory=set)
    seen_values: dict[str, set[int]] = field(default_factory=dict)
    called_functions: set[str] = field(default_factory=set)
    caps_by_name: dict[str, set[str]] = field(default_factory=dict)
    caps_by_file_and_name: dict[tuple[Path, str], set[str]] = field(default_factory=dict)
    bus_by_name: dict[str, set[str]] = field(default_factory=dict)
    bus_by_file_and_name: dict[tuple[Path, str], set[str]] = field(default_factory=dict)
    literal_uses: list[_LiteralPinUse] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level orchestrator (read this first!)
# ---------------------------------------------------------------------------

def parse_cpp(
    cpp_path: str | Path,
    board: BoardSpec | None = None,
    include_dirs: Sequence[str | Path] = (),
) -> ParsedProject:
    """Analyze a C/C++ file or project folder and extract its pin requirements.

    Steps:
        1. Resolve all `.h/.hpp/.c/.cpp/.ino` files to inspect.
        2. Parse each file with Tree-Sitter to collect constants and API calls.
        3. Match constants and numeric pin calls to required hardware capabilities.
        4. Detect which board peripherals (like Wi-Fi or USB-Serial) are active.
    """
    files = _resolve_source_files(cpp_path, include_dirs)
    scan = _scan_files(files)
    requests = _build_pin_requests(scan)
    active_resources = _detect_active_resources(scan.called_functions, board)
    return ParsedProject(requests=requests, active_resources=active_resources)


# ---------------------------------------------------------------------------
# Step 1: Resolve which C/C++ files belong to the target path
# ---------------------------------------------------------------------------

def _resolve_source_files(
    target: str | Path,
    include_dirs: Sequence[str | Path] = (),
) -> list[Path]:
    """Turn a single file or project directory (plus optional include dirs) into sorted files."""
    path = Path(target)
    if path.is_file():
        files = [path]
        extra_dirs = [Path(d) for d in include_dirs if Path(d).is_dir()]
        if not extra_dirs:
            return files
        found = _dedupe_paths([*files, *_collect_files_in_dirs(extra_dirs)])
        return _sort_headers_first(found)

    if not path.is_dir():
        raise FileNotFoundError(f"Source path not found: {target}")

    dirs = _project_search_dirs(path)
    for inc in include_dirs:
        inc_path = Path(inc)
        if inc_path.is_dir():
            dirs.append(inc_path)

    found = _dedupe_paths(_collect_files_in_dirs(dirs))
    return _sort_headers_first(found)


def _project_search_dirs(path: Path) -> list[Path]:
    """Choose search folders for a PlatformIO-style layout (auto-including sibling `include/`)."""
    resolved = path.resolve()
    if resolved.name == "src" and (resolved.parent / "include").is_dir():
        return [resolved.parent / "include", resolved]
    if (resolved / "include").is_dir() or (resolved / "src").is_dir():
        return [d for d in (resolved / "include", resolved / "src") if d.is_dir()]
    return [resolved]


def _collect_files_in_dirs(dirs: Iterable[Path]) -> Iterator[Path]:
    """Yield all C/C++ source and header files inside `dirs`, skipping build/test folders."""
    for directory in dirs:
        for candidate in directory.rglob("*"):
            if (
                candidate.is_file()
                and candidate.suffix.lower() in CPP_EXTS
                # Check only the relative path so testing inside `tests/scenarios/...` still works.
                and IGNORED_DIRS.isdisjoint(candidate.relative_to(directory).parts)
            ):
                yield candidate


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    """Remove duplicate paths while keeping original order."""
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _sort_headers_first(paths: list[Path]) -> list[Path]:
    """Sort `.h`/`.hpp` headers ahead of `.c`/`.cpp`/`.ino` files, then alphabetically."""
    return sorted(paths, key=lambda p: (0 if p.suffix.lower() in HEADER_EXTS else 1, str(p)))


# ---------------------------------------------------------------------------
# Step 2: Walk each file's Tree-Sitter AST to collect definitions & API calls
# ---------------------------------------------------------------------------

def _scan_files(files: list[Path]) -> _SourceScan:
    """Parse every C/C++ file with Tree-Sitter and record all constants and function calls."""
    parser = Parser(CPP_LANGUAGE)
    scan = _SourceScan()
    for file_path in files:
        root = parser.parse(file_path.read_bytes()).root_node
        for name, pin, line in _extract_definitions(root):
            _record_definition(scan, name, pin, file_path, line)
        for fn_name, args, line in _extract_calls(root):
            _record_call(scan, fn_name, args, file_path, line)
    return scan


def _extract_definitions(root: Node) -> list[tuple[str, int, int]]:
    """Find top-level integer constants (`#define NAME 12` and global `const int NAME = 12;`)."""
    defs: list[tuple[str, int, int]] = []
    # Skipping function bodies prevents local loop/counter variables from looking like pins.
    for node in _walk(root, skip_functions=True):
        if node.type == "preproc_def":
            name = _text(node.child_by_field_name("name")).strip()
            pin = _parse_uint(_text(node.child_by_field_name("value")))
            if name and pin is not None:
                defs.append((name, pin, node.start_point.row + 1))
        elif node.type == "declaration":
            defs.extend(_declaration_constants(node))
    return defs


def _declaration_constants(node: Node) -> Iterator[tuple[str, int, int]]:
    """Yield `(name, value, line)` pairs from one integer variable declaration node."""
    type_text = " ".join(_text(node.child_by_field_name("type")).split())
    if type_text not in PIN_VAR_TYPES:
        return
    for child in node.children:
        if child.type != "init_declarator":
            continue
        decl = child.child_by_field_name("declarator")
        val = child.child_by_field_name("value")
        if decl and val and decl.type == "identifier" and val.type == "number_literal":
            pin = _parse_uint(_text(val))
            if pin is not None:
                yield (_text(decl).strip(), pin, child.start_point.row + 1)


def _record_definition(
    scan: _SourceScan,
    name: str,
    pin: int,
    file_path: Path,
    line: int,
) -> None:
    """Save a constant definition while giving conflicting redefinitions guaranteed-unique keys."""
    seen_pins = scan.seen_values.get(name)
    if seen_pins is None:
        scan.seen_values[name] = {pin}
        key = _reserve_unique_key(name, scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))
    elif pin not in seen_pins:
        seen_pins.add(pin)
        key = _reserve_unique_key(f"{name} ({file_path.name})", scan.used_keys)
        scan.definitions.append(_PinDefinition(key, name, pin, file_path, line))


def _extract_calls(root: Node) -> Iterator[tuple[str, list[Node], int]]:
    """Yield `(fn_name, arg_nodes, line)` for every real C/C++ call (ignoring comments/strings)."""
    for node in _walk(root):
        if node.type != "call_expression":
            continue
        fn_node = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if fn_node and args_node:
            fn_name = re.sub(r"\s+", "", _text(fn_node))
            args = [c for c in args_node.named_children if c.type != "comment"]
            yield (fn_name, args, node.start_point.row + 1)


def _record_call(
    scan: _SourceScan,
    fn_name: str,
    args: list[Node],
    file_path: Path,
    line: int,
) -> None:
    """Record a function call and tag its pin arguments with capabilities and bus roles."""
    scan.called_functions.add(fn_name)
    for cap, bus_group, arg in _pin_args_for_call(fn_name, args):
        if arg.type == "identifier":
            ident = _text(arg).strip()
            scan.caps_by_name.setdefault(ident, set()).add(cap)
            scan.caps_by_file_and_name.setdefault((file_path, ident), set()).add(cap)
            if bus_group is not None:
                scan.bus_by_name.setdefault(ident, set()).add(bus_group)
                scan.bus_by_file_and_name.setdefault((file_path, ident), set()).add(bus_group)
        elif arg.type == "number_literal":
            pin = _parse_uint(_text(arg))
            if pin is not None:
                loc = f"{file_path.name}:{line}"
                scan.literal_uses.append(_LiteralPinUse(pin, cap, bus_group, loc))


def _pin_args_for_call(
    fn_name: str,
    args: list[Node],
) -> Iterator[tuple[str, str | None, Node]]:
    """Yield `(capability, bus_group, arg_node)` for positional pin arguments of known APIs."""
    if not args:
        return
    if fn_name in ARG0_CAPABILITIES:
        yield (ARG0_CAPABILITIES[fn_name], None, args[0])
        return

    wire_match = WIRE_CALL_RE.match(fn_name)
    if wire_match and len(args) >= 2:
        # 1-arg Wire.begin(addr) is an I2C slave address, not pin numbers.
        bus = wire_match.group(1)
        yield ("i2c", f"{bus}:sda", args[0])
        yield ("i2c", f"{bus}:scl", args[1])
        return

    spi_match = SPI_CALL_RE.match(fn_name)
    if spi_match:
        # SPI.begin(sck, miso, mosi, ss): clock/data lines share the bus; CS/SS is exclusive GPIO.
        bus = spi_match.group(1)
        for role, arg in zip(("sck", "miso", "mosi"), args[:3]):
            yield ("spi", f"{bus}:{role}", arg)
        if len(args) >= 4:
            yield ("gpio", None, args[3])
        return

    if SERIAL_CALL_RE.match(fn_name) and len(args) >= 3:
        # Serial1.begin(baud, config, rxPin, txPin): skip baud rate & serial config.
        for arg in args[2:4]:
            yield ("uart", None, arg)


# ---------------------------------------------------------------------------
# Step 3 & 4: Build PinRequests and detect active peripheral modules
# ---------------------------------------------------------------------------

def _build_pin_requests(scan: _SourceScan) -> tuple[PinRequest, ...]:
    """Combine collected definitions and direct numeric calls into solver-ready `PinRequest`s."""
    requests: list[PinRequest] = []
    used_keys = set(scan.used_keys)

    for defn in scan.definitions:
        caps, bus_group = _capabilities_and_bus_for(scan, defn)
        if not caps:
            continue  # Skip non-pin constants like BAUD_RATE or DELAY_MS
        requests.append(
            PinRequest(
                name=defn.key,
                pin=defn.pin,
                capabilities=frozenset(caps),
                bus_group=bus_group,
                location=f"{defn.source_file.name}:{defn.line}",
            )
        )

    _merge_or_append_literal_uses(requests, scan.literal_uses, used_keys)
    return tuple(requests)


def _capabilities_and_bus_for(
    scan: _SourceScan,
    defn: _PinDefinition,
) -> tuple[set[str], str | None]:
    """Infer required capabilities and optional shared-bus role for one constant definition."""
    conflicted = len(scan.seen_values.get(defn.raw_name, ())) > 1
    file_key = (defn.source_file, defn.raw_name)

    if conflicted:
        caps = set(
            scan.caps_by_file_and_name.get(file_key) or scan.caps_by_name.get(defn.raw_name, set())
        )
        bus_groups = set(
            scan.bus_by_file_and_name.get(file_key) or scan.bus_by_name.get(defn.raw_name, set())
        )
    else:
        caps = set(scan.caps_by_name.get(defn.raw_name, set()))
        bus_groups = set(scan.bus_by_name.get(defn.raw_name, set()))

    if not caps:
        inferred_cap, inferred_bus = _infer_from_name(defn.raw_name)
        if inferred_cap:
            caps.add(inferred_cap)
        if inferred_bus:
            bus_groups.add(inferred_bus)

    bus_group: str | None = None
    if len(bus_groups) == 1:
        bus_group = next(iter(bus_groups))
    elif len(bus_groups) > 1:
        # Used in conflicting bus roles (e.g. both SDA and SCL) -> cannot share with other signals.
        bus_group = f"mixed:{defn.key}"

    return caps, bus_group


def _infer_from_name(name: str) -> tuple[str | None, str | None]:
    """Fallback heuristic for pin constants not passed directly to an Arduino pin call."""
    words = [w.upper() for w in WORD_RE.findall(name)]
    if not words or words[-1] in NON_PIN_SUFFIXES:
        return None, None

    # Allow both `OLED_SDA` and `OLED_SDA_PIN` by peeking past a trailing PIN/GPIO word.
    role_word = words[-2] if len(words) >= 2 and words[-1] in ("PIN", "GPIO") else words[-1]

    if role_word == "SDA":
        return "i2c", "Wire:sda"
    if role_word == "SCL":
        return "i2c", "Wire:scl"
    if role_word == "MOSI":
        return "spi", "SPI:mosi"
    if role_word == "MISO":
        return "spi", "SPI:miso"
    if role_word in ("SCK", "SCLK"):
        return "spi", "SPI:sck"
    if role_word in ("RX", "TX", "RXD", "TXD"):
        return "uart", None
    if role_word in ("CS", "SS") or "PIN" in words or "GPIO" in words:
        return "gpio", None
    return None, None


def _merge_or_append_literal_uses(
    requests: list[PinRequest],
    literal_uses: list[_LiteralPinUse],
    used_keys: set[str],
) -> None:
    """Attach direct numeric pin calls to matching named pins, or emit new `GPIO_<n>` requests."""
    grouped: dict[tuple[int, str | None], tuple[set[str], str]] = {}
    for use in literal_uses:
        group_key = (use.pin, use.bus_group)
        if group_key not in grouped:
            grouped[group_key] = ({use.capability}, use.location)
        else:
            grouped[group_key][0].add(use.capability)

    ordered_groups = sorted(
        grouped.items(),
        key=lambda item: (item[0][0], item[0][1] or ""),
    )
    for (pin, bus_group), (caps, location) in ordered_groups:
        # If a named constant already owns this exact pin + bus role, merge extra capabilities
        # so e.g. `const int LED = 6; analogRead(6);` checks ADC on GPIO 6 without false duplicates.
        matched_idx = next(
            (i for i, req in enumerate(requests) if req.pin == pin and req.bus_group == bus_group),
            None,
        )
        if matched_idx is not None:
            existing = requests[matched_idx]
            requests[matched_idx] = PinRequest(
                name=existing.name,
                pin=existing.pin,
                capabilities=existing.capabilities | frozenset(caps),
                bus_group=existing.bus_group,
                location=existing.location,
            )
            continue

        base_name = f"GPIO_{pin}"
        if base_name in used_keys and bus_group is not None:
            base_name = f"GPIO_{pin} ({bus_group})"
        key = _reserve_unique_key(base_name, used_keys)
        requests.append(
            PinRequest(
                name=key,
                pin=pin,
                capabilities=frozenset(caps),
                bus_group=bus_group,
                location=location,
            )
        )


def _detect_active_resources(
    called_functions: set[str],
    board: BoardSpec | None,
) -> tuple[str, ...]:
    """Match called C++ functions against the board's `resource_triggers`."""
    if board is None:
        return ()
    return tuple(
        resource
        for resource, patterns in board.resource_triggers.items()
        if any(fn == pat or fn.endswith("." + pat) for pat in patterns for fn in called_functions)
    )


# ---------------------------------------------------------------------------
# Small AST & string utilities
# ---------------------------------------------------------------------------

def _reserve_unique_key(base: str, used_keys: set[str]) -> str:
    """Return `base` if unused, or append ` #2`, ` #3`, ... until globally unique."""
    if base not in used_keys:
        used_keys.add(base)
        return base
    suffix = 2
    while f"{base} #{suffix}" in used_keys:
        suffix += 1
    unique = f"{base} #{suffix}"
    used_keys.add(unique)
    return unique


def _text(node: Node | None) -> str:
    """Decode the source text of a Tree-Sitter AST node safely (tolerating non-UTF-8 comments)."""
    return node.text.decode("utf-8", errors="replace") if node and node.text else ""


def _walk(node: Node, *, skip_functions: bool = False) -> Iterator[Node]:
    """Recursively visit AST nodes, optionally skipping function bodies."""
    if skip_functions and node.type in ("function_definition", "compound_statement"):
        return
    yield node
    for child in node.children:
        yield from _walk(child, skip_functions=skip_functions)


def _parse_uint(raw: str) -> int | None:
    """Strip inline comments, outer parentheses, and integer suffixes; return a non-negative int."""
    cleaned = COMMENT_RE.sub("", raw).strip()
    while cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.rstrip("uUlL")
    return int(cleaned) if cleaned.isdigit() else None
```

### Anhang E: Quelltexte `solver.py`, `cli.py`, `__init__.py`, `pio_hook.py` und `library.json`

#### `mcu_validator/solver.py`

```python
"""Hardware rule checker and Z3 MaxSMT minimal-invasive pin repair solver.

Start reading at `validate()` — it runs 3 clear steps:
  1. `_active_restrictions()` — find pins/capabilities blocked by active modules (Wi-Fi, USB).
  2. `_find_conflicts()`      — check whether the current C++ pin assignments break any rule.
  3. `_solve_reassignment()`  — if conflicts exist, ask Z3 MaxSMT for the smallest valid fix.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from z3 import And, ArithRef, Int, Optimize, Or, sat

from .board import BoardSpec
from .parser import ParsedProject, PinRequest

# Z3 MaxSMT soft-constraint priorities (higher weight strictly dominates lower weights):
KEEP_ORIGINAL_WEIGHT = 1000     # 1st priority: keep already-valid pins unchanged
AVOID_STRAPPING_WEIGHT = 20     # 2nd priority: avoid boot/strapping pins on reassignment
SAVE_SPECIAL_PIN_WEIGHT = 5     # 3rd priority: save scarce ADC/USB pins when plain GPIO suffices

# Hardware capabilities worth preserving for signals that actually require them.
SCARCE_CAPABILITIES = frozenset({"adc", "adc1", "adc2", "usb"})


@dataclass(frozen=True)
class ValidationResult:
    """Final result returned by `validate()`."""

    is_valid: bool
    conflicts: tuple[str, ...]      # Human-readable conflict messages (empty when SAT)
    suggested_pins: dict[str, int]  # Signal name -> verified GPIO number
    repair_possible: bool = True    # False only when no valid assignment fits on this MCU


@dataclass(frozen=True)
class _ActiveRestrictions:
    """Capabilities and physical pins blocked by active modules (e.g. Wi-Fi or USB-Serial)."""

    forbidden_caps: dict[str, str]  # Blocked capability -> reason
    forbidden_pins: dict[int, str]  # Blocked GPIO pin   -> reason


# ---------------------------------------------------------------------------
# Top-level orchestrator (read this first!)
# ---------------------------------------------------------------------------

def validate(project: ParsedProject, board: BoardSpec) -> ValidationResult:
    """Check whether all pin requests fit `board`, and compute a Z3-verified fix if not.

    Raises:
        ValueError: If two `PinRequest` objects in `project.requests` share the same `.name`.
    """
    _ensure_unique_request_names(project.requests)

    restrictions = _active_restrictions(project.active_resources, board)
    conflicts = _find_conflicts(project.requests, board, restrictions)

    if not conflicts:
        kept = {req.name: req.pin for req in project.requests}
        return ValidationResult(is_valid=True, conflicts=(), suggested_pins=kept)

    suggested = _solve_reassignment(project.requests, board, restrictions)
    return ValidationResult(
        is_valid=False,
        conflicts=tuple(conflicts),
        suggested_pins=suggested or {},
        repair_possible=suggested is not None,
    )


# ---------------------------------------------------------------------------
# Step 1: Determine which pins and capabilities are blocked right now
# ---------------------------------------------------------------------------

def _active_restrictions(
    active_resources: tuple[str, ...],
    board: BoardSpec,
) -> _ActiveRestrictions:
    """Evaluate the board's `conflict_rules` against whichever modules are active in code."""
    active = set(active_resources)
    forbidden_caps: dict[str, str] = {}
    forbidden_pins: dict[int, str] = {}

    for rule in board.conflict_rules:
        if rule.when_resource_active not in active:
            continue
        if rule.forbidden_capability:
            forbidden_caps.setdefault(rule.forbidden_capability, rule.reason)
        for pin_num in rule.forbidden_pins:
            forbidden_pins.setdefault(pin_num, rule.reason)

    return _ActiveRestrictions(forbidden_caps=forbidden_caps, forbidden_pins=forbidden_pins)


# ---------------------------------------------------------------------------
# Step 2: Check current pin assignments for hardware conflicts
# ---------------------------------------------------------------------------

def _find_conflicts(
    requests: tuple[PinRequest, ...],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[str]:
    """Validate every requested pin against the board and collect all conflict messages."""
    conflicts: list[str] = []
    seen_on_pin: dict[int, list[PinRequest]] = {}

    for req in requests:
        conflicts.extend(_check_single_pin(req, seen_on_pin.get(req.pin, ()), board, restrictions))
        if req.pin in board.pins:
            seen_on_pin.setdefault(req.pin, []).append(req)

    return conflicts


def _check_single_pin(
    req: PinRequest,
    previous_on_pin: Sequence[PinRequest],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[str]:
    """Run all hardware checks for one `PinRequest`."""
    label = _pin_label(req)
    spec = board.pins.get(req.pin)
    if spec is None:
        return [f"{label}: Pin does not exist on {board.mcu}."]

    errors: list[str] = []
    for prev in previous_on_pin:
        if not _can_share_bus(req, prev, board.shared_capabilities):
            errors.append(f"{label}: Collides with {prev.name} (not a shared bus line).")
            break

    if spec.reserved:
        errors.append(f"{label}: Reserved pin ({spec.note or 'system use'}).")
        return errors

    if req.pin in restrictions.forbidden_pins:
        errors.append(f"{label}: {restrictions.forbidden_pins[req.pin]}")
        return errors

    errors.extend(_check_capabilities(req, spec.capabilities, board, restrictions.forbidden_caps))
    return errors


def _check_capabilities(
    req: PinRequest,
    pin_caps: frozenset[str],
    board: BoardSpec,
    forbidden_caps: dict[str, str],
) -> list[str]:
    """Verify that a pin supports every required capability without hitting blocked banks."""
    label = _pin_label(req)
    errors: list[str] = []
    for cap in sorted(req.capabilities):
        matching = board.expand_capability(cap) & pin_caps
        if not matching:
            errors.append(f"{label}: Does not support capability '{cap}'.")
        elif matching <= forbidden_caps.keys():
            reason = forbidden_caps[min(matching)]
            errors.append(f"{label}: {reason}")
    return errors


# ---------------------------------------------------------------------------
# Step 3: Compute a minimal-invasive reassignment with Z3 MaxSMT (Optimize)
# ---------------------------------------------------------------------------

def _solve_reassignment(
    requests: tuple[PinRequest, ...],
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> dict[str, int] | None:
    """Ask Z3 MaxSMT for a valid pin assignment changing as few pins as possible."""
    opt = Optimize()
    z3_vars: list[ArithRef] = []

    for idx, req in enumerate(requests):
        allowed = _allowed_pins_for(req, board, restrictions)
        if not allowed:
            return None  # Impossible: zero pins on this chip can satisfy this signal
        var = Int(f"pin_{idx}")
        z3_vars.append(var)
        _add_pin_constraints(opt, var, req, allowed, board)

    _add_pairwise_constraints(opt, requests, z3_vars, board)

    if opt.check() != sat:
        return None
    model = opt.model()
    return {req.name: model[var].as_long() for req, var in zip(requests, z3_vars)}


def _allowed_pins_for(
    req: PinRequest,
    board: BoardSpec,
    restrictions: _ActiveRestrictions,
) -> list[int]:
    """List every physical GPIO number on `board` that can legally host `req`."""
    return [
        pin_num
        for pin_num, spec in board.pins.items()
        if not spec.reserved
        and pin_num not in restrictions.forbidden_pins
        and all(
            (board.expand_capability(cap) - restrictions.forbidden_caps.keys()) & spec.capabilities
            for cap in req.capabilities
        )
    ]


def _add_pin_constraints(
    opt: Optimize,
    var: ArithRef,
    req: PinRequest,
    allowed: list[int],
    board: BoardSpec,
) -> None:
    """Add hard domain rules and prioritized soft preferences for one Z3 pin variable."""
    # Hard rule: pin MUST be one of the valid candidate GPIOs.
    opt.add(Or([var == p for p in allowed]))

    # Soft rule 1: Prefer keeping the original pin unchanged if it is valid.
    if req.pin in allowed:
        opt.add_soft(var == req.pin, weight=KEEP_ORIGINAL_WEIGHT)

    # Soft rule 2: Prefer avoiding boot/strapping pins.
    strapping_pins = [p for p in allowed if board.pins[p].strapping]
    if strapping_pins and len(strapping_pins) < len(allowed):
        opt.add_soft(And([var != p for p in strapping_pins]), weight=AVOID_STRAPPING_WEIGHT)

    # Soft rule 3: Save scarce pins (ADC/USB) when this signal doesn't need those capabilities.
    needed_caps = set().union(*(board.expand_capability(cap) for cap in req.capabilities))
    avoid_caps = SCARCE_CAPABILITIES - needed_caps
    scarce_pins = [p for p in allowed if board.pins[p].capabilities & avoid_caps]
    if scarce_pins and len(scarce_pins) < len(allowed):
        opt.add_soft(And([var != p for p in scarce_pins]), weight=SAVE_SPECIAL_PIN_WEIGHT)


def _add_pairwise_constraints(
    opt: Optimize,
    requests: tuple[PinRequest, ...],
    z3_vars: list[ArithRef],
    board: BoardSpec,
) -> None:
    """Enforce pin uniqueness while keeping signals on the same shared bus line coupled together."""
    for i, req_a in enumerate(requests):
        for j in range(i + 1, len(requests)):
            req_b = requests[j]
            if _can_share_bus(req_a, req_b, board.shared_capabilities) and req_a.pin == req_b.pin:
                opt.add(z3_vars[i] == z3_vars[j])
            else:
                opt.add(z3_vars[i] != z3_vars[j])


def _can_share_bus(a: PinRequest, b: PinRequest, shared_caps: frozenset[str]) -> bool:
    """Return True only when both signals share the same single shareable bus capability & line."""
    return (
        a.capabilities == b.capabilities
        and len(a.capabilities) == 1
        and next(iter(a.capabilities)) in shared_caps
        and a.bus_group == b.bus_group
    )


def _pin_label(req: PinRequest) -> str:
    """Format a signal name with its GPIO number and optional file:line location."""
    if req.location:
        return f"{req.name} (GPIO {req.pin}, {req.location})"
    return f"{req.name} (GPIO {req.pin})"


def _ensure_unique_request_names(requests: tuple[PinRequest, ...]) -> None:
    """Guard against duplicate signal names so `suggested_pins` never silently drops a signal."""
    seen: set[str] = set()
    for req in requests:
        if req.name in seen:
            raise ValueError(
                f"Duplicate PinRequest name '{req.name}'; each request must be unique."
            )
        seen.add(req.name)
```

#### `mcu_validator/cli.py`

```python
"""Command-line interface and LLM-Modulo repair report formatter.

Entry point for humans (`mcu-validate` / `python -m mcu_validator.cli`), CI tests,
and PlatformIO (`pio_hook.py`). Ties together `board.py`, `parser.py`, and `solver.py`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .board import BOARDS_DIR, BoardSpec, list_boards, load_board
from .parser import ParsedProject, parse_cpp
from .solver import ValidationResult, validate


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point: parse arguments, validate pins, print the report, and exit.

    Exit codes:
        0 = SAT (all pins valid)
        1 = UNSAT (hardware conflict detected — stops PlatformIO builds)
        2 = Input or configuration error (missing path, unknown board, invalid board JSON)
    """
    args = _parse_args(argv)
    boards_dir = Path(args.boards_dir) if args.boards_dir else BOARDS_DIR

    if args.list_boards:
        boards = list_boards(boards_dir)
        print("Available boards:", ", ".join(boards) if boards else "none")
        sys.exit(0)

    try:
        result, report = validate_path(
            args.path,
            args.board,
            boards_dir=boards_dir,
            include_dirs=args.include_dir,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(report)
    sys.exit(0 if result.is_valid else 1)


def validate_path(
    target: str | Path,
    board_id: str = "esp32-c3",
    *,
    boards_dir: Path = BOARDS_DIR,
    include_dirs: Sequence[str | Path] = (),
) -> tuple[ValidationResult, str]:
    """Run the full 4-stage validation pipeline on a file or project folder."""
    board = load_board(board_id, boards_dir=boards_dir)
    project = parse_cpp(target, board, include_dirs=include_dirs)
    result = validate(project, board)
    return result, format_report(target, board, project, result)


def format_report(
    target: str | Path,
    board: BoardSpec,
    project: ParsedProject,
    result: ValidationResult,
) -> str:
    """Format a validation result as a terminal banner (plus LLM repair prompt on UNSAT)."""
    modules = ", ".join(project.active_resources) if project.active_resources else "none"
    pin_summary = _format_pin_summary(project)
    lines = [
        "=" * 65,
        f" Target         : {target} ({board.mcu})",
        f" Active Modules : {modules}",
        f" Checked Pins   : {pin_summary}",
        "=" * 65,
    ]

    if result.is_valid:
        if not project.requests:
            lines.append(
                " RESULT: SAT (Warning: 0 pin assignments were detected in the scanned files.)"
            )
        else:
            lines.append(" RESULT: SAT (All pins valid! No hardware conflicts detected.)")
        return "\n".join(lines)

    lines.extend([
        " RESULT: UNSAT (Hardware conflicts detected!)\n",
        "--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---\n",
        f"Your C++ code for the {board.mcu} contains the following hardware errors:",
        *(f"  - {conflict}" for conflict in result.conflicts),
        *_format_repair_section(board, project, result),
        "\n-----------------------------------------------------",
    ])
    return "\n".join(lines)


def _format_pin_summary(project: ParsedProject) -> str:
    """Render a compact pin count and preview (e.g. '3 (LED=8, SOIL=1, RELAY=4)')."""
    count = len(project.requests)
    if count == 0:
        return "0"
    preview = ", ".join(f"{req.name}={req.pin}" for req in project.requests[:6])
    if count > 6:
        preview += f", ... (+{count - 6} more)"
    return f"{count} ({preview})"


def _format_repair_section(
    board: BoardSpec,
    project: ParsedProject,
    result: ValidationResult,
) -> list[str]:
    """Build the Z3 repair lines showing which pins to keep and which to change."""
    if not result.repair_possible:
        return [
            f"\nNo valid pin assignment exists on {board.mcu}: "
            "the requested pins exceed available hardware capabilities."
        ]

    lines = ["\nPlease regenerate the code using this exact Z3-verified pin assignment:"]
    for req in project.requests:
        new_pin = result.suggested_pins[req.name]
        if req.pin == new_pin:
            lines.append(f"  - {req.name}: Keep GPIO {req.pin} (unchanged)")
        else:
            lines.append(f"  - {req.name}: Change GPIO {req.pin} -> GPIO {new_pin}")
    return lines


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="mcu-validate",
        description="Validate microcontroller pin assignments in C/C++ with Tree-Sitter + Z3.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="src",
        help="Path to a C/C++ file or project source directory (default: src).",
    )
    parser.add_argument(
        "board",
        nargs="?",
        default="esp32-c3",
        help="Target board name (matching a JSON in boards/) or direct path to a board .json file.",
    )
    parser.add_argument(
        "--boards-dir",
        default=None,
        help="Optional directory containing custom board JSON profiles.",
    )
    parser.add_argument(
        "--include-dir",
        action="append",
        default=[],
        help="Additional header directory to scan alongside the source path (repeatable).",
    )
    parser.add_argument(
        "--list-boards",
        action="store_true",
        help="List all available board profiles and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
```

#### `mcu_validator/__init__.py`

```python
"""Data-driven C++ AST + Z3 SMT hardware pin validator for microcontrollers."""

from .board import BoardSpec, ConflictRule, PinSpec, list_boards, load_board
from .parser import ParsedProject, PinRequest, parse_cpp
from .solver import ValidationResult, validate

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "BoardSpec",
    "ConflictRule",
    "PinSpec",
    "list_boards",
    "load_board",
    "ParsedProject",
    "PinRequest",
    "parse_cpp",
    "ValidationResult",
    "validate",
]
```

#### `pio_hook.py`

```python
"""PlatformIO pre-build hook (SCons script) that runs mcu-pin-solver before compilation.

PlatformIO executes this file automatically when `extra_scripts` points to `pio_hook.py`.
If the validator finds any hardware conflict or configuration error, this script aborts
the build BEFORE the C++ compiler starts.
"""

Import("env")  # Provided by PlatformIO's SCons build environment

import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_PACKAGES = (
    "z3-solver>=4.12.0",
    "tree-sitter>=0.23.0",
    "tree-sitter-cpp>=0.23.0",
)


def _resolve_hook_dir() -> Path:
    """Locate this hook's directory (SCons runs via exec(), so __file__ may be absent)."""
    script_file = globals().get("__file__")
    if script_file:
        return Path(script_file).resolve().parent
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError("Could not determine pio_hook.py directory.")
    return Path(inspect.getfile(frame)).resolve().parent


def _ensure_dependencies(python_cmd: str) -> bool:
    """Ensure Z3 and Tree-Sitter are importable, installing them via pip on first run."""
    check = subprocess.run(
        [python_cmd, "-c", "import z3, tree_sitter, tree_sitter_cpp"],
        capture_output=True,
    )
    if check.returncode == 0:
        return True

    print("\n>>> [MCU-Validator] Installing dependencies (first-time setup)...")
    install = subprocess.run([python_cmd, "-m", "pip", "install", *REQUIRED_PACKAGES])
    if install.returncode != 0:
        pkgs = " ".join(f'"{p}"' for p in REQUIRED_PACKAGES)
        print(
            "\n>>> [MCU-Validator] Automatic pip install failed "
            "(e.g. offline or PEP 668 system Python).\n"
            f">>> Please install manually: {python_cmd} -m pip install {pkgs}\n"
        )
        return False
    return True


# PlatformIO may evaluate extra_scripts more than once per build; only validate once.
if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True

    hook_dir = _resolve_hook_dir()
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))
    include_dir = Path(env.subst("$PROJECT_INCLUDE_DIR"))

    # On Windows, prefer the system `py` launcher instead of modifying PlatformIO's private penv.
    python_cmd = shutil.which("py") or sys.executable
    if not _ensure_dependencies(python_cmd):
        env.Exit(1)

    run_env = os.environ.copy()
    existing_py_path = run_env.get("PYTHONPATH", "")
    run_env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(hook_dir), existing_py_path]))

    cmd = [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id]
    if include_dir.is_dir():
        cmd.extend(["--include-dir", str(include_dir)])

    print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")
    result = subprocess.run(cmd, env=run_env)

    if result.returncode == 1:
        print("\n>>> BUILD STOPPED: Fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)
    elif result.returncode != 0:
        print(
            "\n>>> BUILD STOPPED: MCU-Validator configuration/input error "
            f"(exit code {result.returncode}).\n"
        )
        env.Exit(1)

    print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
```

#### `library.json`

```json
{
  "name": "mcu-pin-solver",
  "version": "0.2.0",
  "description": "Data-driven Neuro-Symbolic Z3 Hardware Pin Validator (LLM-Modulo) for any microcontroller in PlatformIO",
  "keywords": ["microcontroller", "embedded", "z3", "smt", "verification", "llm", "pins", "esp32", "stm32", "rp2040"],
  "repository": {
    "type": "git",
    "url": "https://github.com/DMatheja/mcu-pin-solver.git"
  },
  "authors": [
    {
      "name": "David Matheja",
      "maintainer": true
    }
  ],
  "license": "MIT",
  "frameworks": "*",
  "platforms": "*",
  "export": {
    "include": [
      "mcu_validator/*.py",
      "mcu_validator/boards/*.json",
      "pio_hook.py",
      "library.json",
      "README.md",
      "LICENSE"
    ]
  },
  "build": {
    "extraScript": "pio_hook.py",
    "srcFilter": ["-<*>"]
  }
}
```

### Anhang F: Prompt-Vorlage für neue Mikrocontroller

Vorlage aus `README.md` zur Erstellung weiterer Profile unter `mcu_validator/boards/<chip>.json` (ein fachlicher Abgleich gegen das jeweilige Hersteller-Datenblatt bleibt erforderlich; die Schema-Konformität prüft `BoardSpec.from_dict()` automatisch):

```text
Create a hardware constraint JSON file for the <INSERT MICROCONTROLLER NAME, e.g. Raspberry Pi RP2040> compatible with mcu-pin-solver.

Follow this exact JSON schema and rules:
1. Top-level keys: "mcu", "description", "pins", "capability_aliases", "shared_capabilities", "resource_triggers", "conflict_rules".
2. "pins": Object keyed by pin number as string (only include physically exposed GPIOs/pins). Each pin object must contain:
   - "capabilities": list from ["gpio", "adc", "adc1", "adc2", "pwm", "i2c", "spi", "uart", "usb", "jtag"]
   - "strapping": boolean (true if boot/strapping pin)
   - "reserved": boolean (true if unusable internal flash/PSRAM/system pin; set "capabilities": [])
   - "note": optional short English reason
3. "capability_aliases": map generic names to hardware banks if applicable (e.g. {"adc": ["adc1", "adc2"]}).
4. "shared_capabilities": list of bus capabilities that multiple peripherals may safely share on the same pin (e.g. ["i2c", "spi"]).
5. "resource_triggers": map active peripheral names to C/C++ AST call targets that activate them (e.g. {"wifi": ["WiFi.begin", "WiFi.softAP"], "usb_serial": ["Serial.begin"]}).
6. "conflict_rules": array of rules triggered by keys in "resource_triggers":
   - {"id": "RULE_ID", "when_resource_active": "<module>", "forbidden_capability": "<cap>" OR "forbidden_pins": [..], "reason": "<English explanation>"}

Return only valid JSON with no markdown commentary.
```

### Anhang G: Versuchsskripte zur Evaluation (`v0.2.0`)

#### `experiments.py` (Tree-Sitter-Dump für Abbildung 2.3 sowie Grenzfalltests in Abschnitt 7.4)

```python
"""Verification experiments for v0.2.0 (run from repo root)."""

import sys
import tempfile
from pathlib import Path
from tree_sitter import Parser

sys.path.insert(0, str(Path.cwd()))
from mcu_validator import ParsedProject, PinRequest, load_board, parse_cpp, validate
from mcu_validator.parser import CPP_LANGUAGE

SNIPPET = b"""// WiFi.begin()
#define STATUS_LED 12 // Board-LED
const int SOIL_SENSOR = 5;
void setup() {
    WiFi.begin("MyWiFi");
    analogRead(SOIL_SENSOR);
}
"""


def dump(node, depth=0, field=None):
    txt = (
        node.text.decode("utf-8", errors="replace")
        if node.child_count == 0 or node.type in ("preproc_arg", "comment", "string_literal")
        else ""
    )
    label = f"{field}: " if field else ""
    print("  " * depth + f"{label}{node.type}" + (f"  -> {txt!r}" if txt else ""))
    for i, child in enumerate(node.children):
        dump(child, depth + 1, node.field_name_for_child(i))


dump(Parser(CPP_LANGUAGE).parse(SNIPPET).root_node)

CASES = {
    "a_magic_numbers": '''#include <WiFi.h>
void setup() { Serial.begin(115200); WiFi.begin("x","y"); pinMode(12, OUTPUT); }
void loop() { int raw = analogRead(5); }
''',
    "b_local_counter": '''#define STATUS_LED 3
#define BAUD_RATE 115200
void setup() { pinMode(STATUS_LED, OUTPUT); Serial.begin(BAUD_RATE); }
void loop() { int blinkCount = 0; uint8_t retries = 12; digitalWrite(STATUS_LED, HIGH); }
''',
    "c_tiebreak_swapped": '''#define SERVO_PIN 7
#define BUZZER_PIN 7
void setup() { pinMode(SERVO_PIN, OUTPUT); pinMode(BUZZER_PIN, OUTPUT); }
''',
    "c2_tiebreak_original": '''#define BUZZER_PIN 7
#define SERVO_PIN 7
void setup() { pinMode(BUZZER_PIN, OUTPUT); pinMode(SERVO_PIN, OUTPUT); }
''',
    "d_pigeonhole_6_adc_wifi": '''#include <WiFi.h>
const int S0 = 0; const int S1 = 1; const int S2 = 3; const int S3 = 4; const int S4 = 2; const int S5 = 5;
void setup() { WiFi.begin("x","y"); }
void loop() { analogRead(S0); analogRead(S1); analogRead(S2); analogRead(S3); analogRead(S4); analogRead(S5); }
''',
    "f_specialist_vs_allrounder": '''#include <WiFi.h>
const int A_0 = 0; const int A_3 = 3; const int A_4 = 4;
const int SOIL_SENSOR = 1; const int STATUS_LED = 1;
void setup() { WiFi.begin("x","y"); pinMode(STATUS_LED, OUTPUT); }
void loop() { analogRead(A_0); analogRead(A_3); analogRead(A_4); analogRead(SOIL_SENSOR); }
''',
    "f2_specialist_declared_second": '''#include <WiFi.h>
const int A_0 = 0; const int A_3 = 3; const int A_4 = 4;
const int STATUS_LED = 1; const int SOIL_SENSOR = 1;
void setup() { WiFi.begin("x","y"); pinMode(STATUS_LED, OUTPUT); }
void loop() { analogRead(A_0); analogRead(A_3); analogRead(A_4); analogRead(SOIL_SENSOR); }
''',
    "h_role_shadowing": '''#include <Wire.h>
const int MY_PIN = 6; const int MY_SCL = 7;
void setup() { Wire.begin(MY_PIN, MY_SCL); }
void loop() { analogRead(MY_PIN); }
''',
    "i_constexpr_and_gpio_num_t": '''constexpr int LED_A = 12;
static const uint8_t LED_B = 13;
const gpio_num_t LED_C = GPIO_NUM_14;
void setup() { pinMode(LED_A, OUTPUT); pinMode(LED_B, OUTPUT); }
''',
    "j_ifdef_both_branches": '''#ifdef USE_EXTERNAL_LED
#define STATUS_LED 2
#else
#define STATUS_LED 12
#endif
void setup() { pinMode(STATUS_LED, OUTPUT); }
''',
    "k_wire_vs_wire1_same_pin": '''#include <Wire.h>
const int SDA_A = 6; const int SCL_A = 7; const int SDA_B = 6; const int SCL_B = 7;
void setup() { Wire.begin(SDA_A, SCL_A); Wire1.begin(SDA_B, SCL_B); }
''',
    "l_spi_two_cs_same_pin": '''#include <SPI.h>
const int SCK_P = 6; const int MISO_P = 7; const int MOSI_P = 10; const int CS_A = 7; const int CS_B = 7;
void setup() { SPI.begin(SCK_P, MISO_P, MOSI_P, CS_A); SPI.begin(SCK_P, MISO_P, MOSI_P, CS_B); }
''',
    "m_i2c_sda_equals_scl": '''#include <Wire.h>
#define OLED_SDA 6
#define OLED_SCL 6
void setup() { Wire.begin(OLED_SDA, OLED_SCL); }
''',
}

board = load_board("esp32-c3")
with tempfile.TemporaryDirectory() as tmpdir:
    for name, code in CASES.items():
        path = Path(tmpdir) / f"{name}.cpp"
        path.write_text(code, encoding="utf-8")
        proj = parse_cpp(path, board)
        res = validate(proj, board)
        print(name, "valid=", res.is_valid, "repair=", res.repair_possible, "suggested=", res.suggested_pins)

for reqs in (
    (PinRequest("CAN_TX", 4, frozenset({"can"})), PinRequest("LED", 12, frozenset({"gpio"}))),
    (
        PinRequest("CAN_TX", 4, frozenset({"can"})),
        PinRequest("CAN_RX", 5, frozenset({"can"})),
        PinRequest("LED", 12, frozenset({"gpio"})),
    ),
):
    res = validate(ParsedProject(requests=reqs, active_resources=()), board)
    print("e_empty_domain:", [r.name for r in reqs], "valid=", res.is_valid, "repair=", res.repair_possible, "suggested=", res.suggested_pins)
```

#### `timing.py` (Laufzeitmessung der Regressionsszenarien für Abschnitt 7.5)

```python
"""Runtime measurement for v0.2.0 (run from repo root)."""

import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from mcu_validator import load_board, parse_cpp, validate

N, M = 10, 30
CASES = [
    ("src/main.cpp", "esp32-c3"),
    ("tests/scenarios/00_flash_and_wifi_conflict.cpp", "esp32-c3"),
    ("tests/scenarios/00_flash_and_wifi_conflict.cpp", "esp32-s3"),
    ("tests/scenarios/01_valid_sketch.cpp", "esp32-c3"),
    ("tests/scenarios/02_usb_serial_conflict.cpp", "esp32-c3"),
    ("tests/scenarios/03_duplicate_and_invalid_pin.cpp", "esp32-c3"),
    ("tests/scenarios/04_shared_i2c_bus.cpp", "esp32-c3"),
    ("tests/scenarios/05_ast_ignores_strings_and_comments.cpp", "esp32-c3"),
    ("tests/scenarios/06_multi_file_project/src", "esp32-c3"),
]

ms = lambda xs: statistics.median(xs) * 1000

base = []
for _ in range(N):
    t = time.perf_counter()
    subprocess.run([sys.executable, "-c", "import z3, tree_sitter, tree_sitter_cpp"], capture_output=True)
    base.append(time.perf_counter() - t)
print(f"Baseline: median {ms(base):.0f} ms")

for target, board_id in CASES:
    e2e = []
    rc = None
    for _ in range(N):
        t = time.perf_counter()
        rc = subprocess.run([sys.executable, "-m", "mcu_validator.cli", target, board_id], capture_output=True).returncode
        e2e.append(time.perf_counter() - t)
    tl, tp, ts = [], [], []
    for _ in range(M):
        t0 = time.perf_counter(); board = load_board(board_id)
        t1 = time.perf_counter(); proj = parse_cpp(target, board)
        t2 = time.perf_counter(); validate(proj, board)
        t3 = time.perf_counter()
        tl.append(t1 - t0); tp.append(t2 - t1); ts.append(t3 - t2)
    status = "SAT" if rc == 0 else "UNSAT"
    print(f"{target:55s} {board_id:8s} {status:5s} E2E={ms(e2e):5.0f}ms load={ms(tl):5.2f}ms parse={ms(tp):5.2f}ms solve={ms(ts):5.2f}ms")
```

#### `scaling_benchmark.py` (Skalierungsmessung 3–20 Pins / Dateien für Abschnitt 7.5)

```python
"""Scaling benchmark on ESP32-S3 from 3 up to 20 pins and 20 files."""

from __future__ import annotations

import statistics
import tempfile
import time
from pathlib import Path

from mcu_validator import load_board, parse_cpp, validate

board = load_board("esp32-s3")
valid_pool = [
    1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 21, 38, 39, 40, 41, 42, 47, 48,
]

print("=== SCALING BENCHMARK ON ESP32-S3 (M=15 runs each, UNSAT with 2 conflicts) ===")
for n_pins in (3, 6, 10, 15, 20):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "src"
        inc = root / "include"
        src.mkdir()
        inc.mkdir()

        header_lines = ["#pragma once"]
        for i in range(n_pins):
            if i == 0:
                pin = 26  # reserved SPI flash
            elif i == 1:
                pin = 11  # ADC2 conflict with Wi-Fi
            else:
                pin = valid_pool[i - 2]
            header_lines.append(f"#define SIG_{i} {pin}")
        (inc / "pins.h").write_text("\n".join(header_lines) + "\n", encoding="utf-8")

        (src / "main.cpp").write_text(
            '#include <WiFi.h>\n#include "pins.h"\n'
            'void setup() { WiFi.begin("a", "b"); pinMode(SIG_0, OUTPUT); }\n'
            "void loop() { analogRead(SIG_1); }\n",
            encoding="utf-8",
        )
        for i in range(2, n_pins):
            (src / f"mod_{i:02d}.cpp").write_text(
                f'#include "pins.h"\nvoid init_{i}() {{ pinMode(SIG_{i}, OUTPUT); }}\n',
                encoding="utf-8",
            )

        tp, ts = [], []
        last_res = None
        for _ in range(15):
            t0 = time.perf_counter()
            proj = parse_cpp(src, board)
            t1 = time.perf_counter()
            last_res = validate(proj, board)
            t2 = time.perf_counter()
            tp.append((t1 - t0) * 1000)
            ts.append((t2 - t1) * 1000)

        n_files = 1 + (n_pins - 1)
        p_med = statistics.median(tp)
        s_med = statistics.median(ts)
        print(
            f"n_pins={n_pins:2d} | files={n_files:2d} | valid={last_res.is_valid} "
            f"repair={last_res.repair_possible} | parse={p_med:5.2f}ms | "
            f"solve={s_med:6.2f}ms | inproc_total={p_med + s_med:6.2f}ms"
        )
```

---

## Verzeichnis der verwendeten KI-Hilfsmittel

| Hilfsmittel | Einsatzbereich | Art der Prüfung und Verantwortung |
| :--- | :--- | :--- |
| LLM-Coding-Assistenten (Gemini / Claude) | Unterstützung beim Entwurf von `v0.1.0`, beim Refactoring auf die typisierte Architektur `v0.2.0` (`board.py`, `parser.py`, `solver.py`, `cli.py`, `pio_hook.py`), bei den Board-JSONs sowie beim Aufbau der modularen Testsuite und CI | Eigenständige fachliche Prüfung und Nachvollzug durch den Verfasser; Abgleich der Hardware-Regeln gegen die Espressif-Datenblätter [[9]](#ref-9), [[10]](#ref-10); Absicherung durch 42 automatisierte Tests, `ruff`, `mypy`, GitHub-Actions-CI und realen PlatformIO-Registry-End-to-End-Test |
| LLM-Textassistenten (Gemini / Claude) | Strukturierungshilfe, sprachliche Glättung und Überarbeitung dieser Ausarbeitung auf Stand `v0.2.0` | Eigenständige fachliche Prüfung aller Aussagen durch den Verfasser; empirische Verifikation sämtlicher Code-Auszüge, CLI-Ausgaben, Grenzfallexperimente, Skalierungs- und Laufzeitmessungen am realen Repository; Primärquellen- und DOI-Abgleich |

---

## Ehrenwörtliche Erklärung

Ich erkläre ehrenwörtlich, dass ich die vorliegende Studienarbeit mit dem Thema

> *„Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT“*

selbstständig verfasst und keine anderen als die angegebenen Quellen und Hilfsmittel benutzt habe. Alle wörtlich oder sinngemäß aus Quellen entnommenen Stellen sind als solche kenntlich gemacht. Die verwendeten KI-gestützten Hilfsmittel sind im vorstehenden Verzeichnis vollständig offengelegt. Die Arbeit wurde bisher in gleicher oder ähnlicher Form keiner anderen Prüfungsbehörde vorgelegt und noch nicht veröffentlicht. Ich versichere zudem, dass die eingereichte elektronische Fassung mit gegebenenfalls eingereichten gedruckten Exemplaren übereinstimmt.

Mannheim, den `[TT.MM.JJJJ]`

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
`David Matheja` *(Unterschrift)*
