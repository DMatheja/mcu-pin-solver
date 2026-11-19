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
| Softwarestand | Version `0.2.0` (PlatformIO Registry: `dmatheja/mcu-pin-solver@^0.2.0`; inkl. Arbeitsstand-Erweiterung für nicht-blockierende Strapping-Warnungen) |
| Quellcode (Bestandteil der Abgabe) | https://github.com/DMatheja/mcu-pin-solver |

---

## Kurzfassung

Große Sprachmodelle (*Large Language Models*, LLMs) erzeugen in wenigen Sekunden syntaktisch gültigen und fehlerfrei kompilierbaren Embedded-C++-Code für Mikrocontroller. Bei der Zuweisung physikalischer Anschlüsse (GPIOs) verursachen sie jedoch systematisch Hardware-Konflikte, die für reguläre C++-Compiler unsichtbar bleiben: Sie belegen Leitungen des internen SPI-Flash-Speichers, nutzen Analog-Digital-Wandlerkanäle, die durch ein aktives WLAN-Subsystem (`ADC2`) blockiert oder auf dem Zielsilizium eingeschränkt sind, legen getrennte Signale eines seriellen Busses auf denselben Pin oder verursachen Doppelbelegungen. Im industriellen Embedded-Prototyping ziehen solche erst auf der Zielhardware detektierten Defekte aufwendige Fehlersuche im Labor, manuelle Verdrahtungsänderungen oder kostspielige Leiterplatten-Iterationen nach sich.

Diese Studienarbeit konzipiert, implementiert und evaluiert `mcu-pin-solver` (Release `0.2.0` inklusive der anschließenden Erweiterung um nicht-blockierende Strapping-Warnungen), eine Open-Source-Bibliothek und Kommandozeilenanwendung zur statischen Hardware-Pin-Prüfung *vor* dem Kompiliervorgang. Ein fehlertoleranter GLR-Parser auf Basis von Tree-Sitter (`tree-sitter-cpp`) analysiert ein- und mehrdateiige C/C++-Projekte ohne installierte Cross-Compiler-Toolchain und extrahiert über die benannte Feldsicht auf den konkreten Syntaxbaum (CST) Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Fähigkeiten, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripheriemodule (`wifi`, `usb_serial`). Die Prüfung erfolgt gegen schema-validierte, deklarative JSON-Hardware-Profile, sodass weitere Mikrocontroller ohne Eingriff in den Python-Quelltext ergänzt werden können. Neben harten Konflikten weist der Prüfer im aktuellen Arbeitsstand gezielt nicht-blockierend auf belegte Boot-/Strapping-Pins hin. Bei harten Konflikten löst die Optimierungserweiterung $\nu Z$ des SMT-Solvers Z3 ein *Partial-Weighted-MaxSMT*-Problem mit dreistufiger Gewichtung, das gültige Originalpins bewahrt (`1000`), Strapping-Pins meidet (`20`) und knappe ADC-/USB-Pins schont (`5`). Die Diagnose wird mit Dateizeilen-Verweis als kopierbarer LLM-Modulo-Reparatur-Prompt ausgegeben; ein PlatformIO-Pre-Build-Hook bricht fehlerhafte Builds vor dem Compilerstart ab.

Die Evaluation umfasst 42 automatisierte Tests im Release `v0.2.0` (inklusive neun End-to-End-Regressionsszenarien sowie plattformübergreifender GitHub-Actions-CI unter Windows und Linux mit `ruff` und `mypy`) bzw. 47 Tests im aktuellen Arbeitsstand (+5 Tests für Strapping-Warnungen), zwölf Grenzfallklassen (14 Einzelkonfigurationen bzw. 15 Prüfläufe) im direkten Vergleich zwischen Prototyp `v0.1.0` und Stand `v0.2.0`, Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, einen realen End-to-End-Test über die PlatformIO Registry sowie eine modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung. Typische CLI-Prüfläufe dauern im Median 172 bis 211 ms; fehlerhafte PlatformIO-Builds werden in 1,21 s vor dem Kompilieren gestoppt, während ein konfliktfreies 20-Pin-Projekt in 7,59 ms In-Process (davon 0,06 ms Diagnosezeit) geprüft wird. Verbleibende Systemgrenzen – insbesondere `#ifdef`-Präprozessorzweige, ESP-IDF-Aufzählungstypen (`gpio_num_t`), Drittbibliotheks-Konstruktoren, die `QF_LIA`-MaxSMT-Skalierung bei 20 konfliktbehafteten Pins (1,14 s) sowie das Fehlen einer großskaligen empirischen LLM-Benchmark-Studie – werden kritisch reflektiert.

## Abstract

Large Language Models (LLMs) generate syntactically valid, compilable embedded C++ firmware within seconds, yet they systematically introduce hardware pin conflicts that remain invisible to C++ compilers—such as repurposing internal SPI flash lines, assigning analog sensors to ADC2 channels affected by an active Wi-Fi subsystem or silicon limitations, colliding distinct bus lines, or duplicating GPIOs. In industrial embedded prototyping, uncovering these defects only on physical hardware leads to protracted lab debugging, manual rework, or costly printed circuit board (PCB) respins.

This thesis designs, implements, and evaluates `mcu-pin-solver` (release `0.2.0` plus a subsequent working-tree extension for non-blocking strapping-pin advisories), an open-source pre-build hardware pin validator for PlatformIO and standalone CLI workflows. Using Tree-Sitter's error-tolerant GLR parser (`tree-sitter-cpp`), the tool analyzes single- and multi-file C/C++ projects without requiring a target cross-compiler toolchain, extracting pin constants, direct numeric pin literals, required capability sets, bus-line identities (`Wire:sda`, `SPI:mosi`, etc.), and active peripherals (`wifi`, `usb_serial`) via the named-field projection of the concrete syntax tree (CST). Pin requests are checked against schema-validated, declarative JSON board profiles so additional microcontrollers can be supported without modifying Python code. In addition to blocking hard conflicts, the working-tree refinement surfaces non-blocking advisories whenever valid or repaired assignments rely on boot strapping pins. Whenever hard conflicts occur, Z3's $\nu Z$ engine solves a three-tier Partial Weighted MaxSMT problem that preserves valid original pins (`1000`), avoids strapping pins (`20`), and spares scarce ADC/USB pins (`5`), emitting a copy-paste LLM-Modulo repair prompt with `file:line` references while halting invalid PlatformIO builds before compilation.

