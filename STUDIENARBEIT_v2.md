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

Große Sprachmodelle (*Large Language Models*, LLMs) generieren in wenigen Sekunden syntaktisch gültigen und fehlerfrei kompilierbaren Embedded-C++-Code für Mikrocontroller. Bei der Wahl konkreter Hardware-Anschlüsse (GPIOs) verursachen sie jedoch systematisch physikalische Konflikte, die für reguläre C++-Compiler unsichtbar bleiben: Sie belegen Leitungen des internen SPI-Flash-Speichers, weisen analoge Sensoren Wandlerkanälen zu, die mit dem aktiven WLAN-Subsystem kollidieren (`ADC2`), legen getrennte Signale eines seriellen Busses auf denselben Pin oder belegen Anschlüsse mehrfach. Im industriellen Embedded-Prototyping führen solche erst nach dem Hardware-Aufbau erkannten Defekte zu zeitintensiver Fehlersuche, manuellen Schaltungsänderungen oder kostspieligen Leiterplatten-Neuanfertigungen.

Diese Studienarbeit konzipiert, implementiert und evaluiert `mcu-pin-solver` (Version `0.2.0`), eine Open-Source-Bibliothek und Kommandozeilenanwendung zur statischen Hardware-Pin-Prüfung *vor* dem Kompiliervorgang. Ein fehlertoleranter GLR-Parser auf Basis von Tree-Sitter (`tree-sitter-cpp`) analysiert ein- und mehrdateiige C/C++-Projekte ohne Ziel-Cross-Compiler und extrahiert über die benannte Sicht auf den konkreten Syntaxbaum Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Fähigkeiten, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripheriemodule (`wifi`, `usb_serial`). Die Prüfung erfolgt gegen schema-validierte, deklarative JSON-Hardware-Profile, sodass neue Mikrocontroller ohne Eingriff in den Python-Quelltext ergänzt werden können. Bei detektierten Konflikten löst die Optimierungserweiterung $\nu Z$ des SMT-Solvers Z3 ein Partial-Weighted-MaxSMT-Problem mit dreistufiger Gewichtung, das gültige Originalpins bewahrt (`1000`), Strapping-Pins meidet (`20`) und knappe ADC-/USB-Pins schont (`5`). Das Ergebnis wird mit Dateizeilen-Verweis als direkt einsetzbarer LLM-Modulo-Reparatur-Prompt ausgegeben; ein PlatformIO-Pre-Build-Hook bricht fehlerhafte Builds vor dem Compilerstart ab.

Die Evaluation stützt sich auf 42 automatisierte Tests (darunter neun End-to-End-Regressionsszenarien sowie eine plattformübergreifende GitHub-Actions-CI unter Windows und Linux mit `ruff` und `mypy`), zwölf Grenzfallgruppen in 14 Einzelkonfigurationen im Vergleich zwischen Prototyp `v0.1.0` und Stand `v0.2.0`, Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, einen realen End-to-End-Test über die PlatformIO Registry sowie eine Wirtschaftlichkeits- und Break-even-Betrachtung. Typische CLI-Prüfläufe dauern im Median 172 bis 211 ms; fehlerhafte PlatformIO-Builds werden in 1,21 s gestoppt, während ein konfliktfreies 20-Pin-Projekt in 7,59 ms (In-Process; 0,06 ms Validierungszeit) geprüft wird. Grenzen bei `#ifdef`-Präprozessorzweigen, ESP-IDF-Typen (`gpio_num_t`), Drittbibliotheks-Konstruktoren, dem Übergang in `QF_LIA`-MaxSMT-Laufzeiten über 1 s bei 20 konfliktbehafteten Pins sowie das Fehlen einer großskaligen empirischen LLM-Benchmark-Studie werden kritisch reflektiert.

## Abstract

Large Language Models (LLMs) generate syntactically valid, compilable embedded C++ firmware within seconds, yet they systematically introduce hardware pin conflicts that remain invisible to standard C++ compilers—such as repurposing internal SPI flash lines, assigning analog sensors to ADC2 channels affected by an active Wi-Fi subsystem, colliding distinct bus lines, or duplicating GPIOs. In industrial embedded prototyping, discovering these defects only after wiring a test bench or fabricating a prototype PCB results in costly debugging cycles or board respins.

This thesis designs, implements, and evaluates `mcu-pin-solver` (version `0.2.0`), an open-source pre-build hardware pin validator for PlatformIO and standalone CLI workflows. Using Tree-Sitter's error-tolerant GLR parser (`tree-sitter-cpp`), the tool analyzes single- and multi-file C/C++ projects without requiring a target cross-compiler toolchain, extracting pin constants, direct numeric pin literals, required capability sets, bus-line identities (`Wire:sda`, `SPI:mosi`, etc.), and active peripherals (`wifi`, `usb_serial`) from the named-field projection of the concrete syntax tree. Pin requests are checked against schema-validated, declarative JSON board profiles so additional microcontrollers can be integrated without modifying Python code. Whenever conflicts arise, Z3's $\nu Z$ engine solves a three-tier Partial Weighted MaxSMT optimization problem that preserves valid original pins (`1000`), avoids boot strapping pins (`20`), and spares scarce ADC/USB pins (`5`), emitting a copy-paste LLM-Modulo repair prompt with `file:line` references while halting invalid PlatformIO builds before compilation.

The evaluation comprises 42 automated tests (including nine end-to-end regression scenarios and cross-platform Windows/Linux CI with `ruff` and `mypy`), twelve edge-case groups spanning 14 test configurations comparing prototype `v0.1.0` against `v0.2.0`, runtime and scaling benchmarks up to 20 pins and 21 files, a live PlatformIO Registry end-to-end build test, and a total-cost-of-ownership and break-even analysis. Median CLI runs take 172–211 ms, invalid PlatformIO builds abort in 1.21 s prior to compilation, and valid 20-pin projects pass in-process validation in 7.59 ms (0.06 ms solver stage). Remaining limitations—including `#ifdef` preprocessor branches, ESP-IDF `gpio_num_t` enums, third-party constructors, `QF_LIA` MaxSMT runtime exceeding 1 s at 20 conflicting pins, and the lack of a large-scale benchmark on live LLM-generated firmware—are transparently discussed.

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
  - [6.5 Prioritätsverhalten und Konfliktauflösung bei gegenseitiger Pin-Blockade](#65-prioritätsverhalten-und-konfliktauflösung-bei-gegenseitiger-pin-blockade)
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
| APB | *Advanced Peripheral Bus*, interner Peripheriebus in SoC-Architekturen |
| AST | *Abstract Syntax Tree*, abstrakter Syntaxbaum |
| CDCL | *Conflict-Driven Clause Learning*, Suchverfahren in modernen SAT-Solvern |
| CDCL($T$) | *Conflict-Driven Clause Learning Modulo Theories*, Kopplung von CDCL-SAT-Kern und Theorie-Solvern |
| CI | *Continuous Integration*, automatisierte Prüfung bei jeder Quelltextänderung |
| CLI | *Command Line Interface*, Kommandozeilenschnittstelle |
| CS | *Chip Select*, aktive Auswahlleitung eines SPI-Teilnehmers |
| CST | *Concrete Syntax Tree*, konkreter Syntaxbaum |
| DMA | *Direct Memory Access*, direkter Speicherzugriff ohne CPU-Beteiligung |
| GLR | *Generalized LR*, verallgemeinertes LR-Parsing für lokal mehrdeutige Grammatiken |
| GPIO | *General-Purpose Input/Output*, universeller digitaler Ein-/Ausgangspin |
| HAL | *Hardware Abstraction Layer*, Hardware-Abstraktionsschicht |
| HIL | *Hardware-in-the-Loop*, automatisierter Test gegen reale Zielhardware |
| I2C | *Inter-Integrated Circuit*, synchroner serieller Zweidrahtbus (`SDA`, `SCL`) |
| IO_MUX | *Input/Output Multiplexer*, direkter digitaler Signalmultiplexer im ESP32-SoC |
| JSON | *JavaScript Object Notation*, textbasiertes Datenaustauschformat |
| LEDC | *LED PWM Controller*, Hardware-PWM-Peripherieeinheit der ESP32-Familie |
| LLM | *Large Language Model*, großes Sprachmodell |
| MaxSMT | *Maximum Satisfiability Modulo Theories*, Optimierungsvariante von SMT |
| MCP | *Model Context Protocol*, standardisierte Werkzeugschnittstelle für KI-Agenten |
| MCU | *Microcontroller Unit*, Mikrocontroller |
| MILP | *Mixed-Integer Linear Programming*, gemischt-ganzzahlige lineare Optimierung |
| OMT | *Optimization Modulo Theories*, allgemeine Optimierung über SMT-Theorien |
| PB | *Pseudo-Boolean*, lineare Ungleichungen über booleschen Variablen |
| PSRAM | *Pseudo-Static RAM*, externer bzw. im Gehäuse integrierter Arbeitsspeicher |
| PWM | *Pulse-Width Modulation*, Pulsweitenmodulation |
| `QF_FD` | *Quantifier-Free Finite Domains*, quantorenfreie Logik über endliche Domänen |
| `QF_LIA` | *Quantifier-Free Linear Integer Arithmetic*, quantorenfreie lineare Ganzzahlarithmetik |
| SAR-ADC | *Successive-Approximation-Register ADC*, sukzessiv approximierender Analog-Digital-Wandler |
| SAT | *Satisfiability*, Erfüllbarkeit; zugleich Solver-Status „erfüllbar“ |
| SMT | *Satisfiability Modulo Theories*, Erfüllbarkeit modulo Hintergrundtheorien |
| SoC | *System-on-Chip*, hochintegriertes Ein-Chip-System |
| SPI | *Serial Peripheral Interface*, synchroner serieller Vierdrahtbus (`SCK`, `MISO`, `MOSI`, `CS`) |
| SPS | Speicherprogrammierbare Steuerung (*Programmable Logic Controller*, PLC) |
| TCO | *Total Cost of Ownership*, Gesamtkosten über den Lebenszyklus |
| TRM | *Technical Reference Manual*, technisches Referenzhandbuch eines Halbleiterherstellers |
| UART | *Universal Asynchronous Receiver Transmitter*, asynchrone serielle Schnittstelle |
| UNSAT | *Unsatisfiable*, Solver-Status „nicht erfüllbar“ |
| USB-CDC | *USB Communications Device Class*, virtuelle serielle Schnittstelle über USB |

## Symbolverzeichnis

| Symbol | Bedeutung |
| :--- | :--- |
| $\mathcal{P}$ | Menge aller im Hardware-Profil deklarierten GPIO-Nummern eines Mikrocontrollers |
| $r_i$ | $i$-te aus dem Quelltext extrahierte Pin-Anforderung (`PinRequest`), $i = 1, \dots, n$ |
| $p_i^0$ | im Quelltext spezifizierte (ursprüngliche) GPIO-Nummer von $r_i$ |
| $C_i$ | Menge der von $r_i$ benötigten Fähigkeiten, z. B. $\{\texttt{adc}\}$ oder $\{\texttt{adc}, \texttt{i2c}\}$ |
| $b_i$ | optionale Bus-Leitungsrolle (`bus_group`) von $r_i$, z. B. `Wire:sda`, `SPI:mosi` oder $\bot$ (`None`) |
| $A(c)$ | über `capability_aliases` expandierte Menge konkreter Fähigkeiten, z. B. $A(\texttt{adc}) = \{\texttt{adc1}, \texttt{adc2}\}$ |
| $N_i$ | Vereinigung aller expandierten benötigten Fähigkeiten von $r_i$: $N_i = \bigcup_{c \in C_i} A(c)$ |
| $\text{ForbiddenPins}$ | durch aktive Konfliktregeln gesperrte physische GPIO-Nummern |
| $\text{ForbiddenCaps}$ | durch aktive Konfliktregeln gesperrte Fähigkeiten (z. B. `adc2` bei aktivem `wifi`) |
| $v_i$ | ganzzahlige Z3-Entscheidungsvariable (`pin_i`): zugewiesener GPIO für $r_i$ |
| $P_i$ | zulässige Kandidatenmenge (endliche Domäne) für $r_i$ nach allen harten Pin-Regeln |
| $S,\; S_i$ | Menge der Strapping-Pins des Chips bzw. Teilmenge $S_i = P_i \cap S$ |
| $\mathcal{K}_{\text{scarce}}$ | Menge knapper Spezialfähigkeiten: $\{\texttt{adc}, \texttt{adc1}, \texttt{adc2}, \texttt{usb}\}$ |
| $K_i$ | Menge der Pins in $P_i$, die knappe, von $r_i$ nicht angeforderte Spezialfähigkeiten tragen |
| $\mathbb{I}[\cdot]$ | Indikatorfunktion: $1$, falls die Bedingung erfüllt ist, sonst $0$ |

## Abbildungsverzeichnis

- Abbildung 1.1: Signalpfade und Pin-Multiplexing auf dem ESP32-C3 (GPIO-Matrix, analoge Pad-Verbindungen, USB-PHY und SPI-Flash)
- Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver`
- Abbildung 2.2: Konkreter Syntaxbaum (CST) und abstrakte Sicht (AST) am Beispiel einer C++-Deklaration
- Abbildung 2.3: Von Tree-Sitter erzeugter konkreter Syntaxbaum eines Beispielprogramms
- Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen im Partial-Weighted-MaxSMT-Modell
- Abbildung 5.1: Gesamtarchitektur und Datenfluss im PlatformIO-Build-Prozess (`v0.2.0`)
- Abbildung 6.1: Zweistufiger Ablauf in `validate()` (`mcu_validator/solver.py`)

## Tabellenverzeichnis

- Tabelle 1.1: Fünf Fehlerklassen bei der GPIO-Pin-Belegung und ihre Hardware-Auswirkungen
- Tabelle 3.1: Einordnung verwandter Ansätze und Identifikation der Forschungslücke
- Tabelle 4.1: Funktionale Anforderungen
- Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023
- Tabelle 4.3: Architektur-Invarianten
- Tabelle 5.1: Nutzwertanalyse der Verfahren zur Quelltextanalyse
- Tabelle 5.2: Nutzwertanalyse der Verfahren zur Konfliktlösung
- Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`)
- Tabelle 6.1: Dateien und Struktur des Repositories (`v0.2.0`)
- Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`)
- Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen (`_pin_args_for_call`)
- Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`)
- Tabelle 6.5: Punktebewertung in Szenario 04 (geteilter I2C-Bus gegen einzelnes Störsignal, `v0.2.0`)
- Tabelle 7.1: Mess- und CI-Umgebung (`v0.2.0`)
- Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien
- Tabelle 7.3: Ergebnisse der Grenzfallexperimente auf `esp32-c3` (`v0.1.0` im Vergleich zu `v0.2.0`)
- Tabelle 7.4: Gemessene Laufzeiten der Regressionsszenarien (`v0.2.0`)
- Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`)
- Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung
- Tabelle 7.7: Soll-Ist-Abgleich der Anforderungen und Invarianten (`v0.2.0`)
- Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`

## Listingverzeichnis

- Listing 1.1: Kompilierbares, jedoch auf dem ESP32-C3 hardwarefehlerhaftes C++-Programm
- Listing 5.1: Szenario 0 (`tests/scenarios/00_flash_and_wifi_conflict.cpp`)
- Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (`v0.2.0`)
- Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (`v0.2.0`)
- Listing 6.1: Auszug aus `mcu_validator/boards/esp32-c3.json`
- Listing 6.2: Laden des Hardware-Profils (`load_board`, `mcu_validator/board.py`)
- Listing 6.3: Kollisionssichere Schlüsselvergabe (`_record_definition`, `mcu_validator/parser.py`)
- Listing 6.4: Positionsgenaue Extraktion von Fähigkeiten und Bus-Rollen (`_pin_args_for_call`, `mcu_validator/parser.py`)
- Listing 6.5: Aufbau der harten und weichen Z3-Bedingungen (`_add_pin_constraints`, `mcu_validator/solver.py`)
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

Während Anwendungssoftware auf Desktop- und Serversystemen durch Betriebssystemkernel, Treiberschichten und Speicherverwaltung weitgehend von der physischen Hardware abstrahiert ist, greift Embedded-Firmware auf Mikrocontrollern (*Microcontroller Units*, MCUs) wie den Espressif-SoCs ESP32-C3 und ESP32-S3 unmittelbar über speicherabgebildete Register oder schlanke Hardware-Abstraktionsschichten auf elektrische Chip-Kontakte zu. Diese programmierbaren Ein- und Ausgänge (*General-Purpose Input/Output*, GPIO) sind auf Entwicklungsboards wie dem `esp32-c3-devkitm-1` auf äußere Stiftleisten geführt und nach außen hin optisch nicht unterscheidbar. Intern sind sie jedoch an heterogene Peripherie- und Systembaugruppen gekoppelt:

- **Digitale Ein- und Ausgänge** (`gpio`) schalten und lesen diskrete Logikpegel (bei der ESP32-Familie typischerweise 0 V bis 3,3 V), etwa für Status-LEDs, Relaisstufen oder Taster.
- **Sukzessiv approximierende Analog-Digital-Wandler** (`adc`, 12-Bit SAR-ADC) digitalisieren analoge Sensorspannungen. Sowohl der ESP32-C3 als auch der ESP32-S3 integrieren zwei getrennte Wandlereinheiten (`ADC1` und `ADC2`) mit unterschiedlichem Laufzeitverhalten bei aktivem Funkbetrieb.
- **Pulsweitenmodulation** (`pwm`) wird auf ESP32-Chips durch den *LED PWM Controller* (`LEDC`) erzeugt und dient etwa zur Helligkeits- oder Aktorregelung.
- **Serielle Kommunikationscontroller** (`i2c`, `spi`, `uart`) binden externe Sensoren, Displays, Speichermedien oder Schnittstellenwandler an.
- **Kritische Systemfunktionen** wie die interne SPI-Flash- bzw. PSRAM-Anbindung (`SPI0/1`), die Flash-Versorgung (`VDD_SPI`) oder der integrierte USB-PHY (`USB_D-`/`USB_D+`) teilen sich die begrenzten Gehäusekontakte mit regulären GPIOs.

Um die Vielzahl interner Peripheriesignale auf eine begrenzte Anzahl physischer Pins abzubilden, kombinieren ESP32-SoCs drei unterschiedliche Verschaltungsebenen (Abbildung 1.1): Eine flexible digitale **GPIO-Matrix** vermittelt interne Digitalsignale (I2C, SPI, UART, LEDC-PWM) auf nahezu jeden freien GPIO; der **IO_MUX** stellt direkte, verzögerungsarme digitale Signalpfade für hochfrequente oder standardmäßig fest zugewiesene Schnittstellen bereit (z. B. Flash-SPI0/1, Hochgeschwindigkeits-FSPI, JTAG, Standard-UART0); und **fest verdrahtete analoge Pad-Verbindungen** umgehen die digitale Multiplexer-Logik vollständig, um einzelne Pads unmittelbar mit `ADC1`, `ADC2` oder dem nativen USB-PHY zu verbinden [[9]](#ref-9), [[10]](#ref-10).

```text
  Interne Baugruppen                      Verschaltungsebene          Physische Pins (ESP32-C3)
  ------------------                      ------------------          -------------------------
  Digitale GPIOs, LEDC (PWM),    ───►  GPIO-Matrix (flexibel)  ───►  GPIO 0–10, 18–21
  I2C0, SPI2 (FSPI), UART0/1           (+ IO_MUX für Direktpfade)    (frei routbar; UART0-Std.: 20/21)

  SAR-ADC1 (5 Kanäle)            ───►  Analoger Pad-Pfad (fest) ──►  GPIO 0–4
  SAR-ADC2 (1 Kanal, Erratum)    ───►  Analoger Pad-Pfad (fest) ──►  GPIO 5
  USB Serial/JTAG PHY            ───►  USB-PHY-Pad (fest)       ──►  GPIO 18 (D-), 19 (D+)
  Flash-Versorgung / SPI0/1      ───►  VDD_SPI / IO_MUX (fest)  ──►  GPIO 11 (VDD_SPI), 12–17 (Flash)
```
*Abbildung 1.1: Signalpfade und Pin-Multiplexing auf dem ESP32-C3 (GPIO-Matrix, analoge Pad-Verbindungen, USB-PHY und SPI-Flash; vereinfacht nach [[9]](#ref-9)).*

Durch den Einsatz großer Sprachmodelle (*Large Language Models*, LLMs) lässt sich lauffähige Arduino- bzw. ESP-IDF-Firmware heute in Sekunden aus natürlichsprachlichen Anforderungen generieren. Empirische Studien zeigen jedoch, dass LLMs im Embedded-Kontext zwar häufig syntaktisch einwandfreien Code liefern, bei mikrocontrollerspezifischen Hardware-Randbedingungen jedoch unzuverlässig bleiben [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26). Gerade bei der GPIO-Pin-Zuweisung ist diese Unzuverlässigkeit gravierend, weil entsprechende Defekte den gesamten Kompilier- und Linkvorgang unentdeckt passieren und sich erst auf der realen Schaltung als Fehlfunktion, Boot-Loop oder unplausible Messwerte manifestieren.

### 1.2 Problemstellung und wirtschaftliche Relevanz

Listing 1.1 illustriert ein typisches von einem Sprachmodell erzeugtes Arduino-C++-Programm. Der Quelltext lässt sich mit der RISC-V-Toolchain für den ESP32-C3 ohne eine einzige Compiler-Warnung übersetzen, enthält auf diesem Chip jedoch zwei gravierende Hardware-Defekte.

```cpp
#include <Arduino.h>
#include <WiFi.h>

#define STATUS_LED 12        // Fehler: GPIO 12 gehört zum internen SPI-Flash (SPIHD)
const int SOIL_SENSOR = 5;   // Fehler: GPIO 5 ist ADC2, bei aktivem WLAN unzulässig
const int RELAY_PIN = 4;     // gültig (GPIO + ADC1)

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
*Listing 1.1: Kompilierbares, jedoch auf dem ESP32-C3 hardwarefehlerhaftes C++-Programm.*

Dass der C++-Compiler diese Fehler nicht erkennt, beruht auf drei strukturellen Eigenschaften der Embedded-C++-Toolchain:

1. **Schwache Typisierung von Pin-Nummern.** Die Arduino-C++-API modelliert Hardware-Pins als ungeschützte Ganzzahlen (`void pinMode(uint8_t pin, uint8_t mode)`, `uint16_t analogRead(uint8_t pin)`), die zudem häufig über untypisierte Präprozessor-Makros (`#define`) weitergereicht werden. Durch implizite Ganzzahlkonvertierungen akzeptiert der Compiler `pinMode(12, OUTPUT)` ebenso anstandslos wie einen nicht existierenden Pin `pinMode(32, OUTPUT)`.
2. **Fehlendes Chip- und Board-Modell im Compiler.** Der Cross-Compiler überprüft Syntax, Typkompatibilität und Ziel-Befehlssatz (etwa RV32IMC für den ESP32-C3), besitzt jedoch keine formale Repräsentation der physischen Pad-Verdrahtung, der im Gehäuse angebundenen Flash-Leitungen oder der elektrischen Fähigkeiten einzelner GPIOs.
3. **Übersetzungseinheits-übergreifende Peripherie-Wechselwirkungen.** Der Aufruf `analogRead(5)` ist isoliert betrachtet nicht pauschal illegal; der Konflikt entsteht erst durch die projektweite Kombination mit `WiFi.begin(...)` – potenziell in einer anderen `.cpp`-Übersetzungseinheit. Da C++-Compiler jede Übersetzungseinheit getrennt verarbeiten und keine Peripherie-Interferenzanalyse durchführen, bleibt dieser globale Konflikt unerkannt.

Über das rein technische Risiko hinaus besitzt diese Lücke erhebliche **wirtschaftliche Relevanz**. Bereits Boehm zeigte in seiner grundlegenden Untersuchung zur Software-Ökonomie, dass die Kosten zur Fehlerbehebung über die Phasen des Entwicklungszyklus stark ansteigen [[4]](#ref-4); Boehm und Basili bestätigten dieses Verhältnis später auch für kleinere, iterativ arbeitende Entwicklungsteams mit typischen Kostenfaktoren von 5:1 bis über 100:1 zwischen früher und später Entdeckung [[5]](#ref-5). Im industriellen Embedded-Prototyping – etwa in der angewandten Forschung und Entwicklung bei Freudenberg Technology Innovation (FTI) – potenziert sich dieser Hebel durch die Kopplung an physische Hardware: Wird ein Pin-Konflikt erst nach dem Aufbau eines Laborprüfstands oder nach Fertigung einer kundenspezifischen Prototyp-Leiterplatte entdeckt, fallen neben mehreren Stunden Fehlersuche an Oszilloskop und Logikanalysator im ungünstigsten Fall direkte Fertigungskosten und mehrwöchige Lieferverzögerungen für einen Leiterplatten-Respin an. Eine deterministische *Shift-Left*-Verifikation vor dem Kompilieren adressiert diesen Kostenhebel unmittelbar (vgl. Abschnitt 7.6).

### 1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen

Die technischen Referenzhandbücher der ESP32-Familie [[9]](#ref-9), [[10]](#ref-10) erklären die physikalische Asymmetrie zwischen digitalen und analogen Pins über die drei oben eingeführten Verschaltungsebenen: Digitale Peripheriesignale (I2C, SPI, UART, LEDC-PWM) lassen sich über die **GPIO-Matrix** flexibel auf beliebige freie Ausgangs- und Eingangspins routen (bei lediglich geringer zusätzlicher Synchronisationslatenz von typischerweise zwei APB-Taktzyklen gegenüber direkten `IO_MUX`-Pfaden). Analoge Signale (`ADC1`, `ADC2`) sowie der native USB-PHY sind dagegen über dedizierte analoge Pad-Schalter **fest an definierte physische Pins gebunden**, und die Speicheranbindung (`SPI0/1`, `VDD_SPI`) belegt feste Gehäusekontakte. Während ein digitales Signal somit meist frei verlagert werden kann, verfügen analoge Sensoren nur über eine eng begrenzte, physikalisch fixierte Kandidatenmenge.

Für diese Arbeit wird eine Taxonomie aus **fünf Fehlerklassen** zugrunde gelegt, die das Prüfspektrum von `mcu-pin-solver` definiert (Tabelle 1.1). Sie deckt die im Arduino-/ESP32-Prototyping dominierenden Pin-Fehler systematisch ab, erhebt jedoch keinen Anspruch auf Vollständigkeit hinsichtlich elektrischer Dimensionierung (etwa Strombelastbarkeit, Pegelanpassung oder Peripherie-Instanzbudgets; vgl. Abschnitt 8.2).

1. **Reservierte und nicht existierende Pins.** Beim ESP32-C3 ist GPIO 11 standardmäßig als Flash-Versorgungsspannung (`VDD_SPI`) konfiguriert (nur bei externer Flash-Versorgung und gebranntem `EFUSE_VDD_SPI_AS_GPIO` als GPIO nutzbar), während GPIO 12–17 auf Varianten mit integriertem SPI-Flash fest die Busleitungen (`SPIHD`, `SPIWP`, `SPICS0`, `SPICLK`, `SPID`, `SPIQ`) führen [[9]](#ref-9). Beim ESP32-S3 sind GPIO 26–32 für Quad-SPI-Flash bzw. PSRAM reserviert; auf Modulen mit Octal-SPI-Flash oder Octal-PSRAM (z. B. `ESP32-S3-WROOM-1-N8R8`/`N16R8`) belegen zusätzlich GPIO 33–37 die erweiterten Daten- und Strobe-Leitungen (`SPIIO4`–`SPIIO7`, `SPIDQS`) [[10]](#ref-10). Ein Umkonfigurieren dieser Pins unterbricht das Nachladen von Instruktionen aus dem Flash und führt unmittelbar zu einem Absturz oder Watchdog-Reset. Hinzu kommen auf dem Zielchip nicht existierende bzw. nicht herausgeführte Pin-Nummern (im Folgenden auch informell als *Geister-Pins* bezeichnet) – etwa GPIO 32, das vom älteren ESP32 geläufig ist, auf dem ESP32-C3 jedoch gar nicht existiert.
2. **Konflikte durch aktive Peripherie.** Beide betrachteten SoCs enthalten zwei 12-Bit-SAR-ADCs (`ADC1` und `ADC2`). Während `ADC1` (ESP32-C3: GPIO 0–4; ESP32-S3: GPIO 1–10) vom HF-Subsystem isoliert arbeitet, konkurriert `ADC2` (ESP32-C3: GPIO 5; ESP32-S3: GPIO 11–20) mit dem WLAN-Subsystem um gemeinsam genutzte Hardware-Ressourcen (Arbiter bzw. HF-Leistungsmessung/Kalibrierung) [[11]](#ref-11). Beim ESP32-S3 führt paralleler WLAN-Betrieb zu Arbitrierungskonflikten und fehlgeschlagenen bzw. unzuverlässigen `ADC2`-Messungen; beim ESP32-C3 tritt zusätzlich das im *SoC Errata* dokumentierte Hardware-Erratum `ADC-183` (instabiler Digital-Controller/DMA auf `ADC2`, fehlende Werkskalibrierung, standardmäßige Deaktivierung in neueren ESP-IDF-Versionen) hinzu [[9]](#ref-9), [[11]](#ref-11). Analog belegt die integrierte USB-Serial/JTAG-Schnittstelle fest GPIO 18 (`USB_D-`) und GPIO 19 (`USB_D+`) beim ESP32-C3 bzw. GPIO 19 (`USB_D-`) und GPIO 20 (`USB_D+`) beim ESP32-S3 (dort zusätzlich geteilt mit USB-OTG) [[9]](#ref-9), [[10]](#ref-10).
3. **Fehlende Hardware-Fähigkeit.** Nicht jedes Pad unterstützt jede Funktion. GPIO 6 des ESP32-C3 ist beispielsweise an keinen SAR-ADC angebunden; ein Aufruf `analogRead(6)` wird fehlerfrei kompiliert, liefert zur Laufzeit in Arduino-ESP32 jedoch lediglich `0` zurück, da die interne Kanalzuordnung keinen gültigen ADC-Kanal findet.
4. **Doppelbelegung versus zulässige Bus-Teilung.** Zwei voneinander unabhängige digitale Verbraucher auf demselben Pin erzeugen elektrische Treiberkonflikte (im Extremfall Kurzschlüsse zwischen Ausgangsstufen) oder korrumpieren Steuersignale. Bei geteilten seriellen Bussen ist die gemeinsame Pin-Nutzung für *identische Signalleitungen desselben Bus-Controllers* hingegen ausdrücklich vorgesehen: Mehrere I2C-Geräte teilen sich gemeinsam `SDA` und `SCL` desselben Controllers (`Wire`), mehrere SPI-Geräte teilen sich `SCK`, `MISO` und `MOSI`. Umgekehrt stellen das Zusammenlegen von `SDA` und `SCL`, die Kollision zweier getrennter Bus-Instanzen (`Wire` vs. `Wire1`) oder die Doppelbelegung einer SPI-Chip-Select-Leitung (`CS`/`SS`) harte Fehler dar.
5. **Strapping-Pins (Boot-Konfigurationspins).** Beim Verlassen des Hardware-Resets (steigende Flanke an `CHIP_EN`) tastet der Chip definierte Strapping-Pins ab, um Boot-Modus, ROM-Ausgabe, JTAG-Quelle oder Flash-Versorgungsspannung festzulegen: beim ESP32-C3 GPIO 2, 8 und 9 [[9]](#ref-9), beim ESP32-S3 GPIO 0, 3, 45 (Auswahl der `VDD_SPI`-Spannung 3,3 V vs. 1,8 V) und 46 [[10]](#ref-10). Nach abgeschlossenem Reset lassen sich diese Pins zwar regulär als GPIOs nutzen – wie beispielsweise GPIO 8 für die Onboard-LED des `esp32-c3-devkitm-1` –, externe Pull-up-/Pull-down-Netzwerke oder angeschlossene Lasten können den Bootvorgang jedoch verfälschen oder verhindern. Im Unterschied zu den Klassen 1 bis 4 ist Klasse 5 kein harter Verbotsfehler, sondern ein Vermeidungskriterium bei der automatischen Neuzuweisung.

| Fehlerklasse | Konkretes Beispiel (ESP32-C3) | Folge auf der Zielhardware |
| :--- | :--- | :--- |
| 1 Reservierte / fehlende Pins | `STATUS_LED = 12` (SPI-Flash), `PIR_SENSOR = 32` (nicht vorhanden) | Absturz / Boot-Loop bzw. wirkungslose Ansteuerung |
| 2 Aktive Peripherie | `SOIL_SENSOR = 5` (`ADC2`) bei aktivem `WiFi.begin`; USB auf 18/19 | Fehlgeschlagene Analogmessung bzw. Verlust der USB-Verbindung |
| 3 Fehlende Fähigkeit | `analogRead(6)` (kein ADC-Kanal auf GPIO 6) | Ungültiger Messwert (`0`) ohne Compiler-Warnung |
| 4 Doppelbelegung | `BUZZER_PIN = 7` und `SERVO_PIN = 7`; `SDA = 6` und `SCL = 6` | Signalkorruption, Bus-Blockade oder elektrischer Treiberkonflikt |
| 5 Strapping-Pins | Externe Beschaltung an GPIO 2, 8 oder 9 | Fehlstart in den Download-Modus oder unterdrückter Bootvorgang |

*Tabelle 1.1: Fünf Fehlerklassen bei der GPIO-Pin-Belegung und ihre Hardware-Auswirkungen.*

### 1.4 Zielsetzung und Forschungsfragen

Ziel dieser Studienarbeit ist der Entwurf, die prototypische sowie produktionsreife Implementierung und die empirische Evaluation eines statischen Pre-Build-Prüfwerkzeugs (`mcu-pin-solver`), das die fünf genannten Fehlerklassen in ein- und mehrdateiigen PlatformIO-Projekten vor dem Kompilieren identifiziert, mit präzisem Dateizeilen-Verweis meldet und eine formal geprüfte, minimal-invasive Ersatzbelegung für die Rückführung an ein Sprachmodell berechnet. Das mikrocontrollerspezifische Wissen ist dabei als schema-validierte, deklarative JSON-Datenschicht strikt von der Analyse- und Solver-Logik zu trennen, sodass neue Zielchips ohne Änderung am Python-Code integriert werden können.

Aus dieser Zielsetzung werden drei leitende Forschungsfragen abgeleitet:

- **FF1 – Extraktion:** Wie lassen sich Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Hardware-Fähigkeiten, Bus-Leitungsrollen und aktive Peripheriemodule über mehrere C/C++-Dateien hinweg zuverlässig und fehlalarmarm extrahieren, ohne eine Ziel-Cross-Compiler-Toolchain vorauszusetzen?
- **FF2 – Prüfung und Reparatur:** Wie lässt sich mikrocontrollerspezifisches Hardware-Wissen als validierbare Datenschicht vom Prüfcode entkoppeln und so in ein formales Optimierungsmodell übersetzen, dass im Konfliktfall eine beweisbar zulässige Ersatzbelegung entsteht, die gültige Originalpins bewahrt, geteilte Bus-Leitungen erhält, Strapping-Pins meidet und knappe Spezialpins schont?
- **FF3 – Integration und Praxistauglichkeit:** Wie lässt sich die Prüfung als Python- und PlatformIO-Paket so in bestehende Embedded-Workflows einbetten, dass fehlerhafte Builds vor dem Kompilieren abgebrochen werden, ein direkt verwertbarer LLM-Reparatur-Prompt entsteht und der Einsatz im industriellen Prototyping wirtschaftlich tragfähig bleibt?

**Präzisierung des Verifikationsbegriffs.** Wenn diese Arbeit von *Hardware-Verifikation* spricht, bezeichnet dies eine formale Korrektheits- und Optimalitätsprüfung des *aus dem Quelltext extrahierten Pin-Modells* $\mathcal{M}_{\text{code}}$ gegenüber dem *deklarativen Hardware-Modell* $\mathcal{S}_{\text{board}}$ ($\mathcal{M}_{\text{code}} \models \mathcal{S}_{\text{board}}$). Bewiesen wird damit weder die funktionale Gesamt-Korrektheit der Firmware noch deren elektrische Betriebssicherheit auf Schaltungsebene. Die Vollständigkeit der Fehlererkennung bleibt prinzipbedingt an die syntaktische Extraktionsabdeckung des Parsers sowie an die Datenblatt-Treue des jeweiligen JSON-Profils gebunden (vgl. Abschnitte 7.8 und 8.2).

### 1.5 Methodisches Vorgehen und Aufbau der Arbeit

Die Softwareentwicklung folgte einem iterativen, testgetriebenen Vorgehen in zwei klar abgegrenzten Ausbaustufen:

1. **Prototyp (`v0.1.0`):** Aufbau einer minimalen vertikalen Durchstich-Pipeline aus Tree-Sitter-Parser, Z3-MaxSMT-Solver, zwei Hardware-Profilen (`esp32-c3`, `esp32-s3`), neun End-to-End-Regressionsszenarien und einem PlatformIO-Hook. Mittels gezielter Grenzfallexperimente (*Fault Injection*) wurden anschließend systematisch Extraktions-, Modellierungs- und Paketierungsschwächen identifiziert.
2. **Produktionsreife Überarbeitung (`v0.2.0`):** Auf Grundlage dieser empirischen Befunde wurde die Architektur vollständig refaktoriert – unter Einführung eines eigenen, schema-validierenden Board-Moduls (`board.py`), unveränderlicher typisierter Datenklassen, expliziter Bus-Leitungsrollen (`bus_group`), dreistufig gewichteter MaxSMT-Optimierung, korrigierter `pip`- und PlatformIO-Paketierung sowie 42 modularer Unit- und Integrationstests unter GitHub Actions CI (`ruff`, `mypy`, Windows und Linux).

Diese Ausarbeitung dokumentiert den finalen Softwarestand **`0.2.0`** (identisch zu den in den Anhängen A bis E abgedruckten Quelltexten) und belegt den erreichten Qualitätszuwachs gegenüber `v0.1.0` in Abschnitt 7.4 anhand reproduzierbarer Vergleichsexperimente.

Der weitere Aufbau gliedert sich wie folgt: Kapitel 2 legt die theoretischen Grundlagen in den Bereichen LLMs, neuro-symbolische KI, formale Syntaxanalyse mit Tree-Sitter, SAT/SMT/MaxSMT in Z3 sowie PlatformIO-Build-Mechanismen. Kapitel 3 diskutiert verwandte wissenschaftliche Arbeiten (u. a. Logic-LM, SatLM, LLM4PLC, AutoIOT, EmbedGenius) und klassische Embedded-Werkzeuge und arbeitet die adressierte Forschungslücke heraus. Kapitel 4 spezifiziert funktionale und nicht-funktionale Anforderungen nach ISO/IEC 25010:2023 sowie verbindliche Architektur-Invarianten. Kapitel 5 begründet vier zentrale Entwurfsentscheidungen anhand gewichteter Nutzwert- und Sensitivitätsanalysen und verfolgt ein durchgängiges Beispiel. Kapitel 6 erläutert die modulare Implementierung top-down, einschließlich einer formalen Analyse der Gewichtungsdominanz im MaxSMT-Modell. Kapitel 7 evaluiert das System anhand der Testsuite, der Grenzfallexperimente, von Laufzeit- und Skalierungsmessungen bis 20 Pins, eines realen PlatformIO-Registry-Tests sowie einer TCO- und Break-even-Analyse. Kapitel 8 diskutiert Ergebnisse, Systemgrenzen, KI-gestützte Entwicklungsreflexion und Ausbauperspektiven; Kapitel 9 schließt mit der Beantwortung der Forschungsfragen.

---

## 2 Grundlagen

Dieses Kapitel vermittelt die theoretischen Grundlagen der vier tragenden Säulen des Systems: Sprachmodelle und neuro-symbolische Kopplung (Abschnitte 2.1–2.2), syntaktische Quelltextanalyse mit Tree-Sitter (Abschnitte 2.3–2.4), logische Erfüllbarkeit und MaxSMT-Optimierung mit Z3 (Abschnitte 2.5–2.6) sowie das Build-System PlatformIO (Abschnitt 2.7).

### 2.1 Große Sprachmodelle

Große Sprachmodelle (LLMs) basieren auf autoregressiven neuronalen Netzen der *Transformer*-Architektur [[24]](#ref-24), die auf umfangreichen Korpora aus natürlicher Sprache und Quelltext trainiert werden. Bei der Codegenerierung schätzt das Modell iterativ die bedingte Wahrscheinlichkeitsverteilung über das nächste Token $t_k$ gegeben dem bisherigen Kontext $t_1, \dots, t_{k-1}$,

$$P(t_k \mid t_1, \dots, t_{k-1}),$$

und wählt daraus gemäß der Dekodierungsstrategie das Folgetoken (*Next-Token-Prediction*). Das Modell führt dabei keine symbolische Konsistenzprüfung über die physikalischen Eigenschaften des Zielchips durch, sondern reproduziert statistisch wahrscheinliche Token-Sequenzen.

Für die Mikrocontroller-Pin-Belegung resultieren daraus drei strukturelle Schwächen:

1. **Verzerrung durch Trainingsdaten (*Distributional Bias*).** Öffentlich verfügbare Embedded-Codebasen werden historisch stark vom klassischen ESP32 (Xtensa LX6) dominiert, auf dem etwa GPIO 12 oder GPIO 32 häufig als Standardpins verwendet werden. Es ist plausibel, dass LLMs solche hochfrequenten Pin-Muster auf neuere Varianten wie den ESP32-C3 übertragen, auf denen GPIO 12 zum internen SPI-Flash gehört und GPIO 32 gar nicht existiert.
2. **Fehlende globale Constraint-Erhaltung.** Durch die links-nach-rechts erfolgende Token-Erzeugung existiert keine formale Invarianzprüfung zwischen entfernt stehenden Deklarationen und Peripherieaufrufen: Wird `WiFi.begin(...)` erst später im Funktionskörper oder in einer anderen Datei generiert, erfolgt keine garantierte Rückprüfung, ob eine frühere Zuweisung wie `SOIL_SENSOR = 5` dadurch unzulässig geworden ist.
3. **Unzuverlässige intrinsische Selbstkorrektur.** Huang et al. belegen empirisch, dass LLMs logische und kombinatorische Fehler ohne verlässliches externes Feedback nicht konsistent korrigieren können – reine Selbstüberprüfungsprompts verschlechtern korrekte Lösungen teilweise sogar [[15]](#ref-15).

### 2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip

Garcez und Lamb ordnen die Entwicklung künstlicher Intelligenz in drei Wellen ein [[13]](#ref-13): Die erste, **symbolische** Welle nutzt explizite Logik- und Regelkalküle mit starken Korrektheitsgarantien, stößt jedoch bei offenen, unstrukturierten Aufgaben an Skalierungs- und Modellierungsgrenzen. Die zweite, **neuronale** Welle – repräsentiert durch moderne LLMs – überzeugt durch Generalisierung und hohe Synthesegeschwindigkeit, bietet jedoch keine formalen Garantien. Die dritte Welle, die **neuro-symbolische KI**, kombiniert die generative Leistungsfähigkeit neuronaler Modelle mit der deterministischen Prüf- und Beweiskraft symbolischer Verfahren.

Kambhampati et al. präzisieren dieses Zusammenspiel im **LLM-Modulo-Framework** [[17]](#ref-17): Ein LLM fungiert als flexibler Lösungsgenerator, während deterministische externe Prüfer (*Critics*) jeden Entwurf gegen formale Spezifikationen validieren und präzises, umsetzbares Korrekturfeedback zurückspeisen, bis sämtliche Anforderungen erfüllt sind. Dabei werden unverhandelbare *harte* Prüfer von qualitätsbewertenden *weichen* Prüfern unterschieden.

In `mcu-pin-solver` übernimmt das Sprachmodell die Erzeugung der C++-Firmware, während die symbolische Pipeline aus Tree-Sitter-Parser, deterministischem Regelprüfer und Z3-MaxSMT-Optimierer als externer Hardware-Critic agiert (Abbildung 2.1). Präzisierend ist festzuhalten, dass das Softwarepaket `mcu-pin-solver` selbst kein neuronales Modell enthält; neuro-symbolisch ist das *Gesamtsystem* aus generierendem Sprachmodell und deterministischem Verifikator.

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
  │ 3. Prüfen & Optimieren (Regeln + Z3 MaxSMT vs. JSON-Profil)│
  └───────────────┬──────────────────────────────┬─────────────┘
          UNSAT   ▼                              ▼   SAT
  ┌───────────────────────────────┐  ┌────────────────────────┐
  │ 4. Build stoppen, Reparatur-  │  │ Cross-Compiler startet │
  │    Prompt mit Z3-Lösung       │  └────────────────────────┘
  └───────────────┬───────────────┘
                  └──────► zurück zu 1 (LLM übernimmt geprüfte Pins)
```
*Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver` (in Anlehnung an [[17]](#ref-17)).*

### 2.3 Quelltextanalyse: von regulären Ausdrücken zum Syntaxbaum

Die zuverlässige Extraktion von Pin-Zuweisungen und Peripherieaufrufen aus C++-Quelltext lässt sich mit **regulären Ausdrücken** (*Regex*) prinzipiell nicht fehlerfrei realisieren. In der Chomsky-Hierarchie erkennen reguläre Ausdrücke (ohne nicht-reguläre Rückreferenzen) ausschließlich **Typ-3-Sprachen** (reguläre Sprachen) [[14]](#ref-14). Sie können bereits beliebig tief geschachtelte Klammerstrukturen nicht korrekt erkennen (Pumping-Lemma) und verfügen über kein Verständnis lexikalischer oder syntaktischer Kontexte. Im Embedded-C++-Alltag scheitert eine zeilen- oder textbasierte Regex-Suche daher regelmäßig an elementaren Konstrukten:

1. **Kommentare:** `// WiFi.begin("Test");` oder mehrzeilige Blockkommentare `/* ... */` würden fälschlich als aktive Peripherieaufrufe gewertet.
2. **Zeichenkettenliterale:** `Serial.println("WiFi.begin() fehlgeschlagen");` enthielte ein falsch-positives Auslösemuster.
3. **Gültigkeitsbereiche (Scopes):** Lokale Schleifen- oder Zählvariablen (`int retries = 12;` innerhalb von `loop()`) sind ohne Blockstruktur-Analyse nicht verlässlich von globalen Pin-Konstanten trennbar.
4. **Lexikalische Varianz:** In C++ sind beliebige Leerräume und Zeilenumbrüche zwischen Tokens zulässig, etwa `WiFi . begin ( ... )`.

C++ überschreitet sogar die Klasse der kontextfreien Sprachen (Typ 2): Aufgrund des Präprozessors sowie kontextabhängiger Mehrdeutigkeiten wie dem sogenannten *Lexer Hack* (ein Ausdruck `T * x;` kann je nach Symboltabelle eine Zeigerdeklaration oder eine Multiplikation darstellen) und geschachtelter Template-Klammern ist C++ formal kontextsensitiv. Ein vollständiges Compiler-Frontend [[1]](#ref-1) durchläuft daher nach dem Präprozessor die lexikalische Analyse (Tokenisierung), die syntaktische Analyse (Aufbau eines Ableitungsbaums) sowie die semantische Analyse mit Symbol- und Typauflösung.

Für die Darstellung der syntaktischen Struktur unterscheidet man zwischen dem **konkreten Syntaxbaum** (*Concrete Syntax Tree*, CST), der jedes Eingabetoken einschließlich Interpunktion, Schlüsselwörtern und Kommentaren exakt abbildet, und dem **abstrakten Syntaxbaum** (*Abstract Syntax Tree*, AST), der auf die semantisch tragenden Konstrukte reduziert ist (Abbildung 2.2). Da Kommentare und Zeichenketten im Syntaxbaum als explizit typisierte Knoten (`comment`, `string_literal`) repräsentiert werden, bleibt eine gezielte Traversierung nach Aufrufknoten (`call_expression`) gegen Textinhalte in Kommentaren und Strings strukturell immun.

```text
Quelltext:  const int LED = 12;

Konkreter Syntaxbaum (CST)                Abstrakte Sicht (AST)
declaration                               declaration
 ├── type_qualifier ('const')              ├── Typ:  int
 ├── primitive_type ('int')                └── Name: LED, Wert: 12
 ├── init_declarator
 │    ├── identifier ('LED')
 │    ├── '='  (anonymer Knoten)
 │    └── number_literal ('12')
 └── ';'       (anonymer Knoten)
```
*Abbildung 2.2: Konkreter Syntaxbaum (CST) und abstrakte Sicht (AST) am Beispiel einer C++-Deklaration.*

### 2.4 Tree-Sitter

**Tree-Sitter** ist ein Parser-Generator, der deklarative Sprachgrammatiken in eigenständige, in C generierte, tabellengesteuerte **GLR-Parser** (*Generalized LR*) übersetzt – unter anderem für C++ (`tree-sitter-cpp`) [[6]](#ref-6). Anders als klassische deterministische LR(1)-Parser kann ein GLR-Parser bei lokal mehrdeutigen C++-Konstrukten (die ohne Symboltabelle nicht eindeutig entscheidbar sind) mehrere Ableitungspfade parallel verfolgen und Konflikte über grammatikdefinierte Präzedenzregeln auflösen. Für kontextabhängige lexikalische Konstrukte (wie C++-Raw-String-Literale `R"(...)"`) bindet `tree-sitter-cpp` zusätzlich einen handgeschriebenen *External Scanner* in C ein.

Obschon Tree-Sitter ursprünglich für die inkrementelle Echtzeitanalyse in Code-Editoren entworfen wurde, wird der inkrementelle Re-Parse-Mechanismus in `mcu-pin-solver` nicht benötigt, da jeder Validierungslauf einen einmaligen Batch-Durchlauf über die Projektdateien ausführt. Entscheidend für die vorliegende Architektur sind vier andere Eigenschaften:

1. **Robuste Fehlerbehandlung (*Error Recovery*).** Selbst bei unvollständigen LLM-Codefragmenten oder fehlenden Header-Dateien (`Arduino.h`, ESP-IDF-Bibliotheken) bricht Tree-Sitter nicht ab, sondern isoliert fehlerhafte Stellen lokal als `ERROR`- bzw. `MISSING`-Knoten und liefert für den übrigen Quelltext einen intakten Baum.
2. **Kein Ziel-Compiler erforderlich.** Die Analyse erfolgt vollständig in einer kompakten C-Laufzeitbibliothek mit Python-Anbindung, ohne dass eine Cross-Compiler-Toolchain oder Board-SDK-Header installiert sein müssen.
3. **AST-ähnliche Projektion über den CST.** Tree-Sitter erzeugt intern einen vollständigen **CST** mit exakten Byte-Bereichen (`start_byte`, `end_byte`) und Zeilen-/Spaltenkoordinaten (`start_point`, `end_point`). Durch die Trennung zwischen **benannten Knoten** (`named_children`, entsprechend Grammatikregeln wie `call_expression` oder `identifier`) und **anonymen Knoten** (Interpunktionsliterale wie `(`, `,`, `;`) sowie durch **benannte Felder** (`child_by_field_name("function")`, `"arguments"`, `"name"`, `"value"`) bietet die API jedoch unmittelbar eine komfortable abstrakte Sicht. Zu beachten ist lediglich, dass Kommentarknoten (`comment`) als *Extras* zu den benannten Knoten zählen und in Argumentlisten explizit herausgefiltert werden müssen.
4. **Explizite Abbildung von Präprozessor-Direktiven.** Da Tree-Sitter **keinen C-Präprozessor** ausführt und **keine Typauflösung** betreibt, erscheinen Präprozessor-Direktiven direkt als Syntaxknoten im Baum (`preproc_def`, `preproc_ifdef`, `preproc_else`). Makros werden nicht expandiert, und sämtliche Zweige bedingter Kompilierung (`#ifdef`/`#else`) sind gleichzeitig sichtbar.

Abbildung 2.3 zeigt den realen, gekürzten Syntaxbaum eines Beispielprogramms aus dem Versuchsskript in Anhang G.

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
*Abbildung 2.3: Von Tree-Sitter erzeugter konkreter Syntaxbaum eines Beispielprogramms (gekürzte Ausgabe des Versuchsskripts, siehe Anhang G).*

Drei strukturelle Details aus Abbildung 2.3 prägen die Implementierung in Kapitel 6 unmittelbar: Auskommentierte Aufrufe erscheinen als `comment`, Zeichenketten als `string_literal` innerhalb der Argumentliste, und der Rumpf eines Makros (`preproc_arg`) umfasst die rohe Restzeile **einschließlich nachgestellter Kommentare** (`'12 // Board-LED'`), die vor der Zahlenextraktion lokal bereinigt werden müssen.

### 2.5 SAT, SMT und der Solver Z3

Zur formalen Konfliktlösung setzt `mcu-pin-solver` den SMT-Solver **Z3** von Microsoft Research ein [[7]](#ref-7). Das Verfahren ruht auf drei aufeinander aufbauenden Konzepten der automatischen Beweisführung [[2]](#ref-2):

- **SAT (Aussagenlogische Erfüllbarkeit):** Ein SAT-Solver entscheidet für eine aussagenlogische Formel (typischerweise in konjunktiver Normalform), ob eine Belegung der booleschen Variablen existiert, unter der die Formel wahr wird (`SAT`), oder ob ein Widerspruch vorliegt (`UNSAT`). Moderne Solver arbeiten nach dem **CDCL**-Verfahren (*Conflict-Driven Clause Learning*): Tritt bei der Suche ein Konflikt auf, leitet der Solver mittels Implikationsgraphen eine gelernte Konfliktklausel ab, führt nicht-chronologisches Backtracking durch und schließt den betroffenen Teilraum künftig aus.
- **SMT (Erfüllbarkeit modulo Theorien):** Da GPIO-Nummern diskrete Ganzzahlen darstellen, hebt SMT die aussagenlogische Prüfung auf erststufige Formeln mit interpretierten Hintergrundtheorien an. Im vorliegenden Modell wird jede Pin-Anforderung als ganzzahlige Entscheidungsvariable $v_i \in \mathbb{Z}$ (`z3.Int`) deklariert; sämtliche Bedingungen verwenden ausschließlich Gleichheiten ($v_i = p$, $v_i = v_j$) und Ungleichheiten ($v_i \neq p$, $v_i \neq v_j$). Syntaktisch liegt die Formel damit in der entscheidbaren, NP-vollständigen Logik der quantorenfreien linearen Ganzzahlarithmetik (**`QF_LIA`**) [[2]](#ref-2). Semantisch handelt es sich – da jede Variable über eine explizite Disjunktion auf eine endliche Kandidatenmenge $P_i \subset \mathbb{N}_0$ eingeschränkt ist – um ein endliches Domänen-Erfüllbarkeitsproblem (*Finite-Domain CSP*, verwandt mit **`QF_FD`**). Diese Unterscheidung zwischen syntaktischer `QF_LIA`-Kodierung und semantischer endlicher Domäne erweist sich in Abschnitt 7.5 als zentral für die Erklärung des empirischen Skalierungsverhaltens.
- **CDCL($T$) (historisch DPLL($T$)):** Intern koppelt Z3 einen CDCL-SAT-Kern mit spezialisierten Theorie-Solvern (für `QF_LIA` insbesondere einem dualen Simplex-Verfahren samt Ganzzahligkeits-Branch-and-Bound und Gleichheitspropagation). Der SAT-Kern schlägt boolesche Abstraktionen vor, während der Theorie-Solver deren Konsistenz prüft und bei Widersprüchen generalisierte Theorie-Lemmata an den SAT-Kern zurückmeldet [[2]](#ref-2).

### 2.6 Optimierung mit MaxSMT

Ein reiner Entscheidungs-Solver (`z3.Solver`) gibt eine *beliebige* erfüllende Belegung zurück und dürfte dabei auch bereits gültige, korrekt verdrahtete Pins unnötig verschieben. Für die Embedded-Praxis ist jedoch eine **minimal-invasive** Reparatur erforderlich, die zusätzlich hardwarefreundliche Ausweichpins (keine Strapping-Pins, Schonung knapper ADC-/USB-Ressourcen) bevorzugt.

Formal entspricht dies einem **Partial-Weighted-MaxSMT-Problem**: Gegeben sind eine Menge unverhandelbarer *harter* Bedingungen $H$ (Gewicht $\infty$) sowie gewichtete *weiche* Bedingungen $\{(s_k, w_k)\}$ mit $w_k \in \mathbb{N}_{>0}$. Gesucht ist ein Modell $\mathcal{I} \models H$, das die Summe der Gewichte der erfüllten weichen Bedingungen maximiert (äquivalent zur Minimierung der Summe verletzter Gewichte).

In Z3 wird diese Problemklasse durch die Optimierungserweiterung **$\nu Z$** (`z3.Optimize`) gelöst [[3]](#ref-3), die harte Klauseln über `opt.add(...)` und gewichtete weiche Klauseln über `opt.add_soft(..., weight=w)` aufnimmt (Abbildung 2.4).

```text
  HARTE BEDINGUNGEN (opt.add – physikalisch unverhandelbar)
  • jeder Pin liegt in seiner gültigen Kandidatenmenge P_i (existiert, nicht reserviert,
    nicht durch aktive Peripherie gesperrt, unterstützt alle benötigten Fähigkeiten)
  • paarweise Disjunktheit v_i ≠ v_j – außer bei derselben geteilten Bus-Leitung
    mit identischem Originalpin (z. B. zwei Geräte an Wire:sda), die gekoppelt bleibt (v_i = v_j)
                                     │
                                     ▼  unter allen gültigen Modellen maximieren:
  WEICHE BEDINGUNGEN (opt.add_soft – dreistufige Gewichtung)
  • +1000 Punkte (Stufe 1): Signal behält seinen gültigen Originalpin (v_i = p_i^0)
  •   +20 Punkte (Stufe 2): Signal vermeidet Strapping-Pins (v_i ∉ S_i)
  •    +5 Punkte (Stufe 3): Signal schont knappe Spezialpins (ADC/USB), wenn nicht angefordert
```
*Abbildung 2.4: Harte und dreistufig gewichtete weiche Bedingungen im Partial-Weighted-MaxSMT-Modell.*

Intern verwendet $\nu Z$ für gewichtetes MaxSMT standardmäßig eine inkrementelle Variante des kernbasierten Algorithmus **MaxRes** (*Core-Guided MaxSAT Resolution*) [[3]](#ref-3), [[18]](#ref-18): Solange die aktuellen harten und aktiven weichen Klauseln gemeinsam unerfüllbar sind, extrahiert Z3 einen *unerfüllbaren Kern* $C$ weicher Klauseln mit Minimalgewicht $w_{\min} = \min_{s \in C} w(s)$, hebt die bewiesene untere Schranke der minimalen Verletzungskosten um $w_{\min}$ an, spaltet das Gewicht $w_{\min}$ von den Kernklauseln ab und ersetzt den Kern mittels MaxSAT-Resolutionsschritten durch $|C| - 1$ gewichtserhaltende Kompensationsklauseln. Im Gegensatz zu heuristischen Abbruchverfahren bleibt dabei die Kostenäquivalenz über sämtliche Belegungen gewahrt, sodass die nach Terminierung gefundene Lösung beweisbar global optimal ist. Während die Entscheidungsfrage für `QF_LIA` NP-vollständig ist, ist die gewichtete Optimierungsvariante **NP-schwer**; die praktischen Laufzeitgrenzen bis 20 konfliktbehaftete Signale werden in Abschnitt 7.5 empirisch bestimmt.

### 2.7 PlatformIO und der Build-Prozess

**PlatformIO** ist ein plattformübergreifendes Build- und Bibliotheksökosystem für Embedded-Projekte auf Basis von Python und dem Build-Werkzeug SCons [[20]](#ref-20). Projektkonfiguration, Zielboard (`board`), Framework (`arduino`, `espidf`), Abhängigkeiten (`lib_deps`) und Erweiterungsskripte (`extra_scripts`) werden deklarativ in `platformio.ini` definiert.

Für eine wirksame *Shift-Left*-Prüfung bietet PlatformIO einen definierten Erweiterungspunkt: Ein über `extra_scripts` mit Präfix `pre:` eingebundenes Skript – ebenso ein im Bibliotheksmanifest `library.json` unter `build.extraScript` deklariertes Skript – wird von SCons **vor** dem Aufruf des Ziel-C++-Compilers ausgeführt. Über die injizierte SCons-Umgebung (`Import("env")`) lassen sich Board-Kennung (`env.GetProjectOption("board")`), Quell- und Header-Verzeichnisse (`$PROJECT_SRC_DIR`, `$PROJECT_INCLUDE_DIR`) auslesen und ein fehlerhafter Build unmittelbar mittels `env.Exit(1)` abbrechen. `mcu-pin-solver` nutzt genau diesen Mechanismus als deterministische Qualitäts-Schranke vor dem Kompilieren.

Das Zusammenspiel dieser Grundlagen bildet die konzeptionelle Basis der Arbeit: Tree-Sitter erschließt die C++-Quelltextstruktur fehlertolerant ohne Cross-Compiler, Z3 $\nu Z$ garantiert formale Korrektheit und Optimalität relativ zum Hardware-Modell, und PlatformIO stellt den frühestmöglichen automatisierten Eingriffspunkt im Build-Zyklus bereit.

---

## 3 Verwandte Arbeiten und Stand der Technik

Dieses Kapitel verortet `mcu-pin-solver` in drei einschlägigen Forschungs- und Praxisfeldern: (1) der neuro-symbolischen Kopplung von Sprachmodellen mit formalen Solvern, (2) LLM-gestützten Verfahren für Embedded-, IoT- und Automatisierungssysteme sowie (3) etablierten Werkzeugklassen der industriellen Embedded-Entwicklung. Ziel ist eine kritische Abgrenzung der jeweiligen Annahmen und Systemgrenzen zur präzisen Herausarbeitung der Forschungslücke.

### 3.1 Neuro-symbolische Kopplung von LLMs mit formalen Solvern

Die empirische Beobachtung, dass Sprachmodelle bei kombinatorischer Suche und globaler Konsistenzhaltung systematisch versagen und ohne externes Korrektiv keine verlässliche intrinsische Selbstkorrektur leisten [[15]](#ref-15), hat ab 2023 eine Vielzahl neuro-symbolischer Architekturen hervorgebracht [[13]](#ref-13). Drei richtungsweisende Arbeiten bilden den methodischen Bezugsrahmen dieser Studienarbeit:

- **Logic-LM** (Pan et al., Findings of EMNLP 2023) [[19]](#ref-19) übersetzt natürlichsprachliche Problemstellungen durch ein LLM in formale Repräsentationen (u. a. Prädikatenlogik erster Stufe und Constraint-Programme), delegiert die Inferenz an deterministische Solver und führt deren Fehlermeldungen in einer *Self-Refinement*-Schleife zurück, um syntaktisch oder semantisch fehlerhafte Formalisierungen nachzubessern.
- **SatLM** (Ye et al., NeurIPS 2023) [[27]](#ref-27) überträgt dieses Prinzip explizit auf **SAT/SMT-Solver**: Anstatt das LLM eine imperative Lösungsprozedur erzeugen zu lassen, generiert es eine deklarative Constraint-Spezifikation, während ein automatischer Theorembeweiser die kombinatorische Suche vollständig übernimmt. Die Autoren weisen nach, dass sich Planungs- und Suchfehler gegenüber reinem Chain-of-Thought-Prompting deutlich reduzieren lassen.
- **LLM-Modulo** (Kambhampati et al., ICML 2024) [[17]](#ref-17) verallgemeinert diesen Ansatz zu einer modularen Architektur aus generativem LLM und heterogenen, deterministischen externen Prüfern (*Critics*), die unverhandelbare Korrektheits- und gewichtete Qualitätskriterien getrennt bewerten und strukturiertes Feedback liefern.

**Kritische Abgrenzung (Vermeidung des Formalisierungs-Flaschenhalses).** Sowohl *Logic-LM* [[19]](#ref-19) als auch *SatLM* [[27]](#ref-27) weisen für sicherheits- und hardwarenahe Embedded-Aufgaben eine strukturelle Schwachstelle auf: Das **Sprachmodell selbst** übernimmt die Übersetzung in die formale Logikspezifikation. Halluziniert das Modell bereits beim Aufstellen der SMT-Formel – vergisst es etwa die `ADC2`/WLAN-Ausschlussregel oder ordnet es dem ESP32-C3 fälschlich 36 GPIOs zu –, liefert selbst ein mathematisch exakter SMT-Solver eine physikalisch falsche Lösung. `mcu-pin-solver` dreht diese Aufgabenteilung gezielt um: Das LLM verbleibt in seiner trainingsdichten Domäne und generiert idiomatischen **Arduino-C++-Code**, während ein **deterministischer GLR-Syntaxbaum-Parser** (`tree-sitter-cpp`) gemeinsam mit einer **kuratierten, schema-validierten JSON-Hardware-Spezifikation** die Z3-Formel konstruiert. Übersetzungs-Halluzinationen beim Formulieren der Hardware-Constraints sind damit architektonisch ausgeschlossen; die Zuverlässigkeit hängt ausschließlich von der deterministischen Abdeckung des Parsers und der Datenblatt-Treue der JSON-Datei ab.

### 3.2 Sprachmodelle in der Embedded-, IoT- und Automatisierungsentwicklung

Parallel entstanden zwischen 2024 und 2025 mehrere zentrale Arbeiten zur LLM-gestützten Entwicklung eingebetteter Systeme und industrieller Steuerungen:

- **Empirische Hardware-in-the-Loop-Studie (Englhardt et al., CHI EA 2024)** [[8]](#ref-8): Die Autoren untersuchten GPT-3.5, GPT-4 und PaLM 2 auf realer Mikrocontroller-Hardware mit angeschlossenen Sensoren und Aktoren. Insbesondere GPT-4 erzeugte für viele Aufgaben lauffähigen Code und brauchbare Debugging-Hinweise, scheiterte jedoch wiederholt an hardwarespezifischen Details und erforderte menschliche Rückkopplung. Hardware-in-the-Loop-Tests (HIL) decken physikalische Fehler zwar realitätsnah auf, verlangen aber physisch verdrahtete Prüfstände und greifen im Entwicklungszyklus deutlich später ein als eine statische Pre-Build-Prüfung.
- **LLM4PLC (Fakih et al., ICSE-SEIP 2024)** [[12]](#ref-12): Für speicherprogrammierbare Steuerungen (SPS, IEC 61131-3 Structured Text) koppeln die Autoren ein Sprachmodell in einer iterativen Schleife mit Grammatikprüfer, Compiler und einem symbolischen Modellprüfer (NuSMV), dessen Gegenbeispiele zur Verfeinerung an das LLM zurückgespielt werden. Konzeptionell steht LLM4PLC dieser Arbeit am nächsten. Der wesentliche Unterschied liegt im Fehlerbehebungsmechanismus: LLM4PLC verifiziert funktionales Steuerungsverhalten und überlässt die Korrektur anhand von Gegenbeispielen vollständig dem Sprachmodell, wohingegen `mcu-pin-solver` auf Mikrocontroller-Pin-Constraints spezialisiert ist und die **beweisbar gültige, minimal-invasive Ersatzbelegung selbst per MaxSMT berechnet**, sodass das LLM nur noch verifizierte Zahlenwerte in den Quelltext einsetzen muss.
- **EmbedGenius (Yang et al., 2024)** [[26]](#ref-26) und **AutoIOT (Shen et al., ACM MobiCom 2025)** [[22]](#ref-22): Beide Frameworks automatisieren die Erstellung vollständiger IoT-/AIoT-Firmware (u. a. für ESP32 und Arduino) mittels LLM-Agenten, automatisierter Wissensaufbereitung über Hardware- und Bibliotheksdokumentation sowie iterativer Ausführungs- und Kompilierungsschleifen. Diese Arbeiten unterstreichen die praktische Relevanz der Domäne, zeigen jedoch zugleich, dass rein dokumentations- oder agentengetriebene Ansätze bei gekoppelten Pin-Multiplexing- und Peripheriekonflikten ohne formalen Constraint-Solver weiterhin probabilistisch iterieren müssen. Eine leichtgewichtige, deterministische Pre-Build-Komponente wie `mcu-pin-solver` lässt sich komplementär als lokaler Hardware-Critic in derartige Agenten-Pipelines einbetten.

### 3.3 Klassische Werkzeuge der Embedded-Praxis

Jenseits der KI-Forschung existieren in der industriellen Embedded-Softwareentwicklung vier etablierte Werkzeugklassen, die verwandte, aber konzeptionell anders gelagerte Probleme adressieren:

- **Statische C++-Analysewerkzeuge (`clang-tidy`, `cppcheck`):** Diese Werkzeuge erkennen klassische Softwaredefekte (Speicherfehler, uninitialisierte Variablen, implizite Typkonvertierungen, Stilverstöße), verfügen jedoch über kein Modell des Chip-Pin-Multiplexings oder projektweiter Peripherie-Wechselwirkungen. Zudem setzt `clang-tidy` eine vollständige Cross-Compiler-Konfiguration (`compile_commands.json` und Ziel-Header) voraus.
- **Grafische Hersteller-Konfiguratoren (`STM32CubeMX`)** [[23]](#ref-23): Werkzeuge wie `STM32CubeMX` modellieren Pin-Multiplexing und Peripheriekonflikte für herstellereigene MCUs hochpräzise und bieten sogar einen integrierten automatischen Pinout-Solver (*Find Solutions*). Sie arbeiten jedoch strikt **top-down** und herstellerspezifisch: Der Entwickler konfiguriert Peripherie manuell in einer GUI und generiert daraus Initialisierungscode. Bestehenden oder von einem LLM erzeugten Arduino-/PlatformIO-C++-Code können sie weder herstellerunabhängig einlesen noch minimal-invasiv reparieren.
- **Deklarative Hardware-Beschreibungen in RTOS-Ökosystemen (`Zephyr Devicetree`)** [[28]](#ref-28): Das Devicetree-Konzept trennt Pin- und Peripheriezuweisungen sauber in `.dts`-/`.overlay`-Dateien vom C-Code und validiert sie im Build-System gegen Bindings. Im verbreiteten Arduino-/PlatformIO-Prototyping – genau jenem Ökosystem, für das LLMs den Großteil ihrer Trainingsbeispiele besitzen – sind Pin-Definitionen jedoch unmittelbar im C++-Quelltext eingebettet.
- **Typsichere Hardware-Abstraktionen in Rust (`embedded-hal` / `esp-hal`)** [[21]](#ref-21): Chip-spezifische Rust-HALs auf Basis der `embedded-hal`-Traits nutzen das affine Ownership-Typsystem (Move-Semantik und *Typestate*-Muster) von Rust, um physische Pins als eindeutige, lineare Ressourcen abzubilden. Eine Doppelbelegung oder unzulässige Modusverwendung scheitert dadurch bereits zur Kompilierzeit. Dieses Prinzip lässt sich allerdings nicht auf bestehende C++-Codebasen im Arduino-/ESP-IDF-Ökosystem übertragen und berechnet bei Konflikten keine optimierte Ausweichbelegung.

### 3.4 Kritische Synthese und Forschungslücke

Tabelle 3.1 verdichtet den Literatur- und Werkzeugvergleich entlang von fünf Kriterien, die sich unmittelbar aus den Forschungsfragen FF1 bis FF3 ergeben.

| Ansatz / Referenz | Analysiert vorhandenen Arduino-C++-Code | Deterministisches Chip-Pin-Modell | Berechnet optimierte Ersatzbelegung | Kein physischer Prüfstand / Ziel-Compiler nötig | Einbindung in LLM-Rückkopplung |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logic-LM [[19]](#ref-19) / SatLM [[27]](#ref-27) | nein (NL $\rightarrow$ Logik) | nein (LLM formalisiert selbst) | ja (Solver) | ja | ja |
| Englhardt et al. [[8]](#ref-8) | ja | indirekt über Zielhardware | nein | nein (HIL-Prüfstand) | ja (Mensch-in-Schleife) |
| LLM4PLC [[12]](#ref-12) | nein (SPS-Code) | formaler Modellprüfer (NuSMV) | nein (LLM repariert) | teilweise (SPS-Toolchain) | ja |
| EmbedGenius [[26]](#ref-26) / AutoIOT [[22]](#ref-22) | ja (generierter Code) | nein (Dokumentation / Heuristik) | nein (LLM-Iteration) | nein / teilweise | ja (Agenten-Loop) |
| C++-Linter (`clang-tidy`, `cppcheck`) | ja | nein | nein | teilweise (`cppcheck`) | nein |
| STM32CubeMX [[23]](#ref-23) | nein (GUI $\rightarrow$ Code) | ja (nur STM32) | teilweise (Top-down-GUI-Solver) | ja | nein |
| Zephyr Devicetree [[28]](#ref-28) | nein (`.dts`) | ja | nein | nein (Zephyr-Build) | nein |
| Rust-HAL (`embedded-hal` / `esp-hal`) [[21]](#ref-21) | nein (Rust) | teilweise (Ownership/Typestate) | nein | nein (Rust-Compiler) | nein |
| **`mcu-pin-solver` (diese Arbeit)** | **ja (Teilmenge, vgl. 8.2)** | **ja (schema-validiertes JSON)** | **ja (Z3 MaxSMT)** | **ja** | **ja (Reparatur-Prompt)** |

*Tabelle 3.1: Einordnung verwandter Ansätze und Identifikation der Forschungslücke.*

**Forschungslücke.** Die Synthese offenbart eine klar umrissene Lücke an der Schnittstelle zweier Disziplinen: Bestehende LLM-Embedded-Frameworks [[8]](#ref-8), [[22]](#ref-22), [[26]](#ref-26) stützen sich bei der Hardware-Pin-Belegung auf probabilistische Nachbesserung oder nachgelagerte Hardware-Tests, während klassische Embedded-Werkzeuge [[21]](#ref-21), [[23]](#ref-23), [[28]](#ref-28) entweder herstellerspezifisch top-down operieren oder bestehende Arduino-C++-Projekte nicht ohne Ziel-Toolchain rückwärts analysieren und reparieren. Neuro-symbolische Solver-Pipelines wie Logic-LM [[19]](#ref-19) und SatLM [[27]](#ref-27) wiederum delegieren die Formalisierung an das LLM selbst und bleiben damit anfällig für Spezifikationshalluzinationen. Genau diese Lücke schließt `mcu-pin-solver` durch die Kombination aus deterministischer GLR-Syntaxanalyse, schema-validierter deklarativer Hardware-Spezifikation und minimal-invasiver Z3-MaxSMT-Reparatur als Pre-Build-Schranke in PlatformIO.

---

## 4 Anforderungsanalyse

### 4.1 Akteure und Anwendungsfälle

Das System adressiert drei klar abgrenzbare Akteursrollen:

1. **Embedded-Entwicklerinnen und -Entwickler** starten einen Build über PlatformIO (`pio run`) oder prüfen C++-Quelltext direkt auf der Kommandozeile (`mcu-validate`). Sie benötigen eine verzögerungsarme, fehlalarmarme Rückmeldung mit exaktem `datei:zeile`-Verweis und verständlicher Hardware-Begründung, noch bevor der Cross-Compiler anläuft.
2. **Das Sprachmodell (LLM)** generiert den C++-Firmware-Entwurf und empfängt im Konfliktfall einen kompakten, eindeutigen Reparatur-Prompt, der präzise vorgibt, welche Pin-Zuweisungen unverändert bleiben (`Keep`) und welche durch Z3-geprüfte Alternativen zu ersetzen sind (`Change`).
3. **Maintainer und Hardware-Verantwortliche** pflegen bestehende Profile und ergänzen neue Mikrocontroller ausschließlich über deklarative, schema-geprüfte JSON-Dateien (oder eigene per CLI übergebene Profildateien), ohne in die Python-Implementierung einzugreifen.

### 4.2 Funktionale Anforderungen

Tabelle 4.1 spezifiziert die zehn funktionalen Anforderungen (`FA-01` bis `FA-10`), aus denen sich Architektur, Schnittstellen und Testfälle unmittelbar ableiten.

| ID | Anforderung | Beschreibung |
| :--- | :--- | :--- |
| FA-01 | Hardware-Profil laden und validieren | Anhand einer Board-Kennung (z. B. `esp32-c3-devkitm-1`, `ESP32_S3`) oder eines direkten `.json`-Dateipfads wird das passende Profil (längste normalisierte Übereinstimmung zuerst) geladen und strikt gegen das erwartete Schema validiert. |
| FA-02 | Mehrdatei-Analyse und Include-Ordner | Bei Angabe eines Verzeichnisses `src/` werden alle `.h`-, `.hpp`-, `.c`-, `.cpp`- und `.ino`-Dateien in `src/` sowie einem benachbarten `include/`-Verzeichnis (und optional über `--include-dir` ergänzten Ordnern) rekursiv erfasst; Build- und Testverzeichnisse (`.pio/`, `build/`, `test/`, `tests/`) werden anhand des relativen Pfads ausgeschlossen. |
| FA-03 | Fehlalarmarme Syntaxbaum-Extraktion | Top-Level-Pin-Konstanten (`#define`, globale `int`/`uint8_t`-Deklarationen inkl. `const`/`constexpr`/`static`) sowie direkte numerische Pin-Literale (z. B. `pinMode(12, OUTPUT)`) werden über den Tree-Sitter-Syntaxbaum extrahiert; Kommentare, Zeichenketten, lokale Variablen in Funktionskörpern und fachfremde Konstanten (`BAUD_RATE`, `DELAY_MS`) erzeugen keine Fehlalarme. |
| FA-04 | Kollisionssichere Behandlung widersprüchlicher Definitionen | Identische Definitionen desselben Symbols über mehrere Dateien werden dedupliziert; widersprüchliche Wertzuweisungen desselben Bezeichners bleiben unter garantiert global eindeutigen Schlüsseln sichtbar. |
| FA-05 | Fähigkeiten, Bus-Rollen und aktive Module | Durch positionsgenaue Auswertung bekannter Arduino-/ESP32-API-Aufrufe sowie eine Namens-Fallback-Heuristik werden Mengen benötigter Fähigkeiten (`gpio`, `adc`, `pwm`, `i2c`, `spi`, `uart`), Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) und aktive Peripheriemodule (`wifi`, `usb_serial`) bestimmt. |
| FA-06 | Präzise Einzeldiagnose | Jeder Verstoß (nicht existierender Pin, Kollision, reservierter Pin, fehlende Fähigkeit, Sperre durch aktives Modul) wird einzeln mit `datei:zeile`-Verweis und der hinterlegten Regelbegründung im Klartext ausgegeben. |
| FA-07 | Trennung von Kollision und geteilter Bus-Leitung | Unabhängige Signale, unterschiedliche Bus-Leitungen (`SDA` vs. `SCL`, `SCK` vs. `MOSI`), getrennte Bus-Instanzen (`Wire` vs. `Wire1`) und SPI-Chip-Select-Leitungen (`CS`) dürfen keinen Pin teilen; Signale derselben geteilten Bus-Leitung (z. B. zwei Geräte an `Wire:sda`) dürfen denselben Pin teilen und bleiben bei einer Neuzuweisung gekoppelt. |
| FA-08 | Minimal-invasive Reparatur und Kapazitätsmeldung | Im Konfliktfall berechnet der Solver eine gültige Ersatzbelegung, die gültige Originalpins bewahrt, Strapping-Pins meidet und knappe ADC-/USB-Pins schont. Existiert keine zulässige Belegung, wird dies klar und ohne ungültige Platzhalter (`GPIO None`) gemeldet. |
| FA-09 | Transparenter Bericht und LLM-Reparatur-Prompt | Die Ausgabe weist stets die Anzahl geprüfter Pins aus (inkl. expliziter Warnung bei `0` erkannten Pins) und liefert im `UNSAT`-Fall alle Einzelkonflikte sowie vollständige `Keep`/`Change`-Anweisungen. |
| FA-10 | PlatformIO-Build-Schranke und eigenständige CLI | Als PlatformIO-Bibliothek (`dmatheja/mcu-pin-solver@^0.2.0`) bricht das Werkzeug fehlerhafte Builds vor dem Compilerstart ab; per `pip install .` steht der CLI-Befehl `mcu-validate` eigenständig zur Verfügung. |

*Tabelle 4.1: Funktionale Anforderungen.*

### 4.3 Nicht-funktionale Anforderungen (ISO/IEC 25010:2023)

Die nicht-funktionalen Anforderungen orientieren sich am Produktqualitätsmodell der aktuellen Norm **ISO/IEC 25010:2023** (*SQuaRE*) [[16]](#ref-16). Gegenüber der Vorgängerfassung von 2011 erweitert diese Norm das Modell auf neun Hauptmerkmale – insbesondere ersetzt *Flexibilität* (*Flexibility*, einschließlich *Skalierbarkeit*) das frühere Merkmal *Übertragbarkeit*, und *Funktionale Sicherheit* (*Safety*, u. a. mit den Teilmerkmalen *Operational Constraint* und *Risk Identification*) wurde als eigenständiges Qualitätsmerkmal aufgenommen.

| ID | Merkmal nach ISO/IEC 25010:2023 | Messbares Abnahmekriterium |
| :--- | :--- | :--- |
| NFA-01 | Wartbarkeit – Modifizierbarkeit | Der Python-Quelltext enthält keine fest codierten GPIO-Nummern oder mikrocontrollerspezifischen Konfliktregeln; die Unterstützung eines neuen Chips erfordert ausschließlich eine valide JSON-Profildatei. |
| NFA-02 | Leistungseffizienz – Zeitverhalten | Typische Embedded-Projekte (bis ca. 15–20 Dateien/Pins) werden in unter 1 s (und im konfliktfreien `SAT`-Fall deutlich darunter) geprüft; die empirische Skalierungsgrenze des MaxSMT-Solvers wird transparent vermessen. |
| NFA-03 | Flexibilität – Anpassbarkeit | Vollständig lauffähig unter Windows und Linux ohne installierte Cross-Compiler-Toolchain oder Ziel-SDK-Header. |
| NFA-04 | Funktionale Eignung & Safety (*Operational Constraint*, *Risk Identification*) | Jede ausgegebene Z3-Ersatzbelegung besteht eine unmittelbare automatische Re-Validierung gegen sämtliche harten Regeln des Hardware-Profils und blockiert hardwaregefährdende Pin-Zuweisungen vor dem Build. |
| NFA-05 | Flexibilität – Installierbarkeit | Sowohl `pip install .` (inklusive gebündelter Board-JSONs) als auch die Einbindung über die PlatformIO Registry funktionieren reproduzierbar; Demo-Quelltext wird nicht in fremde Projekte mitkompiliert; der CLI-Aufruf erzeugt unter `python -W error` keine Warnungen. |
| NFA-06 | Wartbarkeit – Testbarkeit | Eine modulare Testsuite deckt sämtliche Kernmodule und alle fünf Fehlerklassen ab und läuft plattformübergreifend in der CI gemeinsam mit statischer Typprüfung (`mypy`) und Linting (`ruff`). |
| NFA-07 | Wartbarkeit – Analysierbarkeit & Modularität | Top-down strukturierte Aufteilung in vier klar abgegrenzte Kernmodule (`board.py`, `parser.py`, `solver.py`, `cli.py`) mit unveränderlichen typisierten Datenklassen und minimalen Laufzeitabhängigkeiten (ausschließlich `z3-solver`, `tree-sitter`, `tree-sitter-cpp`). |

*Tabelle 4.2: Nicht-funktionale Anforderungen nach ISO/IEC 25010:2023 [[16]](#ref-16).*

### 4.4 Architektur-Invarianten und Systemgrenzen

Sechs verbindliche Architektur-Invarianten (Tabelle 4.3) fixieren grundlegende Entwurfsregeln, deren Einhaltung durch die automatisierte Testsuite und die CI-Pipeline kontinuierlich überprüft wird.

| ID | Invariante | Verbindliche Regel |
| :--- | :--- | :--- |
| INV-01 | Strikt datengetriebene Hardware-Schicht | GPIO-Nummern, reservierte Bereiche, Strapping-Pins, Peripherie-Auslöser und Konfliktregeln stehen ausschließlich in `mcu_validator/boards/*.json` (oder nutzerseitig übergebenen JSON-Dateien), niemals im Python-Prüfcode. |
| INV-02 | Syntaxbaum vor Textmuster | C++-Strukturen werden ausschließlich über Tree-Sitter extrahiert; reguläre Ausdrücke operieren lediglich auf kurzen, bereits aus dem Syntaxbaum isolierten Bezeichner-, Funktions- oder Makro-Fragmenten. |
| INV-03 | Global eindeutige Signal-Schlüssel | Widersprüchliche Symboldefinitionen und direkte Pin-Literale erhalten über `_reserve_unique_key` stets global eindeutige Schlüssel, sodass im Solver keine Variablenkollision und kein stiller Datenverlust auftreten kann. |
| INV-04 | Paarweise Bus-Leitungskopplung | Zwei Signale werden genau dann im Solver gekoppelt ($v_i = v_j$), wenn sie dieselbe einzelne teilbare Bus-Fähigkeit, dieselbe `bus_group` und denselben Ausgangspin besitzen; für alle übrigen Paare gilt strikt $v_i \neq v_j$. |
| INV-05 | Stabile Gewichtungshierarchie | Harte Hardware-Regeln werden niemals abgeschwächt. Unter den weichen Bedingungen dominiert das Bewahren gültiger Originalpins (`1000`) global über Strapping-Meidung (`20`) und Spezialpin-Schonung (`5`) für alle unterstützten MCU-Größen ($n \le 39$); auf Einzelpin-Ebene dominiert Strapping-Meidung (`20`) über Spezialpin-Schonung (`5`). |
| INV-06 | Paket- und Laufzeit-Hygiene | `package-data` in `pyproject.toml`, `srcFilter` (`["-<*>"]`) und `export` in `library.json`; kein Vorab-Import von `.cli` in `__init__.py` zur Vermeidung der Python-`runpy`-`RuntimeWarning`. |

*Tabelle 4.3: Architektur-Invarianten.*

**Abgrenzung des Systemumfangs.** Im Fokus stehen die statische syntaktische Extraktion von Pin-Deklarationen, direkten Pin-Aufrufen und Peripherie-Auslösern, die Schema-Validierung und deterministische Prüfung gegen JSON-Profile, die Z3-MaxSMT-Reparatur sowie die Integration in PlatformIO und CLI-Workflows. Explizit **außerhalb des Umfangs** liegen elektrische Schaltungssimulation (Strombelastbarkeit, Pull-up-Dimensionierung, Pegelwandlung), die Modellierung von Peripherie-Instanz- oder Kanalbudgets (z. B. maximale Anzahl gleichzeitiger LEDC-PWM-Kanäle oder I2C-Controller), die Auswertung erst zur Laufzeit berechneter Pin-Nummern sowie das automatische Überschreiben von C++-Quelltextdateien.

---

## 5 Konzeption und Entwurfsentscheidungen

Dieses Kapitel begründet die vier maßgeblichen Entwurfsentscheidungen und verfolgt die Datenverarbeitung anschließend anhand eines durchgängigen Szenarios über alle Schichten hinweg. Für die beiden Verfahrensentscheidungen werden gewichtete Nutzwertanalysen herangezogen. Methodisch ist offenzulegen, dass Kriteriengewichte und Punktbewertungen vom Verfasser projektbezogen festgelegt wurden: Eine Nutzwertanalyse macht Zielkonflikte transparent und nachvollziehbar, ersetzt jedoch keinen objektiven Beweis. Jede Entscheidung wird daher um eine explizite Sensitivitätsbetrachtung ergänzt.

### 5.1 Entscheidung 1: Verfahren zur Quelltextanalyse

Zur Extraktion von Pin-Informationen aus Embedded-C++-Code wurden drei Verfahren verglichen: **A – Reguläre Ausdrücke** direkt auf dem Quelltext, **B – `libclang`** (Compiler-API mit vollständigem C-Präprozessor und semantischer Typauflösung) sowie **C – Tree-Sitter** (`tree-sitter-cpp`, fehlertoleranter GLR-Parser). Die Bewertung erfolgt auf einer Skala von 1 (ungenügend) bis 5 (sehr gut):

| Kriterium | Gewicht | A Regex | B `libclang` | C Tree-Sitter |
| :--- | :---: | :---: | :---: | :---: |
| K1 Robustheit gegenüber Kommentaren, Strings, lokalen Scopes (FA-03) | 25 % | 1 | 5 | 5 |
| K2 Betrieb ohne Ziel-Toolchain und SDK-Header (NFA-03) | 25 % | 5 | 2 | 5 |
| K3 Fehlertoleranz gegenüber unvollständigem Code | 15 % | 4 | 2 | 4 |
| K4 Semantische Tiefe (Präprozessor, `#ifdef`, Typauflösung) | 20 % | 1 | 5 | 2 |
| K5 Installations- und Integrationsaufwand (NFA-05) | 15 % | 5 | 3 | 5 |
| **Gewichteter Nutzwert** | **100 %** | **3,05** | **3,50** | **4,25** |

*Tabelle 5.1: Nutzwertanalyse der Verfahren zur Quelltextanalyse.*

**Begründung.** Reguläre Ausdrücke scheitern prinzipbedingt an K1 (Abschnitt 2.3). `libclang` erzielt zwar maximale semantische Tiefe (vollständige Makroexpansion, Auswertung von `#ifdef`-Zweigen, exakte Auflösung von `gpio_num_t`-Typen), verlangt jedoch eine konfigurierte Cross-Compiler-Umgebung einschließlich sämtlicher Ziel-Header (`Arduino.h`, ESP-IDF-Pfade, Board-Defines) und bricht bei fehlenden Include-Pfaden oder unvollständigen Code-Snippets frühzeitig ab. Tree-Sitter erfordert hingegen lediglich zwei kompakte Python-Wheels, läuft plattformunabhängig ohne Cross-Compiler und liefert dank GLR-Error-Recovery auch für unvollständige LLM-Entwürfe eine verlässliche syntaktische Struktur.

**Sensitivitätsanalyse.** Erhöht man das Gewicht von K4 bei proportionaler Absenkung der übrigen Gewichte, liegt der durchschnittliche Vorteil von Tree-Sitter auf den restlichen Kriterien bei $1{,}6875$ Punkten gegenüber einem Rückstand von $3{,}00$ Punkten auf K4; `libclang` überholt Tree-Sitter erst ab einem K4-Gewicht von $w_4 = 1{,}6875 / 4{,}6875 = 36\,\%$. Solange der betriebsbereite Einsatz ohne installierte Cross-Compiler-Toolchain (K2, K5) ein tragendes Entwicklungsziel bleibt, ist die Entscheidung für Tree-Sitter stabil. Die bewusst in Kauf genommenen Grenzen hinsichtlich `#ifdef` und Typauflösung werden in Abschnitt 8.2 systematisch adressiert.

### 5.2 Entscheidung 2: Verfahren zur Konfliktlösung

Für die Berechnung einer gültigen, minimal-invasiven Ersatzbelegung standen vier Verfahren zur Auswahl: **1 – Deterministische Greedy-Heuristik**, **2 – Reines SMT ohne Optimierung** (`z3.Solver`), **3 – Gemischt-ganzzahlige lineare Optimierung** (MILP, z. B. über PuLP/CBC oder HiGHS) und **4 – Partial Weighted MaxSMT** (`z3.Optimize` / $\nu Z$).

| Kriterium | Gewicht | 1 Heuristik | 2 SMT | 3 MILP | 4 MaxSMT |
| :--- | :---: | :---: | :---: | :---: | :---: |
| K1 Garantierte Optimalität bzgl. Zielfunktion (FA-08) | 30 % | 1 | 1 | 5 | 5 |
| K2 Natürliche Modellierung von Disjunktheit und Bus-Kopplung (FA-07) | 25 % | 2 | 5 | 2 | 5 |
| K3 Abhängigkeiten und Installationsaufwand | 15 % | 5 | 4 | 4 | 4 |
| K4 Laufzeit bei typischen Pin-Zahlen (bis ca. 15–20 Signale) | 15 % | 5 | 5 | 4 | 4 |
| K5 Nachvollziehbarkeit und Wartbarkeit des Modells (NFA-07) | 15 % | 4 | 2 | 3 | 3 |
| **Gewichteter Nutzwert** | **100 %** | **2,90** | **3,20** | **3,65** | **4,40** |

*Tabelle 5.2: Nutzwertanalyse der Verfahren zur Konfliktlösung.*

**Begründung.** Eine gierige Heuristik versagt bei gekoppelten Ressourcenengpässen: Kollidieren beispielsweise eine LED und ein Analogsensor auf dem vorletzten strapping-freien `ADC1`-Pin, kann eine ungünstige Abarbeitungsreihenfolge den Sensor auf einen Strapping-Pin verdrängen oder fälschlich keine Lösung finden, obwohl das Verschieben der LED das Problem global löst (Abschnitt 6.5, Fall 3). Ein reiner Entscheidungs-SMT-Solver (`z3.Solver`) findet zwar eine gültige Belegung, minimiert jedoch nicht die Anzahl der Pin-Änderungen. MILP garantiert dieselbe globale Optimalität wie MaxSMT, erfordert für diskrete Pin-Zuweisungen jedoch binäre Indikatorvariablen $x_{i,p} \in \{0,1\}$ für jedes zulässige Signal-Pin-Paar sowie explizite lineare Gleichungssysteme zur Abbildung paarweiser Bus-Kopplungen ($x_{i,p} = x_{j,p}$ für alle $p \in P_i \cap P_j$). In Z3 MaxSMT genügt demgegenüber eine einzelne Entscheidungsvariable $v_i$ je Signal sowie die unmittelbar lesbare Formulierung $v_a = v_b$ bzw. $v_a \neq v_b$ – ein deutlicher Gewinn für Modellklarheit und Wartbarkeit (NFA-07).

**Sensitivitätsanalyse.** In Tabelle 5.2 erzielt MaxSMT auf vier der fünf Kriterien identische Bewertungen wie MILP und setzt sich ausschließlich über K2 (Modellierungsausdrucksstärke) ab. Eine Revision zugunsten von MILP – oder zugunsten einer booleschen One-Hot-/`QF_FD`-Kodierung innerhalb von Z3 – wird erst relevant, wenn bei großen Mikrocontrollern mit deutlich mehr als 20–30 konfliktbehafteten Signalen K4 (Laufzeitskalierung) neu bewertet und höher als K2 gewichtet werden muss. Die Skalierungsmessung in Abschnitt 7.5 überprüft diesen Übergangspunkt empirisch.

### 5.3 Entscheidung 3: Zweistufiger Ablauf

Übergäbe man sämtliche im Quelltext gefundenen Pin-Zuweisungen unmittelbar als harte Gleichungen ($v_i = p_i^0$) an Z3, erhielte der Anwender im Konfliktfall lediglich ein pauschales `UNSAT` (bzw. einen abstrakten unerfüllbaren Kern) ohne direkte Zuordnung zu konkreten Datenblatt-Regeln. Zugleich müsste der SMT-Solver auch bei vollständig fehlerfreien Builds gestartet werden. `mcu-pin-solver` entkoppelt daher Diagnose und Reparatur in zwei klar getrennte Stufen:

1. **Stufe 1 – Deterministische Regelprüfung (ohne Z3):** Ein linearer Python-Durchlauf prüft jede extrahierte Anforderung gegen das `BoardSpec`-Profil und sammelt sämtliche Verstöße samt `datei:zeile`-Position und menschenlesbarer Regelbegründung (`reason`). Treten keine Konflikte auf, terminiert die Prüfung sofort mit `SAT`, ohne dass Z3 instanziiert wird.
2. **Stufe 2 – Z3-MaxSMT-Optimierung:** Erst wenn Stufe 1 mindestens einen harten Konflikt feststellt, konstruiert das System das MaxSMT-Modell und berechnet eine beweisbar optimale Ersatzbelegung (oder erkennt eine echte Hardware-Überbuchung).

Diese Trennung liefert vollständige Mehrfachdiagnosen in einem Durchlauf und hält gültige Builds nahezu latenzfrei (`0,01` bis `0,06 ms` Prüfzeit selbst bei 20 Pins; vgl. Abschnitt 7.5).

### 5.4 Entscheidung 4: Hardware-Wissen als validierte Daten

Sämtliche mikrocontrollerspezifischen Fakten liegen deklarativ in JSON-Profildateien statt im Python-Quelltext (INV-01). Neben der architektonischen Entkopplung besitzt diese Entscheidung unmittelbare wirtschaftliche Wirkung: Die Integration einer neuen MCU reduziert sich auf das Erstellen und Datenblatt-Prüfen einer JSON-Datei (ca. 1–2 Stunden Aufwand; vgl. Anhang F und Abschnitt 7.6), ohne dass Parser, Regelprüfer oder Solver geändert werden müssen.

Da solche JSON-Profile in der Praxis häufig unter Einbindung von Sprachmodellen erstellt oder erweitert werden, erzwingt `BoardSpec.from_dict()` in Version `0.2.0` eine strenge Schema-Validierung beim Laden (Abschnitt 6.2). Typische Modellierungsfehler – etwa `"capabilities": "gpio"` (Zeichenkette statt Liste, über die Python ansonsten zeichenweise iterieren würde), `"forbidden_pins": ["18"]` (Zeichenkette statt Ganzzahl) oder Tippfehler in `when_resource_active` – werden unmittelbar mit einer präzisen Fehlermeldung zurückgewiesen, statt stillschweigend wirkungslos zu bleiben.

### 5.5 Gesamtarchitektur

Abbildung 5.1 veranschaulicht die modulare Vierschicht-Architektur von Version `0.2.0` entlang des Datenflusses vom PlatformIO-Build-Aufruf bis zur Abbruch- oder Freigabeentscheidung.

```text
  platformio.ini + Projektdateien (include/, src/)
          │   "pio run" startet das Pre-Build-Skript vor dem Cross-Compiler
          ▼
  pio_hook.py
    ├─ Einmal-Ausführungsschutz pro SCons-Build (_MCU_VALIDATOR_RAN)
    ├─ Prüft / installiert Laufzeitpakete (mit Versionsgrenzen & PEP-668-Fehlerhilfe)
    └─ Startet: python -m mcu_validator.cli <src> <board> [--include-dir <include>]
          ▼
  mcu_validator/cli.py  (Einstiegspunkt: mcu-validate / validate_path)
    ├─ 1. board.py  : load_board(board)      → BoardSpec (schema-validiert aus boards/*.json)
    ├─ 2. parser.py : parse_cpp(pfad, board) → ParsedProject (PinRequests + aktive Module)
    ├─ 3. solver.py : validate(proj, board)  → ValidationResult (Stufe 1 + ggf. Z3 MaxSMT)
    └─ 4. cli.py    : format_report(...)     → Diagnosebericht + LLM-Reparatur-Prompt
          │
          ├── SAT   (Exit-Code 0) → Cross-Compiler startet
          ├── UNSAT (Exit-Code 1) → env.Exit(1), Reparatur-Prompt ausgeben
          └── ERROR (Exit-Code 2) → Konfigurations- / Eingabefehler melden
```
*Abbildung 5.1: Gesamtarchitektur und Datenfluss im PlatformIO-Build-Prozess (`v0.2.0`).*

### 5.6 Durchgängiges Beispiel

Um das Zusammenspiel aller vier Module konkret nachvollziehbar zu machen, wird Szenario 0 aus der Regressions-Testsuite (Listing 5.1, inhaltlich entsprechend Listing 1.1) Schritt für Schritt auf einem ESP32-C3 verfolgt.

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

**Schritt 1 – Profil laden und validieren (`board.py`).** Aus `mcu_validator/boards/esp32-c3.json` wird ein unveränderliches `BoardSpec`-Objekt aufgebaut: GPIO 11–17 sind als reserviert markiert (`VDD_SPI` bzw. interner SPI-Flash), GPIO 5 trägt neben digitalen Fähigkeiten lediglich `adc2`, `ADC1` liegt auf GPIO 0–4, Strapping-Pins sind $S = \{2, 8, 9\}$, aktives `wifi` sperrt die Fähigkeit `adc2`, und aktives `usb_serial` sperrt GPIO 18 und 19.

**Schritt 2 – Quelltext analysieren (`parser.py`).** Der Syntaxbaum-Durchlauf extrahiert auf Top-Level-Ebene `STATUS_LED = 12` (Zeile 5; der nachgestellte Zeilenkommentar im `preproc_arg` wird lokal entfernt), `SOIL_SENSOR = 5` (Zeile 6) und `RELAY_PIN = 4` (Zeile 7). Lokale Variablen innerhalb von `setup()` oder `loop()` bleiben unberücksichtigt (`skip_functions=True`). Der Aufruf `analogRead(SOIL_SENSOR)` weist `SOIL_SENSOR` die Fähigkeitsmenge `frozenset({"adc"})` zu; `pinMode`/`digitalWrite` liefern `frozenset({"gpio"})` für `STATUS_LED` und `RELAY_PIN`. Über `resource_triggers` aktivieren `WiFi.begin` und `Serial.begin` die Module `wifi` und `usb_serial`. Das resultierende `ParsedProject` lautet:

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

**Schritt 3 – Deterministische Diagnose (Stufe 1 in `solver.py`).** `STATUS_LED` verletzt das Reservierungsflag auf GPIO 12 (`Internal SPI flash (SPIHD)`). `SOIL_SENSOR` fordert `adc`, expandiert zu $A(\texttt{adc}) = \{\texttt{adc1}, \texttt{adc2}\}$; GPIO 5 bietet hiervon nur `adc2`, das durch die aktive Konfliktregel `WIFI_BLOCKS_ADC2` vollständig gesperrt ist. Die Diagnose gibt unmittelbar den im JSON hinterlegten `reason`-Text aus. `RELAY_PIN` auf GPIO 4 erfüllt alle Bedingungen. Aufgrund der beiden Konflikte wechselt `validate()` in Stufe 2.

**Schritt 4 – MaxSMT-Reparatur (Stufe 2 in `solver.py`).** Für jedes Signal wird die zulässige Kandidatenmenge $P_i$ bestimmt. Da `usb_serial` GPIO 18 und 19 sperrt und GPIO 11–17 reserviert sind, ergeben sich:

$$P_{\text{LED}} = P_{\text{RELAY}} = \{0, 1, \dots, 10, 20, 21\}, \qquad P_{\text{SOIL}} = \{0, 1, 2, 3, 4\}.$$

Als harte Bedingungen gelten die Domänenbindung $v_i \in P_i$ sowie paarweise Verschiedenheit ($v_{\text{LED}} \neq v_{\text{SOIL}}$, $v_{\text{LED}} \neq v_{\text{RELAY}}$, $v_{\text{SOIL}} \neq v_{\text{RELAY}}$). Die weichen Klauseln bewerten jede zulässige Belegung dreistufig:

- **+1000 Punkte (Stufe 1):** Erhaltung des gültigen Originalpins (hier ausschließlich für `RELAY_PIN` mit $p^0 = 4 \in P_{\text{RELAY}}$ realisierbar).
- **+20 Punkte (Stufe 2):** Vermeidung der Strapping-Pins $S_{\text{LED}} = S_{\text{RELAY}} = \{2, 8, 9\}$ bzw. $S_{\text{SOIL}} = \{2\}$.
- **+5 Punkte (Stufe 3):** Schonung knapper, selbst nicht angeforderter Spezialpins (`adc`/`usb`). Für `STATUS_LED` und `RELAY_PIN` ($C_i = \{\texttt{gpio}\}$) sind $K_{\text{LED}} = K_{\text{RELAY}} = \{0, 1, 2, 3, 4, 5\}$ knappe ADC-Pins; unkritische Standard-GPIOs sind $\{6, 7, 10, 20, 21\}$. Für `SOIL_SENSOR` ($N_{\text{SOIL}} = \{\texttt{adc1}, \texttt{adc2}\}$) verbleiben als zu schonende Fähigkeiten nur `adc` und `usb`, die auf keinem Pin aus $P_{\text{SOIL}} = \{0..4\}$ liegen ($K_{\text{SOIL}} = \emptyset$); daher wird für `SOIL_SENSOR` keine Stufe-3-Klausel erzeugt.

| Belegung (`LED`, `Sensor`, `Relais`) | Relais behalten | Strapping-Meidung | Knappe Pins geschont | Summe | Bewertung |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `(12, 5, 4)` – Original | – | – | – | ungültig | verletzt harte Regeln |
| `(6, 3, 10)` | $0$ | $20 + 20 + 20 = 60$ | $5 + 0 + 5 = 10$ | $70$ | Relais unnötig verschoben |
| `(6, 2, 4)` | $1000$ | $20 + 0 + 20 = 40$ | $5 + 0 + 0 = 5$ | $1045$ | Sensor auf Strapping-Pin 2 |
| `(1, 3, 4)` | $1000$ | $20 + 20 + 20 = 60$ | $0 + 0 + 0 = 0$ | $1060$ | LED belegt knappen `ADC1`-Pin 1 |
| **`(6, 3, 4)` – Z3-Ausgabe** | **$1000$** | **$20 + 20 + 20 = 60$** | **$5 + 0 + 0 = 5$** | **$1065$** | **global optimal** |

*Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`).*

Die drei Gewichtsstufen greifen exakt wie beabsichtigt ineinander: `RELAY_PIN` verbleibt auf GPIO 4 (obwohl GPIO 4 ein `ADC1`-Pin ist, überwiegen `1000` Haltepunkte gegenüber `5` Schonungspunkten deutlich), `SOIL_SENSOR` weicht auf den strapping-freien `ADC1`-Pin GPIO 3 aus, und `STATUS_LED` erhält den regulären GPIO 6, statt einen weiteren analogen Kanal zu binden.

**Schritt 5 – Bericht und Profil-Austauschbarkeit (`cli.py`).** Listing 5.2 zeigt die reale CLI-Ausgabe auf dem ESP32-C3 (Exit-Code `1`). Derselbe unveränderte C++-Quelltext passiert die Prüfung auf dem ESP32-S3 fehlerfrei mit `SAT` (Listing 5.3, Exit-Code `0`), da GPIO 12 dort ein nutzbarer GPIO und GPIO 5 ein `ADC1`-Kanal ist. Allein der Austausch des JSON-Hardware-Profils verändert das Verifikationsergebnis – ein unmittelbarer Nachweis der datengetriebenen Entkopplung (Entscheidung 4, INV-01).

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
*Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (`v0.2.0`, Rückgabewert `1`).*

```text
=================================================================
 Target         : tests/scenarios/00_flash_and_wifi_conflict.cpp (ESP32-S3)
 Active Modules : wifi, usb_serial
 Checked Pins   : 3 (STATUS_LED=12, SOIL_SENSOR=5, RELAY_PIN=4)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (`v0.2.0`, Rückgabewert `0`).*

---

## 6 Implementierung

Dieses Kapitel dokumentiert die Umsetzung von `mcu-pin-solver` in Version `0.2.0` anhand der realen Projektdateien. Sämtliche vier Kernmodule sind nach dem Top-down-Prinzip gegliedert: An oberster Stelle steht jeweils die öffentliche Einstiegsfunktion (`load_board`, `parse_cpp`, `validate`, `validate_path`), gefolgt von den Hilfsfunktionen in Ausführungsreihenfolge. Im Hauptteil werden die tragenden Ausschnitte erläutert; die vollständigen Hardware-Profile und Quelltexte sind in den Anhängen A bis E abgedruckt.

### 6.1 Repository und Softwareumgebung

Die Codebasis strukturiert sich in vier Schichten: die Build- und Paketintegration (`pio_hook.py`, `library.json`, `pyproject.toml`), die Orchestrierung und Berichtsausgabe (`cli.py`, `__init__.py`), den Verifikationskern (`board.py`, `parser.py`, `solver.py`) sowie die gebündelten deklarativen Hardware-Profile (`mcu_validator/boards/*.json`). Tabelle 6.1 fasst sämtliche Bestandteile des Repositories zusammen.

| Datei / Ordner | Umfang | Aufgabe |
| :--- | :--- | :--- |
| `mcu_validator/boards/esp32-c3.json` | 50 Zeilen JSON | Hardware-Profil für den ESP32-C3 (Anhang A) |
| `mcu_validator/boards/esp32-s3.json` | 73 Zeilen JSON | Hardware-Profil für den ESP32-S3 (Anhang B) |
| `mcu_validator/board.py` | 284 Zeilen Python | Typisierte Datenklassen, Profil-Auflösung und JSON-Schema-Validierung (Anhang C) |
| `mcu_validator/parser.py` | 541 Zeilen Python | Dateiauflösung, Tree-Sitter-Analyse, Bus-Rollen und Namens-Fallback (Anhang D) |
| `mcu_validator/solver.py` | 284 Zeilen Python | Stufe-1-Diagnose und dreistufige Z3-MaxSMT-Optimierung (Anhang E) |
| `mcu_validator/cli.py` | 178 Zeilen Python | Argument-Parser (`mcu-validate`), Berichtsformatierung, Exit-Codes `0`/`1`/`2` (Anhang E) |
| `mcu_validator/__init__.py` | 21 Zeilen Python | Öffentliche Python-API und `__version__ = "0.2.0"` ohne Vorab-Import von `.cli` (Anhang E) |
| `pio_hook.py` | 92 Zeilen Python | PlatformIO-Pre-Build-Hook inkl. Paketprüfung und `--include-dir`-Übergabe (Anhang E) |
| `library.json` | 33 Zeilen JSON | PlatformIO-Manifest (`0.2.0`) mit `extraScript`, `srcFilter` und `export` (Anhang E) |
| `pyproject.toml` | 42 Zeilen TOML | Python-Paketmetadaten (`package-data` für `boards/*.json`), `ruff`- und `mypy`-Konfiguration |
| `src/main.cpp` und `platformio.ini` | 56 + 11 Zeilen | ESP32-C3-Demo-Projekt für lokale `pio run`-Prüfungen |
| `tests/test_*.py` und `tests/run_tests.py` | 766 Zeilen (42 Tests) + 7 Szenarien | Modulare Unit- und End-to-End-Testsuite (`test_board`, `test_parser`, `test_solver`, `test_cli`, `test_scenarios`) |
| `.github/workflows/ci.yml` | 35 Zeilen YAML | CI-Matrix (Ubuntu & Windows, Python `3.10`/`3.12`) sowie `ruff` und `mypy` |
| `README.md` und `.gitattributes` | 139 + 1 Zeile | Dokumentation, Einbindungsanleitung, Profil-Prompt-Vorlage, LF-Zeilenenden |

*Tabelle 6.1: Dateien und Struktur des Repositories (`v0.2.0`).*

Das Python-Paket `mcu_validator` umfasst insgesamt 1308 Zeilen (zusammen mit `pio_hook.py` 1400 Zeilen, inklusive Docstrings, vollständiger Typannotationen, Schema-Validierung und Leerzeilen). Gegenüber dem minimalen Prototyp `v0.1.0` (379 Zeilen) wurde der Code konsequent in kleine, unveränderliche Datenklassen (`@dataclass(frozen=True)`) und fokussierte Hilfsfunktionen zerlegt, um die Analysierbarkeit und Wartbarkeit (NFA-07) dauerhaft zu sichern. Alle fünf Quellmodule bestehen `ruff` und `mypy` ohne Fehler oder Warnungen; die Testsuite basiert bewusst auf `unittest` aus der Python-Standardbibliothek, um keine zusätzlichen Test-Abhängigkeiten einzuführen.

### 6.2 Hardware-Profile und Schema-Validierung (`board.py`)

Gemäß INV-01 liegen sämtliche GPIO-Nummern, Fähigkeiten, Auslöser und Sperrregeln in JSON-Dateien unter `mcu_validator/boards/`. Die Ablage *innerhalb* des Python-Pakets in Verbindung mit `package-data` in `pyproject.toml` gewährleistet, dass die Profile auch nach einer regulären Installation via `pip install .` oder aus einem Wheel heraus über `Path(__file__).resolve().parent / "boards"` zuverlässig auffindbar bleiben.

Jedes Hardware-Profil gliedert sich neben den Metafeldern `mcu` und `description` in fünf Datenblöcke (Listing 6.1):

1. **`pins`:** Bildet physisch vorhandene GPIO-Nummern (als nicht-negative Ziffern-Strings) auf `capabilities`, `strapping`, `reserved` und optional `note` ab. Nicht existierende Pin-Nummern (wie GPIO 22–25 beim ESP32-S3) fehlen als Schlüssel; reservierte Systempins tragen `"reserved": true` und `"capabilities": []`.
2. **`capability_aliases`:** Expandiert abstrakte API-Fähigkeiten (`"adc"`) auf chipspezifische Hardware-Bänke (`["adc1", "adc2"]`).
3. **`shared_capabilities`:** Kennzeichnet Bus-Fähigkeiten (`["i2c", "spi"]`), deren gleichartige Signalleitungen mehrere Teilnehmer teilen dürfen.
4. **`resource_triggers`:** Ordnet Peripheriemodulen (`"wifi"`, `"usb_serial"`) die auslösenden C++-Aufrufziele zu (`["WiFi.begin", "WiFi.softAP"]`, `["Serial.begin"]`).
5. **`conflict_rules`:** Formuliert kontextabhängige Hardware-Sperren über `when_resource_active` in Kombination mit `forbidden_capability` oder `forbidden_pins` sowie einer Klartextbegründung (`reason`).

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

Listing 6.2 zeigt die Profilauflösung in `mcu_validator/board.py`. Gegenüber `v0.1.0` wurden drei wesentliche Robustheitslücken geschlossen: Erstens normalisiert `load_board()` sowohl `board_id` als auch Dateinamen (`_` $\rightarrow$ `-`, Kleinschreibung) und sortiert Kandidaten absteigend nach Namenslänge, sodass spezifische Profile (`esp32-c3.json`) stets Vorrang vor kürzeren Präfixen (`esp32.json`) besitzen. Zweitens werden direkte `.json`-Dateipfade unmittelbar akzeptiert. Drittens prüft `BoardSpec.from_dict()` sämtliche Schlüssel und Datentypen strikt: Bare Strings in Listenfeldern (`"capabilities": "gpio"`), Booleans oder Strings in `forbidden_pins` (da `bool` in Python eine Unterklasse von `int` ist, wird `not isinstance(p, bool)` explizit erzwungen), nicht definierte Module in `when_resource_active` sowie wirkungslose Konfliktregeln ohne Ziel führen unmittelbar zu einer aussagekräftigen `ValueError`-Ausnahme.

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

Tabelle 6.2 stellt beide mitgelieferten Hardware-Profile den Datenblättern [[9]](#ref-9), [[10]](#ref-10) gegenüber. Gegenüber `v0.1.0` bilden beide Profile die Flexibilität der ESP32-GPIO-Matrix realistisch ab: Alle nicht-reservierten GPIOs tragen `pwm`, `i2c`, `spi` und `uart`, und beim ESP32-C3 ist GPIO 11 explizit als `VDD_SPI` reserviert.

| Merkmal | `mcu_validator/boards/esp32-c3.json` | `mcu_validator/boards/esp32-s3.json` |
| :--- | :--- | :--- |
| CPU-Architektur | RISC-V Single-Core (RV32IMC) | Xtensa LX7 Dual-Core |
| Deklarierte GPIOs | `0–21` (22 Einträge) | `0–21`, `26–48` (45 Einträge; `22–25` fehlen) |
| Reservierte Speicherpins | `11` (`VDD_SPI`), `12–17` (interner SPI-Flash) | `26–32` (Quad-SPI Flash/PSRAM), `33–37` (Octal-SPI Flash/PSRAM, konservativ) |
| Strapping-Pins | `2, 8, 9` (Boot / ROM-Print) | `0` (Boot), `3` (JTAG), `45` (`VDD_SPI`-Spannung), `46` (Boot / ROM-Print; bidirektional I/O) |
| `ADC1` (WLAN-kompatibel) | `0–4` (5 Kanäle) | `1–10` (10 Kanäle) |
| `ADC2` (bei WLAN gesperrt) | `5` (1 Kanal; zudem Erratum `ADC-183`) | `11–20` (10 Kanäle; Arbiter-Konflikt mit WLAN) |
| Native USB-Pins | `18` (`D-`), `19` (`D+`) – USB Serial/JTAG | `19` (`D-`), `20` (`D+`) – USB Serial/JTAG & USB-OTG |
| GPIO-Matrix (`pwm`, `i2c`, `spi`, `uart`) | auf allen 15 freien GPIOs (`0–10`, `18–21`) | auf allen 33 freien GPIOs (`0–21`, `38–48`) |
| Standard-UART0 | `20` (`U0RXD`), `21` (`U0TXD`) | `43` (`U0TXD`), `44` (`U0RXD`) |

*Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`, Angaben nach [[9]](#ref-9), [[10]](#ref-10)).*

Zwei bewusste **Modellierungsentscheidungen** an der Grenze zwischen Datenblatt und Familienprofil sind festzuhalten:

- **Konservative Reservierung von GPIO 33–37 beim ESP32-S3:** Auf reinen Quad-SPI-Varianten ohne Octal-Flash oder Octal-PSRAM (z. B. `N4`/`N8`) sind GPIO 33–37 physisch als freie GPIOs nutzbar; auf verbreiteten Octal-PSRAM-Modulen (z. B. `WROOM-1-N8R8`/`N16R8`) belegt der Octal-Bus jedoch genau diese fünf Leitungen [[10]](#ref-10). Das Familienprofil `esp32-s3.json` reserviert GPIO 33–37 daher konservativ, um Octal-PSRAM-Boards ohne Risiko abzudecken; für reine Quad-Boards kann bei Bedarf ein spezifisches Board-JSON übergeben werden.
- **Pin-Routing-Fähigkeit versus Peripherie-Instanzbudget:** Die GPIO-Matrix erlaubt das Routen von I2C, SPI, UART oder LEDC-PWM auf jeden einzelnen freien GPIO; dennoch besitzt der ESP32-C3 physisch nur 1× I2C, 1× frei nutzbares SPI (`SPI2`/FSPI), 2× UART und 6× LEDC-PWM-Kanäle (ESP32-S3: 2× I2C, 2× SPI, 3× UART, 8× LEDC-PWM) [[9]](#ref-9), [[10]](#ref-10). Ebenso aktiviert `Serial.begin` im Profil konservativ `usb_serial` (Schutz der nativen USB-Pins bei `ARDUINO_USB_CDC_ON_BOOT=1`), während auf Boards mit externer USB-UART-Brücke (`ARDUINO_USB_CDC_ON_BOOT=0`) stattdessen UART0 (GPIO 20/21 bzw. 43/44) belegt ist. Beide Aspekte sind als bewusste Schema-Grenzen in Abschnitt 8.2 eingeordnet.

### 6.3 AST-Parser (`parser.py`)

Der Parser in `mcu_validator/parser.py` ist als vierstufige Pipeline unter `parse_cpp()` implementiert: Dateiauflösung, Syntaxbaum-Scan, Konstruktion der `PinRequest`-Objekte sowie Erkennung aktiver Peripherie.

**1. Dateiauflösung (`_resolve_source_files`).** Einzeldateien werden direkt verarbeitet; bei Übergabe eines Projekt- oder `src/`-Verzeichnisses bindet `_project_search_dirs()` über `path.resolve()` automatisch einen benachbarten `include/`-Ordner ein (was auch bei relativer Angabe `.` aus `src/` heraus funktioniert). Über `include_dirs` (CLI: `--include-dir`) lassen sich weitere Header-Verzeichnisse anfügen. Header-Dateien (`.h`, `.hpp`) werden deterministisch vor Implementierungsdateien (`.c`, `.cpp`, `.ino`) sortiert; Build- und Testverzeichnisse (`.git`, `.pio`, `.venv`, `build`, `test`, `tests`) werden ausschließlich anhand des *relativen* Pfads innerhalb des Suchverzeichnisses ausgeschlossen, sodass Tests innerhalb von `tests/scenarios/...` weiterhin problemlos funktionieren.

**2. Kollisionssichere Schlüsselvergabe (`_record_definition`).** Jede erkannte Top-Level-Pin-Konstante wird als `_PinDefinition` mit Dateipfad und 1-basierter Zeilennummer gespeichert (Listing 6.3). Identische Pin-Werte desselben Symbols über mehrere Dateien werden dedupliziert; widersprüchliche Definitionen desselben Bezeichners erhalten über `_reserve_unique_key()` global eindeutige Schlüssel (`NAME (datei.cpp)`, bei weiteren Konflikten `NAME (datei.cpp) #2` usw.). Damit bleiben selbst dreifache `#ifdef`/`#elif`/`#else`-Verzweigungen oder ein benutzerdefinierter Bezeichner `GPIO_12` neben einem direkten Literal `pinMode(12, OUTPUT)` im Solver kollisionsfrei getrennt (INV-03).

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

**3. Syntaxbaum-Durchlauf und positionsgenaue Argumentauswertung (`_scan_files`, `_pin_args_for_call`).** Die kompilierte Grammatik `CPP_LANGUAGE = Language(tscpp.language())` ist unveränderlich, während jeder Aufruf von `_scan_files()` eine eigene `Parser(CPP_LANGUAGE)`-Instanz anlegt (thread-sicher). Die Dekodierung in `_text()` verwendet `errors="replace"`, sodass Nicht-UTF-8-Kommentare (etwa Windows-1252-Umlaute) keinen Absturz verursachen. Bei der Konstanten-Extraktion überspringt `_walk(root, skip_functions=True)` sowohl `function_definition`- als auch `compound_statement`-Teilbäume, wodurch lokale Schleifen- und Zählvariablen strukturell ausgeschlossen bleiben. Da `tree-sitter-cpp` Qualifizierer (`const`, `constexpr`, `static`) separat vom benannten `type`-Feld abbildet, erfasst `_declaration_constants()` alle Typen in `PIN_VAR_TYPES` (`int`, `unsigned int`, `uint8_t`, `int8_t`, `byte`) unabhängig von ihren Speicherklassen- oder Konstanz-Qualifizierern. `_parse_uint()` entfernt in `preproc_arg`- und `number_literal`-Texten Kommentare, einfache Klammerungen (`#define LED (12)`) und ganzzahlige Suffixe (`12u`, `12UL`); negative Standard-Platzhalter wie `-1` in `SPI.begin(-1, ...)` werden sauber verworfen.

Bei Funktionsaufrufen filtert `_extract_calls()` über `args_node.named_children` sämtliche anonymen Interpunktionsknoten (Kommas, Klammern) heraus und schließt zusätzlich `comment`-Extras aus. Anschließend ordnet `_pin_args_for_call()` jeder relevanten Argumentposition bekannter Arduino-/ESP32-APIs exakt die benötigte Hardware-Fähigkeit und gegebenenfalls eine `bus_group` zu (Listing 6.4, Tabelle 6.3). Dabei werden sowohl Arduino-ESP32 v2.x (`ledcAttachPin`, wie in PlatformIO `espressif32@6.12.0` verwendet) als auch v3.x (`ledcAttach`) abgedeckt; Nicht-Pin-Argumente wie Baudraten (`Serial.begin(115200)`), 1-Argument-I2C-Slave-Adressen (`Wire.begin(0x42)`) oder PWM-Tastgrade (`analogWrite(pin, 128)`) werden präzise ignoriert. Das vierte Argument von `SPI.begin` (Chip-Select `CS`/`SS`) wird gezielt als exklusives `gpio` ohne `bus_group` eingestuft, da jeder SPI-Teilnehmer eine eigene Auswahlleitung benötigt.

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

| Funktionsmuster im Syntaxbaum | Ausgewertete Argumente | Fähigkeit | `bus_group` |
| :--- | :--- | :---: | :---: |
| `pinMode`, `digitalWrite`, `digitalRead`, `digitalPinToInterrupt`, `pulseIn`, `tone`, `noTone` | `args[0]` | `gpio` | `None` |
| `analogRead`, `analogReadMilliVolts` | `args[0]` | `adc` | `None` |
| `analogWrite`, `ledcAttach`, `ledcAttachPin` | `args[0]` | `pwm` | `None` |
| `Wire*.begin`, `Wire*.setPins` (ab 2 Arg.) | `args[0]`, `args[1]` | `i2c` | `<Bus>:sda`, `<Bus>:scl` |
| `SPI*.begin` | `args[0..2]` / `args[3]` | `spi` / `gpio` | `<Bus>:sck/miso/mosi` / `None` |
| `Serial*.begin` (ab 3 Arg.) | `args[2..3]` | `uart` | `None` |

*Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen (`_pin_args_for_call`).*

**4. Fähigkeitsmengen, Namens-Fallback und direkte Pin-Literale (`_build_pin_requests`).** Für jede Konstante werden sämtliche im Projekt beobachteten Fähigkeiten als unveränderliche Menge (`frozenset[str]`) vereinigt; bei widersprüchlicher Nutzung desselben Bezeichners in mehreren Bus-Rollen verhindert ein eindeutiger Marker (`mixed:<key>`) fälschliches Teilen. Konstanten ohne beobachteten Pin-Aufruf und ohne Pin-Namensmuster (`BAUD_RATE`, `DELAY_MS`, `I2C_ADDR`, `LED_COUNT`) werden über `NON_PIN_SUFFIXES` verworfen. Die Fallback-Heuristik `_infer_from_name()` zerlegt Bezeichner in `SNAKE_CASE` und `camelCase` (`OLED_SDA_PIN`, `oledSdaPin`) und blickt vor einer abschließenden Silbe `PIN`/`GPIO` auf das eigentliche Rollenwort (`SDA`, `SCL`, `MOSI`, `MISO`, `SCK`, `RX`, `TX`, `CS`).

Direkte numerische Pin-Literale (`pinMode(12, OUTPUT)`, `analogRead(5)`, `Wire.begin(6, 6)`) verarbeitet `_merge_or_append_literal_uses()`: Besitzt bereits eine benannte Konstante denselben Pin mit identischer `bus_group` (etwa `const int STATUS_LED = 6; analogRead(6);`), werden die zusätzlichen Fähigkeiten auf diesen Eintrag vereinigt, sodass fehlende Fähigkeiten ohne Schein-Kollision geprüft werden; andernfalls entsteht ein eindeutig benannter Eintrag (`GPIO_12`, bei gleicher Nummer mit abweichender Bus-Rolle `GPIO_6 (Wire:scl)`).

Gemäß INV-02 durchsucht kein regulärer Ausdruck den C++-Rohtext; alle fünf in `parser.py` eingesetzten Ausdrücke operieren ausschließlich auf kurzen, bereits aus dem Tree-Sitter-Baum isolierten Token-Strings (Tabelle 6.4).

| Muster in `parser.py` | Isolierte Syntaxbaum-Eingabe | Zweck |
| :--- | :--- | :--- |
| `WIRE_CALL_RE`: `^(Wire\d*)\.(?:begin\|setPins)$` | normalisierter `fn_name` | erkennt `Wire`, `Wire1`, … und extrahiert den Busnamen |
| `SPI_CALL_RE`: `^(SPI\d*)\.begin$` | normalisierter `fn_name` | erkennt `SPI`, `SPI1`, … und extrahiert den Busnamen |
| `SERIAL_CALL_RE`: `^Serial\d*\.begin$` | normalisierter `fn_name` | erkennt Hardware-UART-Aufrufe mit expliziten `rxPin`/`txPin` |
| `COMMENT_RE`: `//.*\|/\*.*?\*/` | `preproc_arg` eines `#define` | entfernt Zeilen- und Blockkommentare hinter Makro-Zahlenwerten |
| `WORD_RE`: `[A-Z]+(?=[A-Z][a-z]\|_|\d\|$)\|[A-Z]?[a-z]+\|\d+` | Bezeichner `name` | tokenisiert `SNAKE_CASE` und `camelCase` für `_infer_from_name()` |

*Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`).*

### 6.4 Regelprüfer und MaxSMT-Solver (`solver.py`)

Die Funktion `validate(project, board)` in `mcu_validator/solver.py` prüft nach einer Eindeutigkeitskontrolle der Signalnamen (`_ensure_unique_request_names`) zweistufig (Abbildung 6.1).

```text
  Eingabe: (ParsedProject, BoardSpec)
                        │
                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Stufe 1: Deterministische Regelprüfung (ohne Z3)                    │
  │ 1. _active_restrictions(): Sperren aus conflict_rules ableiten      │
  │ 2. _find_conflicts(): Für jedes Signal r_i auf Originalpin p_i^0:   │
  │    • Existiert p_i^0 im Hardware-Profil?                            │
  │    • Kollision mit früherem Signal (Ausnahme: _can_share_bus True)? │
  │    • Ist p_i^0 als reserved markiert oder in forbidden_pins?        │
  │    • Unterstützt p_i^0 JEDE Fähigkeit c ∈ C_i ohne Komplettsperre?  │
  └─────────────────────┬─────────────────────────────┬─────────────────┘
          conflicts==[] ▼                             ▼ conflicts != []
  ┌───────────────────────────┐     ┌───────────────────────────────────┐
  │ ValidationResult(SAT)     │     │ Stufe 2: Z3 Optimize (MaxSMT)     │
  │ (Z3 wird nicht gestartet) │     │ berechnet optimale Ersatzbelegung │
  └───────────────────────────┘     └─────────────────┬─────────────────┘
                                                      ▼
                                    ValidationResult(UNSAT, repair_possible)
```
*Abbildung 6.1: Zweistufiger Ablauf in `validate()` (`mcu_validator/solver.py`).*

In Stufe 1 prüft `_check_capabilities()` jede geforderte Fähigkeit $c \in C_i$ mittels Mengenoperationen (`matching = board.expand_capability(c) & pin_caps`). Existiert keine Überschneidung, wird die fehlende Fähigkeit gemeldet; liegen sämtliche passenden Hardware-Bänke in `forbidden_caps` (`matching <= forbidden_caps.keys()`), wird unmittelbar der `reason`-Text der sperrenden Konfliktregel ausgegeben.

Bei mindestens einem Konflikt konstruiert `_solve_reassignment()` das Z3-MaxSMT-Modell (Listing 6.5). Jede Anforderung $r_i$ erhält eine über ihren Index erzeugte ganzzahlige Entscheidungsvariable `Int(f"pin_{idx}")` (Typ `z3.ArithRef`). Ist die Kandidatenmenge $P_i$ für mindestens ein Signal leer, terminiert der Solver sofort mit `None` (`repair_possible=False`) – der fehleranfällige Platzhalter `var == -1` aus `v0.1.0` wurde vollständig beseitigt.

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

**Formale Modellierung.** Für $n$ Anforderungen $r_1, \dots, r_n$ mit Fähigkeitsmengen $C_i$ und Bus-Rollen $b_i$ lautet die zulässige Kandidatenmenge (endliche Domäne):

$$P_i = \Big\{\, p \in \mathcal{P} \;\Big|\; \neg\text{reserved}(p) \;\land\; p \notin \text{ForbiddenPins} \;\land\; \forall c \in C_i:\; \big(\text{caps}(p) \cap (A(c) \setminus \text{ForbiddenCaps})\big) \neq \emptyset \,\Big\}.$$

1. **Domänenbindung (hart):** Existiert ein $i$ mit $P_i = \emptyset$, existiert keine gültige Belegung (`repair_possible=False`). Andernfalls gilt $\bigvee_{p \in P_i} (v_i = p)$.
2. **Paarweise Bus-Leitungskopplung (hart, INV-04):** Zwei Signale sind genau dann bus-kompatibel (`_can_share_bus`), wenn sie dieselbe einzelne, teilbare Bus-Fähigkeit sowie dieselbe Bus-Leitungsrolle aufweisen:
   $$\text{share}(r_i, r_j) \iff C_i = C_j \land |C_i| = 1 \land C_i \subseteq \text{shared\_capabilities} \land b_i = b_j.$$
   (In sämtlichen vom Parser erzeugten `i2c`-/`spi`-Anforderungen ist $b_i \neq \bot$ eindeutig gesetzt; lediglich bei manueller API-Konstruktion mit `bus_group=None` würden zwei gleichartige Signale über `None == None` als kompatibel gewertet.) Für alle $\binom{n}{2}$ Paare $1 \le i < j \le n$ gilt:
   $$v_i = v_j \quad \text{falls } \text{share}(r_i, r_j) \land p_i^0 = p_j^0, \qquad \text{sonst } v_i \neq v_j.$$
   Die Bedingung $p_i^0 = p_j^0$ stellt sicher, dass nur jene Bus-Teilnehmer gekoppelt bleiben, die im Quelltext bereits dieselbe physische Leitung teilten.
3. **Dreistufige Zielfunktion (weich, INV-05):** Mit $S_i = P_i \cap S$, $N_i = \bigcup_{c \in C_i} A(c)$ und der Menge unnötig belegter Spezialpins
   $$K_i = \big\{\, p \in P_i \;\big|\; \text{caps}(p) \cap (\mathcal{K}_{\text{scarce}} \setminus N_i) \neq \emptyset \,\big\}, \qquad \mathcal{K}_{\text{scarce}} = \{\texttt{adc}, \texttt{adc1}, \texttt{adc2}, \texttt{usb}\},$$
   maximiert Z3 $\nu Z$:
   $$\max \sum_{i=1}^{n} \Big( 1000 \cdot \mathbb{I}[p_i^0 \in P_i \land v_i = p_i^0] \;+\; 20 \cdot \mathbb{I}[\emptyset \subset S_i \subset P_i \land v_i \notin S_i] \;+\; 5 \cdot \mathbb{I}[\emptyset \subset K_i \subset P_i \land v_i \notin K_i] \Big).$$

Die Schutzbedingungen $\emptyset \subset S_i \subset P_i$ bzw. $\emptyset \subset K_i \subset P_i$ vermeiden triviale oder unvermeidbar unerfüllbare weiche Klauseln, wenn alle erlaubten Pins einer Anforderung Strapping- oder Spezialpins sind.

**Mathematische Dominanzanalyse der Gewichtsstufen.** Da jedes Signal über Stufe 2 und Stufe 3 maximal $20 + 5 = 25$ Zusatzpunkte beitragen kann, ist die globale Dominanz von Stufe 1 (`1000`) gegenüber sämtlichen Stufen-2- und Stufen-3-Abwägungen zusammen mathematisch garantiert, solange $25 \cdot n < 1000$, also für **$n \le 39$** Signale. Auf dem ESP32-C3 (maximal 15 freie GPIOs, höchstens $25 \cdot 15 = 375 < 1000$) und dem ESP32-S3 (maximal 33 freie GPIOs, höchstens $25 \cdot 33 = 825 < 1000$) kann daher kein noch so günstiger Tausch von Strapping- oder Spezialpins das unnötige Verschieben eines einzigen gültigen Originalpins rechtfertigen. Zwischen Stufe 2 (`20`) und Stufe 3 (`5`) besteht hingegen strikte **Einzelsignal-Dominanz** ($20 > 5$), jedoch keine globale lexikographische Dominanz über beliebige Signalketten: Würde das Ausweichen auf einen einzelnen Strapping-Pin (`-20`) mindestens fünf andere Signale gleichzeitig von knappen Spezialpins befreien (`+25`), überwöge die Summe der Stufe-3-Gewichte. Für größere MCUs ($n \ge 40$) oder eine strikt globale lexikographische Ordnung bietet Z3 $\nu Z$ eine native Multi-Objective-Konfiguration (`priority="lex"`), die in Abschnitt 8.4 als gezielte Erweiterung aufgegriffen wird.

### 6.5 Prioritätsverhalten und Konfliktauflösung bei gegenseitiger Pin-Blockade

Bei konkurrierenden Signalen auf demselben Ausgangspin entscheidet ausschließlich die Zielfunktion aus Abschnitt 6.4 ohne fest codierte Bezeichnerprioritäten. Drei strukturelle Fallgruppen treten auf:

1. **Symmetrische Einzelsignale (Gleichstand).** Belegen `BUZZER_PIN = 7` und `SERVO_PIN = 7` (beide `gpio`) denselben Pin, erzielen beide Minimalreparaturen identische Zielfunktionswerte ($1000 + 40 + 10 = 1050$). Die Grenzfallexperimente `c` und `c2` (Abschnitt 7.4) belegen, dass den Gleichstand nicht die Deklarationsreihenfolge im Quelltext, sondern die interne Such- und Kernextraktionsheuristik von Z3 auflöst (in beiden Reihenfolgen verblieb `SERVO_PIN` auf GPIO 7, während `BUZZER_PIN` auf GPIO 20 bzw. GPIO 6 auswich). Bei unveränderter Eingabe und fester Z3-Version bleibt das Ergebnis reproduzierbar.
2. **Geteilter Bus gegen einzelnes Störsignal („Bus-Trägheit“).** In Szenario 04 sind `OLED_SDA = 6` und `BME280_SDA = 6` über `Wire:sda` gekoppelt ($v_{\text{OLED\_SDA}} = v_{\text{BME280\_SDA}}$) und tragen gemeinsam $2 \times 1000 = 2000$ Haltepunkte, gegenüber lediglich `1000` Haltepunkten für `STATUS_LED = 6`. Tabelle 6.5 dokumentiert diese rechnerische Bus-Trägheit: Alle vier I2C-Signale verbleiben auf GPIO 6/7, während ausschließlich die LED auf den freien Standard-GPIO 20 ausweicht.

| Variante in Szenario 04 (`v0.2.0`) | Haltepunkte | Strapping-Meidung | Knappe Pins geschont | Summe | Ergebnis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **A (Z3-Lösung):** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 20 | $4 \times 1000 = 4000$ | $5 \times 20 = 100$ | $5 \times 5 = 25$ | **$4125$** | **global optimal** |
| **B:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 1 (`ADC1`) | $4000$ | $100$ | $4 \times 5 + 0 = 20$ | $4120$ | verworfen |
| **C:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 2 (Strapping + `ADC1`) | $4000$ | $4 \times 20 = 80$ | $20$ | $4100$ | verworfen |
| **D:** `STATUS_LED` bleibt auf 6, `SDA`-Paar $\rightarrow$ 20 | $3 \times 1000 = 3000$ | $100$ | $25$ | $3125$ | verworfen |

*Tabelle 6.5: Punktebewertung in Szenario 04 (geteilter I2C-Bus gegen einzelnes Störsignal, `v0.2.0`).*

3. **Spezialist gegen Allrounder.** Kollidieren bei aktivem WLAN ein Analogsensor (`SOIL_SENSOR = 1`, benötigt `adc1`) und eine digitale LED (`STATUS_LED = 1`, `gpio`), während die übrigen strapping-freien `ADC1`-Pins (0, 3, 4) bereits belegt sind, verbliebe dem Sensor bei Verdrängung nur noch der Strapping-Pin GPIO 2 (`4080` Punkte). Weicht stattdessen die LED auf den regulären GPIO 7 aus (`4105` Punkte), gewinnt diese Lösung genau **25 Punkte** (`+20` Strapping-Meidung für den Sensor, `+5` Schonung des `ADC1`-Pins für die LED). Die Experimente `f` und `f2` bestätigen diese Spezialisten-Priorität unabhängig von der Deklarationsreihenfolge.

### 6.6 Bericht, CLI und Reparatur-Prompt (`cli.py`)

Das Modul `mcu_validator/cli.py` stellt über `argparse` den Kommandozeilenbefehl `mcu-validate` (sowie `python -m mcu_validator.cli`) mit eindeutiger Exit-Code-Semantik bereit: `0` (`SAT`), `1` (`UNSAT`, Hardware-Konflikt) und `2` (Eingabe- oder Konfigurationsfehler wie fehlender Pfad, unbekanntes Board oder fehlerhafte Board-JSON – sauber über `stderr` gemeldet ohne unformatierte Python-Stacktraces).

Über `--list-boards`, `--boards-dir`, `--include-dir` (wiederholbar) und `--version` lässt sich das Werkzeug flexibel in lokale Workflows und CI-Pipelines integrieren. Der Berichtskopf nennt stets `Checked Pins : N (...)` und gibt bei `0` erkannten Pins eine explizite Warnung aus, um ein trügerisches `SAT` bei syntaktisch nicht erfasstem Code zu verhindern. Im `UNSAT`-Fall folgen sämtliche Einzelkonflikte mit `datei:zeile`-Verweis sowie die vollständige `Keep`/`Change`-Liste (oder eine unmissverständliche Kapazitätsmeldung bei `repair_possible=False`). Gemäß INV-06 verzichtet `mcu_validator/__init__.py` auf den Import von `.cli`, sodass `python -W error -m mcu_validator.cli` ohne `runpy`-`RuntimeWarning` ausgeführt wird.

### 6.7 Integration in PlatformIO und Paketierung (`pio_hook.py`, `library.json`, `pyproject.toml`)

`mcu-pin-solver` ist dual paketiert: als reguläres Python-Paket (`pyproject.toml` mit `setuptools` und `package-data` für `boards/*.json`) sowie als PlatformIO-Bibliothek (`dmatheja/mcu-pin-solver@^0.2.0` in der PlatformIO Registry). Listing 6.6 zeigt die Kernlogik des SCons-Pre-Build-Hooks und die Exportkonfiguration.

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

Fünf Härtungsmaßnahmen sichern den produktiven Einsatz: (1) Übergabe von `$PROJECT_INCLUDE_DIR` per `--include-dir`, (2) versionsbeschränkte Paketprüfung mit klarer Fehlerhilfe bei Offline-Umgebungen oder geschützten System-Python-Installationen (PEP 668), (3) saubere Trennung zwischen Exit-Code `1` (Pin-Konflikt) und `2` (Konfigurationsfehler), (4) Schutz vor mehrfacher SCons-Skriptausführung über den Umgebungsmerker `_MCU_VALIDATOR_RAN` sowie (5) vollständige Isolation des Demo-Codes (`"srcFilter": ["-<*>"]` und selektives `export.include`), sodass fremde PlatformIO-Projekte keine fremden `.cpp`-Dateien kompilieren.

Insgesamt vereint Version `0.2.0` damit eine klar geschichtete, top-down lesbare Python-Architektur mit strenger Schema-Validierung, formal charakterisierter MaxSMT-Gewichtung und reproduzierbarer Paketierung für CLI- und PlatformIO-Umgebungen.

---

## 7 Evaluation

Die empirische Evaluation von `mcu-pin-solver` (`v0.2.0`) ruht auf fünf Säulen: (1) der automatisierten Testsuite aus 42 Tests samt plattformübergreifender CI-Matrix, (2) zwölf Grenzfallgruppen in 14 Einzelkonfigurationen im direkten Vergleich zwischen `v0.1.0` und `v0.2.0`, (3) Laufzeit- und Skalierungsmessungen bis 20 Pins und 21 Dateien, (4) einem realen End-to-End-Build-Test über die PlatformIO Registry sowie (5) einer TCO- und Break-even-Betrachtung.

### 7.1 Evaluationsdesign und Messumgebung

Die Testsuite gliedert sich in fünf modulare Dateien (`tests/test_board.py`, `test_parser.py`, `test_solver.py`, `test_cli.py`, `test_scenarios.py`). Zur Absicherung von NFA-04 wendet `test_scenarios.py` in jedem `UNSAT`-Szenario die von Z3 vorgeschlagenen Pin-Nummern unmittelbar auf das `ParsedProject` an und re-validiert das Ergebnis gegen sämtliche harten Regeln des Hardware-Profils.

Alle Zeitmessungen wurden auf der in Tabelle 7.1 dokumentierten Umgebung erhoben. Zur Kompensation betriebssystembedingter Schwankungen wurden jeweils Mediane über $N = 10$ vollständige Subprozess-Aufrufe bzw. $M = 30$ In-Process-Durchläufe (im Skalierungsbenchmark $M = 15$) gebildet.

| Komponente | Spezifikation |
| :--- | :--- |
| Prozessor / Betriebssystem (lokal) | AMD Ryzen 9 3900X 12-Core Processor, Microsoft Windows 10 Pro |
| Python-Laufzeit (lokal) | Python `3.14.7` |
| Solver und Parser | `z3-solver` `5.4.1.0`, `tree-sitter` `0.26.1`, `tree-sitter-cpp` `0.23.4` |
| PlatformIO Core (lokal) | PlatformIO Core `6.2.0` (Plattform `espressif32` `6.12.0`, Arduino-Framework) |
| CI-Umgebung (GitHub Actions) | `ubuntu-latest` & `windows-latest`, Python `3.10` & `3.12`, plus `ruff` & `mypy` |

*Tabelle 7.1: Mess- und CI-Umgebung (`v0.2.0`).*

### 7.2 Automatisierte Testsuite und Regressionsszenarien

Der Testlauf `python -m unittest discover -s tests -v` bestand alle **42 Tests** lokal in ca. 3,4 s sowie in sämtlichen fünf Jobs der GitHub-Actions-CI (`lint`, `ubuntu-latest` 3.10/3.12, `windows-latest` 3.10/3.12):

- **`test_board.py` (12 Tests):** Konsistenz aller mitgelieferten Board-JSONs, Präfix-Sortierung, Unterstrich-Normalisierung, direkte `.json`-Pfade sowie sieben Schema-Negativtests.
- **`test_parser.py` (11 Tests):** Nicht-Pin-Konstanten und lokale Variablen, geklammerte Makros `(12)` und Suffixe `12u`, Latin-1-Kommentare, direkte Pin-Literale inklusive Fähigkeits-Merge, 3-Wege-`#ifdef`-Schlüssel, `GPIO_12`-Kollisionsschutz, Namens-Fallback (`OLED_SDA_PIN`, `oledSdaPin`, `SPI_MOSI_PIN`), `Serial1`, dateiübergreifende Konflikte und `--include-dir`.
- **`test_solver.py` (8 Tests):** `SDA == SCL` (benannt und literal), `Wire` vs. `Wire1`, SPI-`CS` und `SCK == MOSI`, Schonung knapper ADC-Pins, Überbuchung (`repair_possible=False`), leeres Projekt und Schutz gegen doppelte Signalnamen.
- **`test_cli.py` (7 Tests):** `--list-boards`, `--version`, `--boards-dir`, Warnungsfreiheit unter `python -W error`, Exit-Code `2` ohne Stacktrace bei unbekanntem Board bzw. fehlerhafter JSON-Datei sowie 0-Pin-Warnung.
- **`test_scenarios.py` (4 Testmethoden über 9 Konstellationen):** Sämtliche neun End-to-End-Regressionsszenarien (Tabelle 7.2) einschließlich automatischer Re-Validierung der Z3-Vorschläge.

| Nr. | Zielpfad | Board | Erwartet & Gemessen | Geprüfter Sachverhalt |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `src/main.cpp` | `esp32-c3` | SAT | Demo-Sketch (`STATUS_LED=8` [Onboard-LED/Strapping, weich erlaubt], `SOIL_SENSOR=1`, `RELAY_PIN=4`, `WiFi.softAP`, `Serial.begin`) |
| 2 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1 & 2: Flash-Pin 12 und `ADC2` (Pin 5) bei aktivem WLAN |
| 3 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | Identischer Code auf ESP32-S3 gültig (Pin 12 regulär, Pin 5 in `ADC1`) |
| 4 | `tests/scenarios/01_valid_sketch.cpp` | `esp32-c3` | SAT | Positivkontrolle: fehlerfreier Sketch mit WLAN und USB-Serial |
| 5 | `tests/scenarios/02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 2: `Serial.begin` sperrt native USB-Pins 18 und 19 |
| 6 | `tests/scenarios/03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1, 3, 4: Doppelbelegung (7), fehlender Pin (32), fehlendes ADC (6) |
| 7 | `tests/scenarios/04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 4: geteilter I2C-Bus auf 6/7 bleibt gekoppelt, LED weicht aus |
| 8 | `tests/scenarios/05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | Syntaxbaum ignoriert `WiFi.begin(...)` in Kommentar und Zeichenkette |
| 9 | `tests/scenarios/06_multi_file_project/src` | `esp32-c3` | UNSAT | Mehrdatei-Analyse: `include/pins.h` + `src/main.cpp` + `src/sensors.cpp` |

*Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien.*

### 7.3 Ausgewählte Szenarien im Detail

Szenario 0 wurde bereits in Abschnitt 5.6 detailliert betrachtet. Die Listings 7.1 bis 7.5 dokumentieren die realen CLI-Ausgaben von Version `0.2.0` für die Szenarien 02 bis 06.

In **Szenario 02** (Listing 7.1) sperrt `Serial.begin(115200)` die nativen USB-Pins 18 und 19. `ENABLE_PIN` (GPIO 6) bleibt unverändert; dank der dritten Prioritätsstufe landen `STEP_PIN` und `DIR_PIN` auf den Standard-GPIOs 21 und 10, statt knappe `ADC1`-Pins zu verbrauchen.

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
*Listing 7.1: CLI-Ausgabe für Szenario 02 (`v0.2.0`, Rückgabewert `1`).*

In **Szenario 03** (Listing 7.2) meldet Stufe 1 sämtliche drei Fehlerklassen in einem Durchlauf samt exakten Zeilenangaben. `POTI_PIN` wechselt auf `ADC1` (GPIO 0), `PIR_SENSOR` auf GPIO 10, und `BUZZER_PIN` übernimmt den durch `POTI_PIN` freigewordenen Standard-GPIO 6.

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
*Listing 7.2: CLI-Ausgabe für Szenario 03 (`v0.2.0`, Rückgabewert `1`).*

**Szenario 04** (Listing 7.3) demonstriert die in Abschnitt 6.5 hergeleitete Bus-Trägheit: Alle vier gekoppelten I2C-Signale verbleiben unverändert auf GPIO 6/7, während nur `STATUS_LED` auf GPIO 20 verlagert wird.

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
*Listing 7.3: CLI-Ausgabe für Szenario 04 (`v0.2.0`, Rückgabewert `1`).*

**Szenario 05** (Listing 7.4) bestätigt die Immunität der Syntaxbaum-Analyse gegenüber `WiFi.begin(...)` innerhalb von Kommentaren und Zeichenkettenliteralen (`Active Modules : none`, `SAT`).

```text
=================================================================
 Target         : tests/scenarios/05_ast_ignores_strings_and_comments.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 1 (SOIL_SENSOR=5)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 7.4: CLI-Ausgabe für Szenario 05 (`v0.2.0`, Rückgabewert `0`).*

**Szenario 06** (Listing 7.5) aggregiert `include/pins.h`, `src/main.cpp` und `src/sensors.cpp`, ordnet beide Konflikte exakt ihren Header-Definitionen (`pins.h:4` und `pins.h:5`) zu und weist `STATUS_LED` den freien Standard-GPIO 10 zu (ohne USB-Pin GPIO 18 zu beanspruchen).

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
*Listing 7.5: CLI-Ausgabe für Szenario 06 (`v0.2.0`, Rückgabewert `1`).*

### 7.4 Grenzfallexperimente und Entwicklung von v0.1.0 zu v0.2.0

Tabelle 7.3 dokumentiert zwölf gezielte Grenzfallgruppen in insgesamt **14 Einzelkonfigurationen** (`a, b, c, c2, d, e, f, f2, h, i, j, k, l, m`; 13 C++-Testfälle in `CASES` plus der synthetische Leere-Domäne-Test `e` mit zwei Teilkonfigurationen, Anhang G) auf dem `esp32-c3`-Profil und stellt den Prototyp `v0.1.0` dem finalen Stand `v0.2.0` gegenüber. Neun systematische Schwachstellen aus `v0.1.0` wurden in `v0.2.0` vollständig behoben; die beiden bewusst verbleibenden Grenzen (`i` und `j`) fließen in Abschnitt 8.2 ein. Anzumerken ist zu Fall `k`, dass der reale ESP32-C3 physisch lediglich einen Hardware-I2C-Controller (`I2C0`) besitzt; der Test prüft am `esp32-c3`-Profil gezielt die chip-agnostische Trennung getrennter Bus-Instanzen (`Wire` vs. `Wire1`), die in der Praxis etwa auf dem zweikanaligen ESP32-S3 relevant ist.

| ID | Getestete Konstellation | Verhalten in `v0.1.0` | Gemessenes Verhalten in `v0.2.0` | Bewertung (`v0.2.0`) |
| :---: | :--- | :--- | :--- | :--- |
| `a` | Direkte Literale (`pinMode(12, OUTPUT); analogRead(5);`) + `WiFi` | `SAT` (**False Negative**) | `UNSAT`: `GPIO_12 -> 10`, `GPIO_5 -> 0` | **behoben** |
| `b` | Lokale Zähler (`blinkCount`, `retries`) & `BAUD_RATE 115200` | `UNSAT` (**False Positive**) | Nur `STATUS_LED = 3` geprüft $\rightarrow$ `SAT` | **behoben** |
| `c`, `c2` | Gleichstand `BUZZER_PIN = 7` / `SERVO_PIN = 7`, beide Reihenfolgen | `BUZZER_PIN` blieb (Z3-Heuristik) | `SERVO_PIN` bleibt in beiden Fällen (`BUZZER -> 20` bzw. `6`) | Gleichstand weiterhin solverabhängig |
| `d` | 6 Analogsensoren `S0..S5` + WLAN (nur 5 `ADC1`-Pins vorhanden) | `GPIO None` für alle 6 Signale | `repair_possible=False`, klare Kapazitätsmeldung (Listing 7.6) | **behoben** |
| `e` | Synthetische Fähigkeit `'can'` ($P_i = \emptyset$, 1 bzw. 2 Signale) | `CAN_TX: -1` bzw. `-1 != -1`-Bruch | Konsistent `repair_possible=False`, `suggested={}` | **behoben** |
| `f`, `f2` | `SOIL_SENSOR = 1` (`adc`) vs. `STATUS_LED = 1` (`gpio`), beide Reihenfolgen | `SOIL_SENSOR = 1`, `LED -> 7` | In beiden Fällen `SOIL_SENSOR = 1`, `STATUS_LED -> 7` (+25 Pkt.) | Spezialist-Priorität bestätigt |
| `h` | Doppelrolle: `Wire.begin(MY_PIN, MY_SCL)` + `analogRead(MY_PIN)` | Nur `'adc'`; Vorschlag ohne I2C | `capabilities={'adc', 'i2c'}` $\rightarrow$ `MY_PIN -> 0` (`ADC1` & `I2C`) | **behoben** |
| `i` | `constexpr int LED_A = 12;`, `static const uint8_t LED_B = 13;`, `const gpio_num_t LED_C = GPIO_NUM_14;` | `LED_A`, `LED_B` erkannt; `LED_C` ignoriert | `LED_A -> 7`, `LED_B -> 6`; `gpio_num_t` weiterhin ignoriert | **verbleibende Grenze** |
| `j` | `#ifdef USE_EXTERNAL_LED` (Pin 2) / `#else` (Pin 12) | Beide Zweige $\rightarrow$ `UNSAT` | Beide Zweige mit eindeutigen Schlüsseln $\rightarrow$ `UNSAT` (kollisionsfrei auch bei 3 Zweigen) | **verbleibende Grenze** (False Positive) |
| `k` | `Wire.begin(SDA_A, SCL_A)` & `Wire1.begin(SDA_B, SCL_B)` auf 6/7 | `SAT` (**False Negative**) | `UNSAT` (`Wire` $\neq$ `Wire1`), 4 getrennte Pins (`6, 20, 10, 7`) | **behoben** |
| `l` | Zwei `SPI.begin`-Aufrufe mit `MISO_P = 7`, `CS_A = 7`, `CS_B = 7` | `SAT` (**False Negative**) | `UNSAT` (`CS` als `gpio`), alle 5 Signale getrennt (`6, 21, 10, 7, 20`) | **behoben** |
| `m` | `OLED_SDA = 6` und `OLED_SCL = 6` in `Wire.begin(OLED_SDA, OLED_SCL)` | `SAT` (**False Negative**) | `UNSAT` (`Wire:sda` $\neq$ `Wire:scl`), `OLED_SDA=6`, `OLED_SCL -> 10` | **behoben** (neu geprüft) |

*Tabelle 7.3: Ergebnisse der Grenzfallexperimente auf `esp32-c3` (`v0.1.0` im Vergleich zu `v0.2.0`).*

Listing 7.6 dokumentiert die bereinigte Ausgabe im Überbuchungsfall `d` (Schubfachprinzip: 6 `ADC1`-Forderungen bei 5 physischen `ADC1`-Pins): Anstelle fehlerhafter `GPIO None`-Zeilen meldet `v0.2.0` unmissverständlich die ausgeschöpfte Hardware-Kapazität.

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
*Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, `v0.2.0`, Rückgabewert `1`).*

### 7.5 Laufzeit-, Skalierungsmessung und PlatformIO-End-to-End-Prüfung

**Regressionsszenarien.** Tabelle 7.4 fasst die gemessenen Medianlaufzeiten aller neun Standardszenarien zusammen. Als Prozess-Basislinie beanspruchten allein der Start des Python-Interpreters und der Import von `z3`, `tree_sitter` und `tree_sitter_cpp` im Median **139 ms**.

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

**Skalierung bis 20 Pins und 21 Dateien.** Da die Standardszenarien lediglich 1 bis 5 Signale umfassen, vermisst `scaling_benchmark.py` (Anhang G) synthetische Multi-Datei-Projekte auf dem größeren **ESP32-S3** (45 deklarierte GPIOs, 33 frei nutzbar) von 3 bis 20 Signalen – sowohl im `UNSAT`-Fall (2 Konflikte: reservierter Flash-Pin GPIO 26 und `ADC2`-Pin GPIO 11 bei aktivem WLAN) als auch im konfliktfreien 20-Pin-`SAT`-Fall (Tabelle 7.5).

| Signale ($n$) | Dateien | Fall | Paarweise Ungleichungen $\binom{n}{2}$ | Parsen ($M=15$) | Lösen ($M=15$) | Summe In-Process |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 3 | 3 | UNSAT (2 Konflikte) | 3 | 1,86 ms | 47,46 ms | 49,32 ms |
| 6 | 6 | UNSAT (2 Konflikte) | 15 | 2,81 ms | 125,42 ms | 128,23 ms |
| 10 | 10 | UNSAT (2 Konflikte) | 45 | 4,12 ms | 299,31 ms | 303,43 ms |
| 15 | 15 | UNSAT (2 Konflikte) | 105 | 5,80 ms | 650,44 ms | 656,25 ms |
| 20 | 20 | UNSAT (2 Konflikte) | 190 | 7,34 ms | 1132,81 ms | 1140,15 ms |
| **20** | **21** | **SAT (konfliktfrei)** | **– (Stufe 1)** | **7,53 ms** | **0,06 ms** | **7,59 ms** |

*Tabelle 7.5: Skalierungsmessung auf ESP32-S3 von 3 bis 20 Pins und bis zu 21 Dateien (`v0.2.0`).*

Die Messreihe liefert zwei zentrale Befunde:

1. **Lineares Parsing und hohe Wirksamkeit des zweistufigen Ablaufs.** Das Tree-Sitter-Parsing skaliert strikt linear mit rund 0,35 ms pro Datei. Dank Entscheidung 3 dauert das konfliktfreie 20-Pin-/21-Datei-Projekt In-Process insgesamt nur **7,59 ms** (~150 ms E2E) – rund **150-fach** schneller als der konflikthafte Gesamtlauf (`1140,15 ms`); betrachtet man isoliert die Validierungs- bzw. Lösungsphase (`0,06 ms` in Stufe 1 gegenüber `1132,81 ms` in Stufe 2), übersteigt der Geschwindigkeitsvorteil den Faktor **18.800**.
2. **Ursache des überlinearen MaxSMT-Wachstums bei $n = 20$.** Im `UNSAT`-Fall bleibt die End-to-End-Laufzeit bis $n = 15$ konfliktbehaftete Signale unter 1 s (~0,80 s), überschreitet diese Schwelle jedoch bei $n = 20$ (`1140,15 ms` In-Process, ~1,28 s E2E). Ursache ist nicht allein die quadratische Anzahl von $\binom{20}{2} = 190$ Ungleichungen, sondern das Zusammenspiel dreier Z3-Faktoren: (a) Durch die Deklaration als `z3.Int` verarbeitet $\nu Z$ die Formel im **`QF_LIA`-Arithmetik-Backend**, in dem jede Ungleichung $v_i \neq v_j$ als Disjunktion linearer Ungleichungen ($v_i < v_j \lor v_i > v_j$) mit dem Simplex-Theorie-Solver interagiert; (b) bei bis zu 60 gewichteten weichen Klauseln lösen wiederholte MaxRes-Kernextraktionen häufige Übergänge zwischen SAT-Kern und Arithmetik-Theorie aus; und (c) die zahlreichen hinsichtlich der Zielfunktion völlig äquivalenten freien Standard-GPIOs des ESP32-S3 erzeugen kombinatorische **Symmetrien**, die den Suchraum aufblähen. Abschnitt 8.4 leitet daraus gezielte Kodierungsverbesserungen ab (`QF_FD`/One-Hot-PB und lexikographische Zielfunktionen).

**Realer End-to-End-Test über die PlatformIO Registry.** Zur Prüfung aus Anwendersicht wurde `mcu-pin-solver@0.2.0` in einem separaten, leeren PlatformIO-Projekt installiert:

1. `pio pkg install` bezog **`dmatheja/mcu-pin-solver@0.2.0`** (20,71 KB) direkt aus der öffentlichen PlatformIO Registry.
2. Ein `pio run` auf fehlerhaftem ESP32-C3-Quelltext (`STATUS_LED = 12`, `SOIL_SENSOR = 5`, `WiFi.begin`) brach den Build über `pio_hook.py` in **1,21 s** (`UNSAT`, Exit-Code `1`) *vor* dem Compilerstart ab und gab die Diagnose (`main.cpp:3`, `main.cpp:4`) samt Z3-Reparaturvorschlag aus.
3. Nach Übernahme der vorgeschlagenen Pins passierte `pio run` den Validator (`SAT`), übersetzte das Projekt mit der RISC-V-Toolchain und erzeugte `firmware.elf` und `firmware.bin` fehlerfrei in **17,76 s** (Exit-Code `0`).
4. Ein separater `git clone` des öffentlichen Repositories in ein leeres Verzeichnis bestand `pip install .`, `mcu-validate --list-boards` und sämtliche 42 Tests ohne manuelle Nachkonfiguration.

### 7.6 Wirtschaftliche Bewertung

Um neben der technischen Tragfähigkeit den betriebswirtschaftlichen Nutzen im industriellen Embedded-Prototyping – etwa im F&E-Kontext von Freudenberg Technology Innovation (FTI) – belastbar zu bewerten, werden Gesamtkosten (*Total Cost of Ownership*, TCO), Einsparpotenziale und Break-even-Punkte auf Basis explizit ausgewiesener, konservativer Modellannahmen gegenübergestellt.

**1. Kostenseite (TCO).**

- **Lizenz- und Betriebskosten:** Der gesamte Technologie-Stack (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`, PlatformIO, GitHub Actions) steht unter permissiven Open-Source-Lizenzen (MIT/BSD). Es fallen **0 € Lizenzkosten** und **keine laufenden API- oder Token-Gebühren** an. Im Vergleich zu einem Cloud-basierten „LLM-as-a-Judge“-Prüfverfahren entfallen zugleich Datenschutz- und IP-Risiken durch den Upload proprietärer Firmware, da die Prüfung vollständig lokal abläuft.
- **Einmaliger Entwicklungsaufwand:** Der Erstellungsaufwand im Rahmen dieser 5-ECTS-Studienarbeit liegt bei ca. **150 Stunden** (bei einem kalkulatorischen internen Vollkostensatz von 80–120 €/h entspricht dies 12.000–18.000 €; für anwendende Teams, welche die veröffentlichte Open-Source-Bibliothek direkt einsetzen, entfällt dieser Initialaufwand).
- **Integrations- und Pflegeaufwand:** Die Einbindung in ein PlatformIO-Projekt erfordert zwei Zeilen in `platformio.ini` (< 10 Minuten). Das Erstellen und Datenblatt-Prüfen eines neuen Chip-Profils (`boards/<chip>.json`) beansprucht dank Schema-Validierung und Prompt-Vorlage ca. **1–2 Stunden** (~100–240 €); für fortlaufende Abhängigkeits- und Profilpflege werden konservativ **4 Stunden pro Jahr** (~400 €) angesetzt.

**2. Nutzenseite (Fehlervermeidung und Durchlaufzeit).** Gemäß der *Cost-of-Change*-Relation von Boehm [[4]](#ref-4) und Boehm/Basili [[5]](#ref-5) steigen die Behebungskosten stark an, sobald ein Hardware-Defekt die Kodierungsphase verlässt:

- **Vermiedene Labor-Fehlersuche:** Ein unerkannter `ADC2`/WLAN- oder Flash-Pin-Konflikt zeigt sich auf der Hardware meist durch unspezifische Boot-Loops oder Null-Messwerte. Eine Fehlersuche mit Oszilloskop, Logikanalysator und Datenblattstudium bindet rasch **2 bis 4 Entwicklerstunden** (kalkulatorisch **160–480 €** pro Vorfall).
- **Vermiedene Prototyp-Leiterplatten-Iterationen (PCB-Respin):** Gelangt eine fehlerhafte Pin-Belegung in eine kundenspezifische Prototyp-Platine, entstehen Fertigungs- und Bestückungskosten von typischerweise **300–1.000 €** zuzüglich **1–2 Wochen Projektverzögerung**.
- **Verkürzter Iterationszyklus:** Der Pre-Build-Abbruch nach **1,21 s** spart gegenüber einem vollständigen Kompilier- und Flash-Zyklus (~20–30 s) unmittelbar Wartezeit; zugleich ersetzt der deterministische Z3-Vorschlag typischerweise 2–4 erfolglose LLM-Selbstkorrektur-Schleifen [[15]](#ref-15) samt zugehörigem Zeit- und Token-Verbrauch.

**3. Modellhafte Break-even-Betrachtung.** Tabelle 7.6 quantifiziert drei konservative Einsatzszenarien bei einem mittleren internen Stundensatz von **100 €/h** (ohne Einrechnung vermiedener PCB-Respin-Kosten in den Szenarien A und B als zusätzliche Sicherheitsmarge).

| Szenario (Annahme: 100 €/h, 3 h gespart je verhindertem Pin-Fehler) | Aufwand | Einsparung je Vorfall | Break-even | Jährlicher Netto-Nutzen (konservativ) |
| :--- | :---: | :---: | :--- | :--- |
| **A: Nutzung fertiger Profile** (ESP32-C3/-S3 in 1 Team, 5 Entwickler) | ~1 h Setup + 4 h Pflege = **500 €/Jahr 1** | **300 €** (3 h Debug) | ab **2** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.500 €/Jahr** |
| **B: Ergänzung eines neuen Chips** (z. B. RP2040/STM32, 2 h JSON + Prüfung) | ~2 h Profil + 5 h Setup/Pflege = **700 €/Jahr 1** | **300 €** (3 h Debug) | ab **3** verhinderten Fehlern | bei 10 Fehlern/Jahr: **+2.300 €/Jahr** |
| **C: Vollkosten inkl. Eigenentwicklung** (150 h = 15.000 €, 1 Team) | **15.000 €** einmalig + **400 €/Jahr** | **300 €** Debug (bzw. **1.000 €** inkl. Respin) | ~50 Debug-Fehler bzw. ~15 Respins (bezogen auf Initialkosten; inkl. Pflege leicht höher) | langfristig positiv bei mehrjähriger Team- oder Open-Source-Nutzung |

*Tabelle 7.6: Modellhafte Wirtschaftlichkeits- und Break-even-Betrachtung (Modellannahmen im Text dokumentiert).*

**4. Wirtschaftliche Risiken und Grenzen.** Dem Nutzen stehen drei Risiken gegenüber: (1) Neue Silizium-Revisionen oder SDK-Änderungen (wie die Verschärfung der `ADC2`-Sperre im ESP-IDF-Treiber [[11]](#ref-11)) erfordern Pflege der JSON-Profile. (2) Schnittstellenänderungen in Drittpaketen (`tree-sitter`, `z3-solver`) erzeugen Wartungsaufwand, der durch Versionsgrenzen und automatisierte CI eingedämmt wird. (3) Aufgrund verbleibender False Negatives (Abschnitt 8.2) darf `mcu-pin-solver` ein manuelles Schaltplan-Review vor einer kostenintensiven Leiterplatten-Fertigung **nicht ersetzen**, sondern entfaltet seinen optimalen wirtschaftlichen Hebel als nahezu kostenlose automatisierte Frühprüfstufe im täglichen Prototyping.

### 7.7 Soll-Ist-Abgleich

Tabelle 7.7 bewertet den Erfüllungsgrad sämtlicher in Kapitel 4 aufgestellten Anforderungen und Architektur-Invarianten am Stand `v0.2.0`.

| ID | Anforderung / Invariante | Status | Nachweis / Einschränkung |
| :--- | :--- | :---: | :--- |
| FA-01 | Hardware-Profil laden & validieren | erfüllt | `load_board` (längstes Präfix, `_`/`-`, direkter `.json`-Pfad) + strenge Schema-Validierung (`test_board.py`) |
| FA-02 | Mehrdatei-Analyse & `--include-dir` | erfüllt | Erfasst `include/` + `src/` sowie `--include-dir`; schließt `.pio/`, `build/`, `test/`, `tests/` aus |
| FA-03 | Fehlalarmarme Extraktion | weitgehend erfüllt | Erfasst Makros (inkl. `(12)`), Deklarationen (`12u`, `constexpr`, `static`) und Literale; ignoriert Kommentare, Strings, lokale Scopes und Nicht-Pin-Konstanten; offene Grenzen bei `#ifdef` (`j`) und `gpio_num_t` (`i`) |
| FA-04 | Kollisionssichere Widerspruchsbehandlung | erfüllt | `_reserve_unique_key` trennt widersprüchliche Definitionen und Literale global eindeutig (auch bei 3 `#ifdef`-Zweigen) |
| FA-05 | Fähigkeiten, Bus-Rollen & Module | erfüllt | Fähigkeitsmengen (`h`), positionsgenaue `Wire`/`SPI`/`Serial`-Auswertung inkl. `bus_group` und Namens-Fallback (`OLED_SDA_PIN`) |
| FA-06 | Präzise Einzeldiagnose | erfüllt | Meldet sämtliche Einzelkonflikte mit `datei:zeile`-Verweis und Regelbegründung (`reason`) |
| FA-07 | Kollision vs. geteilte Bus-Leitung | erfüllt | Koppelt geteilte Bus-Leitungen (`Wire:sda`), lehnt `SDA == SCL` (`m`), `Wire` vs. `Wire1` (`k`), `SCK == MOSI` und doppelte SPI-`CS` (`l`) ab |
| FA-08 | Minimal-invasive Reparatur & Kapazitätsmeldung | erfüllt | Dreistufige MaxSMT-Gewichtung (`1000`/`20`/`5`) + klare Meldung bei `repair_possible=False` (`d`, `e`) |
| FA-09 | Transparenter Bericht & Prompt | erfüllt | Zeigt `Checked Pins`, warnt bei `0` Pins und erzeugt kopierbare `Keep`/`Change`-Anweisungen |
| FA-10 | Build-Schranke & CLI | erfüllt | Verifiziert über `pip install .`, `mcu-validate` und realen PlatformIO-Registry-End-to-End-Lauf (`0.2.0`) |
| NFA-01–NFA-07 | Qualitätsanforderungen (ISO/IEC 25010:2023) | weitgehend erfüllt | 0 chip-spezifische Regeln in Python, 42 Tests, 5/5 grüne CI-Jobs (`ruff`, `mypy`); Zeitverhalten `< 1 s` erfüllt für alle `SAT`-Fälle bis 20 Pins (`7,59 ms` In-Process) und `UNSAT` bis 15 Pins (`0,80 s` E2E); bei 20 Pins `UNSAT` ~1,28 s E2E |
| INV-01–INV-06 | Architektur-Invarianten | erfüllt | Sämtliche sechs Invarianten im Codebestand umgesetzt und durch automatisierte Tests abgesichert |

*Tabelle 7.7: Soll-Ist-Abgleich der Anforderungen und Invarianten (`v0.2.0`).*

### 7.8 Gültigkeit der Ergebnisse (Threats to Validity)

Nach der empirischen Software-Engineering-Systematik von Wohlin et al. [[25]](#ref-25) werden drei Validitätsdimensionen kritisch eingeordnet:

- **Interne Validität:** Subprozess-Startzeiten unter Windows unterliegen Einflüssen von Hintergrunddiensten, Virenscannern und Dateisystem-Caches. Durch 10 bis 30 Wiederholungen, Auswertung des ausreißerrobusten Medians sowie die strikte Trennung von End-to-End-Subprozesszeiten und In-Process-Messungen wird diese Störgröße methodisch kontrolliert.
- **Externe Validität:** Sämtliche 42 Tests, neun Regressionsszenarien, zwölf Grenzfallgruppen (14 Konfigurationen) sowie die synthetischen Skalierungsprojekte wurden im Rahmen dieser Arbeit konstruiert. Eine großskalige empirische Benchmark-Studie über eine repräsentative Stichprobe realer, von mehreren aktuellen Sprachmodellen erzeugter Embedded-Projekte (analog zu [[8]](#ref-8) oder [[22]](#ref-22)) liegt bislang **nicht** vor. Zudem decken die mitgelieferten Profile gegenwärtig zwei Espressif-Familien (ESP32-C3 und ESP32-S3) ab; weitere verbreitete Architekturen (RP2040, STM32, ESP32-C6) sind konzeptionell über das offene JSON-Schema vorbereitet, aber noch nicht eingepflegt.
- **Konstruktgültigkeit:** Das Ergebnis `SAT` bescheinigt formal ausschließlich die Konsistenz des *syntaktisch extrahierten Pin-Modells* relativ zum *geladenen JSON-Hardware-Profil* ($\mathcal{M}_{\text{code}} \models \mathcal{S}_{\text{board}}$). Elektrische Eigenschaften (Strombelastbarkeit, Pull-up-Widerstände, Spannungspegel), Peripherie-Instanzbudgets sowie syntaktisch nicht erfasste C++-Konstrukte (Abschnitt 8.2) liegen außerhalb des geprüften Konstrukts.

---

## 8 Diskussion, Grenzen und Ausblick

### 8.1 Diskussion der Ergebnisse

Die Evaluation belegt zweierlei. Zum einen lässt sich die in Kapitel 3 identifizierte Forschungslücke – deterministische Syntaxbaum-Extraktion ohne LLM-Formalisierungshalluzinationen, gekoppelt mit schema-validiertem Hardware-Wissen und Z3-MaxSMT-Reparatur – in einem kompakten, klar modularisierten Werkzeug praxistauglich schließen. Der reale PlatformIO-Registry-End-to-End-Test bestätigt den Nutzen im Entwicklungsalltag unmittelbar: Ein fehlerhafter Build bricht nach 1,21 s noch vor dem Start der RISC-V-Toolchain ab und liefert präzise `datei:zeile`-Diagnosen samt einer Z3-geprüften Ersatzbelegung, die gültige Originalpins, geteilte Bus-Leitungen und knappe `ADC1`-Kanäle gleichermaßen bewahrt.

Zum anderen unterstreicht der Vergleich zwischen Prototyp `v0.1.0` und Version `v0.2.0` den methodischen Wert gezielter *Fault-Injection*- und Skalierungsexperimente: Erst die systematische Konstruktion von Grenzfällen (Abschnitt 7.4) und der 20-Pin-Skalierungsbenchmark (Abschnitt 7.5) legten neun konkrete Defekte in `v0.1.0` sowie das `QF_LIA`-MaxSMT-Laufzeitknie bei rund 20 konfliktbehafteten Signalen offen.

### 8.2 Verbleibende Grenzen des Systems

Auch in Version `0.2.0` bestehen sechs klar benennbare Systemgrenzen, die unmittelbar aus den getroffenen Architekturentscheidungen folgen (Tabelle 8.1):

1. **Präprozessor-Verzweigungen (`#ifdef` / `#else`).** Da Tree-Sitter keinen C-Präprozessor ausführt, werden sämtliche Zweige bedingter Kompilierung gleichzeitig traversiert. Enthält ein für ein anderes Zielboard vorgesehener inaktiver Zweig einen auf dem aktuellen Zielchip unzulässigen Pin (Experiment `j`), entsteht weiterhin ein False Positive – wenngleich global eindeutige Schlüssel (`_reserve_unique_key`) nun selbst bei dreifachen Verzweigungen jede Solver-Kollision verhindern.
2. **Spezielle C++-Typen und berechnete Ausdrücke.** ESP-IDF-Aufzählungstypen wie `const gpio_num_t LED = GPIO_NUM_14;` (Experiment `i`) werden doppelt ausgeschlossen, da `gpio_num_t` nicht in `PIN_VAR_TYPES` enthalten ist und `GPIO_NUM_14` im Syntaxbaum ein `identifier` statt eines `number_literal` ist. Ebenso bleiben Pin-Arrays (`const int pins[] = {...}`), klassische `enum`-Definitionen sowie arithmetische Makroausdrücke (`#define LED (BASE + 2)`) unberücksichtigt.
3. **Drittbibliotheks-Konstruktoren und -Methoden.** Wird eine Pin-Konstante ausschließlich an eine unbekannte Bibliotheks-API übergeben (etwa `myServo.attach(OUT_1)` oder `OneWire bus(DATA_LINE)`) und entspricht ihr Bezeichner nicht den Namensmustern in `_infer_from_name()`, bleibt sie unentdeckt (False Negative); bei Konstruktoren wie `DHT dht(DHT_PIN, DHT22);` greift lediglich der generische `gpio`-Fallback.
4. **USB-Serial-Annahme bei externer USB-UART-Brücke.** Die mitgelieferten ESP32-Profile koppeln `Serial.begin` pauschal an `usb_serial` und sperren GPIO 18/19 (C3) bzw. 19/20 (S3). Auf Entwicklungsboards mit externem USB-UART-Wandlerchip (`ARDUINO_USB_CDC_ON_BOOT=0`, etwa dem CP2102N auf `esp32-c3-devkitm-1`) wirkt diese Regel zweifach ungenau: Sie sperrt die nativen USB-Pins möglicherweise zu konservativ, schützt jedoch umgekehrt die tatsächlich von `Serial` genutzten Standard-UART0-Pins (GPIO 20/21 bzw. 43/44) nicht.
5. **Hardware-Modellierungstiefe, Varianten und Solver-Skalierung.** Bisher liegen Profile für ESP32-C3 und ESP32-S3 vor (mit konservativer Reservierung von GPIO 33–37 beim ESP32-S3 für Octal-PSRAM-Module). Optionale Schema-Felder für reine Eingangspins (`input_only`, etwa GPIO 34–39 beim klassischen ESP32), Peripherie-Instanz- und Kanalbudgets (z. B. 1× I2C und 6× LEDC-Kanäle beim ESP32-C3 vs. 2× I2C und 8× LEDC beim ESP32-S3) sowie siliziumspezifische Treiber-Errata (`ADC-183` / `CONFIG_ADC_ONESHOT_FORCE_USE_ADC2_ON_C3` [[11]](#ref-11)) sind noch nicht modelliert. Zudem erreicht die `QF_LIA`-MaxSMT-Laufzeit bei 20 konfliktbehafteten Pins 1,14 s (Tabelle 7.5), und ab $n \ge 40$ Signalen wäre die globale Dominanz des fixen Haltegewichts `1000` über $25n$ nicht mehr garantiert (Abschnitt 6.4).
6. **Manuelle LLM-Rückkopplung und ausstehende LLM-Benchmark-Studie.** Der Reparatur-Prompt wird derzeit manuell in die LLM-Sitzung kopiert; eine systematische empirische Messung der Pin-Fehlerraten mehrerer realer Sprachmodelle vor und nach dem Einsatz von `mcu-pin-solver` steht als Folgestudie aus.

| Nr. | Verbleibende Grenze (`v0.2.0`) | Betroffenes Modul | Auswirkung | Gezielter Ausbaupfad |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `#ifdef` / `#else`-Zweige | `parser.py` | False Positive bei Alternativ-Konfigurationen (`j`) | Auswertung aktiver `-D`-Build-Flags aus `platformio.ini` |
| 2 | `gpio_num_t`, Arrays, `enum`, Rechen-Makros | `parser.py` | False Negative (`i`) | Erweiterung um `GPIO_NUM_<n>`, `enumerator` und einfache Konstantenfaltung |
| 3 | Drittbibliotheks-APIs / Konstruktoren | `parser.py` | False Negative ohne `PIN`-Namensmuster | Deklarativ konfigurierbare API-Signaturen je Projekt |
| 4 | `Serial.begin` vs. externe USB-UART-Brücke | `boards/*.json` / `pio_hook.py` | Zu strenge USB-Sperre bzw. fehlender UART0-Schutz | Auswertung von `-DARDUINO_USB_CDC_ON_BOOT` aus PlatformIO |
| 5 | Katalog, Schema-Tiefe, Instanzbudgets & MaxSMT | `boards/*.json` / `solver.py` | Nur C3/S3; ~1,14 s bei 20 Konflikt-Pins; Gewichtsgrenze $n \ge 40$ | `input_only`, Instanzbudgets, `QF_FD`/PB-Kodierung, $\nu Z$-`priority="lex"` |
| 6 | Manueller Prompt & kein LLM-Benchmark | Workflow / Evaluation | Kopierschritt nötig; externe Validität offen | `--json` / MCP-Schnittstelle + systematische Multi-LLM-Studie |

*Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`.*

### 8.3 Reflexion der KI-gestützten Entstehung

Sowohl die Implementierung von `v0.1.0` und `v0.2.0` als auch Entwürfe dieser Ausarbeitung entstanden unter dokumentierter Mitwirkung großer Sprachmodelle (vgl. Verzeichnis der verwendeten KI-Hilfsmittel). Dabei trat die zentrale These dieser Studienarbeit – die Notwendigkeit deterministischer Verifikation gegenüber statistisch plausiblen LLM-Ausgaben – zweimal unmittelbar im eigenen Arbeitsprozess zutage:

1. **Empirische Widerlegung plausibler Hypothesen:** Ein früher Entwurf behauptete, Z3 löse Gleichstände zwischen identisch gewichteten Signalen deterministisch entlang der Deklarationsreihenfolge auf – erst die Experimente `c` und `c2` widerlegten diese Annahme direkt am laufenden Code und führten zur exakten Analyse der Z3-Heuristik in Abschnitt 6.5.
2. **Aufdeckung subtiler Defekte durch Unit-Tests, CI und Skalierungsbenchmarks:** Beim Ausbau der Namensheuristik in `v0.2.0` überlas der reguläre Ausdruck `WORD_RE` zunächst Großbuchstaben-Tokens vor Unterstrichen (`OLED_SDA_PIN`), weil der Lookahead Unterstriche nicht einschloss; erst der dedizierte Unit-Test machte den Fehler sofort sichtbar. Ebenso zeigte erst die produktive GitHub-Actions-CI-Matrix, dass `ubuntu-latest` keine vorkonfigurierten Python-3.9-Binaries mehr bereitstellt, während erst der 20-Pin-Skalierungsbenchmark (Tabelle 7.5) das Überschreiten der 1-Sekunden-Schwelle im `QF_LIA`-MaxSMT-Betrieb aufdeckte.

Automatisierte Tests, statische Typ- und Stilprüfungen (`mypy`, `ruff`) sowie empirische Messungen am realen Zielsystem erwiesen sich somit als unverzichtbares Korrektiv im KI-gestützten Software-Engineering.

### 8.4 Ausblick

Aus dem erreichten Stand `0.2.0` ergeben sich vier technisch und methodisch klar priorisierte Ausbaustufen:

1. **Einbindung von PlatformIO-Build-Flags (`-D`):** Durch das Auslesen der aktiven Präprozessor-Definitionen aus der SCons-Umgebung (`CPPDEFINES`) ließen sich sowohl bedingte `#ifdef`-Zweige selektiv auswerten als auch native USB-CDC-Konfigurationen (`ARDUINO_USB_CDC_ON_BOOT=1`) zuverlässig von Boards mit externer USB-UART-Brücke (`0` $\rightarrow$ Schutz von UART0) unterscheiden.
2. **Vollautomatisierter Agenten-Kreislauf (`--json` / MCP):** Eine strukturierte `--json`-Ausgabe sowie ein darauf aufbauender *Model Context Protocol*-(MCP-)Server erlauben KI-Coding-Agenten (analog zu AutoIOT [[22]](#ref-22) oder EmbedGenius [[26]](#ref-26)), `mcu-validate` direkt als deterministischen Hardware-Critic aufzurufen und Pin-Konflikte mit begrenzter Iterationszahl vollautomatisch aufzulösen.
3. **Solver-Beschleunigung und strenge Lexikographie für große MCUs (> 20–60 Pins):** Um das `QF_LIA`-Laufzeitknie aus Tabelle 7.5 und die feste Gewichtsgrenze ($n \ge 40$) zu überwinden, bieten sich zwei kombinierbare Schritte in Z3 an: Erstens die Umstellung von `z3.Int` mit expliziten paarweisen `!=`-Klauseln auf eine **boolesche One-Hot- / Pseudo-Boolean-Kodierung** ($x_{i,p} \in \mathbb{B}$ mit `PbEq`/`AtMost`) bzw. eine **`QF_FD`-Endlich-Domänen-Formulierung**, sodass MaxRes ohne arithmetische Simplex-Fallunterscheidungen unmittelbar auf dem CDCL-SAT-Kern arbeitet und Symmetrien effizienter abgebaut werden; zweitens die Nutzung der nativen **lexikographischen Zielpriorisierung** in $\nu Z$ (`opt.set("priority", "lex")`) mit drei getrennten Zielfunktionen, welche strikte globale Prioritätshierarchie für beliebig viele Signale garantiert.
4. **Profil-Katalog, Schema-Erweiterung und empirische Multi-LLM-Studie:** Ergänzung datenblattgeprüfter Profile für den klassischen ESP32 (inklusive optionalem `input_only`-Attribut), ESP32-C6, RP2040 und STM32 sowie optionaler Peripherie-Instanzbudgets (z. B. Anzahl verfügbarer I2C-Controller und LEDC-Kanäle), begleitet von einer systematischen empirischen Studie, welche die Hardware-Korrektheitsrate mehrerer aktueller LLMs mit und ohne `mcu-pin-solver` quantifiziert.

---

## 9 Fazit

Mit `mcu-pin-solver` (Version `0.2.0`) hat diese Studienarbeit ein datengetriebenes Pre-Build-Verifikations- und Reparaturwerkzeug für Embedded-C++-Pin-Belegungen konzipiert, in zwei iterativen Ausbaustufen gehärtet, als Open-Source-Paket auf GitHub sowie in der PlatformIO Registry veröffentlicht und empirisch evaluiert. Die in Abschnitt 1.4 formulierten Forschungsfragen lassen sich abschließend wie folgt beantworten:

- **Zu FF1 (Extraktion ohne Ziel-Toolchain):** Mittels des fehlertoleranten GLR-Parsers `tree-sitter-cpp` werden Top-Level-Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Fähigkeiten, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) und aktive Peripheriemodule über verteilte `include/`- und `src/`-Verzeichnisse hinweg ohne installierten Cross-Compiler in wenigen Millisekunden extrahiert (unter 2 ms für drei Dateien, 7,53 ms für 21 Dateien). Durch die Nutzung der benannten Syntaxbaum-Sicht erzeugen Kommentare, Zeichenketten, lokale Funktionsvariablen und Nicht-Pin-Konstanten keine Fehlalarme; als konzeptionelle Grenzen verbleiben `#ifdef`-Verzweigungen, ESP-IDF-Typen wie `gpio_num_t` und nicht registrierte Drittbibliotheks-APIs.
- **Zu FF2 (Validierte Datentrennung und MaxSMT-Reparatur):** Durch die strikte Trennung in schema-validierte, deklarative JSON-Hardware-Profile (`mcu_validator/boards/*.json`) ist der Verifikationskern vollständig chip-agnostisch, wie der identische Quelltext mit unterschiedlichem Prüfergebnis auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`) unmittelbar belegt. Die zweistufige Pipeline kombiniert eine nahezu verzögerungsfreie Diagnose mit Dateizeilen-Verweis in Stufe 1 (`0,01–0,06 ms` bei `SAT` selbst für 20 Pins) mit einer Partial-Weighted-MaxSMT-Optimierung in Z3 $\nu Z$ (`1000` / `20` / `5`), die gültige Originalpins für alle unterstützten MCU-Größen ($n \le 39$) streng dominant bewahrt, geteilte Bus-Leitungen gekoppelt erhält, Strapping-Pins meidet, knappe ADC-/USB-Pins schont und Hardware-Überbuchungen eindeutig meldet.
- **Zu FF3 (Integration, Praxistauglichkeit und Wirtschaftlichkeit):** Über `pio_hook.py`, `library.json` (`"srcFilter": ["-<*>"]`) und gebündelte Paketdaten in `pyproject.toml` lässt sich `mcu-pin-solver` sowohl eigenständig per `pip install .` (`mcu-validate`) als auch nahtlos über die PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) einsetzen. Der reale End-to-End-Registry-Test bestätigte den Build-Abbruch in 1,21 s vor dem Compilerstart und die anschließende fehlerfreie Firmware-Erzeugung nach Übernahme der Z3-Vorschläge; alle 42 automatisierten Tests sowie `ruff` und `mypy` bestehen unter Windows und Linux. Bei 0 € Lizenz- und laufenden API-Kosten amortisiert sich der Einsatz in einem Embedded-Entwicklungsteam unter konservativen Annahmen bereits nach wenigen verhinderten Labor-Fehlersuchen.

Zusammenfassend zeigt `mcu-pin-solver` am produktiven System, dass die gezielte Arbeitsteilung zwischen generativem Sprachmodell, deterministischem Syntaxbaum-Parser, validierter Hardware-Datenschicht und formalem Z3-MaxSMT-Solver eine schnelle, transparente und wirtschaftlich überzeugende Schutzschicht für das moderne Embedded-Prototyping bildet.

---

## Literaturverzeichnis

- <a id="ref-1"></a>**[1] Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006):** *Compilers: Principles, Techniques, and Tools* (2. Aufl.). Addison-Wesley, Boston.
- <a id="ref-2"></a>**[2] Barrett, C., Sebastiani, R., Seshia, S. A., & Tinelli, C. (2021):** *Satisfiability Modulo Theories.* In: Biere, A., Heule, M., van Maaren, H., & Walsh, T. (Hrsg.): *Handbook of Satisfiability* (2. Aufl.), Frontiers in Artificial Intelligence and Applications, Bd. 336, S. 1267–1329, IOS Press.
- <a id="ref-3"></a>**[3] Bjørner, N., Phan, A.-D., & Fleckenstein, L. (2015):** *$\nu Z$ – An Optimizing SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2015)*, Lecture Notes in Computer Science, Bd. 9035, S. 194–199, Springer. DOI: `10.1007/978-3-662-46681-0_14`.
- <a id="ref-4"></a>**[4] Boehm, B. W. (1981):** *Software Engineering Economics.* Prentice-Hall, Englewood Cliffs, NJ.
- <a id="ref-5"></a>**[5] Boehm, B., & Basili, V. R. (2001):** *Software Defect Reduction Top 10 List.* IEEE Computer, Bd. 34, Nr. 1, S. 135–137. DOI: `10.1109/2.962984`.
- <a id="ref-6"></a>**[6] Brunsfeld, M. (2018):** *Tree-sitter – An incremental parsing system for programming tools.* Online-Dokumentation: `https://tree-sitter.github.io/tree-sitter/`.
- <a id="ref-7"></a>**[7] De Moura, L., & Bjørner, N. (2008):** *Z3: An Efficient SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2008)*, Lecture Notes in Computer Science, Bd. 4963, S. 337–340, Springer. DOI: `10.1007/978-3-540-78800-3_24`.
- <a id="ref-8"></a>**[8] Englhardt, Z., Li, R., Nissanka, D., Zhang, Z., Narayanswamy, G., Breda, J., Liu, X., Patel, S., & Iyer, V. (2024):** *Exploring and Characterizing Large Language Models for Embedded System Development and Debugging.* In: *Extended Abstracts of the CHI Conference on Human Factors in Computing Systems (CHI EA '24)*. DOI: `10.1145/3613905.3650764` (Preprint: `arXiv:2307.03817`).
- <a id="ref-9"></a>**[9] Espressif Systems (2024):** *ESP32-C3 Series Datasheet*, *ESP32-C3 Technical Reference Manual* & *ESP32-C3 Series SoC Errata.* Espressif Systems, Shanghai.
- <a id="ref-10"></a>**[10] Espressif Systems (2024):** *ESP32-S3 Series Datasheet* & *ESP32-S3 Technical Reference Manual.* Espressif Systems, Shanghai.
- <a id="ref-11"></a>**[11] Espressif Systems (2024):** *ESP-IDF Programming Guide – Analog to Digital Converter (ADC) Oneshot Mode Driver & Hardware Limitations (ESP32-C3 / ESP32-S3).* Online-Dokumentation: `https://docs.espressif.com/projects/esp-idf/`.
- <a id="ref-12"></a>**[12] Fakih, M., Dharmaji, R., Moghaddas, Y., Quiros Araya, G., Ogundare, O., & Al Faruque, M. A. (2024):** *LLM4PLC: Harnessing Large Language Models for Verifiable Programming of PLCs in Industrial Control Systems.* In: *IEEE/ACM 46th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP 2024)*, S. 192–203 (Preprint: `arXiv:2401.05443`).
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