The evaluation comprises 42 automated tests in release `v0.2.0` (including nine end-to-end regression scenarios and cross-platform Windows/Linux CI with `ruff` and `mypy`), expanded to 47 tests in the working tree (+5 tests for strapping warnings), twelve edge-case classes (14 distinct configurations / 15 runs) comparing prototype `v0.1.0` against `v0.2.0`, runtime and scaling benchmarks up to 20 pins and 21 files, a live PlatformIO Registry end-to-end build test, and a total-cost-of-ownership and break-even model. Median CLI runs take 172–211 ms, invalid PlatformIO builds abort in 1.21 s prior to compilation, and conflict-free 20-pin projects pass in-process validation in 7.59 ms (0.06 ms validation stage). Remaining limitations—including `#ifdef` preprocessor branches, ESP-IDF `gpio_num_t` enums, third-party constructors, `QF_LIA` MaxSMT runtime reaching 1.14 s at 20 conflicting pins, and the absence of a large-scale empirical benchmark on live LLM-generated firmware—are critically examined.

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
  - [2.3 Quelltextanalyse: von regulären Ausdrücken zum Syntaxbaum](#23-quelltextanalyse-von-regulären-ausdrücken-zum-syntaxbaum)
  - [2.4 Tree-Sitter](#24-tree-sitter)
  - [2.5 SAT, SMT und der Solver Z3](#25-sat-smt-und-der-solver-z3)
  - [2.6 Optimierung mit Partial Weighted MaxSMT](#26-optimierung-mit-partial-weighted-maxsmt)
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
  - [6.3 Syntaxbaum-Parser (`parser.py`)](#63-syntaxbaum-parser-parserpy)
  - [6.4 Regelprüfer, Strapping-Warnungen und MaxSMT-Solver (`solver.py`)](#64-regelprüfer-strapping-warnungen-und-maxsmt-solver-solverpy)
  - [6.5 Prioritätsverhalten bei gegenseitiger Pin-Blockade](#65-prioritätsverhalten-bei-gegenseitiger-pin-blockade)
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
| CDCL($T$) | *Conflict-Driven Clause Learning Modulo Theories* (historisch auch DPLL($T$)) |
| CI | *Continuous Integration*, automatisierte Qualitätssicherung bei jeder Änderung |
| CLI | *Command Line Interface*, Kommandozeilenschnittstelle |
| CS | *Chip Select*, Auswahlleitung eines SPI-Teilnehmers (auch SS, *Slave Select*) |
| CST | *Concrete Syntax Tree*, konkreter Syntaxbaum |
| GLR | *Generalized LR*, verallgemeinerter Bottom-up-Parser für mehrdeutige Grammatiken |
| GPIO | *General-Purpose Input/Output*, frei konfigurierbarer digitaler Ein-/Ausgang |
| HIL | *Hardware-in-the-Loop*, automatisierter Test auf realer Zielhardware |
| I2C | *Inter-Integrated Circuit*, serieller Open-Drain-Zweidrahtbus (SDA, SCL) |
| IO_MUX | *I/O Multiplexer*, fester digitaler Direktpfad und Pad-Konfigurationseinheit in ESP32-SoCs |
| JSON | *JavaScript Object Notation*, textbasiertes Datenformat |
| LEDC | *LED PWM Controller*, Hardware-PWM-Peripherie der ESP32-Familie |
| LLM | *Large Language Model*, großes Sprachmodell |
| MaxSMT | *Maximum Satisfiability Modulo Theories*, Optimierungsvariante von SMT |
| MCP | *Model Context Protocol*, standardisierte Werkzeugschnittstelle für KI-Agenten |
| MCU | *Microcontroller Unit*, Mikrocontroller |
| MILP | *Mixed-Integer Linear Programming*, gemischt-ganzzahlige lineare Optimierung |
| OPI | *Octal Peripheral Interface*, 8-Bit-Octal-SPI-Anbindung für Flash/PSRAM |
| PCB | *Printed Circuit Board*, gedruckte Leiterplatte |
| PSRAM | *Pseudo-Static RAM*, externer bzw. im Package integrierter Arbeitsspeicher |
| PWM | *Pulse-Width Modulation*, Pulsweitenmodulation |
| `QF_IDL` | *Quantifier-Free Integer Difference Logic*, quantorenfreie Ganzzahl-Differenzlogik |
| `QF_LIA` | *Quantifier-Free Linear Integer Arithmetic*, quantorenfreie lineare Ganzzahlarithmetik |
| SAT | *Satisfiability*, Erfüllbarkeit; auch Prüfergebnis „erfüllbar“ |
| SMT | *Satisfiability Modulo Theories*, Erfüllbarkeit modulo Hintergrundtheorien |
| SPI | *Serial Peripheral Interface*, synchroner serieller Bus |
| TCO | *Total Cost of Ownership*, Gesamtkosten über den Lebenszyklus |
| UART | *Universal Asynchronous Receiver Transmitter*, asynchrone serielle Schnittstelle |
| UNSAT | *Unsatisfiable*, Prüfergebnis „nicht erfüllbar“ |
| USB-CDC | *USB Communications Device Class*, serielle Schnittstelle über nativen USB-PHY |
| XIP | *Execute-in-Place*, direkte Befehlsausführung aus externem/integriertem SPI-Flash über Cache |

## Symbolverzeichnis

| Symbol | Bedeutung |
| :--- | :--- |
| $\mathcal{P}$ | Menge aller im Hardware-Profil geführten GPIO-Nummern eines Mikrocontrollers |
| $r_i$ | $i$-te aus dem Quelltext extrahierte Pin-Anforderung (`PinRequest`), $i = 1, \dots, n$ |
| $p_i^0$ | im Quelltext notierte (ursprüngliche) Pin-Nummer von $r_i$ |
| $C_i$ | Menge der von $r_i$ benötigten Fähigkeiten, z. B. $\{\texttt{adc}\}$ oder $\{\texttt{adc}, \texttt{i2c}\}$ |
| $b_i$ | optionale Bus-Leitungsrolle (`bus_group`) von $r_i$, z. B. `Wire:sda`, `SPI:mosi` oder $\bot$ (`None`) |
| $A(c)$ | über `capability_aliases` aufgelöste Menge konkreter Fähigkeiten, z. B. $A(\texttt{adc}) = \{\texttt{adc1}, \texttt{adc2}\}$ |
| $v_i$ | ganzzahlige Entscheidungsvariable in Z3 (`pin_i`): Ziel-GPIO für $r_i$ |
| $P_i$ | Menge der für $r_i$ unter allen harten Regeln zulässigen Pins (Kandidatendomäne) |
| $S$, $S_i$ | Menge aller Strapping-Pins des Chips bzw. der zulässigen Strapping-Pins $S_i = P_i \cap S$ |
| $K_i$ | Menge der Pins in $P_i$ mit knappen Spezialfähigkeiten aus $\text{SCARCE} \setminus \bigcup_{c \in C_i} A(c)$ |
| $\mathbb{I}[\cdot]$ | Indikatorfunktion: $1$, wenn die Bedingung gilt, sonst $0$ |

## Abbildungsverzeichnis

- Abbildung 1.1: Signalpfade und Pin-Multiplexing beim ESP32-C3 (GPIO-Matrix vs. fest verdrahtete Pfade)
- Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver`
- Abbildung 2.2: Konkreter Syntaxbaum (CST) und abstrakter Syntaxbaum (AST) im Vergleich (schematisch)
- Abbildung 2.3: Von Tree-Sitter erzeugter konkreter Syntaxbaum eines Beispielprogramms (mit benannten Feldern)
- Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen in Partial Weighted MaxSMT
- Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess
- Abbildung 6.1: Zweistufiger Ablauf inklusive nicht-blockierender Strapping-Warnungen in `validate()` (`mcu_validator/solver.py`)

## Tabellenverzeichnis

- Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung
- Tabelle 3.1: Einordnung verwandter Ansätze und Forschungslücke
- Tabelle 4.1: Funktionale Anforderungen
- Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023
- Tabelle 4.3: Architektur-Invarianten
- Tabelle 5.1: Nutzwertanalyse Quelltextanalyse
- Tabelle 5.2: Nutzwertanalyse Konfliktlösung
- Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`)
- Tabelle 6.1: Dateien des Repositories (`v0.2.0` und Arbeitsstand-Erweiterung)
- Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`)
- Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen
- Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`)
- Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`)
- Tabelle 7.1: Messumgebung (`v0.2.0`)
- Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien
- Tabelle 7.3: Ergebnisse der zwölf Grenzfallklassen (`v0.1.0` im Vergleich zu `v0.2.0`)
- Tabelle 7.4: Gemessene Laufzeiten der Regressionsszenarien (`v0.2.0`)
- Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`)
- Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung
- Tabelle 7.7: Soll-Ist-Abgleich (`v0.2.0` inkl. Arbeitsstand-Erweiterung)
- Tabelle 8.1: Verbleibende Systemgrenzen

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
- Listing 6.6: Nicht-blockierende Strapping-Warnung auf `src/main.cpp` (Arbeitsstand)
- Listing 6.7: Kern des PlatformIO-Hooks (`pio_hook.py`) und der Paketkonfiguration (`library.json`)
- Listing 7.1: CLI-Ausgabe für Szenario 02 (`v0.2.0`)
- Listing 7.2: CLI-Ausgabe für Szenario 03 (`v0.2.0`)
- Listing 7.3: CLI-Ausgabe für Szenario 04 (`v0.2.0`)
- Listing 7.4: CLI-Ausgabe für Szenario 05 (`v0.2.0`)
- Listing 7.5: CLI-Ausgabe für Szenario 06 (`v0.2.0`)
- Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, inkl. nicht-blockierender Strapping-Warnung)

---

# Hauptteil

## 1 Einleitung

### 1.1 Ausgangssituation

Während Anwendungssoftware auf Desktop- oder Serversystemen über Betriebssystem-Abstraktionen und Gerätetreiber von der physischen Hardware entkoppelt ist, greift Embedded-Firmware auf einem **Mikrocontroller** (*Microcontroller Unit*, MCU) wie dem ESP32-C3 oder ESP32-S3 von Espressif unmittelbar auf elektrische Anschlüsse zu. Diese Anschlüsse werden als **GPIOs** (*General-Purpose Input/Output*) bezeichnet und auf Entwicklungsplatinen wie dem `esp32-c3-devkitm-1` über Stiftleisten nach außen geführt.

Obwohl alle GPIO-Kontakte auf der Platine äußerlich gleichartig erscheinen, sind sie im Silizium an stark unterschiedliche interne Peripherie- und Systembaugruppen angebunden:

- **Digitale Ein- und Ausgänge (`gpio`)** schalten diskrete Logikpegel (0 V / 3,3 V), beispielsweise für LEDs, Relais-Treiberstufen oder Taster.
- **Analog-Digital-Wandler (`adc`)** digitalisieren analoge Sensorspannungen; die ESP32-Familie unterteilt ihre Wandlerkanäle in zwei unabhängige Einheiten, `ADC1` und `ADC2`.
- **Pulsweitenmodulation (`pwm`)** erzeugt über Hardware-Timer (bei Espressif der *LED PWM Controller*, `LEDC`) zeitmodulierte Steuersignale für Aktoren, Servos oder Beleuchtung.
- **Serielle Bus-Controller (`i2c`, `spi`, `uart`)** verbinden Sensoren, Displays oder Funkmodule.
- **System- und Speicherschnittstellen** wie der interne SPI-Flash-Programmspeicher (`SPI0`/`SPI1`) sowie der native USB-Transceiver belegen fest zugeordnete Anschluss-Pads.

Da moderne SoCs weit mehr interne Peripheriesignale besitzen als physische Gehäusepins, verteilen sie digitale Signale über interne Multiplexer auf die äußeren Kontakte (**Pin-Multiplexing**). Dabei existieren jedoch grundlegend verschiedene Signalpfade (Abbildung 1.1): Während digitale Peripheriesignale über die frei schaltbare **GPIO-Matrix** auf nahezu jeden nicht reservierten Pin geroutet werden können, sind der Programmspeicher-Bus (über den **IO_MUX**), die analogen **ADC-Eingänge** sowie der native **USB-PHY** physikalisch fest an bestimmte Pads verdrahtet.

```text
  Interne Baugruppen                 Signalpfad                 Äußere Pins (ESP32-C3)
  ------------------                 ----------                 ----------------------
  Digitale GPIOs, LEDC/PWM,  ──►  GPIO-Matrix (flexibel)  ──┬─► GPIO 0–4   (auch ADC1; 2 Strapping)
  I2C, GP-SPI (SPI2), UART                                  ├─► GPIO 5     (auch ADC2)
                                                            ├─► GPIO 6–10  (Digital; 8, 9 Strapping)
                                                            └─► GPIO 20–21 (Digital; Standard-UART0)
  Analog-Wandler ADC1 / ADC2 ──►  Analog-MUX (fest)       ────► GPIO 0–4 (ADC1), GPIO 5 (ADC2)
  Interner SPI-Flash/VDD_SPI ──►  IO_MUX / Versorgung     ────► GPIO 11–17 (reserviert, nicht nutzbar)
  USB-Serial/JTAG-PHY        ──►  USB-PHY (fest)          ────► GPIO 18, 19 (bei nativem USB belegt)
```
*Abbildung 1.1: Signalpfade und Pin-Multiplexing beim ESP32-C3 (GPIO-Matrix vs. fest verdrahtete Pfade; Angaben nach [[9]](#ref-9)).*

Mit großen Sprachmodellen (LLMs) lässt sich Embedded-Firmware heute aus natürlichsprachlichen Spezifikationen generieren – etwa für eine ESP32-C3-Anwendung mit Status-LED, Bodenfeuchtesensor, Relais, WLAN und serieller Konsole. Empirische Untersuchungen belegen jedoch, dass LLMs zwar in Sekunden syntaktisch plausiblen C++-Code erzeugen, bei hardwarenahen Details aber nicht zuverlässig im ersten Durchlauf fehlerfrei arbeiten [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26). Gerade Fehlbelegungen von Pins sind tückisch, weil sie die gesamte Übersetzungskette unbeanstandet passieren und sich erst nach dem Flashen auf der physischen Schaltung manifestieren.

### 1.2 Problemstellung und wirtschaftliche Relevanz

Listing 1.1 illustriert ein typisches, von einem Sprachmodell generiertes Arduino-C++-Programm. Der Cross-Compiler (`riscv32-esp-elf-g++`) übersetzt diesen Code ohne Warnung oder Fehler; auf einem ESP32-C3 ist er dennoch in zwei Punkten physikalisch fehlerhaft.

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

Dass die C++-Toolchain diese Fehler nicht erkennt, beruht auf drei strukturellen Ursachen:

1. **Untypisierte Ganzzahl-Schnittstellen.** In Arduino-ESP32 sind Pin-Parameter schlicht als vorzeichenlose 8-Bit-Ganzzahlen deklariert (z. B. `void pinMode(uint8_t pin, uint8_t mode)`). Durch implizite Ganzzahlkonvertierungen in C++ akzeptiert der Compiler beliebige Werte wie `12`, `32` oder sogar negative Ganzzahlen ohne Fehler (sofern nicht explizit strenge Warnflags aktiviert sind).
2. **Fehlendes Hardware- und SoC-Modell im Compiler.** Der Compiler prüft C++-Syntax, Typsystem und Ziel-ABI, besitzt jedoch keinerlei Kenntnis darüber, welche GPIO-Nummern auf dem konkreten Chip physisch existieren, welche Pads mit dem internen Flash-Speicher verbunden sind oder welche analogen Wandlerkanäle an welchen Kontakten anliegen.
3. **Übersetzungseinheiten-lokale Prüfung bei projektweiten Wechselwirkungen.** Der Aufruf `analogRead(5)` ist isoliert betrachtet zulässig (solange kein Silizium-Erratum oder Funkkonflikt greift). Unzulässig wird er im gezeigten Sketch erst durch das Zusammenspiel mit `WiFi.begin(...)` – potenziell in einer völlig anderen Übersetzungseinheit (`.cpp`-Datei). Da C++-Compiler jede Übersetzungseinheit isoliert übersetzen und der Linker lediglich Symbole auflöst, bleiben solche modulübergreifenden Hardware-Interaktionen vollständig unsichtbar.

Über das technische Defizit hinaus besitzt diese Verifikationslücke erhebliche **wirtschaftliche Relevanz**. Bereits Boehm zeigte in seiner grundlegenden Untersuchung zur Software-Ökonomie, dass die Fehlerbehebungskosten mit fortschreitender Entwicklungsphase überproportional ansteigen [[4]](#ref-4); Boehm und Basili bestätigten typische Kostenverhältnisse von 5:1 bis über 100:1 zwischen früher und später Fehlerentdeckung auch für kleinere, iterativ arbeitende Teams [[5]](#ref-5). Im industriellen Embedded-Prototyping – etwa in der angewandten Forschung und Entwicklung bei Freudenberg Technology Innovation (FTI) – verschärft die Kopplung an physische Hardware diesen Kostendruck: Wird ein Pin-Konflikt erst nach dem Aufbau eines Prüfstands oder nach Fertigung einer Prototyp-Leiterplatte erkannt, fallen neben mehrstündiger Fehlersuche mit Oszilloskop oder Logikanalysator im ungünstigsten Fall Fertigungskosten und Lieferverzögerungen für einen Platinen-Respin an. Eine automatische *Shift-Left*-Prüfung vor dem Kompiliervorgang setzt unmittelbar an diesem Kostenhebel an (vgl. Abschnitt 7.6).

### 1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen

Die Datenblätter und *Technical Reference Manuals* der ESP32-C3- und ESP32-S3-Familie [[9]](#ref-9), [[10]](#ref-10) unterscheiden drei physische Signalpfade zwischen interner Peripherie und äußeren Anschluss-Pads:

- Die **GPIO-Matrix** bildet ein flexibles digitales Vollkreuzungs-Koppelfeld: Digitale Peripheriesignale (GPIO, LEDC/PWM, I2C, GP-SPI, UART) lassen sich per Software auf nahezu jeden freien Pin legen (mit minimaler zusätzlicher Signallaufzeit von typischerweise zwei APB-Taktzyklen gegenüber Direktpfaden, was erst bei hohen SPI-Takten oberhalb von 40 MHz relevant wird).
- Der **IO_MUX** stellt feste, latenzarme digitale Direktpfade für zeitkritische Schnittstellen (insbesondere `SPI0`/`SPI1`-Flash und -PSRAM, JTAG sowie Standard-`UART0`) bereit und steuert die elektrischen Pad-Eigenschaften (Pull-up/Pull-down, Treiberstärke).
- **Direkte Analog- und PHY-Pfade** koppeln die analogen Wandlereingänge (`ADC1`/`ADC2`) sowie den differenziellen **USB-Serial/JTAG-** (und beim ESP32-S3 zusätzlich den **USB-OTG-**) Transceiver unter vollständiger Umgehung der digitalen GPIO-Matrix direkt an feste Pads, da analoge Messspannungen und USB-Differenzsignale keine digitalen Logikgatter passieren können.

Diese physikalische Asymmetrie erklärt, warum digitale Signale meist frei umgelegt werden können, während analoge Sensoren, Flash-Speicher und nativer USB an feste Pin-Gruppen gebunden bleiben. Für die vorliegende Arbeit werden fünf praxisrelevante Fehlerklassen unterschieden (Tabelle 1.1). Die Taxonomie deckt den Prüfgegenstand des Werkzeugs ab, erhebt jedoch keinen Anspruch auf Vollständigkeit hinsichtlich elektrischer Dimensionierungsfehler.

1. **Reservierte und nicht vorhandene Pins.** Beim ESP32-C3 ist GPIO 11 standardmäßig als Spannungsversorgung `VDD_SPI` für den internen Flash beschaltet (eine Umwidmung erfordert das Brennen der eFuse `VDD_SPI_AS_GPIO`), während GPIO 12–17 (`SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPID`, `SPIQ`) den integrierten SPI-Flash anbinden [[9]](#ref-9). Eine Umkonfiguration dieser Pins unterbricht das *Execute-in-Place*-Nachladen (XIP) des Instruction-Caches und löst unmittelbare Abstürze oder Watchdog-Resets aus. Beim ESP32-S3 belegen Flash und Quad-PSRAM stets GPIO 26–32; bei Modulen mit Octal-SPI-(OPI-)Flash oder Octal-PSRAM (z. B. verbreitete N8R8-/N16R8-Varianten) sind zusätzlich GPIO 33–37 (`SPIIO4`–`SPIIO7`, `SPIDQS`) belegt [[10]](#ref-10). Das Profil `esp32-s3.json` sperrt GPIO 26–37 daher konservativ vollständig, um modulübergreifende Sicherheit zu gewährleisten. Zudem fehlen auf dem ESP32-S3 die Nummern GPIO 22–25 im Registerraum vollständig, und Nummern wie GPIO 32 (vom älteren ESP32 bekannt) existieren auf dem ESP32-C3 gar nicht (**Geister-Pins**).
2. **Konflikte durch aktive Peripherie.** Zwischen dem WLAN-RF-Subsystem und dem Wandler `ADC2` besteht eine Hardware-Ressourcenkonkurrenz: Auf dem ESP32-S3 (GPIO 11–20) arbitriert ein Hardware-Arbiter zwischen Wi-Fi und `ADC2`, sodass Analogmessungen bei aktivem WLAN fehlschlagen können (`ESP_ERR_TIMEOUT`) [[11]](#ref-11). Auf dem ESP32-C3 (GPIO 5, einziger Kanal `ADC2_CH0`) verschärft ein dokumentiertes Silizium-Erratum dieses Verhalten, sodass ESP-IDF v5+ `ADC2` auf dem C3 standardmäßig vollständig sperrt (Ausnahme nur explizit via `CONFIG_ADC_ONESHOT_FORCE_USE_ADC2_ON_C3`) [[11]](#ref-11). `ADC1` (C3: GPIO 0–4; S3: GPIO 1–10) arbeitet hingegen unabhängig vom Funkbetrieb. Analog belegt die native USB-Serial/JTAG-Schnittstelle (bei `ARDUINO_USB_CDC_ON_BOOT=1`) fest die Pins GPIO 18/19 (C3) bzw. GPIO 19/20 (S3).
3. **Fehlende Fähigkeit.** Nicht jedes Pad ist mit jeder Peripherie verbunden. So besitzt GPIO 6 auf dem ESP32-C3 keinen analogen Multiplexer-Pfad zu `ADC1` oder `ADC2`; `analogRead(6)` liefert keine gültige Spannungsmessung. Ebenso verfügt GPIO 0 auf dem ESP32-S3 über keinen ADC-Kanal.
4. **Doppelbelegung – und die erlaubte Bus-Ausnahme.** Zwei unabhängige Signale auf demselben Pin verursachen Treiberkonflikte oder verfälschte Signalpegel. Bei seriellen Bussen ist das Teilen bestimmter Leitungen hingegen physikalisch vorgesehen: I2C arbeitet als Open-Drain-Zweidrahtbus mit Adressierung, weshalb mehrere Sensoren dieselbe `SDA`- und dieselbe `SCL`-Leitung teilen dürfen. Bei SPI teilen sich mehrere Teilnehmer die Leitungen `SCK`, `MISO` und `MOSI`. Umgekehrt dürfen verschiedene Leitungen desselben Busses (`SDA` vs. `SCL`, `SCK` vs. `MOSI`), getrennte Bus-Instanzen (`Wire` vs. `Wire1`) oder zwei SPI-Chip-Select-Leitungen (`CS`/`SS`) *niemals* denselben Pin belegen.
5. **Strapping-Pins (Boot-Konfiguration).** Während des Reset-Vorgangs tastet der Mikrocontroller definierte Strapping-Pins ab, um Boot-Modus, ROM-Ausgabe oder Flash-Versorgungsspannung festzulegen: beim ESP32-C3 sind dies GPIO 2, 8 und 9 (ein externer Pull-down an GPIO 2 oder 8 während des Resets verhindert den regulären SPI- bzw. Download-Boot) [[9]](#ref-9), beim ESP32-S3 GPIO 0 (Boot-Modus), GPIO 3 (JTAG-Quelle), GPIO 45 (`VDD_SPI`-Spannungswahl 3,3 V vs. 1,8 V – ein versehentliches High beim Reset verhindert den Start an 3,3-V-Flash-Chips) und GPIO 46 (Boot-Modus / ROM-Log; darf beim Reset nicht High gezogen werden) [[10]](#ref-10). Anders als die Klassen 1 bis 4 ist Klasse 5 kein harter Laufzeitfehler (Entwicklungsboards nutzen etwa GPIO 8 auf dem ESP32-C3 häufig für eine Onboard-LED), stellt aber ein reales Schaltungsrisiko dar. Das Werkzeug adressiert Klasse 5 daher zweifach: durch **nicht-blockierende Hardware-Warnungen** im Prüfbericht (Arbeitsstand) sowie durch gezielte **Meidung als zweithöchste Optimierungsstufe** im Z3-Solver.

| Fehlerklasse | Beispiel (ESP32-C3) | Folge auf der Hardware |
| :--- | :--- | :--- |
| 1 Reservierte/fehlende Pins | `STATUS_LED = 12`, `PIR_SENSOR = 32` | XIP-Absturz / Watchdog-Reset bzw. wirkungsloser Code |
| 2 Aktive Peripherie | `SOIL_SENSOR = 5` (`ADC2`) mit `WiFi.begin` | Messfehler / `ESP_ERR_TIMEOUT` bzw. blockierter Wandler |
| 3 Fehlende Fähigkeit | `analogRead(6)` | Keine gültigen Analogmesswerte |
| 4 Doppelbelegung | `BUZZER_PIN = 7` und `SERVO_PIN = 7`; `SDA = 6` und `SCL = 6` | Signalkollision / Treiberkonflikt / blockierter Bus |
| 5 Strapping-Pins | Externe Pull-up-/Pull-down-Last an GPIO 2, 8 oder 9 | Fehlstart, falsche `VDD_SPI`-Spannung (S3) oder Boot-Loop |

*Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung.*

### 1.4 Zielsetzung und Forschungsfragen

Ziel dieser Studienarbeit ist die Konzeption, Implementierung und Evaluation eines deterministischen, wartbaren Pre-Build-Werkzeugs (`mcu-pin-solver`), das die fünf Fehlerklassen in PlatformIO- und C/C++-Projekten vor dem Kompilieren erkennt, mit Dateiname und Zeilennummer diagnostiziert, Strapping-Risiken transparent warnt und bei harten Konflikten eine formal geprüfte, minimal-invasive Ersatzbelegung berechnet, die ein Sprachmodell direkt übernehmen kann. Das Hardware-Wissen soll vollständig als schema-validierte Datenschicht vom Prüfcode entkoppelt sein, sodass weitere Mikrocontroller ausschließlich über neue JSON-Profile ergänzt werden können.

Hieraus leiten sich drei Forschungsfragen ab:

- **FF1 – Extraktion:** Wie lassen sich Pin-Definitionen, direkte Pin-Literale, Mengen benötigter Pin-Fähigkeiten, Bus-Leitungsrollen und aktive Peripherie über mehrdateiige C/C++-Projekte hinweg zuverlässig aus dem Quelltext extrahieren, ohne eine Cross-Compiler-Toolchain des Zielchips vorauszusetzen?
- **FF2 – Prüfung und Reparatur:** Wie lässt sich chipspezifisches Hardware-Wissen als schema-validierte Datenschicht vom Prüfcode trennen und in ein Optimierungsproblem überführen, das im Konfliktfall eine Ersatzbelegung berechnet, die möglichst wenige gültige Pins verändert, geteilte Bus-Leitungen zusammenhält, Strapping-Pins meidet und knappe Spezialpins schont?
- **FF3 – Integration und Praxistauglichkeit:** Wie lässt sich die Prüfung als Python- und PlatformIO-Paket so in den Build-Prozess einbinden, dass fehlerhafte Builds vor dem Compilerstart gestoppt werden, ein direkt verwertbarer Reparatur-Prompt entsteht und der Einsatz im industriellen Embedded-Prototyping wirtschaftlich tragfähig bleibt?

**Präzisierung des Verifikationsbegriffs.** Der im Titel verwendete Begriff *Hardware-Verifikation* bezeichnet eine **relative formale Verifikation** des *aus dem Quelltext extrahierten Pin-Modells* gegen ein *deklaratives Modell der Zielhardware*. Hierbei sind zwei Ebenen strikt zu trennen: Das Z3-Backend arbeitet **korrekt und vollständig relativ zum extrahierten Modell** (*Solver-Korrektheit*: jede ausgegebene Belegung erfüllt nachweislich sämtliche harten Profilregeln, und im Überbuchungsfall wird die Unlösbarkeit exakt nachgewiesen). Das Tree-Sitter-Frontend hingegen ist eine **statische Best-Effort-Approximation** von C++, die bei nicht abgedeckten Sprachkonstrukten False Negatives und bei `#ifdef`-Zweigen False Positives aufweisen kann (vgl. Kapitel 7 und 8). Es wird folglich nicht die funktionale Gesamtcorrectness der Firmware bewiesen, sondern die formale Konsistenz der erkannten Pin-Belegung gegenüber dem Hardware-Profil.

### 1.5 Methodisches Vorgehen und Aufbau der Arbeit

Die Umsetzung erfolgte iterativ und testgetrieben in zwei klar abgegrenzten Releases sowie einer anschließenden gezielten Verfeinerung im Arbeitsverzeichnis:

1. **Prototyp (`v0.1.0`):** Aufbau einer minimalen vertikalen Pipeline aus Tree-Sitter-Parser, Z3-MaxSMT-Solver, zwei Chip-Profilen (`esp32-c3`, `esp32-s3`), neun Regressionsszenarien und einem PlatformIO-Hook. Mittels systematischer Grenzfallexperimente (*Fault Injection*) wurden anschließend gezielt Schwachstellen identifiziert.
2. **Produktionsreife Überarbeitung (`v0.2.0`):** Vollständiges architektonisches Refactoring auf Basis der empirischen Befunde – mit dediziertem, schema-validierendem Board-Modul (`board.py`), typisierten Datenklassen, Bus-Leitungsrollen (`bus_group`), dreistufiger MaxSMT-Gewichtung, korrigierter `pip`- und PlatformIO-Paketierung sowie 42 modularen Tests unter GitHub Actions CI (`ruff`, `mypy`, Windows & Linux). Dieser freigegebene Stand bildet die Grundlage sämtlicher Benchmarks und ist im Quellcode-Anhang (Anhänge A–G) vollständig abgedruckt.
3. **Arbeitsstand-Erweiterung (nicht-blockierende Strapping-Warnungen):** Auf Basis der kritischen Reflexion von Fehlerklasse 5 wurden `solver.py` und `cli.py` im Arbeitsverzeichnis um nicht-blockierende Hardware-Warnungen für belegte Strapping-Pins (`ValidationResult.warnings`, `_find_strapping_warnings`) samt fünf zusätzlichen Tests (insgesamt 47 Tests) erweitert. Wo diese Erweiterung über den abgedruckten `v0.2.0`-Stand der Anhänge hinausgeht, wird dies im Hauptteil explizit ausgewiesen.

**Aufbau der Arbeit:** Kapitel 2 führt in die theoretischen Grundlagen ein (LLMs, LLM-Modulo, CST/AST und Tree-Sitter, SAT/SMT/CDCL($T$), Partial Weighted MaxSMT mit $\nu Z$/MaxRes, PlatformIO). Kapitel 3 analysiert verwandte Arbeiten aus neuro-symbolischer KI, LLM-Embedded-Forschung und klassischer Embedded-Praxis und arbeitet die Forschungslücke heraus. Kapitel 4 spezifiziert Akteure, funktionale Anforderungen, nicht-funktionale Anforderungen nach ISO/IEC 25010:2023 sowie Architektur-Invarianten. Kapitel 5 begründet vier zentrale Entwurfsentscheidungen mittels Nutzwert- und Sensitivitätsanalysen und verfolgt ein durchgängiges Beispiel. Kapitel 6 erläutert die Implementierung aller Module top-down. Kapitel 7 evaluiert Testsuite, Grenzfallexperimente, Laufzeit- und Skalierungsverhalten, PlatformIO-Registry-Integration sowie Wirtschaftlichkeit. Kapitel 8 diskutiert Ergebnisse, Systemgrenzen, die KI-gestützte Entstehung und Ausbauperspektiven; Kapitel 9 beantwortet die Forschungsfragen.

---

## 2 Grundlagen

Dieses Kapitel erläutert die drei technologischen Säulen von `mcu-pin-solver`: generative Sprachmodelle und neuro-symbolische KI (2.1–2.2), statische Quelltextanalyse mittels konkreter und abstrakter Syntaxbäume sowie Tree-Sitter (2.3–2.4) sowie logische Verifikation und Optimierung mit Z3 und Partial Weighted MaxSMT (2.5–2.6). Abschnitt 2.7 beschreibt die Build-Orchestrierung in PlatformIO.

### 2.1 Große Sprachmodelle

Ein großes Sprachmodell basiert auf der *Transformer*-Architektur [[24]](#ref-24) und wird autoregressiv auf umfangreichen Text- und Quellcodekorpora trainiert. Bei der Codegenerierung prädiziert das Modell sequenziell die bedingte Wahrscheinlichkeitsverteilung des jeweils nächsten Tokens $t_k$ gegeben dem bisherigen Kontext $t_1, \dots, t_{k-1}$:

$$P(t_k \mid t_1, \dots, t_{k-1}).$$

Das Modell führt hierbei keine symbolische Constraint-Prüfung gegen das Datenblatt des Zielchips durch, sondern sampelt statistisch wahrscheinliche Token-Fortsetzungen. Für die Hardware-Pin-Belegung resultieren daraus drei strukturelle Schwächen:

1. **Trainingsdaten-Verzerrung (*Corpus Skew*):** Öffentliche Codebeispiele im Internet sind stark vom älteren klassischen ESP32 (Xtensa LX6) dominiert, auf dem etwa GPIO 12, 32 oder 33 regelmäßig genutzt werden. Sprachmodelle übertragen diese hochfrequenten Muster regelmäßig auf pin-inkompatible Nachfolger wie den ESP32-C3 (RISC-V), auf dem GPIO 12 zum internen SPI-Flash gehört und GPIO 32 physisch nicht existiert.
2. **Fehlende globale Konsistenzprüfung:** Da die Generierung streng sequenziell von links nach rechts erfolgt, verifiziert das Modell beim Ausgeben von `WiFi.begin(...)` in einer späteren Funktion oder Datei nicht mit formaler Garantie, ob eine zuvor gewählte Pin-Konstante (`SOIL_SENSOR = 5`) dadurch einen `ADC2`-Konflikt auslöst.
3. **Grenzen intrinsischer Selbstkorrektur:** Huang et al. zeigen empirisch, dass LLMs logische und kombinatorische Fehler ohne zuverlässiges externes Feedback nicht konsistent korrigieren können – wiederholte Selbstprüfungs-Prompts verschlechtern korrekte Ausgangslösungen teilweise sogar [[15]](#ref-15).

### 2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip

Garcez und Lamb gliedern die Entwicklung der Künstlichen Intelligenz in drei Paradigmenwellen [[13]](#ref-13): Die erste, **symbolische** Welle beruht auf expliziter Logik und formalen Regeln, die überprüfbare Korrektheit bieten, aber auf offene, unstrukturierte Aufgaben schwer skalieren. Die zweite, **neuronale** Welle – repräsentiert durch tiefe Netze und LLMs – generiert flexibel aus natürlicher Sprache, liefert jedoch keine Korrektheitsgarantien. Die dritte Welle, die **neuro-symbolische KI**, koppelt beide Ansätze komplementär.

Kambhampati et al. präzisieren dieses Zusammenspiel im **LLM-Modulo-Framework** [[17]](#ref-17): Das Sprachmodell fungiert als kreativer *Generator* von Lösungskandidaten, während deterministische externe Prüfer (*Critics*) diese gegen formale Spezifikationen validieren und präzises, umsetzbares Korrekturfeedback zurückspeisen. Dabei trennt das Framework zwischen **harten Prüfern** (unverhandelbare Korrektheitsbedingungen) und **weichen Prüfern** (Qualitäts- und Präferenzkriterien).

Übertragen auf die Embedded-Entwicklung übernimmt das Sprachmodell den raschen Entwurf der Anwendungslogik, während `mcu-pin-solver` als deterministischer Hardware-Prüfer und MaxSMT-Reparaturorakel agiert (Abbildung 2.1). Zur begrifflichen Schärfe ist festzuhalten: `mcu-pin-solver` selbst enthält kein neuronales Netz, sondern realisiert ausschließlich die **symbolische Prüf- und Optimierungskomponente**; „neuro-symbolisch“ ist das *Gesamtsystem* aus generierendem Sprachmodell und formalem Verifikator.

```text
  ┌────────────────────────────────────────────────────────────┐
  │ 1. Generieren (LLM): Nutzerwunsch → Embedded-C++-Code      │
  └──────────────────────────────┬─────────────────────────────┘
                                 ▼
  ┌────────────────────────────────────────────────────────────┐
  │ 2. Extrahieren (Tree-Sitter): Pins, Fähigkeiten, Bus-Rollen│
  └──────────────────────────────┬─────────────────────────────┘
                                 ▼
  ┌────────────────────────────────────────────────────────────┐
  │ 3. Prüfen & Reparieren (Regeln + Z3 gegen JSON-Profil)     │
  └───────────────┬──────────────────────────────┬─────────────┘
          UNSAT   ▼                              ▼   SAT (+ ggf. Strapping-Warnung)
  ┌───────────────────────────────┐  ┌────────────────────────┐
  │ 4. Build stoppen, Reparatur-  │  │ Cross-Compiler startet │
  │    Prompt mit Z3-Lösung       │  └────────────────────────┘
  └───────────────┬───────────────┘
                  └──────► zurück zu 1 (LLM übernimmt geprüfte Pins)
```
*Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver` (nach dem Prinzip aus [[17]](#ref-17)).*

### 2.3 Quelltextanalyse: von regulären Ausdrücken zum Syntaxbaum

Zur zuverlässigen Extraktion von Pin-Zuweisungen und API-Aufrufen aus C++-Quelltext reichen **reguläre Ausdrücke** (*Regex*) prinzipiell nicht aus. Klassische reguläre Ausdrücke beschreiben in der Chomsky-Hierarchie lediglich Typ-3-Sprachen (reguläre Sprachen), die durch endliche Automaten erkannt werden [[14]](#ref-14). Aufgrund des Pumping-Lemmas können sie weder beliebig tief geschachtelte Block- und Klammerstrukturen noch lexikalische Kontexte zuverlässig verfolgen. Zwar gehen moderne Regex-Engines wie Python `re` durch Rückwärtsreferenzen über strikte Typ-3-Sprachen hinaus, bleiben für Programmiersprachen aber fehleranfällig und unwartbar. C++ liegt in seiner syntaktischen Komplexität sogar oberhalb rein kontextfreier Grammatiken (Typ 2), da Konstrukte wie der *Most Vexing Parse*, verschachtelte Template-Winkelklammern oder mehrdeutige Ausdrücke wie `A * b;` (Multiplikation vs. Zeigerdeklaration) kontextsensitive Disambiguierung erfordern.

Eine textbasierte Regex-Suche scheitert daher bereits an elementaren Alltagsfällen:

1. **Kommentare:** `// WiFi.begin("Test");` oder `/* pinMode(12, OUTPUT); */` lösen fälschlich Treffer aus.
2. **Zeichenkettenliterale:** `Serial.println("Bitte WiFi.begin() prüfen");` wird nicht von ausführbarem Code unterschieden.
3. **Gültigkeitsbereiche (Scopes):** Lokale Zählvariablen wie `int retries = 12;` in `loop()` ähneln textuell globalen Pin-Deklarationen.
4. **Syntaktische Formatierung:** Beliebige Leerzeichen oder Zeilenumbrüche wie `WiFi . begin(\n  "SSID"\n)` zerreißen einfache Zeilenmuster.

Ein **Parser** orientiert sich stattdessen am Frontend eines Compilers [[1]](#ref-1): Die *lexikalische Analyse* zerlegt den Zeichenstrom in klassifizierte Tokens (`const`, `int`, `LED`, `=`, `12`, `;`), aus denen die *syntaktische Analyse* eine hierarchische Baumstruktur aufbaut. Man unterscheidet den **konkreten Syntaxbaum** (*Concrete Syntax Tree*, CST), der jedes syntaktische Zeichen inklusive Interpunktion und Kommentaren verlustfrei abbildet, vom **abstrakten Syntaxbaum** (*Abstract Syntax Tree*, AST), der auf die semantisch tragende Programmstruktur reduziert ist (Abbildung 2.2). Da Kommentare (`comment`) und Zeichenketten (`string_literal`) im Syntaxbaum eigenständige Knotentypen bilden, sind sie bei einer gezielten Suche nach `call_expression`-Knoten strukturell ausgeschlossen.

```text
Quelltext:  const int LED = 12;

Konkreter Syntaxbaum (CST)                Abstrakter Syntaxbaum (AST)
declaration                               VarDecl
 ├── type_qualifier: "const"               ├── Qualifiers: [const]
 ├── type: primitive_type ("int")          ├── Type:       int
 ├── declarator: init_declarator           ├── Name:       LED
 │    ├── declarator: identifier ("LED")   └── InitValue:  12
 │    ├── "="
 │    └── value: number_literal ("12")
 └── ";"
```
*Abbildung 2.2: Konkreter Syntaxbaum (CST) und abstrakter Syntaxbaum (AST) im Vergleich (schematisch).*

### 2.4 Tree-Sitter

**Tree-Sitter** ist ein in C implementiertes, inkrementelles Parser-Generator-Framework mit produktiven Sprachgrammatiken, darunter `tree-sitter-cpp` [[6]](#ref-6). Intern erzeugt Tree-Sitter einen **GLR-Parser** (*Generalized LR*, nach dem Tomita-Verfahren): Stößt die Analyse auf grammatikalische Mehrdeutigkeiten in C++ – etwa ohne Symboltabelle nicht unmittelbar entscheidbare Deklarations- vs. Ausdruckskonstrukte –, verfolgt der Parser mehrere Ableitungspfade parallel und löst sie anhand nachfolgender Tokens oder Grammatik-Präzedenzen auf.

Für `mcu-pin-solver` sind drei Eigenschaften von Tree-Sitter ausschlaggebend (während die für Editoren gedachte inkrementelle Differenz-Aktualisierung im Batch-Betrieb pro Build nicht benötigt wird):

1. **GLR-Fehlertoleranz ohne Ziel-Header:** Tree-Sitter erzeugt selbst bei unvollständigen Codefragmenten oder fehlenden System-Headern (`Arduino.h`, ESP-IDF) einen vollständigen, traversierbaren Baum und isoliert syntaktische Defekte lokal in `ERROR`-Knoten.
2. **Betrieb ohne Cross-Compiler-Toolchain:** Die Python-Anbindung (`tree-sitter >= 0.23.0` und `tree-sitter-cpp >= 0.23.0` über die PyCapsule-`Language`-API) ist vollständig eigenständig und benötigt weder `gcc`/`clang` noch plattformspezifische Include-Pfade.
3. **CST mit benannter AST-Projektion und exakten Positionen:** Obwohl Tree-Sitter intern einen verlustfreien CST mit allen anonymen Interpunktions-Tokens (`;`, `(`, `,`) aufbaut, stellt es über **benannte Knoten** (`is_named`, `named_children`) und **benannte Grammatikfelder** (`child_by_field_name("name")`, `"value"`, `"function"`, `"arguments"`) eine kompakte AST-ähnliche Sicht bereit. Jeder Knoten trägt 0-basierte Zeilen- und Spaltenkoordinaten (`start_point.row`), aus denen sich präzise 1-basierte Dateiverweise ableiten lassen.

Zwei technische Besonderheiten von `tree-sitter-cpp` sind für die Implementierung wesentlich: Zum einen werden Kommentare in der Grammatik als benannte `extras`-Knoten (`comment`) geführt und können daher innerhalb von `named_children` – etwa in einer `argument_list` wie `Wire.begin(/* sda */ 6, 7)` – auftreten; der Parser muss sie vor einer Positionsauswertung explizit herausfiltern. Zum anderen führt Tree-Sitter **weder einen C-Präprozessor noch eine C++-Typauflösung** aus: Makros werden nicht expandiert, sämtliche Zweige einer `#ifdef`-Verzweigung erscheinen gleichzeitig im Baum, und der Rumpf einer `#define`-Direktive (`preproc_arg`) umfasst unzerlegt den gesamten Zeilenrest einschließlich eines nachfolgenden Kommentars (Abbildung 2.3).

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
*Abbildung 2.3: Von Tree-Sitter erzeugter konkreter Syntaxbaum eines Beispielprogramms mit benannten Feldern (gekürzte Ausgabe des Versuchsskripts, siehe Anhang G).*

### 2.5 SAT, SMT und der Solver Z3

Für die formale Konfliktlösung setzt `mcu-pin-solver` den SMT-Solver **Z3** von Microsoft Research ein [[7]](#ref-7). Die zugrunde liegende Entscheidungsarchitektur baut auf drei aufeinander aufbauenden Konzepten auf [[2]](#ref-2):

- **SAT und CDCL:** Das aussagenlogische Erfüllbarkeitsproblem (*Boolean Satisfiability*, SAT) fragt nach einer Wahrheitsbelegung boolescher Variablen, die eine Formel in konjunktiver Normalform erfüllt (`SAT`) oder ihre Unerfüllbarkeit beweist (`UNSAT`). Moderne SAT-Solver verwenden *Conflict-Driven Clause Learning* (CDCL): Durch Einheitspropagation (*Unit Propagation*), Implikationsgraphen-Analyse bei Konflikten, Lernen neuer Konfliktklauseln (typischerweise nach dem 1-UIP-Schema) und nicht-chronologisches Backjumping schneiden sie große konfliktbehaftete Teilbäume frühzeitig ab.
- **SMT und `CDCL(T)`:** *Satisfiability Modulo Theories* (SMT) erweitert SAT um entscheidbare Hintergrundtheorien erster Stufe – etwa lineare Ganzzahlarithmetik, Bitvektoren oder Arrays. Die dominierende Architektur **`CDCL(T)`** (historisch auch als **`DPLL(T)`** bezeichnet [[2]](#ref-2)) koppelt einen CDCL-SAT-Kern lose (*lazy SMT*) mit spezialisierten Theorie-Solvern: Der SAT-Kern abstrahiert Theorieatome als boolesche Literale, während der Theorie-Solver Konsistenz prüft, Theorie-Implikationen propagiert und im Konfliktfall neue Theorie-Lemmata in den SAT-Kern einspeist.
- **Theorie-Einordnung der Pin-Belegung:** In `mcu-pin-solver` wird jede Pin-Anforderung als ganzzahlige Entscheidungsvariable $v_i \in \mathbb{Z}$ (`z3.Int`) kodiert. Sämtliche erzeugten Bedingungen fallen damit in die entscheidbare (NP-vollständige) Theorie der **quantorenfreien linearen Ganzzahlarithmetik (`QF_LIA`)** [[2]](#ref-2). Strukturell noch enger betrachtet treten keinerlei Additionen oder Multiplikationen auf, sondern ausschließlich Gleichheiten und Ungleichheiten gegen Konstanten oder Variablen ($v_i = p$, $v_i \neq p$, $v_i = v_j$, $v_i \neq v_j$) über endlichen Domänen $P_i \subset \mathbb{Z}$. Das Problem liegt somit im **endlichen Gleichheitsfragment** (einer Teilmenge von `QF_IDL` bzw. `QF_LIA`) und ist mathematisch äquivalent zu einem gewichteten *List-Coloring*-Problem auf einem Konfliktgraphen. Gerade diese Einordnung ist für das Skalierungsverhalten von `z3.Optimize` von zentraler Bedeutung (vgl. Abschnitt 7.5 und 8.4).

### 2.6 Optimierung mit Partial Weighted MaxSMT

Ein gewöhnlicher SMT-Solver liefert eine *beliebige* erfüllende Belegung und könnte dabei auch bereits gültige, auf einer realen Schaltung verdrahtete Pins unnötig verschieben. Gesucht ist stattdessen eine **minimal-invasive** Reparatur, die zusätzlich Boot-Strapping-Pins meidet und knappe Analog-/USB-Pins schont.

Diese Aufgabenstellung entspricht einem **Partial-Weighted-MaxSMT-Problem**: Eine Menge **harter Bedingungen** $\mathcal{H}$ (Gewicht $\infty$) muss ausnahmslos erfüllt sein, während eine Menge **weicher Bedingungen** $\{(\psi_k, w_k)\}$ mit positiven Gewichten $w_k \in \mathbb{N}^+$ möglichst hochgewichtet erfüllt werden soll. Z3 unterstützt diese Problemklasse über seine Optimierungserweiterung **$\nu Z$** (`z3.Optimize`) [[3]](#ref-3). Mathematisch äquivalent zur Maximierung der Summe aller erfüllten Wunschgewichte minimiert $\nu Z$ intern die Strafsumme der verletzten weichen Bedingungen:

$$\max \sum_{k} w_k \cdot \mathbb{I}[\psi_k] \;\Longleftrightarrow\; \min \sum_{k} w_k \cdot \mathbb{I}[\neg\psi_k].$$

Abbildung 2.4 fasst die harten und dreistufig gewichteten weichen Bedingungen in `mcu-pin-solver` zusammen.

```text
  HARTE BEDINGUNGEN (müssen ausnahmslos gelten, Gewicht ∞)
  • Jeder Pin existiert, ist nicht reserviert und unterstützt alle benötigten Fähigkeiten
  • Keine Sperre durch aktive Peripherie (z. B. ADC2 bei WLAN, USB-Pins bei nativem Serial)
  • Paarweise verschiedene Pins – außer Signale derselben geteilten Bus-Leitung
    (z. B. Wire:sda) mit gleichem Originalpin, die gekoppelt bleiben (v_i = v_j)
                              │
                              ▼  unter allen zulässigen Lösungen (Partial Weighted MaxSMT):
  WEICHE BEDINGUNGEN (dreistufige Gewichtung)
  • +1000 Punkte (Stufe 1): Signal behält seinen gültigen Originalpin
  •   +20 Punkte (Stufe 2): Signal meidet Boot-/Strapping-Pins
  •    +5 Punkte (Stufe 3): Signal schont knappe Spezialpins (ADC/USB), sofern nicht benötigt
```
*Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen in Partial Weighted MaxSMT.*

Intern löst $\nu Z$ gewichtete MaxSMT-Instanzen standardmäßig mit dem kernbasierten Verfahren **MaxRes** [[3]](#ref-3), [[18]](#ref-18): Der Solver prüft zunächst unter der Annahme, dass alle aktiven weichen Bedingungen gleichzeitig gelten. Ist dies unerfüllbar, extrahiert der zugrunde liegende SMT-Kern einen **unerfüllbaren Kern** (*Unsatisfiable Core*) $C = \{\psi_{j_1}, \dots, \psi_{j_m}\}$ sich gegenseitig ausschließender weicher Bedingungen. Anschließend bestimmt MaxRes das kleinste Gewicht $w_{\min} = \min_{\psi \in C} w(\psi)$ innerhalb des Kerns, spaltet schwerere Bedingungen des Kerns in Anteile der Gewichte $w_{\min}$ und $w(\psi) - w_{\min}$ auf (*Weight Splitting*), erhöht die bewiesene untere Strafschranke um $w_{\min}$ und ersetzt die $m$ Kernklauseln durch $m - 1$ gewichtete MaxSAT-Resolutionsklauseln (*Compensation Clauses*), die exakt einen Verstoß im Kern ohne Verfälschung der Zielfunktion erlauben [[18]](#ref-18). Sobald die verbleibende Formel erfüllbar wird, ist das gefundene Modell **nachweislich global optimal**. Da Partial Weighted MaxSMT (wie bereits gewichtetes List-Coloring) im allgemeinen Fall **NP-schwer** ist, wird das praktische Laufzeit- und Skalierungsverhalten bis 20 Signale in Abschnitt 7.5 empirisch untersucht.

### 2.7 PlatformIO und der Build-Prozess

**PlatformIO** ist ein plattformübergreifendes Build- und Abhängigkeitsökosystem für Embedded-Projekte auf Basis des Python-Build-Werkzeugs **SCons** [[20]](#ref-20). Ein Projekt deklariert Zielboard (`board`), Framework, Bibliotheksabhängigkeiten (`lib_deps`) und Erweiterungsskripte (`extra_scripts`) in `platformio.ini`. Eine über die PlatformIO Registry eingebundene Bibliothek kann in ihrem Manifest `library.json` ein Feld `build.extraScript` definieren, das SCons automatisch lädt und **vor** dem Aufruf der Cross-Compiler-Toolchain ausführt (wobei `build.srcFilter` steuert, welche C/C++-Dateien der Bibliothek selbst kompiliert werden). Da SCons solche Skripte mittels `exec()` in einer vorbereiteten Umgebung (`Import("env")`) ausführt, kann das Skript Projektoptionen wie `board`, `$PROJECT_SRC_DIR` und `$PROJECT_INCLUDE_DIR` direkt auslesen und den Build im Fehlerfall über `env.Exit(1)` unmittelbar vor der Kompilierung abbrechen.

> **Zwischenfazit Kapitel 2:** Tree-Sitter liefert über seinen fehlertoleranten GLR-Parser eine präzise syntaktische Sicht auf C++-Projekte ohne Ziel-Compiler; Z3 ($\nu Z$) ermöglicht formale Korrektheitsprüfung und nachweislich optimale Reparaturen via Partial Weighted MaxSMT; PlatformIO bietet über SCons-Pre-Build-Hooks den frühestmöglichen Eingriffspunkt vor dem Kompiliervorgang.

---

## 3 Verwandte Arbeiten und Stand der Technik

Dieses Kapitel ordnet `mcu-pin-solver` in drei Forschungs- und Anwendungsfelder ein: (1) neuro-symbolische Kopplung von LLMs mit formalen Solvern, (2) LLM-gestützte Embedded-, IoT- und Automatisierungsentwicklung sowie (3) etablierte Werkzeuge der Embedded-Praxis. Ziel ist die präzise Herausarbeitung von Stärken, Grenzen und der bestehenden Forschungslücke.

### 3.1 Neuro-symbolische Kopplung von LLMs mit formalen Solvern

Die Erkenntnis, dass LLMs bei kombinatorischen Randbedingungen systematisch Fehler erzeugen und ohne externes Korrektiv nicht verlässlich zur Selbstkorrektur fähig sind [[15]](#ref-15), hat eine Reihe einflussreicher neuro-symbolischer Architekturen hervorgebracht [[13]](#ref-13):

- **Logic-LM** (Pan et al., Findings of EMNLP 2023) [[19]](#ref-19) übersetzt natürlichsprachliche Logikaufgaben mittels eines LLMs in formale Repräsentationen (u. a. Prädikatenlogik erster Stufe und Constraint-Programme), delegiert die Inferenz an deterministische Solver und nutzt deren Fehlermeldungen in einer iterativen *Self-Refinement*-Schleife zur Syntax- und Formulierungskorrektur.
- **SatLM** (Ye et al., NeurIPS 2023) [[27]](#ref-27) überträgt diesen Ansatz explizit auf **SAT/SMT-Solver**: Anstatt das LLM imperative Lösungsalgorithmen generieren zu lassen, formuliert es eine deklarative Constraint-Spezifikation, während der Theorembeweiser die kombinatorische Suche übernimmt. Dadurch sinken Planungs- und Suchfehler gegenüber reinem *Chain-of-Thought*-Prompting drastisch.
- **LLM-Modulo** (Kambhampati et al., ICML 2024) [[17]](#ref-17) abstrahiert dieses Prinzip zu einer allgemeinen Generator-Critic-Architektur, in der spezialisierte externe Verifikatoren harte Korrektheits- und weiche Präferenzkriterien unabhängig vom Sprachmodell prüfen.

**Kritische Abgrenzung (Autoformalisierungs-Engpass).** Sowohl *Logic-LM* [[19]](#ref-19) als auch *SatLM* [[27]](#ref-27) leiden für die Embedded-Praxis an einem fundamentalen **Autoformalisierungs-Engpass**: Das LLM muss die formale Logikspezifikation selbst erzeugen. Vergisst oder verfälscht das Sprachmodell dabei eine Hardware-Restriktion (etwa die `ADC2`/WLAN-Sperre), beweist selbst ein korrekter SMT-Solver eine falsche Aussage über ein unvollständiges Modell. `mcu-pin-solver` kehrt diese Rollenverteilung gezielt um: Das LLM verbleibt in seiner Domänenstärke – der Generierung idiomatischen Arduino-C++-Codes –, während ein **deterministischer Tree-Sitter-Parser** gemeinsam mit einem **datenblattgeprüften, schema-validierten JSON-Profil** die vollständige Z3-Instanz konstruiert. Autoformalisierungs-Halluzinationen beim Aufstellen der Hardware-Constraints sind damit strukturell ausgeschlossen.

### 3.2 Sprachmodelle in der Embedded-, IoT- und Automatisierungsentwicklung

Parallel entstanden zwischen 2024 und 2025 wegweisende Arbeiten zur LLM-gestützten Firmware- und Steuerungsentwicklung:

- **Empirische HIL-Studie (Englhardt et al., CHI EA 2024)** [[8]](#ref-8): Die Autoren evaluierten GPT-3.5, GPT-4 und PaLM 2 anhand realer Mikrocontroller-Aufgaben mit Sensoren und Aktoren. Zwar erzeugte insbesondere GPT-4 häufig funktional sinnvolle Ansätze und hilfreiche Debugging-Hinweise, scheiterte jedoch wiederholt an hardwarenahen Konfigurations- und Pin-Details und erforderte menschliche Rückkopplung. *Hardware-in-the-Loop*-Tests (HIL) decken solche Defekte zwar zuverlässig auf, setzen aber physisch aufgebaute Prüfstände voraus und greifen im Entwicklungsprozess zu spät.
- **LLM4PLC (Fakih et al., ICSE-SEIP 2024)** [[12]](#ref-12): Für speicherprogrammierbare Steuerungen (SPS, IEC 61131-3 *Structured Text*) koppeln die Autoren ein LLM iterativ mit Syntaxprüfer, Compiler und dem formalen Modellprüfer NuSMV, dessen Gegenbeispiele an das Sprachmodell zurückgespeist werden. Konzeptionell ist LLM4PLC der engste Verwandte zu `mcu-pin-solver`. Ein entscheidender Unterschied liegt jedoch in der Arbeitsteilung bei der Reparatur: Während NuSMV lediglich Gegenbeispiele meldet und die eigentliche Korrektursynthese dem LLM überlässt, berechnet `mcu-pin-solver` die **nachweislich optimale, minimal-invasive Ersatzbelegung selbst per MaxSMT**, sodass das LLM keine kombinatorische Suche mehr leisten, sondern lediglich konkrete GPIO-Nummern substituieren muss.
- **EmbedGenius (Yang et al., 2024)** [[26]](#ref-26) und **AutoIOT (Shen et al., ACM MobiCom 2025)** [[22]](#ref-22): Beide Frameworks automatisieren die Erstellung vollständiger IoT-/Embedded-Anwendungen (u. a. für ESP32 und Arduino) über LLM-Agenten, *Retrieval-Augmented Generation* (RAG) auf Hardware-Dokumentation und iteratives Testen. Diese Arbeiten bestätigen die hohe Praxisrelevanz des Problemfelds, zeigen aber zugleich, dass rein RAG- oder promptgetriebene Agenten bei gekoppelten Pin-Multiplexing-Konflikten ohne formalen Solver probabilistisch vorgehen. Ein leichtgewichtiger Pre-Build-Verifikator wie `mcu-pin-solver` ergänzt solche Agenten-Pipelines komplementär als deterministischer Hardware-Critic.

### 3.3 Klassische Werkzeuge der Embedded-Praxis

In der etablierten Embedded-Entwicklung existieren vier Werkzeugklassen, die verwandte Teilprobleme adressieren, aber auf andere Workflows zugeschnitten sind:

- **Statische C++-Analysatoren (`clang-tidy`, `cppcheck`):** Erkennen klassische Software- und Speichersicherheitsfehler (Undefined Behavior, Speicherlecks, implizite Typkonvertierungen), verfügen jedoch über kein Modell für das Pin-Multiplexing, Strapping-Pins oder Peripherie-Arbiter eines konkreten Mikrocontrollers.
- **Grafische Hersteller-Konfiguratoren (`STM32CubeMX`)** [[23]](#ref-23): Modellieren Pin-Multiplexing und Peripheriekonflikte sehr detailliert und bieten innerhalb ihrer grafischen Oberfläche auch automatisches Pin-Remapping in `.ioc`-Projektmodellen. Sie arbeiten jedoch strikt **top-down** (GUI $\rightarrow$ generierter Initialisierungscode) und können bestehenden oder LLM-generierten Arduino-C++-Quelltext nicht rückwärts analysieren und reparieren.
- **Deklarative Hardware-Beschreibungen in RTOS-Buildsystemen (`Zephyr Devicetree`)** [[28]](#ref-28): Lagern Pin-Konfigurationen und `pinctrl`-Zuordnungen sauber in `.dts`- und `.overlay`-Dateien aus und prüfen diese zur Buildzeit innerhalb der Zephyr-CMake-Toolchain. Im verbreiteten Arduino-/PlatformIO-Prototyping, das den Großteil der LLM-Trainingsdaten prägt, stehen Pin-Zuweisungen jedoch direkt im C++-Code.
- **Typsichere Hardware-Abstraktionen in Rust (`embedded-hal` mit Chip-HALs wie `esp-hal`)** [[21]](#ref-21): Während `embedded-hal` plattformunabhängige Treiber-Traits definiert, bilden die zugehörigen chipspezifischen HAL-Crates physische Pins über Rusts affines Ownership-Typsystem und Typestate-Muster als eindeutige Singleton-Ressourcen ab, sodass Doppelbelegungen und bestimmte Fähigkeitsfehler bereits zur Compilezeit abgewiesen werden. Dieser Ansatz steht dem gewachsenen Arduino-C++-Ökosystem jedoch nicht zur Verfügung und berechnet im Konfliktfall keine optimierte Ausweichbelegung.

### 3.4 Kritische Synthese und Forschungslücke

Tabelle 3.1 fasst den Literatur- und Werkzeugvergleich entlang von fünf für die Forschungsfragen maßgeblichen Kriterien zusammen.

| Ansatz / Referenz | Prüft vorhandenen Arduino-C++-Code | Deterministisches Chip-Pin-Modell | Berechnet optimierte Ersatzbelegung | Kein physischer Prüfstand / Ziel-Compiler nötig | Einbindung in LLM-Rückkopplung |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logic-LM [[19]](#ref-19) / SatLM [[27]](#ref-27) | nein (NL $\rightarrow$ Logik) | nein (LLM formalisiert selbst) | ja (Solver) | ja | ja |
| Englhardt et al. [[8]](#ref-8) | ja | indirekt über Zielhardware | nein | nein (HIL-Aufbau) | ja (Mensch-in-Schleife) |
| LLM4PLC [[12]](#ref-12) | nein (SPS-Code) | formaler Modellprüfer | nein (LLM repariert) | teilweise (SPS-Toolchain) | ja |
| EmbedGenius [[26]](#ref-26) / AutoIOT [[22]](#ref-22) | ja (generierter Code) | nein (RAG / Heuristik) | nein (LLM-Iteration) | nein / teilweise | ja (Agenten-Loop) |
| C++-Linter (`clang-tidy`) | ja | nein | nein | teilweise (`compile_commands`) | nein |
| STM32CubeMX [[23]](#ref-23) | nein (GUI $\rightarrow$ Code) | ja | teilweise (GUI-Remapping im `.ioc`-Modell) | ja | nein |
| Zephyr Devicetree [[28]](#ref-28) | nein (`.dts`) | ja | nein | nein (Zephyr-Build) | nein |
| Rust `embedded-hal` / Chip-HALs [[21]](#ref-21) | nein (Rust) | ja (Ownership / Typestate) | nein | nein (Rust-Compiler) | nein |
| **`mcu-pin-solver` (diese Arbeit)** | **ja (Teilmenge, vgl. 8.2)** | **ja (validiertes JSON)** | **ja (Z3 MaxSMT)** | **ja** | **ja (Reparatur-Prompt)** |

*Tabelle 3.1: Einordnung verwandter Ansätze und Forschungslücke.*

**Forschungslücke.** Die Bestandsaufnahme offenbart eine klare Lücke an der Schnittstelle zweier bislang getrennter Welten: Aktuelle LLM-Embedded-Frameworks [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26) verlassen sich bei der Pin-Wahl auf probabilistische Selbstkorrektur, RAG-Heuristiken oder späte Hardware-Tests, während klassische Embedded-Werkzeuge [[21]](#ref-21), [[23]](#ref-23), [[28]](#ref-28) keinen bestehenden Arduino-C++-Code ohne Ziel-Toolchain rückwärts analysieren und minimal-invasiv reparieren. Neuro-symbolische Solver-Ansätze wie Logic-LM [[19]](#ref-19) und SatLM [[27]](#ref-27) belegen zwar die Stärke externer Theorembeweiser, unterliegen aber dem Autoformalisierungs-Engpass. `mcu-pin-solver` schließt genau diese Lücke durch die Kombination aus deterministischer Tree-Sitter-Extraktion, schema-validiertem JSON-Hardware-Profil und Z3-MaxSMT-Reparatur unmittelbar als Pre-Build-Schranke in PlatformIO.

---

## 4 Anforderungsanalyse

### 4.1 Akteure und Anwendungsfälle

Das System adressiert drei klar abgegrenzte Nutzergruppen:

1. **Embedded-Entwicklerinnen und -Entwickler** starten einen PlatformIO-Build (`pio run`) oder rufen `mcu-validate` lokal bzw. in einer CI-Pipeline auf. Sie erwarten, dass harte Pin-Konflikte vor dem Kompilieren mit Dateiname und Zeilennummer blockierend gemeldet werden, während Strapping-Pin-Risiken transparent als nicht-blockierende Warnung erscheinen.
2. **Das Sprachmodell (LLM)** generiert den C++-Entwurf und erhält im `UNSAT`-Fall einen strukturierten, unmissverständlichen Reparatur-Prompt, um ausschließlich die konflikthaften Pin-Nummern durch die Z3-verifizierte Belegung zu ersetzen.
3. **Maintainer und Hardware-Ingenieure** ergänzen neue Mikrocontroller über deklarative JSON-Profile (im Paketordner oder als direkte `.json`-Datei per CLI) ohne Eingriffe in den Python-Code.

### 4.2 Funktionale Anforderungen

| ID | Anforderung | Beschreibung |
| :--- | :--- | :--- |
| FA-01 | Hardware-Profil laden und validieren | Aus einer Board-Kennung (z. B. `esp32-c3-devkitm-1`) oder einem direkten `.json`-Dateipfad wird das passende Profil (längstes normalisiertes Präfix zuerst) geladen und streng gegen das erwartete Schema validiert. |
| FA-02 | Mehrere Dateien & Include-Ordner | Bei Angabe von `src/` werden sämtliche `.h`, `.hpp`, `.c`, `.cpp`, `.ino` in `src/` sowie dem Nachbarordner `include/` (und optional via `--include-dir` ergänzten Ordnern) analysiert; Build- und Testordner (`.pio/`, `test/`, `tests/`) bleiben ausgeschlossen. |
| FA-03 | Fehlalarmfreie Syntaxbaum-Extraktion | Top-Level-Pin-Konstanten (`#define`, globale `int`/`uint8_t`-Deklarationen) sowie direkte Pin-Literale (z. B. `pinMode(12, OUTPUT)`) werden über Tree-Sitter extrahiert; Kommentare, Zeichenketten, lokale Variablen und fachfremde Konstanten (`BAUD_RATE`, `DELAY_MS`) erzeugen keine Fehlalarme. |
| FA-04 | Eindeutige Behandlung von Widersprüchen | Identische Definitionen desselben Symbols über mehrere Dateien werden dedupliziert; widersprüchliche Redefinitionen bleiben unter garantiert eindeutigen Schlüsseln sichtbar. |
| FA-05 | Fähigkeiten, Bus-Rollen und Module | Aus Funktionsaufrufen (positionsgenaue Argumentauswertung) und einer Namens-Fallback-Heuristik werden Mengen benötigter Fähigkeiten (`gpio`, `adc`, `pwm`, `i2c`, `spi`, `uart`), Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripheriemodule (`wifi`, `usb_serial`) abgeleitet. |
| FA-06 | Präzise Diagnose & Strapping-Warnungen | Jeder harte Verstoß (Pin fehlt, Kollision, reserviert, Fähigkeit fehlt, Sperre durch aktives Modul) wird einzeln mit `datei:zeile`-Verweis und konkreter Regelbegründung gemeldet; im aktuellen Arbeitsstand werden belegte Boot-/Strapping-Pins zusätzlich als nicht-blockierende Hardware-Warnungen ausgegeben. |
| FA-07 | Kollision vs. geteilte Bus-Leitung | Unabhängige Signale, verschiedene Bus-Leitungen (`SDA` vs. `SCL`, `SCK` vs. `MOSI`), getrennte Bus-Instanzen (`Wire` vs. `Wire1`) und SPI-`CS`-Leitungen dürfen keinen Pin teilen; Signale derselben Bus-Leitung (z. B. mehrere Geräte an `Wire:sda`) dürfen teilen und bleiben bei einer Reparatur gekoppelt. |
| FA-08 | Minimale Reparatur & Kapazitätsmeldung | Bei harten Konflikten berechnet Z3 eine gültige Ersatzbelegung, die Originalpins bewahrt, Strapping-Pins meidet und knappe ADC-/USB-Pins schont. Existiert keine zulässige Belegung, wird dies sauber ohne `GPIO None` gemeldet. |
| FA-09 | Transparenter Bericht & Reparatur-Prompt | Der Bericht nennt die Anzahl geprüfter Pins (inkl. Warnung bei `0` erkannten Pins), führt ggf. nicht-blockierende Strapping-Warnungen auf und liefert im `UNSAT`-Fall alle Einzelkonflikte sowie eine vollständige `Keep`/`Change`-Anweisung. |
| FA-10 | Build-Schranke und CLI | Als PlatformIO-Bibliothek (`dmatheja/mcu-pin-solver@^0.2.0`) stoppt das Werkzeug fehlerhafte Builds vor dem Compilerstart; via `pip install .` steht der CLI-Befehl `mcu-validate` eigenständig bereit. |

*Tabelle 4.1: Funktionale Anforderungen.*

### 4.3 Nicht-funktionale Anforderungen (ISO/IEC 25010:2023)

Die nicht-funktionalen Qualitätsanforderungen folgen dem Produktqualitätsmodell der aktuellen Norm **ISO/IEC 25010:2023** (*SQuaRE*) [[16]](#ref-16), welche die Ausgabe von 2011 insbesondere um das eigenständige Hauptmerkmal *Safety (Funktionale Sicherheit / Betriebssicherheit)* erweitert und *Portability* zu *Flexibility (Flexibilität)* neu strukturiert.

| ID | Merkmal (ISO/IEC 25010:2023) | Abnahmekriterium |
| :--- | :--- | :--- |
| NFA-01 | Wartbarkeit – Modifizierbarkeit | Der Python-Quelltext enthält keine chipspezifischen Pin-Nummern oder Chipnamen; ein neuer Mikrocontroller erfordert ausschließlich eine deklarative JSON-Datei. |
| NFA-02 | Leistungseffizienz – Zeitverhalten | Ein Prüflauf für ein typisches Embedded-Projekt (bis ca. 15–20 Dateien/Pins) bleibt unter 1 s (bzw. im `SAT`-Fall deutlich darunter); Skalierungsgrenzen werden transparent vermessen. |
| NFA-03 | Flexibilität – Anpassbarkeit | Plattformunabhängiger Betrieb unter Windows und Linux ohne installierte Cross-Compiler-Toolchain oder Ziel-Header. |
| NFA-04 | Funktionale Eignung & Safety – Korrektheit / Risikovermeidung | Jede ausgegebene Z3-Ersatzbelegung besteht eine sofortige Re-Validierung gegen alle harten Profilregeln; hardwaregefährdende Zuweisungen werden vor dem Kompilieren blockiert. |
| NFA-05 | Flexibilität – Installierbarkeit | Sowohl `pip install .` (inklusive gebündelter Board-JSONs) als auch die Einbindung über die PlatformIO Registry funktionieren eigenständig; Beispiel-Quelltext wird nicht mitkompiliert; der CLI-Aufruf läuft frei von Python-Warnungen. |
| NFA-06 | Wartbarkeit – Testbarkeit | Eine modulare Unit- und End-to-End-Testsuite deckt sämtliche Kernmodule und Fehlerklassen ab und läuft in der CI zusammen mit statischer Typprüfung (`mypy`) und Linting (`ruff`). |
| NFA-07 | Wartbarkeit – Analysierbarkeit | Top-down lesbare Strukturierung in vier getrennte Kernmodule (`board.py`, `parser.py`, `solver.py`, `cli.py`) mit unveränderlichen typisierten Datenklassen und minimalen Laufzeitabhängigkeiten (ausschließlich `z3-solver`, `tree-sitter` und `tree-sitter-cpp`). |

*Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023 [[16]](#ref-16).*

### 4.4 Architektur-Invarianten und Systemgrenzen

Sechs verbindliche Architektur-Invarianten (Tabelle 4.3) sichern die Trennung von Hardware-Daten, Syntaxbaum-Analyse und formalem Solver ab und werden durch die Testsuite sowie die CI-Pipeline automatisiert überwacht.

| ID | Invariante | Regel |
| :--- | :--- | :--- |
| INV-01 | Keine Chip-Logik in Python | Physische GPIO-Nummern, reservierte Bereiche, Strapping-Pins, Peripherie-Auslöser und Konfliktregeln liegen ausschließlich in `mcu_validator/boards/*.json` (oder nutzerseitig übergebenen JSON-Dateien). |
| INV-02 | Syntaxbaum zuerst | C++-Strukturen werden ausschließlich über Tree-Sitter extrahiert; reguläre Ausdrücke operieren niemals auf dem C++-Rohtext, sondern nur auf kurzen, bereits aus dem CST isolierten Teilzeichenketten. |
| INV-03 | Eindeutige Schlüsselvergabe | Widersprüchliche Redefinitionen und direkte Pin-Literale erhalten über `_reserve_unique_key` global eindeutige Schlüssel, sodass im Solver keine Variablenkollision auftritt. |
| INV-04 | Paarweise Bus-Leitungskopplung | Zwei Signale werden genau dann gekoppelt ($v_i = v_j$), wenn sie dieselbe einzelne teilbare Bus-Fähigkeit, dieselbe `bus_group` und denselben Ausgangspin besitzen; andernfalls gilt strikt $v_i \neq v_j$. |
| INV-05 | Priorisierte dreistufige Gewichtung | Harte Hardware-Regeln werden niemals abgeschwächt; auf Einzelsignalebene (und global für Stufe 1 bis $n \le 39$ Signale) dominiert der Erhalt gültiger Originalpins (`1000`) die Strapping-Meidung (`20`) und diese die Schonung knapper Spezialpins (`5`). |
| INV-06 | Paket-Hygiene | `package-data` in `pyproject.toml`, `srcFilter` und `export` in `library.json`; kein Vorab-Import von `.cli` in `__init__.py` (verhindert `runpy`-`RuntimeWarning` bei `python -m mcu_validator.cli`). |

*Tabelle 4.3: Architektur-Invarianten.*

**Systemabgrenzung.** Im Leistungsumfang enthalten sind die statische Syntaxbaum-Analyse von Pin-Deklarationen, direkten Pin-Aufrufen und Peripherie-Auslösern, die Schema-Validierung und Prüfung gegen JSON-Profile, die Z3-MaxSMT-Reparatur sowie die PlatformIO-Build-Integration. **Nicht enthalten** sind elektrische Schaltungssimulationen (z. B. Strombelastbarkeit, Spannungspegel-Anpassung oder I2C-Pull-up-Dimensionierung), eine Datenflussanalyse für erst zur Laufzeit berechnete Pin-Nummern sowie das automatische Überschreiben von Projekt-Quelltexten.

---

## 5 Konzeption und Entwurfsentscheidungen

Dieses Kapitel begründet die vier zentralen Architekturentscheidungen und verfolgt anschließend ein durchgängiges Beispiel über alle Schichten des Systems. Für die Verfahrensauswahl kommen Nutzwertanalysen zum Einsatz. Dabei wird methodisch transparent offengelegt, dass Gewichte und Punktbewertungen durch den Verfasser festgelegt wurden: Nutzwertanalysen strukturieren mehrdimensionale Zielkonflikte nachvollziehbar, ersetzen jedoch keinen formalen Beweis. Deshalb ergänzt jeweils eine Sensitivitätsbetrachtung, ab welcher Gewichtsverschiebung eine alternative Option den Vorzug erhielte.

### 5.1 Entscheidung 1: Verfahren zur Quelltextanalyse

Zur Wahl standen drei Verfahren: **A – Reguläre Ausdrücke** direkt auf dem C++-Rohtext, **B – `libclang`** (Compiler-API mit vollständiger Präprozessor- und Typauflösung) sowie **C – Tree-Sitter** (`tree-sitter-cpp`). Die Bewertung erfolgte auf einer Skala von 1 (ungenügend) bis 5 (sehr gut):

| Kriterium | Gewicht | A Regex | B `libclang` | C Tree-Sitter |
| :--- | :---: | :---: | :---: | :---: |
| K1 Robustheit gegen Kommentare, Zeichenketten, Scopes (FA-03) | 25 % | 1 | 5 | 5 |
| K2 Betrieb ohne Ziel-Toolchain und System-Header (NFA-03) | 25 % | 5 | 2 | 5 |
| K3 Fehlertoleranz gegenüber unvollständigem Code | 15 % | 4 | 2 | 4 |
| K4 Semantische Tiefe (Makroexpansion, `#ifdef`, Typen) | 20 % | 1 | 5 | 2 |
| K5 Installations- und Integrationsaufwand | 15 % | 5 | 3 | 5 |
| **Nutzwert** | 100 % | **3,05** | **3,50** | **4,25** |

*Tabelle 5.1: Nutzwertanalyse Quelltextanalyse.*

**Begründung.** Reguläre Ausdrücke scheitern prinzipiell an K1 (Abschnitt 2.3). `libclang` liefert zwar maximale semantische Tiefe (vollständige Präprozessor-Auswertung, Typauflösung für `gpio_num_t` und `enum`), erfordert jedoch eine konsistente Kompilierungsdatenbank (`compile_commands.json`) oder exakte Ziel-Include-Pfade (`-I`, `-D`, Target-Triple `--target=riscv32-unknown-elf`), die vor dem ersten PlatformIO-Build oder in isolierten CLI-Umgebungen häufig fehlen oder fehlschlagen. Tree-Sitter hingegen ist als kompaktes Python-Paket mit eingebettetem C-GLR-Parser plattformübergreifend und toolchain-frei lauffähig.

**Sensitivität.** Bei proportionaler Reskalierung der übrigen Gewichte überholt `libclang` Tree-Sitter exakt ab einem Gewicht von $w_4 = 36\,\%$ für K4 (Differenz $+3 \cdot w_4 - 1{,}35 \cdot \frac{1-w_4}{0{,}80} = 0 \iff w_4 = 0{,}36$). Solange Portabilität, fehlertoleranter Pre-Build-Betrieb und Null-Konfiguration dominieren, bildet Tree-Sitter die stabil beste Wahl; die resultierenden semantischen Grenzen (`#ifdef`, `gpio_num_t`) werden in Kapitel 8 explizit adressiert.

### 5.2 Entscheidung 2: Verfahren zur Konfliktlösung

Für die Berechnung einer minimal-invasiven Ersatzbelegung wurden vier Verfahren verglichen: **1 – Eigene gierige Heuristik**, **2 – SMT ohne Optimierung** (`z3.Solver`), **3 – Gemischt-ganzzahlige lineare Optimierung** (MILP, z. B. PuLP/HiGHS) und **4 – Partial Weighted MaxSMT** (`z3.Optimize`).

| Kriterium | Gewicht | 1 Heuristik | 2 SMT | 3 MILP | 4 MaxSMT |
| :--- | :---: | :---: | :---: | :---: | :---: |
| K1 Nachweislich optimale Lösung bzgl. Zielfunktion (FA-08) | 30 % | 1 | 1 | 5 | 5 |
| K2 Ausdrucksstärke für Gleichheit, Ungleichheit, Kopplung (FA-07) | 25 % | 2 | 5 | 2 | 5 |
| K3 Abhängigkeiten und Installationsaufwand | 15 % | 5 | 4 | 4 | 4 |
| K4 Laufzeit bei typischen Pin-Zahlen (bis ca. 15–20 Signale) | 15 % | 5 | 5 | 4 | 4 |
| K5 Nachvollziehbarkeit und Wartbarkeit des Modells | 15 % | 4 | 2 | 3 | 3 |
| **Nutzwert** | 100 % | **2,90** | **3,20** | **3,65** | **4,40** |

*Tabelle 5.2: Nutzwertanalyse Konfliktlösung.*

**Begründung.** Eine gierige Zuweisungsheuristik versagt bei gekoppelten Ressourcenengpässen: Kollidieren beispielsweise eine LED und ein Analogsensor auf dem vorletzten freien `ADC1`-Pin, kann eine ungünstige Abarbeitungsreihenfolge den Sensor auf einen Strapping-Pin verdrängen oder fälschlich keine Lösung finden, obwohl ein Ausweichen der LED den Konflikt optimal löst (Abschnitt 6.5, Fall 3). Reines SMT (`z3.Solver`) findet zwar eine gültige Belegung, minimiert aber nicht die Anzahl verschobener Pins. MILP erreicht dieselbe globale Optimalität und nutzt effiziente LP-Relaxationen, erfordert aber binäre Indikatorvariablen $x_{i,p} \in \{0, 1\}$ für jede Signal-Pin-Kombination sowie lineare Kopplungs- und Kardinalitätsungleichungen ($x_{i,p} = x_{j,p}$, $\sum_i x_{i,p} \le 1$). In Z3 MaxSMT genügen eine einzelne Ganzzahlvariable $v_i$ je Signal sowie unmittelbar lesbare Ausdrücke $v_a = v_b$ und $v_a \neq v_b$ in rund 70 Zeilen Python-Code – ein deutlicher Vorteil für Wartbarkeit und Analysierbarkeit (NFA-07).

**Sensitivität.** Der Vorsprung von MaxSMT gegenüber MILP speist sich vor allem aus K2 (Modellierungsfreundlichkeit). Erst für große Mikrocontroller mit mehr als 20–30 gleichzeitig konfliktbehafteten Signalen bieten eine boolesche One-Hot-MaxSAT-Kodierung oder ein MILP-Solver substantielle Laufzeitvorteile (vgl. Skalierungsmessung in Abschnitt 7.5 und Optimierungsausblick in Abschnitt 8.4).

### 5.3 Entscheidung 3: Zweistufiger Ablauf

Übergäbe man alle Originalpins direkt als harte Bedingungen an Z3, lieferte der Solver im Fehlerfall lediglich ein pauschales `UNSAT` ohne menschenlesbare Erklärung der Einzelverstöße. Zudem würde bei jedem konfliktfreien Kompilierlauf unnötig der Optimierungssolver gestartet. Deshalb trennt die Architektur strikt zwei Stufen:

1. **Stufe 1 – Deterministische Regeldiagnose (ohne Z3):** Ein linearer Python-Durchlauf prüft jede extrahierte Anforderung gegen das Hardware-Profil und sammelt sämtliche Klartextfehler samt `datei:zeile`-Verweis. Bestehen keine harten Konflikte, prüft der Arbeitsstand abschließend noch auf nicht-blockierende Strapping-Warnungen und beendet die Validierung sofort mit `SAT` – Z3 wird überhaupt nicht instanziiert.
2. **Stufe 2 – MaxSMT-Reparatur (nur bei Konflikten):** Nur wenn Stufe 1 mindestens einen harten Verstoß erkennt, konstruiert `solver.py` die Z3-Optimierungsinstanz, berechnet die optimale Ersatzbelegung und bewertet anschließend etwaige Strapping-Warnungen auf der *resultierenden* Zielbelegung.

Diese Zweiteilung garantiert, dass alle Fehler eines Projekts in einem Durchlauf gemeldet werden und konfliktfreie Builds praktisch latenzfrei bleiben (`0,01–0,06 ms` Validierungszeit selbst bei 20 Pins, Abschnitt 7.5).

### 5.4 Entscheidung 4: Hardware-Wissen als validierte Daten

Alle chipspezifischen Fakten liegen vollständig getrennt vom Python-Code in deklarativen JSON-Dateien (`mcu_validator/boards/*.json`, INV-01). Diese Trennung ist sowohl architektonisch als auch wirtschaftlich tragend: Die Unterstützung eines neuen Mikrocontrollers reduziert sich auf die Erstellung und Datenblatt-Prüfung einer JSON-Datei (ca. 1–2 Stunden Aufwand, Anhang F und Abschnitt 7.6), ohne Prüf- oder Solver-Code anzupassen.

Da JSON-Profile in der Praxis auch mit LLM-Unterstützung erstellt oder manuell editiert werden können, validiert `BoardSpec.from_dict()` jede geladene Datei strikt gegen das erwartete Schema (Abschnitt 6.2). Typische Fehler – etwa eine Zeichenkette `"gpio"` statt einer Liste `["gpio"]`, Textwerte `["18"]` oder Boolesche Werte `[true]` in `forbidden_pins` (wobei in Python `isinstance(True, int)` tückischerweise `True` ergibt und daher explizit abgefangen wird), unbekannte Modulnamen in `when_resource_active` oder wirkungslose Regeln ohne Ziel – führen unmittelbar zu einer verständlichen `ValueError`-Diagnose mit Exit-Code `2`, statt stillschweigend ignoriert zu werden.

### 5.5 Gesamtarchitektur

Abbildung 5.1 zeigt die modulare Vierschicht-Architektur vom PlatformIO-Buildstart bis zum Exit-Code.

```text
  platformio.ini + Projektdateien (include/, src/)
          │   "pio run" startet das SCons-Pre-Build-Skript vor dem Cross-Compiler
          ▼
  pio_hook.py
    ├─ Einmal-Ausführung pro Build (Merker _MCU_VALIDATOR_RAN)
    ├─ prüft / installiert Python-Pakete (mit Versionsgrenzen & PEP-668-Hilfe)
    └─ ruft auf: python -m mcu_validator.cli <src> <board> [--include-dir <include>]
          ▼
  mcu_validator/cli.py  (Einstiegspunkt: mcu-validate / validate_path)
    ├─ 1. board.py  : load_board(board)      → BoardSpec (validiert aus boards/*.json)
    ├─ 2. parser.py : parse_cpp(pfad, board) → ParsedProject (PinRequests + aktive Module)
    ├─ 3. solver.py : validate(proj, board)  → ValidationResult (Diagnose, Warnungen, ggf. Z3)
    └─ 4. cli.py    : format_report(...)     → Bericht, Warnungen + kopierbarer Prompt
          │
          ├── SAT   (Exit-Code 0) → ggf. nicht-blockierende Strapping-Warnungen; Compiler startet
          ├── UNSAT (Exit-Code 1) → env.Exit(1), Fehlerbericht & Z3-Reparatur-Prompt ausgeben
          └── ERROR (Exit-Code 2) → Konfigurations- / Schema- / Eingabefehler auf stderr melden
```
*Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess.*

### 5.6 Durchgängiges Beispiel

Das folgende Beispiel verfolgt Szenario 0 aus der Testsuite (Listing 5.1) durch sämtliche fünf Verarbeitungsschritte auf dem ESP32-C3. Es entspricht funktional Listing 1.1.

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

**Schritt 1 – Profil laden und validieren (`board.py`).** Aus `mcu_validator/boards/esp32-c3.json` erzeugt `load_board()` ein typisiertes `BoardSpec`-Objekt: GPIO 11–17 sind reserviert (`VDD_SPI` und interner SPI-Flash), GPIO 5 trägt ausschließlich `adc2`, `ADC1` liegt auf GPIO 0–4, Strapping-Pins sind $\{2, 8, 9\}$, aktives `wifi` sperrt die Fähigkeit `adc2`, und aktives `usb_serial` sperrt die Pins $\{18, 19\}$.

**Schritt 2 – Quelltext analysieren (`parser.py`).** Tree-Sitter extrahiert außerhalb von Funktionskörpern die drei Definitionen `STATUS_LED = 12` (Zeile 5; der nachgestellte Zeilenkommentar im `preproc_arg` wird durch `_parse_uint` entfernt), `SOIL_SENSOR = 5` (Zeile 6) und `RELAY_PIN = 4` (Zeile 7). Die lokale Variable `int reading` innerhalb von `loop()` wird aufgrund von `skip_functions=True` ignoriert. Aus `analogRead(SOIL_SENSOR)` folgt `capabilities = frozenset({"adc"})`; aus `pinMode`/`digitalWrite` folgt für die übrigen beiden Signale `frozenset({"gpio"})`. `WiFi.begin` und `Serial.begin` lösen `wifi` und `usb_serial` aus:

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

**Schritt 3 – Deterministische Diagnose (Stufe 1 in `solver.py`).** `STATUS_LED` liegt auf dem reservierten Flash-Pin GPIO 12 (`Internal SPI flash (SPIHD)`). `SOIL_SENSOR` fordert `adc` an, was über `capability_aliases` auf `{"adc1", "adc2"}` expandiert wird; GPIO 5 bietet hiervon lediglich `adc2`, welche durch die aktive Regel `WIFI_BLOCKS_ADC2` gesperrt ist. Die Diagnose übernimmt unmittelbar den `reason`-Text der Regel. `RELAY_PIN` (GPIO 4) verletzt keine Regel. Da zwei harte Konflikte vorliegen, startet Stufe 2.

**Schritt 4 – MaxSMT-Reparatur (Stufe 2 in `solver.py`).** Für jedes Signal bestimmt `_allowed_pins_for()` die zulässige Kandidatenmenge (da `usb_serial` aktiv ist, entfallen GPIO 18 und 19):

$$P_{\text{LED}} = P_{\text{RELAY}} = \{0, 1, \dots, 10, 20, 21\}, \qquad P_{\text{SOIL}} = \{0, 1, 2, 3, 4\}.$$

Als harte Bedingung gelten Domänenbindung und paarweise Verschiedenheit ($v_{\text{LED}} \neq v_{\text{SOIL}}$, $v_{\text{LED}} \neq v_{\text{RELAY}}$, $v_{\text{SOIL}} \neq v_{\text{RELAY}}$). Die dreistufigen weichen Bedingungen bewerten jede gültige Lösung wie folgt:

- **+1000 Punkte (Stufe 1):** Erhalt des gültigen Originalpins (hier für `RELAY_PIN` auf GPIO 4 erfüllbar).
- **+20 Punkte (Stufe 2):** Meidung der Strapping-Pins $S = \{2, 8, 9\}$.
- **+5 Punkte (Stufe 3):** Schonung knapper, vom Signal nicht benötigter Spezialpins (`adc`/`usb`). Für `STATUS_LED` und `RELAY_PIN` (nur `gpio`) sind $K_{\text{LED}} = K_{\text{RELAY}} = \{0, 1, 2, 3, 4, 5\}$ knappe ADC-Pins; nicht knappe Pins sind $\{6, 7, 8, 9, 10, 20, 21\}$, sodass unter gleichzeitiger Strapping-Meidung die fünf idealen Standard-GPIOs $\{6, 7, 10, 20, 21\}$ verbleiben. Für `SOIL_SENSOR` wird `adc` auf `{"adc1", "adc2"}` expandiert; kein Pin in $P_{\text{SOIL}}$ trägt `usb`, weshalb $K_{\text{SOIL}} = \emptyset$ gilt und die dritte weiche Klausel entfällt.

| Belegung (LED, Sensor, Relais) | Relais behalten | Strapping-Meidung | Knappe Pins geschont | Summe | Bewertung |
| :--- | :---: | :---: | :---: | :---: | :--- |
| (12, 5, 4) – Original | – | – | – | ungültig | verletzt harte Regeln |
| (6, 3, 10) | 0 | 20 + 20 + 20 = 60 | 5 + 0 + 5 = 10 | 70 | Relais unnötig verschoben |
| (6, 2, 4) | 1000 | 20 + 0 + 20 = 40 | 5 + 0 + 0 = 5 | 1045 | Sensor auf Strapping-Pin 2 |
| (1, 3, 4) | 1000 | 20 + 20 + 20 = 60 | 0 + 0 + 0 = 0 | 1060 | LED belegt knappen `ADC1`-Pin 1 |
| (6, 3, 4) – Ausgabe von Z3 | 1000 | 20 + 20 + 20 = 60 | 5 + 0 + 0 = 5 | **1065** | **optimal** |

*Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`).*

Die drei Gewichtungsstufen greifen präzise ineinander: `RELAY_PIN` verbleibt auf GPIO 4 (obwohl GPIO 4 ein `ADC1`-Pin ist, dominieren `1000` Haltepunkte die `5` Schonungspunkte), `SOIL_SENSOR` weicht auf den strapping-freien `ADC1`-Pin GPIO 3 aus, und `STATUS_LED` erhält mit GPIO 6 einen regulären Standard-GPIO ohne unnötigen Verbrauch eines `ADC1`-Kanals. Da kein Signal der Zielbelegung `(6, 3, 4)` auf einem Strapping-Pin liegt, fallen auch im Arbeitsstand keine Strapping-Warnungen an.

**Schritt 5 – Ausgabe (`cli.py`).** Listing 5.2 zeigt die tatsächliche CLI-Ausgabe auf dem ESP32-C3. Dieselbe C++-Datei besteht auf dem ESP32-S3 mit `SAT` (Listing 5.3), da GPIO 12 dort ein regulärer GPIO ist und GPIO 5 zu `ADC1` gehört. Allein der Wechsel des deklarativen JSON-Profils verändert das Prüfergebnis ohne eine einzige Änderung am Prüfcode.

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

Dieses Kapitel erläutert die Umsetzung von `mcu-pin-solver` anhand der realen Projektmodule. Sämtliche vier Kernmodule (`board.py`, `parser.py`, `solver.py`, `cli.py`) folgen konsequent dem Top-down-Prinzip: Die jeweilige Einstiegsfunktion (`load_board`, `parse_cpp`, `validate`, `validate_path`) steht am Dateianfang, gefolgt von den internen Hilfsfunktionen in Ausführungsreihenfolge. Die Anhänge A bis E enthalten die vollständigen Quelltexte des freigegebenen Releases `0.2.0`; die anschließende Arbeitsstand-Erweiterung um nicht-blockierende Strapping-Warnungen in `solver.py` und `cli.py` wird in den Abschnitten 6.1, 6.4 und 6.6 explizit mit dokumentiert.

### 6.1 Repository und Softwareumgebung

Die Codebasis gliedert sich in vier Schichten: die Build- und Paketintegration (`pio_hook.py`, `library.json`, `pyproject.toml`), Orchestrierung und Berichtsformatierung (`cli.py`, `__init__.py`), den deterministischen Prüfkern (`board.py`, `parser.py`, `solver.py`) sowie die gebündelten Hardware-Profile (`mcu_validator/boards/*.json`). Tabelle 6.1 fasst sämtliche Projektdateien und ihren Umfang zusammen.

| Datei / Ordner | Umfang (`v0.2.0` / Arbeitsstand) | Aufgabe |
| :--- | :--- | :--- |
| `mcu_validator/boards/esp32-c3.json` | 50 Zeilen JSON | Hardware-Profil für den ESP32-C3 (Anhang A) |
| `mcu_validator/boards/esp32-s3.json` | 73 Zeilen JSON | Hardware-Profil für den ESP32-S3 (Anhang B) |
| `mcu_validator/board.py` | 284 Zeilen Python | Typisierte Datenklassen, Profil-Auflösung und Schema-Validierung (Anhang C) |
| `mcu_validator/parser.py` | 541 Zeilen Python | Dateiauflösung, Tree-Sitter-CST-Analyse, Bus-Rollen, Namens-Fallback (Anhang D) |
| `mcu_validator/solver.py` | 284 / 342 Zeilen Python | Stufe-1-Diagnose, Strapping-Warnungen (Arbeitsstand) und Z3-MaxSMT-Solver (Anhang E: `v0.2.0`) |
| `mcu_validator/cli.py` | 178 / 195 Zeilen Python | CLI (`mcu-validate`), Berichts- & Warnungsformatierung, Exit-Codes `0`/`1`/`2` (Anhang E: `v0.2.0`) |
| `mcu_validator/__init__.py` | 21 Zeilen Python | Öffentliche Python-API & `__version__ = "0.2.0"` ohne Vorab-Import von `.cli` (Anhang E) |
| `pio_hook.py` | 92 Zeilen Python | PlatformIO-Pre-Build-Hook inkl. Abhängigkeitsprüfung und `--include-dir` (Anhang E) |
| `library.json` | 33 Zeilen JSON | PlatformIO-Manifest (`0.2.0`) mit `extraScript`, `srcFilter` und `export` (Anhang E) |
| `pyproject.toml` | 42 Zeilen TOML | Paketmetadaten (`package-data` für `boards/*.json`), `ruff`- und `mypy`-Konfiguration |
| `src/main.cpp` und `platformio.ini` | 56 + 11 Zeilen | ESP32-C3-Demo-Projekt (`STATUS_LED=8`, `SOIL_SENSOR=1`, `RELAY_PIN=4`) |
| `tests/test_*.py` und `tests/run_tests.py` | 766 (42 Tests) / 857 Zeilen (47 Tests) + 7 Szenarien | Modulare Unit- und End-to-End-Testsuite (`test_board`, `test_parser`, `test_solver`, `test_cli`, `test_scenarios`) |
| `.github/workflows/ci.yml` | 35 Zeilen YAML | CI-Matrix (Ubuntu & Windows, Python `3.10`/`3.12`) + `ruff` & `mypy` |
| `README.md` und `.gitattributes` | 139 + 1 Zeile | Einführung, Installationsanleitung, JSON-Prompt-Vorlage, LF-Zeilenenden |

*Tabelle 6.1: Dateien des Repositories (`v0.2.0` gemäß Anhängen A–E sowie Arbeitsstand-Erweiterung).*

Das Paket `mcu_validator` umfasst im Release `0.2.0` 1308 Zeilen (mit `pio_hook.py` 1400 Zeilen) und im aktuellen Arbeitsstand 1383 Zeilen (mit `pio_hook.py` 1475 Zeilen), jeweils einschließlich Docstrings, Typannotationen und Schema-Validierung. Die Testsuite nutzt bewusst ausschließlich `unittest` aus der Python-Standardbibliothek, um keine zusätzlichen Entwicklungsabhängigkeiten zu erzwingen; alle fünf Module des Releases `v0.2.0` bestehen `ruff` und `mypy` fehler- und warnungsfrei.

### 6.2 Hardware-Profile und Schema-Validierung (`board.py`)

Gemäß INV-01 liegen sämtliche GPIO-Definitionen, Fähigkeiten und Sperrregeln als JSON-Dateien innerhalb des Pakets unter `mcu_validator/boards/`. Durch `package-data` in `pyproject.toml` werden diese Profile bei `pip install .` oder aus einem Wheel heraus direkt mitinstalliert.

Jedes Profil strukturiert das Hardware-Wissen neben `mcu` und `description` in fünf klar getrennte Abschnitte (Listing 6.1):

1. **`pins`:** Bildet physisch vorhandene Pin-Nummern (als Ziffern-Strings) auf `capabilities`, `strapping`, `reserved` und optional `note` ab. Nicht existierende Nummern (wie GPIO 22–25 beim ESP32-S3) fehlen als Schlüssel; reservierte Systempins tragen `"reserved": true` und `"capabilities": []`.
2. **`capability_aliases`:** Löst generische Fähigkeitsnamen (`"adc"`) in chipspezifische Hardware-Banken (`["adc1", "adc2"]`) auf.
3. **`shared_capabilities`:** Kennzeichnet Bus-Fähigkeiten (`["i2c", "spi"]`), deren Daten-/Taktleitungen von mehreren Teilnehmern gemeinsam genutzt werden dürfen.
4. **`resource_triggers`:** Ordnet Peripherieressourcen (`"wifi"`, `"usb_serial"`) den auslösenden C++-Aufrufen zu (`["WiFi.begin", "WiFi.softAP"]`, `["Serial.begin"]`).
5. **`conflict_rules`:** Definiert zustandsabhängige Sperren über `when_resource_active` in Verbindung mit `forbidden_capability` oder `forbidden_pins` sowie einer Klartextbegründung (`reason`).

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

Listing 6.2 zeigt die Profilauflösung in `mcu_validator/board.py`. Gegenüber `v0.1.0` schließen drei Härtungen typische Fehlerquellen: (1) `_normalize_name()` vereinheitlicht Groß-/Kleinschreibung und Unterstriche (`_` $\rightarrow$ `-`), während `candidates` absteigend nach Stammlänge sortiert werden, sodass etwa `esp32-c3.json` stets vor einem allgemeineren `esp32.json` greift. (2) Direkte `.json`-Dateipfade (z. B. `mcu-validate src ./custom_board.json`) werden unmittelbar akzeptiert. (3) `BoardSpec.from_dict()` validiert jeden Schlüssel und Datentyp streng – einschließlich der expliziten Prüfung `isinstance(p, int) and not isinstance(p, bool)` für `forbidden_pins` (da `bool` in Python eine Unterklasse von `int` ist), der Ablehnung bloßer Strings anstelle von Listen bei `capabilities`, der Konsistenzprüfung von `when_resource_active` gegen `resource_triggers` sowie der Zurückweisung wirkungsloser Regeln ohne Sperrziel.

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

Tabelle 6.2 vergleicht beide mitgelieferten Hardware-Profile anhand der Hersteller-Datenblätter [[9]](#ref-9), [[10]](#ref-10). Beide Profile spiegeln die Flexibilität der ESP32-GPIO-Matrix wider, indem sämtliche nicht reservierten GPIOs `pwm`, `i2c`, `spi` und `uart` unterstützen; zugleich markieren sie die JTAG-Pads (`4–7` auf C3, `39–42` auf S3), die auf Entwicklungsboards ohne eFuse-JTAG-Sperre regulär als GPIOs nutzbar bleiben. Beim ESP32-S3 sind GPIO 33–37 konservativ in den reservierten Bereich einbezogen, damit das Profil sowohl Quad-SPI- als auch Octal-SPI-Flash/PSRAM-Module absichert.

| Merkmal | `mcu_validator/boards/esp32-c3.json` | `mcu_validator/boards/esp32-s3.json` |
| :--- | :--- | :--- |
| Prozessorarchitektur | RISC-V Single-Core (RV32IMC) | Xtensa LX7 Dual-Core |
| Eingetragene GPIOs | `0–21` (22 physische GPIOs) | `0–21`, `26–48` (45 physische GPIOs; `22–25` fehlen) |
| Reservierter Flash / PSRAM | `11–17` (`VDD_SPI` + interner SPI-Flash) | `26–37` (`26–32` SPI-Flash/QPI; `33–37` konservativ für OPI) |
| Strapping-Pins | `2, 8, 9` (Boot-Modus, ROM-Log) | `0, 3, 45, 46` (Boot, JTAG, `VDD_SPI`-Spannung, ROM-Log) |
| `ADC1` (unabhängig von WLAN) | `0–4` (5 Kanäle) | `1–10` (10 Kanäle; GPIO 0 ohne ADC) |
| `ADC2` (bei WLAN gesperrt) | `5` (1 Kanal, `ADC2_CH0`) | `11–20` (10 Kanäle; `19/20` auch USB) |
| Native USB-Pins | `18` (D-), `19` (D+) | `19` (D-), `20` (D+) |
| GPIO-Matrix (`pwm`, `i2c`, `spi`, `uart`) | alle freien GPIOs (`0–10`, `18–21`) | alle freien GPIOs (`0–21`, `38–48`) |
| Standard-UART0 / JTAG-Pads | UART0: `20` (RX), `21` (TX); JTAG: `4–7` | UART0: `43` (TX), `44` (RX); JTAG: `39–42` |

*Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`, Angaben nach [[9]](#ref-9), [[10]](#ref-10)).*

### 6.3 Syntaxbaum-Parser (`parser.py`)

Der Parser in `mcu_validator/parser.py` gliedert sich in vier top-down angeordnete Schritte innerhalb von `parse_cpp()`: Dateiauflösung, CST-Durchlauf, Konstruktion der `PinRequest`-Objekte sowie Erkennung aktiver Peripherie.

**1. Dateiauflösung (`_resolve_source_files`).** Einzeldateien werden direkt geparst; bei einem Verzeichnis `src/` ergänzt `_project_search_dirs()` über `path.resolve()` automatisch einen Nachbarordner `include/` (sodass auch relative Aufrufe wie `.` innerhalb von `src/` korrekt funktionieren). Zusätzliche Header-Verzeichnisse lassen sich über `--include-dir` einbinden. Die Sortierung stellt `.h`/`.hpp`-Header vor `.c`/`.cpp`/`.ino`-Implementierungsdateien; Build- und Testverzeichnisse (`.git`, `.pio`, `.venv`, `__pycache__`, `build`, `test`, `tests`, `venv`) werden ausschließlich über die *relativen* Pfadbestandteile ausgeschlossen, damit Tests innerhalb von `tests/scenarios/...` weiterhin funktionieren.

**2. Kollisionssichere Schlüsselvergabe (`_record_definition`).** Jede erkannte Top-Level-Pin-Konstante wird als `_PinDefinition` mit Dateipfad und 1-basierter Zeilennummer gespeichert (Listing 6.3). Gleiche Werte desselben Bezeichners über mehrere Dateien werden dedupliziert; widersprüchliche Redefinitionen erhalten über `_reserve_unique_key()` garantiert global eindeutige Schlüssel (`NAME (datei.cpp)`, bei Mehrfachkonflikten zusätzlich ` #2`, ` #3`, …). Selbst dreifache `#ifdef`/`#elif`/`#else`-Zweige innerhalb derselben Datei oder ein nutzerdefinierter Bezeichner `GPIO_12` neben `pinMode(12, OUTPUT)` können im Solver keine Schlüsselkollision verursachen (INV-03).

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

**3. Tree-Sitter-Durchlauf und positionsgenaue API-Auswertung (`_scan_files`, `_pin_args_for_call`).** Die kompilierte Grammatik `CPP_LANGUAGE = Language(tscpp.language())` ist unveränderlich und wird einmalig auf Modulebene geladen; jeder Aufruf von `_scan_files()` erzeugt eine eigene `Parser(CPP_LANGUAGE)`-Instanz (Thread-Sicherheit). `_text()` dekodiert Knotenbytes mit `errors="replace"`, damit Nicht-UTF-8-Kommentare (z. B. Windows-1252-Umlaute) keinen Abbruch bewirken. Bei der Deklarationsextraktion überspringt `_walk(..., skip_functions=True)` Knoten vom Typ `function_definition` und `compound_statement`, wodurch lokale Variablen ausgeschlossen bleiben; Klassen- und Strukturmitglieder sind in `tree-sitter-cpp` als `field_declaration` (nicht `declaration`) typisiert und bleiben ebenfalls automatisch unberührt. Zugleich erfasst `_declaration_constants()` auch qualifizierte Deklarationen wie `constexpr int` oder `static const uint8_t`, da Qualifizierer Geschwisterknoten des `type`-Felds sind. `_parse_uint()` bereinigt Inline-Kommentare im unzerlegten `preproc_arg`, äußere Klammerpaare (`#define LED (12)`) sowie ganzzahlige Suffixe (`12u`, `12UL`).

In `_extract_calls()` werden die Argumente einer `call_expression` über `[c for c in args_node.named_children if c.type != "comment"]` gewonnen. Das explizite Herausfiltern von `comment`-Knoten ist für Tree-Sitter-Grammatiken wesentlich, da Kommentare als benannte `extras` innerhalb von `named_children` auftauchen und ohne Filterung die Positionsindizes verschieben würden (z. B. bei `Wire.begin(/* sda */ 6, 7)`). Anschließend wertet `_pin_args_for_call()` gezielt die ESP32-Arduino-Signaturen aus (Listing 6.4, Tabelle 6.3), die dank der GPIO-Matrix explizite Pin-Remapping-Parameter akzeptieren – darunter beide Generationen der ESP32-LEDC-PWM-API (`ledcAttachPin` aus Arduino-ESP32 v2.x und `ledcAttach` aus v3.x) sowie mehrparametrige `Wire*`, `SPI*`- und `Serial*`-Aufrufe. Nicht-Pin-Argumente wie Baudraten (`Serial.begin(115200)`), 1-Argument-I2C-Slave-Adressen (`Wire.begin(0x42)`) oder PWM-Tastgrade (`analogWrite(pin, 128)`) werden ausgeschlossen; ebenso werden negative Sentinel-Werte für ungenutzte SPI-Leitungen (z. B. `-1` in `SPI.begin(18, -1, 23, 5)`) in `tree-sitter-cpp` als `unary_expression` statt `number_literal` geparst und daher ohne Fehlalarm ignoriert. Jeder teilbaren Bus-Leitung wird eine eindeutige **`bus_group`** zugewiesen (`Wire:sda`, `Wire:scl`, `Wire1:sda`, `SPI:sck`, `SPI:miso`, `SPI:mosi`), während das vierte `SPI.begin`-Argument (Chip-Select `CS`/`SS`) als exklusives `gpio` ohne `bus_group` klassifiziert wird.

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

| Funktionsmuster im CST | Ausgewertete Argumente | Fähigkeit | `bus_group` |
| :--- | :--- | :---: | :---: |
| `pinMode`, `digitalWrite`, `digitalRead`, `digitalPinToInterrupt`, `pulseIn`, `tone`, `noTone` | `args[0]` | `gpio` | `None` |
| `analogRead`, `analogReadMilliVolts` | `args[0]` | `adc` | `None` |
| `analogWrite`, `ledcAttach` (v3), `ledcAttachPin` (v2) | `args[0]` | `pwm` | `None` |
| `Wire*.begin`, `Wire*.setPins` (ab 2 Arg.) | `args[0]`, `args[1]` | `i2c` | `<Bus>:sda`, `<Bus>:scl` |
| `SPI*.begin` | `args[0..2]` / `args[3]` | `spi` / `gpio` | `<Bus>:sck/miso/mosi` / `None` |
| `Serial*.begin` (ab 3 Arg.) | `args[2..3]` | `uart` | `None` |

*Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen.*

**4. Fähigkeitsmengen, Namens-Fallback und direkte Pin-Literale (`_build_pin_requests`).** Alle an einer Konstante beobachteten Fähigkeiten werden vereinigt (`frozenset[str]`), sodass Mehrfachrollen wie `{"adc", "i2c"}` vollständig erhalten bleiben. Wird eine Konstante in widersprüchlichen Bus-Rollen verwendet (z. B. sowohl als `Wire:sda` als auch als `Wire:scl`), markiert `_capabilities_and_bus_for()` sie über `mixed:<key>` als nicht teilbar. Konstanten ohne erkannten Pin-Aufruf werden über `_infer_from_name()` geprüft: Der Zerleger trennt `SNAKE_CASE` und `camelCase` (`OLED_SDA_PIN`, `oledSdaPin`), verwirft Nicht-Pin-Endungen (`NON_PIN_SUFFIXES` wie `BAUD`, `DELAY`, `ADDR`, `COUNT`, `MS`, `FREQ`) und betrachtet vor einem nachgestellten `PIN`/`GPIO` das eigentliche Rollenwort (`SDA`, `SCL`, `MOSI`, `MISO`, `SCK`, `RX`, `TX`, `CS`).

Direkte Zahlenliterale (`pinMode(12, OUTPUT)`, `analogRead(5)`, `Wire.begin(6, 6)`) verarbeitet `_merge_or_append_literal_uses()`: Gehört derselbe Pin mit identischer `bus_group` bereits einer benannten Konstante (z. B. `const int STATUS_LED = 6; analogRead(6);`), werden die zusätzlichen Fähigkeiten ohne Fehl-Duplikat auf diese Konstante zusammengeführt; andernfalls entsteht ein eindeutig benannter Eintrag (`GPIO_12`, bei unterschiedlichem Bus-Kontext `GPIO_6 (Wire:scl)`). Gemäß INV-02 arbeitet kein regulärer Ausdruck auf dem C++-Rohtext; sämtliche fünf kompilierten Muster sowie die lokale Whitespace-Normalisierung in `_extract_calls()` verarbeiten ausschließlich zuvor aus dem CST isolierte Kurzzeichenketten (Tabelle 6.4).

| Regulärer Ausdruck in `parser.py` | Isolierte CST-Eingabe | Zweck |
| :--- | :--- | :--- |
| `WIRE_CALL_RE`: `^(Wire\d*)\.(?:begin\|setPins)$` | Funktionsname `fn_name` | erkennt `Wire`, `Wire1`, … und extrahiert den Busnamen |
| `SPI_CALL_RE`: `^(SPI\d*)\.begin$` | Funktionsname `fn_name` | erkennt `SPI`, `SPI1`, … und extrahiert den Busnamen |
| `SERIAL_CALL_RE`: `^Serial\d*\.begin$` | Funktionsname `fn_name` | erkennt Hardware-UART-Aufrufe mit `rxPin`/`txPin` |
| `COMMENT_RE`: `//.*\|/\*.*?\*/` | `preproc_arg` eines `#define` | entfernt Zeilen- und Blockkommentare hinter Zahlenwerten |
| `WORD_RE`: `[A-Z]+(?=[A-Z][a-z]\|_|\d\|$)\|[A-Z]?[a-z]+\|\d+` | Bezeichner `name` | zerlegt `SNAKE_CASE` und `camelCase` für `_infer_from_name()` |
| Inline `re.sub(r"\s+", "", ...)` | `function`-Knoten in `_extract_calls()` | normalisiert Leerzeichen wie `WiFi . begin` vor dem Abgleich |

*Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`).*

### 6.4 Regelprüfer, Strapping-Warnungen und MaxSMT-Solver (`solver.py`)

Die Funktion `validate(project, board)` in `mcu_validator/solver.py` sichert zunächst eindeutige Signalnamen (`_ensure_unique_request_names`) und arbeitet dann zweistufig – im aktuellen Arbeitsstand ergänzt um die gezielte Auswertung nicht-blockierender Strapping-Warnungen (Abbildung 6.1).

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
  ┌─────────────────────────────┐   ┌─────────────────────────────────────┐
  │ _find_strapping_warnings()  │   │ Stufe 2: Z3 Optimize (PW-MaxSMT)    │
  │ auf Originalpins p_i^0      │   │ berechnet minimale Ersatzbelegung   │
  │ (Z3 wird nicht gestartet)   │   └─────────────────┬───────────────────┘
  └─────────────┬───────────────┘                     ▼
                │                   ┌─────────────────────────────────────┐
                │                   │ _find_strapping_warnings() auf      │
                │                   │ Zielbelegung (bzw. p_i^0 bei UNSAT) │
                ▼                   └─────────────────┬───────────────────┘
  ValidationResult(SAT, warnings)                     ▼
                                    ValidationResult(UNSAT, repair, warnings)
```
*Abbildung 6.1: Zweistufiger Ablauf inklusive nicht-blockierender Strapping-Warnungen in `validate()` (`mcu_validator/solver.py`).*

In Stufe 1 prüft `_check_capabilities()` jede geforderte Fähigkeit $c \in C_i$ einzeln über Mengenoperationen (`matching = board.expand_capability(c) & pin_caps`). Sind sämtliche passenden Wandlerbanken gesperrt (`matching <= forbidden_caps.keys()`), wird direkt der `reason`-Text der sperrenden Regel gemeldet.

**Nicht-blockierende Strapping-Warnungen (Arbeitsstand-Erweiterung).** Im Release `v0.2.0` wirkte das Attribut `strapping: true` ausschließlich als weiche Bedingung in Stufe 2, sodass konfliktfreie Programme auf einem Strapping-Pin (etwa `STATUS_LED = 8` in `src/main.cpp`) ohne Hinweis passierten. Die Erweiterung in `solver.py` ergänzt `ValidationResult` um das Feld `warnings: tuple[str, ...] = ()` sowie die Hilfsfunktion `_find_strapping_warnings(requests, board, restrictions, assigned_pins=None)`:

- Im **`SAT`-Fall** (`assigned_pins=None`) prüft die Funktion sämtliche Originalpins $p_i^0$ gegen `spec.strapping` (unter Ausschluss reservierter oder gesperrter Pins) und erzeugt eine nicht-blockierende Warnung samt `datei:zeile`-Verweis und Pin-Notiz.
- Im **`UNSAT`-Fall** wird die Funktion auf der **berechneten Z3-Zielbelegung** (`assigned_pins=suggested`) ausgeführt (nur bei `repair_possible=False` erfolgt der Rückfall auf $p_i^0$). Diese gezielte Wahl vermeidet veraltete Doppelmeldungen, wenn Z3 ein fehlerhaftes Signal ohnehin von einem Strapping-Pin wegverschiebt (z. B. `BAD_ADC = 8` $\rightarrow$ `ADC1`), warnt aber sowohl dann, wenn ein gültiger Strapping-Pin bewusst beibehalten wird (`STATUS_LED = 8`), als auch dann, wenn Z3 mangels Alternativen gezwungen ist, ein Signal auf einen Strapping-Pin zu legen – in diesem Fall explizit markiert als `suggested GPIO 2` (z. B. beim fünften `ADC1`-Sensor unter aktivem WLAN).

**Aufbau des Partial-Weighted-MaxSMT-Modells.** Erkennt Stufe 1 mindestens einen harten Konflikt, konstruiert `_solve_reassignment()` die Z3-Instanz (Listing 6.5). Jede Anforderung $r_i$ erhält eine über ihren Index erzeugte Ganzzahlvariable `Int(f"pin_{idx}")` (Typ `z3.ArithRef`). Ist die Kandidatenmenge $P_i$ für ein Signal leer, bricht der Solver sofort mit `None` (`repair_possible=False`) ab – der fehleranfällige Sentinel `var == -1` des Prototyps `v0.1.0` existiert nicht mehr.

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

Formal lautet das Partial-Weighted-MaxSMT-Modell für $n$ Anforderungen $r_i$ ($i \in \{1, \dots, n\}$) mit Fähigkeitsmenge $C_i$ und Bus-Leitungsrolle $b_i$:

$$P_i = \Big\{\, p \in \mathcal{P} \;\Big|\; \neg\text{reserved}(p) \;\land\; p \notin \text{ForbiddenPins} \;\land\; \forall c \in C_i:\; \big(\text{caps}(p) \cap (A(c) \setminus \text{ForbiddenCaps})\big) \neq \emptyset \,\Big\}$$

1. **Domänenbindung (hart):** Existiert ein $i$ mit $P_i = \emptyset$, ist keine Reparatur möglich (`repair_possible=False`). Andernfalls gilt $\bigvee_{p \in P_i} (v_i = p)$.
2. **Paarweise Bus-Leitungskopplung (hart, INV-04):** Zwei Signale dürfen genau dann denselben Pin teilen (`_can_share_bus`), wenn sie dieselbe einzelne teilbare Bus-Fähigkeit *und* dieselbe Bus-Leitungsrolle besitzen:
   $$\text{share}(r_i, r_j) \iff C_i = C_j \land |C_i| = 1 \land C_i \subseteq \text{shared\_capabilities} \land b_i = b_j.$$
   Für alle $\binom{n}{2}$ Paare $1 \le i < j \le n$ gilt damit:
   $$v_i = v_j \quad \text{falls } \text{share}(r_i, r_j) \land p_i^0 = p_j^0, \qquad \text{sonst } v_i \neq v_j.$$
3. **Dreistufige Zielfunktion (weich, INV-05):** Sei $S_i = P_i \cap S$ die Menge der zulässigen Strapping-Pins und
   $$K_i = \Big\{\, p \in P_i \;\Big|\; \text{caps}(p) \cap \Big(\text{SCARCE\_CAPABILITIES} \setminus \bigcup_{c \in C_i} A(c)\Big) \neq \emptyset \,\Big\}$$
   die Menge der Pins mit knappen, von $r_i$ selbst nicht benötigten Spezialfähigkeiten (auf dem ESP32-S3 bei inaktivem USB zieht ein reiner ADC-Sensor folglich nicht-USB-ADC-Pins den doppelt belegten Pins GPIO 19/20 vor). Z3 maximiert:
   $$\max \sum_{i=1}^{n} \Big( 1000 \cdot \mathbb{I}[p_i^0 \in P_i \land v_i = p_i^0] \;+\; 20 \cdot \mathbb{I}[\emptyset \subset S_i \subset P_i \land v_i \notin S_i] \;+\; 5 \cdot \mathbb{I}[\emptyset \subset K_i \subset P_i \land v_i \notin K_i] \Big).$$

**Mathematische Analyse der Gewichtungsdominanz.** Die Bedingung $\emptyset \subset S_i \subset P_i$ bzw. $\emptyset \subset K_i \subset P_i$ verhindert die Erzeugung trivialer oder prinzipiell unerfüllbarer weicher Klauseln (wenn etwa alle Kandidaten in $P_i$ Strapping- oder ADC-Pins sind). Hinsichtlich der Rangfolge der Gewichte (`1000`, `20`, `5`) ist präzise zwischen **lokaler** und **globaler** Dominanz zu unterscheiden:

- Für jedes **einzelne Signal** gilt streng $1000 \gg 20 > 5$.
- **Global über $n$ Signale** summieren sich die Stufen 2 und 3 auf höchstens $25n$ Punkte; damit dominiert Stufe 1 (`1000`) garantiert global für alle Konfigurationen mit $25n < 1000 \iff n \le 39$ (was den ESP32-C3 vollständig und praktisch alle ESP32-S3-Schaltungen abdeckt).
- Zwischen **Stufe 2 (`20`) und Stufe 3 (`5`)** gilt hingegen $20 / 5 = 4$: In einer konstruierten, stark gekoppelten Situation könnte das Inkaufnehmen eines einzelnen Strapping-Pins (`-20`) theoretisch von fünf gleichzeitig freigegebenen knappen Pins (`+25`) aufgewogen werden. Soll eine strikt $n$-unabhängige lexikografische Dominanz erzwungen werden, unterstützt Z3 $\nu Z$ hierfür nativ mehrkriterielle lexikografische Optimierung (`opt.set(priority='lex')` mit benannten Zielgruppen `id="keep"`, `id="strapping"`, `id="scarce"`) [[3]](#ref-3). In `v0.2.0` wurde bewusst die kompakte Einzelzielsumme gewählt, die einen einzelnen MaxRes-Durchlauf benötigt und zugleich als Basis für eine spätere Erweiterung dient (Abschnitt 8.4). Die Fähigkeitsklasse `SCARCE_CAPABILITIES` ist als generische, pin-freie Heuristikkonstante formuliert und berührt INV-01 bezüglich konkreter Chip-Pin-Nummern nicht; für Mikrocontroller mit weiteren knappen Funktionsgruppen (z. B. DAC oder kapazitive Touch-Kanäle) lässt sie sich perspektivisch ins Board-JSON auslagern.

### 6.5 Prioritätsverhalten bei gegenseitiger Pin-Blockade

Konkurrieren mehrere Signale um denselben Pin, entscheidet ausschließlich die Zielfunktion aus Abschnitt 6.4 ohne fest codierte Namensprioritäten:

1. **Fall 1 – Symmetrische Einzelsignale (Gleichstand).** Liegen `BUZZER_PIN = 7` und `SERVO_PIN = 7` (beide `gpio`) auf demselben Pin, erreichen beide symmetrischen Reparaturen dieselbe optimale Punktzahl ($1000 + 40 + 10 = 1050$). Bei mehreren global optimalen Modellen hängt die Wahl des konkreten Modells von internen Heuristiken des Solvers ab (CDCL-Phase-Saving, Variablenreihenfolge im Simplex-Kern und Reihenfolge der MaxRes-Kerne) – die Experimente `c` und `c2` (Abschnitt 7.4) belegen, dass **nicht** die Deklarationsreihenfolge im C++-Code maßgeblich ist (in beiden Reihenfolgen blieb `SERVO_PIN` auf GPIO 7, während `BUZZER_PIN` auswich). Für identische Eingaben und eine feste Z3-Version bleibt das Ergebnis reproduzierbar.
2. **Fall 2 – Geteilter Bus gegen einzelnes Störsignal („Bus-Trägheit“).** In Szenario 04 sind `OLED_SDA = 6` und `BME280_SDA = 6` über `Wire:sda` gekoppelt ($v_{\text{OLED\_SDA}} = v_{\text{BME280\_SDA}}$) und vereinen $2 \times 1000 = 2000$ Haltepunkte gegenüber nur `1000` Punkten für `STATUS_LED = 6`. Tabelle 6.5 zeigt diese rechnerische Bus-Trägheit: Alle vier I2C-Signale verbleiben unverändert auf GPIO 6/7, und ausschließlich die LED wechselt auf den freien Standard-GPIO 20.

| Variante in Szenario 04 (`v0.2.0`) | Haltepunkte | Strapping-Meidung | Knappe Pins geschont | Summe | Ergebnis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **A (Z3-Lösung):** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 20 | $4 \times 1000 = 4000$ | $5 \times 20 = 100$ | $5 \times 5 = 25$ | **4125** | **optimal** |
| **B:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 1 (`ADC1`) | $4000$ | $100$ | $4 \times 5 + 0 = 20$ | 4120 | verworfen |
| **C:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 2 (Strapping + `ADC1`) | $4000$ | $4 \times 20 = 80$ | $20$ | 4100 | verworfen |
| **D:** `STATUS_LED` bleibt auf 6, SDA-Paar $\rightarrow$ 20 | $3 \times 1000 = 3000$ | $100$ | $25$ | 3125 | verworfen |

*Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`).*

3. **Fall 3 – Spezialist gegen Allrounder.** Kollidieren bei aktivem WLAN ein Analogsensor (`SOIL_SENSOR = 1`, benötigt `adc1`) und eine LED (`STATUS_LED = 1`, `gpio`) bei bereits belegten `ADC1`-Pins 0, 3 und 4, bliebe dem Sensor nur noch der Strapping-Pin GPIO 2. Weicht stattdessen die LED auf den Standard-GPIO 7 aus, gewinnt diese Variante exakt **25 Punkte** (`+20` Strapping-Meidung für den Sensor plus `+5` Schonung des `ADC1`-Pins für die LED). Die Experimente `f` und `f2` bestätigen diese Entscheidung unabhängig von der Deklarationsreihenfolge.

### 6.6 Bericht, CLI und Reparatur-Prompt (`cli.py`)

Das Modul `mcu_validator/cli.py` stellt über `argparse` die Kommandozeilenschnittstelle `mcu-validate` (sowie `python -m mcu_validator.cli`) mit drei sauber getrennten Exit-Codes bereit: `0` (`SAT`, auch bei rein nicht-blockierenden Warnungen), `1` (`UNSAT`, blockierender Hardware-Konflikt) und `2` (Eingabe-, Board- oder JSON-Schemafehler auf `stderr` ohne Python-Stacktrace).

Über `--list-boards`, `--boards-dir`, `--include-dir` (wiederholbar) und `--version` lässt sich das Werkzeug flexibel in Skripte und CI-Pipelines einbinden. Der Berichtskopf nennt stets `Checked Pins : N (...)` und gibt bei `0` erkannten Pins eine explizite Warnung aus, um trügerische Sicherheit bei nicht abgedeckter C++-Syntax zu vermeiden. In der Arbeitsstand-Erweiterung ergänzt `_format_warning_section()` den Abschnitt `Warnings (non-blocking):` sowohl bei `SAT` (Listing 6.6 am realen Demo-Projekt `src/main.cpp` mit `STATUS_LED = 8`) als auch bei `UNSAT`, falls die finale Belegung einen Strapping-Pin nutzt. Im `UNSAT`-Fall folgen sämtliche Einzelkonflikte mit `datei:zeile`-Verweis sowie die vollständige `Keep`/`Change`-Anweisung (oder ein expliziter Kapazitätshinweis bei `repair_possible=False`). Gemäß INV-06 importiert `mcu_validator/__init__.py` bewusst nicht `.cli`, sodass `python -W error -m mcu_validator.cli` ohne `runpy`-`RuntimeWarning` ausführt.

```text
=================================================================
 Target         : src/main.cpp (ESP32-C3)
 Active Modules : wifi, usb_serial
 Checked Pins   : 3 (STATUS_LED=8, SOIL_SENSOR=1, RELAY_PIN=4)
=================================================================
 RESULT: SAT (All pins valid, with 1 hardware warning.)

Warnings (non-blocking):
  - STATUS_LED (GPIO 8, main.cpp:6): Strapping pin (ROM log / boot). External pull-up/down circuitry may affect boot behavior.
```
*Listing 6.6: Nicht-blockierende Strapping-Warnung auf `src/main.cpp` (Arbeitsstand, Rückgabewert 0).*

### 6.7 Integration in PlatformIO und Paketierung (`pio_hook.py`, `library.json`, `pyproject.toml`)

`mcu-pin-solver` wird dual als Python-Paket (`pip install .`) sowie über die öffentliche PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) bereitgestellt. Listing 6.7 zeigt die Kernlogik von `pio_hook.py` und die Paketkonfiguration in `library.json`.

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
*Listing 6.7: Kern des PlatformIO-Hooks (`pio_hook.py`) und der Paketkonfiguration (`library.json`).*

Sechs technische Härtungen sichern den produktiven Betrieb ab: (1) robuste Pfadermittlung über `inspect.getfile(inspect.currentframe())`, da SCons das Skript via `exec()` ohne garantiertes `__file__` lädt; (2) Bevorzugung des Windows-`py`-Launchers, um PlatformIOs privates `penv` nicht zu verunreinigen, kombiniert mit expliziter `PYTHONPATH`-Übergabe auf das Hook-Verzeichnis; (3) Übergabe von `$PROJECT_INCLUDE_DIR` per `--include-dir`; (4) versionsbeschränkte Paketprüfung (`tree-sitter>=0.23.0` wegen der PyCapsule-`Language`-API) inklusive klarer Fehlerhilfe für Offline-Umgebungen oder PEP-668-geschützte System-Pythons; (5) klare Trennung von Exit-Code `1` (Pin-Konflikt) und `2` (Konfigurationsfehler) sowie Schutz gegen SCons-Doppelausführung über `_MCU_VALIDATOR_RAN`; (6) saubere Isolation des Demo-Codes (`"srcFilter": ["-<*>"]`) und Bündelung der Board-Profile via `package-data` in `pyproject.toml`.

> **Zwischenfazit Kapitel 6:** Die Implementierung verbindet eine top-down gegliederte Vierschicht-Architektur mit strenger Schema-Validierung, präziser CST-Bus-Rollenerkennung, nicht-blockierenden Strapping-Warnungen, einem klar formalisierten Partial-Weighted-MaxSMT-Modell und gehärteter Dual-Paketierung für Python und PlatformIO.

---

## 7 Evaluation

Dieses Kapitel evaluiert `mcu-pin-solver` entlang von fünf Säulen: (1) der automatisierten Testsuite samt plattformübergreifender CI-Matrix, (2) zwölf Grenzfallklassen im direkten Vergleich zwischen Prototyp `v0.1.0` und Stand `v0.2.0`, (3) Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, (4) einem realen End-to-End-Build-Test über die PlatformIO Registry sowie (5) einer modellhaften Wirtschaftlichkeits- und Break-even-Betrachtung.

### 7.1 Evaluationsdesign und Messumgebung

Die Testsuite verteilt sich auf fünf modulare Dateien (`tests/test_board.py`, `test_parser.py`, `test_solver.py`, `test_cli.py`, `test_scenarios.py`). In sämtlichen `UNSAT`-End-to-End-Szenarien wendet der Test zusätzlich die von Z3 berechneten Ersatzpins auf das `ParsedProject` an und validiert dieses erneut (`_revalidate_suggestion`) – damit wird die relative Korrektheit jeder Reparatur (NFA-04) automatisiert verifiziert.

Sämtliche Laufzeit- und Skalierungsmessungen sowie die GitHub-Actions-CI-Durchläufe wurden auf dem freigegebenen Release **`v0.2.0`** (42 Tests) in der in Tabelle 7.1 dokumentierten Umgebung erhoben (Mediane über $N = 10$ Subprozess-Läufe bzw. $M = 30$ In-Process-Läufe; Skalierungstest $M = 15$). Die anschließende Arbeitsstand-Erweiterung um nicht-blockierende Strapping-Warnungen ergänzt einen einzelnen linearen $O(n)$-Wörterbuchdurchlauf über `board.pins` (`< 0,05 ms`) und wurde lokal mit allen **47 Tests** verifiziert.

| Komponente | Spezifikation |
| :--- | :--- |
| Prozessor / Betriebssystem (lokal) | AMD Ryzen 9 3900X 12-Core Processor, Microsoft Windows 10 Pro |
| Python-Version (lokal) | Python `3.14.7` |
| Solver und Parser | `z3-solver` `5.4.1.0`, `tree-sitter` `0.26.1`, `tree-sitter-cpp` `0.23.4` |
| PlatformIO Core (lokal) | PlatformIO Core `6.2.0` (Espressif32 `6.12.0`, Arduino-Framework) |
| CI-Umgebung (GitHub Actions, `v0.2.0`) | `ubuntu-latest` & `windows-latest`, Python `3.10` & `3.12`, plus `ruff` & `mypy` |

*Tabelle 7.1: Messumgebung (`v0.2.0`).*

### 7.2 Automatisierte Testsuite und Regressionsszenarien

Im Release `v0.2.0` bestand `python -m unittest discover -s tests -v` sämtliche **42 Tests** lokal in ca. 3,4 s sowie in allen fünf Jobs der GitHub-Actions-CI (`lint` mit `ruff` & `mypy`, `ubuntu-latest` 3.10/3.12, `windows-latest` 3.10/3.12). Im aktuellen Arbeitsstand bestehen alle **47 Tests** lokal in 3,73 s:

- **`test_board.py` (12 Tests):** Konsistenz aller mitgelieferten Board-JSONs, Präfix-Sortierung, Unterstrich-Normalisierung, direkte `.json`-Pfade sowie sieben Schema-Negativtests (u. a. Strings statt Listen, `bool` in `forbidden_pins`, unbekannte Auslöser).
- **`test_parser.py` (11 Tests):** Ausschluss von Nicht-Pin-Konstanten & lokalen Variablen, `(12)` & `12u`, Latin-1-Kommentare, direkte Pin-Literale inkl. Fähigkeits-Merge, 3-Wege-`#ifdef`-Schlüssel, `GPIO_12`-Kollisionsschutz, Namens-Fallback (`OLED_SDA_PIN`, `oledSdaPin`, `SPI_MOSI_PIN`), `Serial1`, dateiübergreifende Konflikte und `--include-dir`.
- **`test_solver.py` (8 Tests in `v0.2.0`; 11 Tests im Arbeitsstand):** `SDA == SCL` (benannt und literal), `Wire` vs. `Wire1`, SPI-`CS` & `SCK == MOSI`, Schonung knapper ADC-Pins, Überbuchung (`repair_possible=False`), leeres Projekt, Schutz gegen doppelte Signalnamen sowie **+3 Tests** für nicht-blockierende Strapping-Warnungen (`SAT` mit/ohne Strapping-Pin, Beibehaltung, erzwungene Z3-Ausweichbelegung `suggested GPIO 2` und Wegfall veralteter Warnungen nach Umlegung).
- **`test_cli.py` (7 Tests in `v0.2.0`; 9 Tests im Arbeitsstand):** `--list-boards`, `--version`, `--boards-dir`, Warnungsfreiheit (`python -W error`), Exit-Code `2` ohne Stacktrace bei unbekanntem Board bzw. fehlerhafter JSON, 0-Pin-Warnung sowie **+2 CLI-Tests** für Ausgabe und Weglassen von `Warnings (non-blocking):` bei Exit-Code `0`.
- **`test_scenarios.py` (4 Testmethoden über 9 End-to-End-Konstellationen):** Alle neun Regressionsszenarien (Tabelle 7.2) inklusive automatischer Re-Validierung sämtlicher Z3-Vorschläge.

| Nr. | Zielpfad | Board | Erwartet & Gemessen | Geprüfter Sachverhalt |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `src/main.cpp` | `esp32-c3` | SAT *(Arbeitsstand: +1 Strapping-Warnung)* | Demo-Sketch (`STATUS_LED=8`, `SOIL_SENSOR=1`, `RELAY_PIN=4`, `WiFi.softAP`, `Serial.begin`) |
| 2 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1 & 2: Flash-Pin 12 und `ADC2` (Pin 5) bei aktivem WLAN |
| 3 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | Identischer Code auf ESP32-S3 gültig (Pin 12 regulär, Pin 5 in `ADC1`) |
| 4 | `tests/scenarios/01_valid_sketch.cpp` | `esp32-c3` | SAT | Positivkontrolle: fehlerfreier Sketch ohne Strapping-Pins mit WLAN & USB-Serial |
| 5 | `tests/scenarios/02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 2: `Serial.begin` sperrt USB-Pins 18 und 19 |
| 6 | `tests/scenarios/03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1, 3, 4: Doppelbelegung (7), Geister-Pin (32), fehlendes ADC (6) |
| 7 | `tests/scenarios/04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 4: I2C-Bus auf 6/7 bleibt gekoppelt erhalten, LED weicht aus |
| 8 | `tests/scenarios/05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | CST ignoriert `WiFi.begin(...)` in Kommentar und Zeichenkette |
| 9 | `tests/scenarios/06_multi_file_project/src` | `esp32-c3` | UNSAT | Mehrere Dateien: `include/pins.h` + `src/main.cpp` + `src/sensors.cpp` |

*Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien.*

### 7.3 Ausgewählte Szenarien im Detail

Szenario 0 wurde bereits in Abschnitt 5.6 behandelt, und das Demo-Projekt `src/main.cpp` (Szenario 1, inklusive der nicht-blockierenden Strapping-Warnung auf GPIO 8 im Arbeitsstand) ist in Listing 6.6 dargestellt. Die Listings 7.1 bis 7.5 dokumentieren die realen CLI-Ausgaben für die Szenarien 02 bis 06 (in sämtlichen dieser Szenarien treten keine Strapping-Warnungen auf, sodass die Ausgaben zwischen `v0.2.0` und dem aktuellen Arbeitsstand bitidentisch sind).

In **Szenario 02** (Listing 7.1) sperrt `Serial.begin(115200)` die USB-Pins 18 und 19. `ENABLE_PIN` (GPIO 6) bleibt unangetastet; dank Stufe 3 weichen `STEP_PIN` und `DIR_PIN` auf die regulären GPIOs 21 und 10 aus, statt knappe `ADC1`-Pins zu belegen.

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

In **Szenario 03** (Listing 7.2) erkennt Stufe 1 alle drei Fehler in einem Durchlauf mit Dateizeilen-Verweis. `POTI_PIN` wechselt auf `ADC1` (GPIO 0), `PIR_SENSOR` auf GPIO 10 und `BUZZER_PIN` auf den durch `POTI_PIN` frei gewordenen GPIO 6.

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

**Szenario 04** (Listing 7.3) demonstriert die Bus-Trägheit aus Abschnitt 6.5: Alle vier gekoppelten I2C-Signale verbleiben unverändert auf GPIO 6/7, und ausschließlich `STATUS_LED` wechselt auf den regulären GPIO 20.

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

**Szenario 05** (Listing 7.4) bestätigt die Immunität der CST-Analyse gegenüber auskommentierten oder in Zeichenketten zitierten Modul-Aufrufen (`Active Modules : none`, `SAT`).

```text
=================================================================
 Target         : tests/scenarios/05_ast_ignores_strings_and_comments.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 1 (SOIL_SENSOR=5)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 7.4: CLI-Ausgabe für Szenario 05 (`v0.2.0`, Rückgabewert 0).*

**Szenario 06** (Listing 7.5) wertet `include/pins.h`, `src/main.cpp` und `src/sensors.cpp` projektweit zusammen aus, ordnet beide Konflikte präzise den Zeilen `pins.h:4` und `pins.h:5` zu und verlegt `STATUS_LED` auf den freien Standard-GPIO 10, ohne den knappen USB-Pin GPIO 18 zu verbrauchen.

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

Tabelle 7.3 dokumentiert **zwölf Grenzfallklassen** (entsprechend 14 Einzelkonfigurationen bzw. 15 Prüfläufen im Versuchsskript `experiments.py` in Anhang G: 13 C++-Testfälle plus zwei programmatische Leerdomänen-Varianten unter `e`; Buchstabe `g` wurde in der historischen Versuchsnummerierung übersprungen) auf dem `esp32-c3`-Profil und stellt Prototyp `v0.1.0` unmittelbar dem Stand `v0.2.0` gegenüber. Neun in `v0.1.0` identifizierte Defekte wurden vollständig behoben; die beiden bewusst verbleibenden semantischen Grenzen (`i` bei `gpio_num_t` und `j` bei `#ifdef`) werden in Abschnitt 8.2 eingeordnet.

| ID | Getestete Grenzfallklasse | Verhalten in `v0.1.0` | Gemessenes Verhalten in `v0.2.0` | Bewertung (`v0.2.0`) |
| :---: | :--- | :--- | :--- | :--- |
| `a` | Direkte Literale (`pinMode(12, OUTPUT); analogRead(5);`) + `WiFi` | `SAT` (**False Negative**) | `UNSAT`: `GPIO_12 -> 10`, `GPIO_5 -> 0` | **behoben** |
| `b` | Lokale Zähler (`blinkCount`, `retries`) & `BAUD_RATE 115200` | `UNSAT` (**False Positive**) | Nur `STATUS_LED = 3` geprüft $\rightarrow$ `SAT` | **behoben** |
| `c`, `c2` | Gleichstand `BUZZER_PIN = 7` / `SERVO_PIN = 7` (beide Reihenfolgen) | `BUZZER_PIN` blieb (Z3-Heuristik) | `SERVO_PIN` bleibt in beiden Fällen (`BUZZER -> 20` bzw. `6`) | Gleichstand weiterhin solverabhängig |
| `d` | 6 Analogsensoren `S0..S5` + WLAN (nur 5 `ADC1`-Pins vorhanden) | `GPIO None` für alle 6 Signale | `repair_possible=False`, klare Kapazitätsmeldung (Listing 7.6) | **behoben** |
| `e` | Synthetische Fähigkeit `'can'` ($P_i = \emptyset$, 1 bzw. 2 Signale) | `CAN_TX: -1` bzw. `-1 != -1`-Bruch | Sofort konsistent `repair_possible=False`, `suggested={}` | **behoben** |
| `f`, `f2` | `SOIL_SENSOR = 1` (`adc`) vs. `STATUS_LED = 1` (`gpio`), beide Reihenfolgen | `SOIL_SENSOR = 1`, `LED -> 7` | In beiden Fällen `SOIL_SENSOR = 1`, `STATUS_LED -> 7` (+25 Pkt.) | Spezialist-Priorität bestätigt |
| `h` | Doppelrolle: `Wire.begin(MY_PIN, MY_SCL)` + `analogRead(MY_PIN)` | Nur `'adc'`; Vorschlag ohne I2C | `capabilities={'adc', 'i2c'}` $\rightarrow$ `MY_PIN -> 0` (`ADC1` & `I2C`) | **behoben** |
| `i` | `constexpr int LED_A = 12;`, `static const uint8_t LED_B = 13;`, `const gpio_num_t LED_C = GPIO_NUM_14;` | `LED_A`, `LED_B` erkannt; `LED_C` ignoriert | `LED_A -> 7`, `LED_B -> 6`; `gpio_num_t` weiterhin ignoriert | **verbleibende Grenze** (Typ + `identifier`) |
| `j` | `#ifdef USE_EXTERNAL_LED` (Pin 2) / `#else` (Pin 12) | Beide Zweige $\rightarrow$ `UNSAT` | Beide Zweige mit eindeutigen Schlüsseln $\rightarrow$ `UNSAT` (kein Absturz bei 3 Zweigen) | **verbleibende Grenze** (False Positive) |
| `k` | `Wire.begin(SDA_A, SCL_A)` & `Wire1.begin(SDA_B, SCL_B)` auf 6/7 | `SAT` (**False Negative**) | `UNSAT` (`Wire` $\neq$ `Wire1`), 4 getrennte Pins (`6, 20, 10, 7`) | **behoben** *(synthetisch auf C3, s. u.)* |
| `l` | Zwei `SPI.begin`-Aufrufe mit `MISO_P = 7`, `CS_A = 7`, `CS_B = 7` | `SAT` (**False Negative**) | `UNSAT` (`CS` als `gpio`), alle 5 Signale getrennt (`6, 21, 10, 7, 20`) | **behoben** |
| `m` | `OLED_SDA = 6` und `OLED_SCL = 6` in `Wire.begin(OLED_SDA, OLED_SCL)` | `SAT` (**False Negative**) | `UNSAT` (`Wire:sda` $\neq$ `Wire:scl`), `OLED_SDA=6`, `OLED_SCL -> 10` | **behoben** (neu geprüft) |

*Tabelle 7.3: Ergebnisse der zwölf Grenzfallklassen auf `esp32-c3` (`v0.1.0` im Vergleich zu `v0.2.0`).*

Zwei technische Detailbeobachtungen vertiefen Tabelle 7.3: Erstens wird `LED_C` in Experiment `i` aus **zwei** unabhängigen AST-Gründen nicht erfasst – sowohl weil `"gpio_num_t"` nicht in `PIN_VAR_TYPES` steht als auch weil der Initialisierer `GPIO_NUM_14` ein `identifier`- und kein `number_literal`-Knoten ist. Zweitens prüft Experiment `k` die Bus-Instanz-Trennung (`Wire:sda` vs. `Wire1:sda`) synthetisch gegen das Profil `esp32-c3`; physisch verfügt der ESP32-C3 jedoch nur über **einen** Hardware-I2C-Controller (`I2C0`, während erst der ESP32-S3 mit `I2C0` und `I2C1` zwei unabhängige Hardware-I2C-Busse besitzt [[9]](#ref-9), [[10]](#ref-10)). Die Modellierung von Peripherie-Controller-Budgets bildet daher eine konkrete Ausbaudimension (Abschnitt 8.2).

Listing 7.6 dokumentiert die Ausgabe im Überbuchungsfall `d` (`d_pigeonhole_6_adc_wifi.cpp`) im aktuellen Arbeitsstand: Anstelle von `GPIO None` meldet das System unmissverständlich die ausgeschöpfte `ADC1`-Kapazität und weist zugleich nicht-blockierend auf den im Originalcode belegten Strapping-Pin `S4 (GPIO 2)` hin (im reinen Release `v0.2.0` entfällt lediglich der Block `Warnings (non-blocking):`).

```text
=================================================================
 Target         : d_pigeonhole_6_adc_wifi.cpp (ESP32-C3)
 Active Modules : wifi
 Checked Pins   : 6 (S0=0, S1=1, S2=3, S3=4, S4=2, S5=5)
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

Warnings (non-blocking):
  - S4 (GPIO 2, d_pigeonhole_6_adc_wifi.cpp:2): Strapping pin (boot mode). External pull-up/down circuitry may affect boot behavior.

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - S5 (GPIO 5, d_pigeonhole_6_adc_wifi.cpp:2): ADC2 cannot be used while Wi-Fi is active on ESP32-C3.

No valid pin assignment exists on ESP32-C3: the requested pins exceed available hardware capabilities.

-----------------------------------------------------
```
*Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, Arbeitsstand inkl. nicht-blockierender Strapping-Warnung, Rückgabewert 1).*

### 7.5 Laufzeit-, Skalierungsmessung und PlatformIO-End-to-End-Prüfung

**Regressionsszenarien.** Tabelle 7.4 dokumentiert die gemessenen Medianlaufzeiten für alle neun Standardszenarien (`v0.2.0`). Als Basislinie beanspruchte allein der Start des Python-Interpreters samt Import von `z3`, `tree_sitter` und `tree_sitter_cpp` im Median **139 ms**.

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

**Skalierung bis 20 Pins und 21 Dateien.** Da die Standardszenarien lediglich 1 bis 5 Pins umfassen, vermisst ein eigener Skalierungsbenchmark (`scaling_benchmark.py`, Anhang G) synthetische Multi-Datei-Projekte auf dem größeren **ESP32-S3** (45 physische Pins) von 3 bis 20 Signalen – zum einen im `UNSAT`-Fall mit zwei Konflikten (Flash-Pin 26 sowie `ADC2`-Pin 11 bei aktivem WLAN) und zum anderen im konfliktfreien 20-Pin-/21-Datei-`SAT`-Fall (Tabelle 7.5).

| Signale ($n$) | Dateien | Fall | Paarweise Ungleichungen $\binom{n}{2}$ | Parsen ($M=15$) | Lösen ($M=15$) | Summe In-Process |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 3 | 3 | UNSAT (2 Konflikte) | 3 | 1,86 ms | 47,46 ms | 49,32 ms |
| 6 | 6 | UNSAT (2 Konflikte) | 15 | 2,81 ms | 125,42 ms | 128,23 ms |
| 10 | 10 | UNSAT (2 Konflikte) | 45 | 4,12 ms | 299,31 ms | 303,43 ms |
| 15 | 15 | UNSAT (2 Konflikte) | 105 | 5,80 ms | 650,44 ms | 656,25 ms |
| 20 | 20 | UNSAT (2 Konflikte) | 190 | 7,34 ms | 1132,81 ms | 1140,15 ms |
| **20** | **21** | **SAT (konfliktfrei)** | **– (Stufe 1)** | **7,53 ms** | **0,06 ms** | **7,59 ms** |

*Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`).*

Die Messreihe liefert zwei zentrale Erkenntnisse:

1. **Lineares Parsing und Beschleunigung durch den zweistufigen Ablauf:** Das Tree-Sitter-Parsing skaliert strikt linear mit rund `0,35 ms` pro Datei. Durch den Verzicht auf Z3 im `SAT`-Fall (Entscheidung 3) benötigt ein konfliktfreies 20-Pin-/21-Datei-Projekt lediglich `0,06 ms` reine Validierungszeit (gegenüber `1132,81 ms` Z3-Lösezeit ein Faktor von **~18.880** in der Lösephase) bzw. **7,59 ms** In-Process insgesamt (gegenüber `1140,15 ms` ein Faktor von **~150**; rund 150 ms E2E inklusive Python-Start).
2. **Ursachen der `QF_LIA`-MaxSMT-Skalierung bei $n = 20$:** Im `UNSAT`-Fall steigt die Lösezeit nahezu quadratisch mit $n$ (`47 -> 125 -> 299 -> 650 -> 1133 ms`, empirisch $\approx O(n^{1{,}7}\text{–}n^{2{,}0})$): Bis 15 konfliktbehaftete Signale bleibt auch die End-to-End-Zeit deutlich unter 1 s (~0,80 s), während bei 20 Signalen auf dem 45-Pin-Chip 1,14 s In-Process (~1,28 s E2E) erreicht werden. Hierfür wirken **zwei** Z3-interne Mechanismen zusammen: Erstens erzeugt die Kodierung über unbeschränkte `z3.Int`-Variablen (`QF_LIA`) bei $n = 20$ exakt $\binom{20}{2} = 190$ paarweise Ungleichungen $v_i \neq v_j$ (neben 20 Domänendisjunktionen der Länge 30–31), die der LIA-Simplex-Theoriesolver disjunktiv in $(v_i < v_j) \lor (v_i > v_j)$ aufspalten muss. Zweitens liegen in `scaling_benchmark.py` 16 der 18 gültigen `gpio`-Signale (`SIG_2..SIG_17`) auf `ADC1`/`ADC2`-Pins (`1..10`, `12..18`); damit entstehen **16 unvermeidbare unerfüllbare Kerne** zwischen den Stufe-1-Halteklauseln (`var == req.pin`, Gewicht `1000`) und den Stufe-3-Schonungsklauseln (`var not in scarce_pins`, Gewicht `5`), welche ebenso viele `MaxRes`-Kernextraktions- und Resolutionsrunden über dem `QF_LIA`-Kern erzwingen. Konkrete Kodierungsoptimierungen für größere Mikrocontroller behandelt Abschnitt 8.4.

**Realer End-to-End-Test über die PlatformIO Registry.** Zur Überprüfung aus Anwendersicht wurde `mcu-pin-solver@0.2.0` in einem separaten, leeren Projektverzeichnis installiert:

1. `pio pkg install` lud **`dmatheja/mcu-pin-solver@0.2.0`** (20,71 KB) direkt aus der öffentlichen PlatformIO Registry.
2. Ein `pio run` mit fehlerhaftem ESP32-C3-Code (`STATUS_LED = 12`, `SOIL_SENSOR = 5`, `WiFi.begin`) brach den Build über `pio_hook.py` in **1,21 s** (`UNSAT`, Exit-Code `1`) *vor* dem Compilerstart ab und gab die Diagnose (`main.cpp:3`, `main.cpp:4`) samt Z3-Reparaturvorschlag aus.
3. Nach Übernahme der reparierten Pins bestand `pio run` die Validierung (`SAT`), übersetzte das Projekt mit der RISC-V-Toolchain und erzeugte `firmware.elf` sowie `firmware.bin` fehlerfrei in **17,76 s** (Exit-Code `0`).
4. Ein separater `git clone` von GitHub in ein leeres Verzeichnis bestand `pip install .`, `mcu-validate --list-boards` sowie die gesamte Testsuite ohne manuelle Anpassung.

### 7.6 Wirtschaftliche Bewertung

Um neben der technischen Machbarkeit auch den ökonomischen Nutzen im Embedded-Prototyping – etwa im industriellen F&E-Kontext wie bei Freudenberg Technology Innovation (FTI) – einzuordnen, wird eine **plausibilisierte Modellrechnung** für Gesamtkosten (*Total Cost of Ownership*, TCO), Einsparpotenziale und Break-even anhand konservativer, explizit offengelegter Annahmen aufgestellt (keine empirische Feldmessung an realen FTI-Projekten).

**1. Kostenseite (TCO).**

- **Lizenz- und laufende Betriebskosten:** Der gesamte Software-Stack (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`, PlatformIO, GitHub Actions) steht unter permissiven Open-Source-Lizenzen (MIT/BSD). Es fallen **0 € Lizenzkosten** und **keine laufenden API- oder Token-Gebühren** an. Gegenüber einem alternativen „LLM-as-a-Judge“-Ansatz entfallen sowohl Cloud-Kosten als auch Vertraulichkeitsrisiken durch den Upload proprietärer Firmware an externe Endpunkte – die Prüfung läuft vollständig lokal.
- **Einmaliger Entwicklungsaufwand:** Der Erstellungsaufwand im Rahmen dieser 5-ECTS-Studienarbeit liegt bei ca. **150 Stunden** (bei einem kalkulatorischen Vollkostensatz von 80–120 €/h entspricht dies 12.000–18.000 €; für Anwenderteams, welche die veröffentlichte Open-Source-Bibliothek nutzen, entfällt dieser Initialaufwand).
- **Inkrementeller Integrations- und Pflegeaufwand:** Die Einbindung in ein PlatformIO-Projekt erfordert zwei Zeilen in `platformio.ini` (< 10 Minuten). Das Erstellen und Datenblatt-Prüfen eines weiteren Chip-Profils (`boards/<chip>.json`) dauert dank Schema-Validierung und Prompt-Vorlage ca. **1–2 Stunden** (~100–240 €); für laufende Abhängigkeits- und Profilpflege eines Teams werden konservativ ca. **4 Stunden pro Jahr** (~400 €) angesetzt.

**2. Nutzenseite (Fehlervermeidung und Zeitersparnis).**
Entsprechend der *Cost-of-Change*-Kurve nach Boehm [[4]](#ref-4) und Boehm/Basili [[5]](#ref-5) steigen Behebungskosten steil an, sobald ein Fehler die Implementierungsphase verlässt:

- **Vermiedene Hardware-Fehlersuche (Labor/Prüfstand):** Ein unentdeckter `ADC2`/WLAN- oder Flash-Pin-Konflikt äußert sich auf der Platine häufig in unspezifischen Boot-Loops oder fehlerhaften Messwerten. Eine Fehlersuche mit Oszilloskop, Logikanalysator und Datenblattstudium bindet erfahrungsgemäß **2 bis 4 Entwicklerstunden** (kalkulatorisch **160–480 €** pro Vorfall).
- **Vermiedene Leiterplatten-Iterationen (PCB-Respin):** Gelangt ein fehlerhafter LLM-Pin-Entwurf in eine kundenspezifische Prototyp-Leiterplatte, entstehen direkte Fertigungs- und Bestückungskosten von typischerweise **300–1.000 €** zuzüglich **1–2 Wochen Durchlaufzeitverlust**.
- **Beschleunigter Build- und LLM-Iterationszyklus:** Der Pre-Build-Abbruch in **1,21 s** spart gegenüber einem vollständigen Kompilier- und Flash-Zyklus (~20–30 s) unmittelbar Wartezeit; zudem ersetzt die deterministische Z3-Reparatur oft mehrere erfolglose LLM-Selbstkorrektur-Runden [[15]](#ref-15).

**3. Modellhafte Break-even-Betrachtung.**
Tabelle 7.6 fasst drei Szenarien bei einem mittleren kalkulatorischen Stundensatz von **100 €/h** zusammen (in den Szenarien A und B konservativ ohne Anrechnung möglicher PCB-Respin-Kosten).

| Szenario (Annahme: 100 €/h, 3 h gespart je verhindertem Pin-Fehler) | Laufender Aufwand (Jahr 1) | Einsparung je Vorfall | Break-even | Jährlicher Netto-Nutzen (konservativ) |
| :--- | :---: | :---: | :--- | :--- |
| **A: Nutzung fertiger Profile** (ESP32-C3/-S3, 1 Team à 5 Entwickler) | ~1 h Setup + 4 h Pflege = **500 €** | **300 €** (3 h Debug) | ab **2** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.500 €/Jahr** |
| **B: Ergänzung eines neuen Chips** (z. B. RP2040/STM32, 2 h JSON + Prüfung) | ~2 h Profil + 5 h Setup/Pflege = **700 €** | **300 €** (3 h Debug) | ab **3** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.300 €/Jahr** |
| **C: Vollkosten-Betrachtung inkl. Eigenentwicklung** (150 h = 15.000 €, 1 Team) | **15.000 €** einmalig + **400 €/Jahr** | **300 €** Debug (bzw. **1.000 €** inkl. Respin) | ~50 Debug-Fehler oder ~15 verhinderte Respins | langfristig positiv bei mehrjähriger Team- oder Open-Source-Nutzung |

*Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung (Annahmen explizit im Text dokumentiert).*

**4. Wirtschaftliche Risiken und Grenzen.**
Dem positiven Nutzen stehen drei Risiken gegenüber: (1) Neue Silizium-Revisionen oder Framework-Änderungen (wie die ESP-IDF-`adc_oneshot`-Einschränkungen [[11]](#ref-11)) erfordern Pflege der JSON-Profile. (2) Schnittstellenänderungen in Drittpaketen (`tree-sitter`, `z3-solver`) erzeugen Wartungsaufwand, der durch Versionsgrenzen und automatisierte CI begrenzt wird. (3) Aufgrund verbleibender False Negatives des statischen Parsers (Abschnitt 8.2) darf `mcu-pin-solver` kein elektrisches Schaltplan-Review vor einer Leiterplattenfertigung **ersetzen**, sondern wirkt wirtschaftlich optimal als praktisch kostenlose Frühstufe vor dem ersten Hardware-Aufbau.

### 7.7 Soll-Ist-Abgleich

Tabelle 7.7 gleicht sämtliche funktionalen und nicht-funktionalen Anforderungen sowie Architektur-Invarianten aus Kapitel 4 gegen den erreichten Stand ab.

| ID | Anforderung / Invariante | Status | Begründung / Einschränkung |
| :--- | :--- | :---: | :--- |
| FA-01 | Hardware-Profil laden & validieren | erfüllt | `load_board` (längstes Präfix, `_`/`-`, direkter `.json`-Pfad) + strenge Schema-Validierung (`test_board.py`) |
| FA-02 | Mehrere Dateien & `--include-dir` | erfüllt | Liest `include/` + `src/` sowie `--include-dir`; schließt `.pio/`, `test/`, `tests/` über relative Pfade aus |
| FA-03 | Fehlalarmfreie Syntaxbaum-Extraktion | weitgehend erfüllt | Erfasst Makros (inkl. `(12)`), Deklarationen (`12u`, `constexpr`) und Literale; ignoriert Kommentare, Strings, lokale Variablen und Nicht-Pin-Konstanten; offene Grenzen bei `#ifdef` (`j`) und `gpio_num_t` (`i`) |
| FA-04 | Eindeutige Behandlung von Widersprüchen | erfüllt | `_reserve_unique_key` trennt alle abweichenden Definitionen und Literale eindeutig (auch bei 3 `#ifdef`-Zweigen) |
| FA-05 | Fähigkeiten, Bus-Rollen & Module | erfüllt | Mehrfachfähigkeiten als Menge (`h`), positionsgenaue `Wire`/`SPI`/`Serial`-Auswertung inkl. `bus_group` und Namens-Fallback (`OLED_SDA_PIN`) |
| FA-06 | Präzise Diagnose & Strapping-Warnungen | erfüllt | Meldet alle harten Verstöße einzeln mit `datei:zeile`-Verweis und `reason`; Arbeitsstand ergänzt nicht-blockierende Strapping-Warnungen |
| FA-07 | Kollision vs. geteilte Bus-Leitung | erfüllt | Koppelt geteilte Bus-Leitungen (`Wire:sda`), lehnt `SDA == SCL` (`m`), `Wire` vs. `Wire1` (`k`), `SCK == MOSI` und doppelte SPI-`CS` (`l`) ab |
| FA-08 | Minimale Reparatur & Kapazitätsmeldung | erfüllt | Dreistufige MaxSMT-Gewichtung (`1000`/`20`/`5`) + klare Meldung bei `repair_possible=False` (`d`, `e`) |
| FA-09 | Transparenter Bericht & Prompt | erfüllt | Zeigt `Checked Pins`, warnt bei `0` Pins und bei Strapping-Nutzung und erzeugt kopierbare `Keep`/`Change`-Anweisungen |
| FA-10 | Build-Schranke & CLI | erfüllt | Verifiziert über `pip install .`, `mcu-validate` und realen PlatformIO-Registry-End-to-End-Lauf (`0.2.0`) |
| NFA-01–NFA-07 | Qualitätsanforderungen (ISO/IEC 25010:2023) | weitgehend erfüllt | 0 chipspezifische Pin-Regeln in Python; 42 Tests (`v0.2.0`, 5/5 grüne CI-Jobs mit `ruff`/`mypy`) bzw. 47 Tests im Arbeitsstand; Zeitverhalten `< 1 s` erfüllt für alle `SAT`-Fälle bis 20 Pins (`7,59 ms` In-Process) und `UNSAT` bis 15 Pins (`0,80 s` E2E), bei 20 Pins `UNSAT` ~1,28 s E2E |
| INV-01–INV-06 | Architektur-Invarianten | erfüllt | Alle sechs Invarianten im Codebestand und durch automatisierte Tests abgesichert (inkl. mathematischer Präzisierung von INV-05) |

*Tabelle 7.7: Soll-Ist-Abgleich (`v0.2.0` inkl. Arbeitsstand-Erweiterung).*

### 7.8 Gültigkeit der Ergebnisse (Threats to Validity)

In Anlehnung an die vier Validitätsdimensionen empirischer Software-Engineering-Studien nach Wohlin et al. [[25]](#ref-25) werden die methodischen Grenzen der Evaluation wie folgt eingeordnet:

- **Schlussfolgerungsgültigkeit (*Conclusion Validity*):** Die Laufzeitmessungen beruhen auf Medianen über $N = 10$ bzw. $M = 15\text{–}30$ Läufe ohne vollständige Konfidenzintervalle. Zudem liegen im synthetischen Skalierungsbenchmark (Tabelle 7.5) 16 von 18 gültigen Signalen gezielt auf `ADC`-Pins, was eine hohe Anzahl an Stufe-1/Stufe-3-MaxRes-Kernen provoziert; Projekte mit einem höheren Anteil reiner Standard-GPIOs lösen tendenziell schneller, während Projekte mit noch enger gekoppelten Konflikten langsamer skalieren können.
- **Interne Gültigkeit (*Internal Validity*):** Prozess-Startzeiten unter Windows unterliegen Einflüssen durch Hintergrunddienste, Virenscanner und Dateisystem-Caches. Durch wiederholte Läufe, Medianbildung sowie getrennte Erfassung von Subprozess- und In-Process-Zeiten (Laden, Parsen, Lösen) ist dieser Störeinfluss methodisch kontrolliert.
- **Externe Gültigkeit (*External Validity*):** Sämtliche Tests, neun Regressionsszenarien, zwölf Grenzfallklassen und Skalierungsprojekte wurden im Rahmen dieser Arbeit konstruiert. Es liegt bislang **kein** großskaliger empirischer Benchmark über eine breite Stichprobe real von verschiedenen Sprachmodellen erzeugter Embedded-Firmware vor (wie etwa in [[8]](#ref-8) oder [[22]](#ref-22)). Darüber hinaus umfassen die mitgelieferten Profile bislang ESP32-C3 und ESP32-S3; weitere Familien (RP2040, STM32, ESP32-C6) sind über das Schema vorbereitet, aber noch nicht profiliert.
- **Konstruktgültigkeit (*Construct Validity*):** Das Ergebnis `SAT` misst ausschließlich die Konsistenz des *vom Tree-Sitter-Parser extrahierten Pin-Modells* gegen das *hinterlegte JSON-Profil*. Elektrische Randbedingungen (Strombelastbarkeit, Pull-up-Dimensionierung) sowie syntaktisch nicht abgedeckte C++-Konstrukte (Abschnitt 8.2) liegen außerhalb des geprüften Konstrukts.

---

## 8 Diskussion, Grenzen und Ausblick

### 8.1 Diskussion der Ergebnisse

Die Evaluation stützt zwei zentrale Befunde. Erstens zeigt die produktive Umsetzung, dass sich die in Kapitel 3 identifizierte Forschungslücke – deterministische CST-Extraktion ohne LLM-Autoformalisierungsfehler, gekoppelt mit schema-validiertem Hardware-Wissen und Z3-MaxSMT-Reparatur – in einem kompakten, wartbaren Werkzeug praxistauglich schließen lässt. Der Live-Test über die PlatformIO Registry bestätigt die unmittelbare Alltagstauglichkeit: Ein fehlerhafter Build bricht nach 1,21 s vor dem Cross-Compiler ab und liefert Dateizeile sowie eine Z3-verifizierte, minimal-invasive Ersatzbelegung. Durch die anschließende Erweiterung um nicht-blockierende Strapping-Warnungen werden nun auch potenzielle Boot-Risiken (Klasse 5) auf konfliktfreien oder reparierten Sketchen sichtbar gemacht, ohne reguläre Entwicklungsboards (wie `STATUS_LED = 8` auf dem ESP32-C3 DevKitM-1) fälschlich zu blockieren.

Zweitens unterstreicht der Übergang von Prototyp `v0.1.0` zu Version `v0.2.0` den methodischen Wert gezielter Grenzfallexperimente: Erst systematische *Fault-Injection*-Tests (Abschnitt 7.4) und der 20-Pin-Skalierungstest (Abschnitt 7.5) legten neun konkrete Schwächen von `v0.1.0` sowie die `QF_LIA`-MaxSMT-Übergangsgrenze bei rund 20 konfliktbehafteten Signalen offen.

### 8.2 Verbleibende Grenzen des Systems

Aus den bewussten Architekturentscheidungen ergeben sich sechs klar umrissene Systemgrenzen (Tabelle 8.1):

1. **Präprozessor-Verzweigungen (`#ifdef` / `#else`) und Makro-Expansion.** Da Tree-Sitter keinen C-Präprozessor ausführt, erscheinen alle Zweige bedingter Kompilierung gleichzeitig im CST. Ein inaktiver Zweig für ein anderes Board erzeugt daher weiterhin ein False Positive (Experiment `j`), wenngleich `_reserve_unique_key` jeden Solver-Absturz verhindert.
2. **Spezielle C++-Typen und Ausdrücke.** ESP-IDF-Aufzählungen (`const gpio_num_t LED = GPIO_NUM_14;`, Experiment `i`, bedingt durch Typ außerhalb von `PIN_VAR_TYPES` und `identifier`-Initialisierer), Pin-Arrays (`int pins[] = {...}`), `enum`-Definitionen sowie berechnete Konstanten (`#define LED (BASE + 2)`) werden nicht ausgewertet. (Positiv bleibt festzuhalten, dass negative Sentinel-Werte wie `-1` in `SPI.begin(18, -1, 23, 5)` als `unary_expression` geparst und daher ohne Fehlalarm ignoriert werden.)
3. **Drittbibliotheks-Konstruktoren und -Methoden.** Pins, die ausschließlich an externe Bibliotheken übergeben werden (z. B. `myServo.attach(OUT_1)` oder `OneWire bus(DATA_LINE)`) und kein Pin-Namensmuster (`PIN`, `GPIO`, `SDA`, …) tragen, bleiben unentdeckt; Konstruktoren wie `DHT dht(DHT_PIN, DHT22);` greifen lediglich auf den generischen `gpio`-Fallback zurück.
4. **Board-spezifische `Serial`- und Flash-/PSRAM-Annahmen.** In den ESP32-Profilen aktiviert `Serial.begin(...)` stets `usb_serial` und sperrt GPIO 18/19 (C3) bzw. 19/20 (S3); auf Boards mit externer USB-UART-Brücke (`ARDUINO_USB_CDC_ON_BOOT=0`, Nutzung von `UART0` auf GPIO 20/21 bzw. 43/44) kann dies zu konservativ sein. Entsprechend sperrt `esp32-s3.json` die Octal-SPI-Pins GPIO 33–37 konservativ auch auf reinen Quad-SPI-Varianten.
5. **Chip-Katalog, Peripherie-Budgets, Gewichtungs-Grenzen und Skalierung.** Neben der aktuellen Beschränkung auf ESP32-C3 und ESP32-S3 modelliert das Schema bislang weder reine Eingangs-Pins (`input_only`, z. B. GPIO 34–39 beim klassischen ESP32) noch chipweite **Peripherie-Controller-Budgets** (der ESP32-C3 besitzt physisch nur 1× I2C, 1× GP-SPI, 2× UART und 6× LEDC-PWM-Kanäle; der ESP32-S3 2× I2C, 2× GP-SPI, 3× UART und 8× LEDC [[9]](#ref-9), [[10]](#ref-10)) oder Silizium-Errata (`CONFIG_ADC_ONESHOT_FORCE_USE_ADC2_ON_C3` [[11]](#ref-11)). Im Solver ist `SCARCE_CAPABILITIES` noch global in Python definiert, zwischen Stufe 2 (`20`) und Stufe 3 (`5`) besteht ab fünf gekoppelten Signalen ein theoretischer Gewichts-Trade-off, und die `QF_LIA`-MaxSMT-Laufzeit erreicht bei 20 konfliktbehafteten Pins ~1,14 s (Tabelle 7.5).
6. **Manueller Rückkopplungskreis und fehlender Live-LLM-Benchmark.** Der Reparatur-Prompt wird noch manuell in den LLM-Chat übertragen, und eine systematische empirische Messung der Pin-Fehlerraten realer Sprachmodelle vor gegenüber nach dem Einsatz von `mcu-pin-solver` steht als Folgestudie noch aus.

| Nr. | Verbleibende Grenze | Ort | Auswirkung | Möglicher Ausbau |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `#ifdef` / `#else`-Zweige | `parser.py` | False Positive bei Alternativ-Konfigs (`j`) | Makro-Filter über `-D`-Build-Flags aus `platformio.ini` |
| 2 | `gpio_num_t`, Arrays, `enum`, Rechen-Makros | `parser.py` | False Negative (`i`) | Erweiterung der CST-Regeln um `GPIO_NUM_<n>` und `enumerator` |
| 3 | Drittbibliotheks-Aufrufe / Konstruktoren | `parser.py` | False Negative ohne `PIN`-Namensmuster | Konfigurierbare API-Signaturen im Profil oder Projektrahmen |
| 4 | `Serial.begin` bei UART-Bridge & OPI-PSRAM | `boards/*.json` / `pio_hook.py` | Ggf. zu konservative Sperren (USB / GPIO 33–37) | Auswertung von `-DARDUINO_USB_CDC_ON_BOOT` & Speicher-Modi aus PlatformIO |
| 5 | Katalog, Controller-Budgets & 20-Pin-MaxSMT | `boards/*.json` / `solver.py` | Nur C3/S3; keine Bus-Zählgrenzen; ~1,14 s bei 20 Konflikten | Optionale Felder (`input_only`, Budgets, `scarce_capabilities`), One-Hot-MaxSAT & `priority='lex'` |
| 6 | Manueller Prompt & fehlender LLM-Benchmark | Workflow / Evaluation | Kopierschritt nötig; externe Validität offen | MCP-Tool / `--json` + systematische empirische LLM-Studie |

*Tabelle 8.1: Verbleibende Systemgrenzen.*

### 8.3 Reflexion der KI-gestützten Entstehung

Sowohl die schrittweise Entwicklung der Codebasis als auch Entwürfe dieser Ausarbeitung entstanden unter dokumentierter Mitwirkung großer Sprachmodelle (vgl. Verzeichnis der verwendeten KI-Hilfsmittel). Dabei spiegelte sich die Grundthese dieser Studienarbeit unmittelbar im eigenen Entwicklungsprozess wider:

1. **Empirische Widerlegung plausibler Annahmen:** Ein früher Textentwurf behauptete, Z3 löse Gleichstände zwischen identischen Signalen deterministisch nach Deklarationsreihenfolge auf – erst die Experimente `c` und `c2` widerlegten diese Annahme am realen Solver.
2. **Subtile Defekte erst durch Tests, CI und Skalierung sichtbar:** Beim Ausbau der Namensheuristik in `v0.2.0` übersah der reguläre Ausdruck `WORD_RE` zunächst Großbuchstaben-Wörter vor Unterstrichen (`OLED_SDA_PIN`), weil der Lookahead Unterstriche nicht enthielt; erst der neu erstellte Unit-Test deckte den Defekt sofort auf. Ebenso offenbarte erst die GitHub-Actions-CI-Matrix das Fehlen vorinstallierter Python-3.9-Binaries auf `ubuntu-latest`, während erst der 20-Pin-Skalierungstest die `QF_LIA`-Laufzeitgrenze bei 1,14 s sichtbar machte.

Automatisierte Tests, statische Typ- und Stilprüfungen (`mypy`, `ruff`) sowie reale End-to-End-Messungen bildeten damit ein unverzichtbares Korrektiv gegenüber oberflächlich plausiblen KI-Ausgaben.

### 8.4 Ausblick

Aufbauend auf dem erreichten Stand bieten sich vier konkrete, wirkungsvolle Ausbaustufen an:

1. **Integration von PlatformIO-Build-Flags (`-D`):** Durch Auslesen aktiver Präprozessor-Definitionen aus dem SCons-Environment ließen sich sowohl `#ifdef`-Zweige selektiv auswerten als auch native USB-CDC-Boards (`ARDUINO_USB_CDC_ON_BOOT=1`) zuverlässig von Boards mit externer USB-UART-Brücke sowie Quad- von Octal-PSRAM-Varianten trennen.
2. **Automatisierter Agenten-Kreislauf (MCP / `--json`):** Eine strukturierte `--json`-Ausgabe sowie ein leichtgewichtiger MCP-Server erlauben es KI-Coding-Agenten (komplementär zu AutoIOT [[22]](#ref-22) oder EmbedGenius [[26]](#ref-26)), `mcu-validate` direkt als deterministischen Hardware-Critic aufzurufen und Konflikte mit begrenzter Iterationszahl vollautomatisch zu bereinigen.
3. **Solver-Optimierung für große Mikrocontroller (> 20–60 Pins):** Für große MCUs (z. B. STM32 mit > 60 Pins) sollte die Kodierung von unbeschränkten `z3.Int`-Variablen (`QF_LIA`) auf eine **boolesche One-Hot-MaxSAT-Kodierung** ($x_{i,p} \in \{0, 1\}$ mit `PbEq`/`AtMost`-Kardinalitätsbedingungen) oder Bitvektoren umgestellt werden; dadurch entfällt die kostspielige disjunktive Simplex-Aufspaltung von Ungleichheiten $v_i \neq v_j$ vollständig (während ein bloßer Ersatz durch `z3.Distinct(...)` in `QF_LIA` zwar den Python-AST-Overhead senkt und interne Propagatoren nutzt, das grundsätzliche LIA-Verhalten aber nicht im selben Maße eliminiert). Ergänzend vermeiden geschützte bzw. bedingte Stufe-3-Klauseln unnötige `MaxRes`-Kerne bei unveränderten ADC-Pins, und `opt.set(priority='lex')` mit benannten Zielgruppen sichert exakte, $n$-unabhängige lexikografische Dominanz [[3]](#ref-3).
4. **Katalog-Ausbau, Peripherie-Budgets und empirische LLM-Studie:** Ergänzung datenblattgeprüfter Profile für den klassischen ESP32 (inkl. `input_only`), ESP32-C6, RP2040 und STM32, Aufnahme chipweiter Controller-Budgets (maximale Anzahl I2C-/SPI-/UART-/LEDC-Instanzen) als Kardinalitätsbedingungen im Solver sowie eine systematische empirische Vergleichsstudie über mehrere aktuelle Sprachmodelle (Messung der Hardware-Korrektheitsrate mit gegenüber ohne `mcu-pin-solver`).

---

## 9 Fazit

Die vorliegende Studienarbeit hat mit `mcu-pin-solver` (Release `0.2.0` inklusive der Arbeitsstand-Erweiterung um nicht-blockierende Strapping-Warnungen) ein datengetriebenes, neuro-symbolisches Pre-Build-Werkzeug zur statischen Verifikation und MaxSMT-Reparatur von GPIO-Pin-Belegungen in Embedded-C++-Projekten konzipiert, iterativ gehärtet, auf GitHub sowie der PlatformIO Registry veröffentlicht und empirisch evaluiert. Die drei Forschungsfragen lassen sich abschließend wie folgt beantworten:

- **Zu FF1 (Extraktion ohne Ziel-Toolchain):** Mithilfe von Tree-Sitters fehlertolerantem GLR-Parser (`tree-sitter-cpp`) und seiner benannten Feldsicht auf den CST werden Top-Level-Pin-Konstanten, direkte Pin-Literale, Fähigkeitsmengen, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripherie über mehrdateiige `include/`- und `src/`-Strukturen hinweg ohne Cross-Compiler in wenigen Millisekunden (unter 2 ms für 3 Dateien, 7,53 ms für 21 Dateien) extrahiert. Kommentare, Zeichenketten, lokale Variablen und fachfremde Konstanten erzeugen keine Fehlalarme; verbleibende Grenzen bei `#ifdef`-Zweigen, `gpio_num_t` und Drittbibliotheks-Konstruktoren sind präzise lokalisiert.
- **Zu FF2 (Validierte Datentrennung und Partial-Weighted-MaxSMT-Reparatur):** Durch die vollständige Auslagerung des Hardware-Wissens in schema-validierte JSON-Profile (`mcu_validator/boards/*.json`) ist der Prüfcode frei von chipspezifischen Pin-Regeln, wie der unmittelbare Vergleich identischen C++-Codes auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`) belegt. Die zweistufige Architektur kombiniert eine nahezu latenzfreie Diagnose samt Dateizeilen-Verweis und nicht-blockierenden Strapping-Warnungen in Stufe 1 (`0,01–0,06 ms` bei `SAT` selbst für 20 Pins) mit einer dreistufig gewichteten Partial-Weighted-MaxSMT-Reparatur in Z3 $\nu Z$ (`1000` / `20` / `5`), die gültige Pins bewahrt, geteilte Bus-Leitungen zusammenhält, Strapping-Pins meidet, knappe ADC-/USB-Pins schont und Hardware-Überbuchungen sauber meldet.
- **Zu FF3 (Integration, Praxistauglichkeit und Wirtschaftlichkeit):** Über `pio_hook.py`, `library.json` (`"srcFilter": ["-<*>"]`) und gebündelte Paketdaten in `pyproject.toml` ist das Werkzeug sowohl eigenständig via `pip install .` (`mcu-validate`) als auch direkt über die PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) nutzbar. Der Live-Registry-Test belegte den Build-Abbruch in 1,21 s vor dem Cross-Compiler sowie die fehlerfreie Firmware-Erzeugung nach Übernahme der Z3-Vorschläge; 42 Tests im Release `v0.2.0` (5/5 grüne CI-Jobs mit `ruff` und `mypy` unter Windows und Linux) bzw. 47 Tests im aktuellen Arbeitsstand sichern die Codequalität ab. Bei 0 € Lizenz- und API-Kosten amortisiert sich der Einsatz laut konservativer Modellrechnung bereits ab zwei bis drei verhinderten Hardware-Fehlersuchen.

Zusammenfassend demonstriert `mcu-pin-solver` am produktiven System, dass die Verbindung aus generativem Sprachmodell, deterministischer Tree-Sitter-Analyse, schema-validierten Hardware-Profilen und formaler Z3-MaxSMT-Optimierung eine schnelle, transparente und wirtschaftlich sinnvolle Sicherheitsbarriere im Embedded-Prototyping bildet.

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
- <a id="ref-9"></a>**[9] Espressif Systems (2024):** *ESP32-C3 Series Datasheet*, *ESP32-C3 Technical Reference Manual* & *ESP32-C3 Series SoC Errata.* Espressif Systems, Shanghai.
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
