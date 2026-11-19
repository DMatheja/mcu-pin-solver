# Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT

## Deckblatt

**Duale Hochschule Baden-Württemberg (DHBW)**  
Studienakademie: `[Standort eintragen]`  
Studienbereich Technik – Studiengang: `[z. B. Informatik]`

**STUDIENARBEIT**  
Modul `[T4_3100 / T4_3200 / T4_3101 – zutreffendes Modul eintragen]` (5./6. Theoriephase)

**Thema:**  
**Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT**  
*Konzeption, Implementierung und Evaluation einer Pre-Build-Pin-Prüfung für PlatformIO (`mcu-pin-solver`)*

| Angabe | Eintrag |
| :--- | :--- |
| Verfasser | David Matheja |
| Matrikelnummer | 9809395 |
| Kurs | `[eintragen]` |
| Dualer Partner | `[eintragen]` |
| Bearbeitungszeitraum | `[TT.MM.JJJJ – TT.MM.JJJJ]` |
| Betreuer/in bzw. Gutachter/in | `[eintragen]` |
| Umfang | 5 ECTS-Leistungspunkte (Workload 150 Stunden) |
| Softwarestand | Version `0.2.0` (PlatformIO Registry: `dmatheja/mcu-pin-solver@^0.2.0`) |
| Quellcode | https://github.com/DMatheja/mcu-pin-solver |

---

## Kurzfassung

Große Sprachmodelle (*Large Language Models*, LLMs) erzeugen in wenigen Sekunden C++-Code für Mikrocontroller, der auf den ersten Blick lauffähig wirkt. Bei der Wahl der Anschluss-Pins (GPIOs) unterlaufen ihnen jedoch Fehler, die kein Compiler bemerkt: Sie nutzen etwa Pins, an denen intern der Programmspeicher hängt, messen Spannungen mit einem Analog-Digital-Wandler, der durch aktives WLAN gesperrt ist, verwechseln I2C- oder SPI-Leitungen oder belegen einen Pin doppelt. Der Compiler erkennt das nicht, weil Pin-Nummern im Arduino-Ökosystem gewöhnliche Ganzzahlen sind und er die Hardware des Zielchips nicht kennt.

Diese Arbeit konzipiert, implementiert und evaluiert `mcu-pin-solver` (Version `0.2.0`), eine Bibliothek und Kommandozeilenanwendung, die solche Hardware-Konflikte *vor* dem Kompilieren erkennt. Ein Parser auf Basis von Tree-Sitter (`tree-sitter-cpp`) liest den Quelltext als Syntaxbaum und extrahiert Pin-Konstanten, direkte Pin-Literale, benötigte Fähigkeiten, Bus-Leitungsrollen sowie aktive Peripherie (z. B. WLAN, USB-Serial). Die Prüfung erfolgt gegen schema-validierte, austauschbare JSON-Hardware-Profile, sodass neue Mikrocontroller ohne Änderung am Python-Code ergänzt werden können. Bei Konflikten berechnet der Solver Z3 über ein dreistufig gewichtetes Optimierungsproblem (MaxSMT) eine minimal-invasive Ersatzbelegung, die gültige Originalpins bewahrt, Strapping-Pins meidet und knappe Spezialpins (ADC/USB) schont. Das Ergebnis wird samt Dateizeilen-Verweis als Reparatur-Prompt für das Sprachmodell ausgegeben; ein Pre-Build-Hook bricht fehlerhafte PlatformIO-Builds vor dem Compilerstart ab.

Alle 42 automatisierten Tests (darunter neun End-to-End-Szenarien) bestehen unter Windows und Linux; ein CLI-Prüflauf dauert im Median rund 0,17 bis 0,21 s. Ein realer End-to-End-Test über die PlatformIO Registry bestätigt, dass fehlerhafte Builds in 1,21 s vor dem Kompilieren gestoppt und korrigierte Projekte fehlerfrei übersetzt werden. Zugleich dokumentiert die Evaluation verbleibende Grenzen – insbesondere bei `#ifdef`-Zweigen, ESP-IDF-Aufzählungstypen (`gpio_num_t`), Konstruktoren von Drittbibliotheken und dem Fehlen einer großskaligen empirischen Studie mit realem LLM-Code.

## Abstract

Large Language Models generate plausible embedded C++ code within seconds, yet they frequently assign microcontroller pins incorrectly—for example, selecting pins wired to internal flash memory, analog inputs blocked by an active Wi-Fi radio, overlapping bus lines, or duplicate pins. Compilers cannot detect these faults because pin numbers are plain integers and the compiler has no model of board-level hardware constraints.

This thesis designs, implements, and evaluates `mcu-pin-solver` (version `0.2.0`), a pre-build hardware pin validator for PlatformIO and standalone CLI workflows. A Tree-Sitter-based parser (`tree-sitter-cpp`) extracts pin constants, direct numeric pin calls, required capabilities, bus-line identities, and active peripherals from the C/C++ syntax tree and checks them against schema-validated JSON hardware profiles, enabling support for new microcontrollers without changing Python code. Whenever conflicts exist, Z3 solves a three-tier weighted MaxSMT optimization problem that preserves valid original pins, avoids strapping pins, and spares scarce ADC/USB pins. The tool emits a copy-paste LLM-Modulo repair prompt with `file:line` references and aborts faulty PlatformIO builds before compilation starts.

All 42 automated tests (including nine end-to-end scenarios) pass across Windows and Linux in CI, with a median CLI runtime of 0.17–0.21 s. A live PlatformIO Registry end-to-end test confirms that invalid builds are halted in 1.21 s prior to compilation and compile cleanly once repaired. Remaining limitations—such as `#ifdef` preprocessor branches, ESP-IDF `gpio_num_t` enums, third-party library constructors, and the lack of a large-scale benchmark on live LLM-generated firmware—are transparently evaluated.

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
  - [1.2 Problemstellung](#12-problemstellung)
  - [1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen](#13-fünf-fehlerklassen-und-ihre-elektronischen-ursachen)
  - [1.4 Zielsetzung und Forschungsfragen](#14-zielsetzung-und-forschungsfragen)
  - [1.5 Vorgehen und Aufbau der Arbeit](#15-vorgehen-und-aufbau-der-arbeit)
- [2 Grundlagen](#2-grundlagen)
  - [2.1 Große Sprachmodelle](#21-große-sprachmodelle)
  - [2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip](#22-neuro-symbolische-ki-und-das-llm-modulo-prinzip)
  - [2.3 Quelltextanalyse: vom Text zum Syntaxbaum](#23-quelltextanalyse-vom-text-zum-syntaxbaum)
  - [2.4 Tree-Sitter](#24-tree-sitter)
  - [2.5 SAT, SMT und der Solver Z3](#25-sat-smt-und-der-solver-z3)
  - [2.6 Optimierung mit MaxSMT](#26-optimierung-mit-maxsmt)
  - [2.7 PlatformIO und der Build-Prozess](#27-platformio-und-der-build-prozess)
- [3 Verwandte Arbeiten und Stand der Technik](#3-verwandte-arbeiten-und-stand-der-technik)
  - [3.1 Sprachmodelle in der Embedded- und Automatisierungsentwicklung](#31-sprachmodelle-in-der-embedded--und-automatisierungsentwicklung)
  - [3.2 Werkzeuge der Embedded-Praxis](#32-werkzeuge-der-embedded-praxis)
  - [3.3 Einordnung und Forschungslücke](#33-einordnung-und-forschungslücke)
- [4 Anforderungsanalyse](#4-anforderungsanalyse)
  - [4.1 Akteure und Anwendungsfälle](#41-akteure-und-anwendungsfälle)
  - [4.2 Funktionale Anforderungen](#42-funktionale-anforderungen)
  - [4.3 Nicht-funktionale Anforderungen](#43-nicht-funktionale-anforderungen)
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
  - [7.5 Laufzeitmessung und PlatformIO-End-to-End-Prüfung](#75-laufzeitmessung-und-platformio-end-to-end-prüfung)
  - [7.6 Soll-Ist-Abgleich](#76-soll-ist-abgleich)
  - [7.7 Gültigkeit der Ergebnisse](#77-gültigkeit-der-ergebnisse)
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
| I2C | *Inter-Integrated Circuit*, serieller Zweidrahtbus (SDA, SCL) |
| JSON | *JavaScript Object Notation*, textbasiertes Datenformat |
| LLM | *Large Language Model*, großes Sprachmodell |
| MaxSMT | *Maximum Satisfiability Modulo Theories*, Optimierungsvariante von SMT |
| MILP | *Mixed-Integer Linear Programming*, gemischt-ganzzahlige lineare Optimierung |
| MCU | *Microcontroller Unit*, Mikrocontroller |
| PSRAM | *Pseudo-Static RAM*, zusätzlicher Arbeitsspeicher |
| PWM | *Pulse-Width Modulation*, Pulsweitenmodulation |
| SAT | *Satisfiability*, Erfüllbarkeit; auch Ergebnis „erfüllbar“ |
| SMT | *Satisfiability Modulo Theories*, Erfüllbarkeit modulo Theorien |
| SPI | *Serial Peripheral Interface*, schneller serieller Bus |
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
- Tabelle 3.1: Einordnung verwandter Ansätze
- Tabelle 4.1: Funktionale Anforderungen
- Tabelle 4.2: Nicht-funktionale Anforderungen
- Tabelle 4.3: Architektur-Invarianten
- Tabelle 5.1: Nutzwertanalyse Quelltextanalyse
- Tabelle 5.2: Nutzwertanalyse Konfliktlösung
- Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0 (`v0.2.0`)
- Tabelle 6.1: Dateien des Repositories (`v0.2.0`)
- Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`)
- Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten und Bus-Rollen
- Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`)
- Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`)
- Tabelle 7.1: Messumgebung
- Tabelle 7.2: Ergebnisse der neun End-to-End-Regressionsszenarien
- Tabelle 7.3: Ergebnisse der Grenzfallexperimente (`v0.1.0` im Vergleich zu `v0.2.0`)
- Tabelle 7.4: Gemessene Laufzeiten (`v0.2.0`)
- Tabelle 7.5: Soll-Ist-Abgleich (`v0.2.0`)
- Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`

## Listingverzeichnis

- Listing 1.1: Kompilierbares, aber auf dem ESP32-C3 fehlerhaftes Programm
- Listing 5.1: Szenario 0 (`00_flash_and_wifi_conflict.cpp`)
- Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (`v0.2.0`)
- Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (`v0.2.0`)
- Listing 6.1: Auszug aus `mcu_validator/boards/esp32-c3.json`
- Listing 6.2: Laden und Schema-Validierung des Hardware-Profils (`board.py`, Auszug)
- Listing 6.3: Kollisionssichere Schlüsselvergabe (`_record_definition` und `_reserve_unique_key`)
- Listing 6.4: Extraktion von Pin-Deklarationen und Bus-Argumenten (`parser.py`, Auszug)
- Listing 6.5: Aufbau des MaxSMT-Modells im Solver (`solver.py`, Auszug)
- Listing 6.6: Kern des PlatformIO-Hooks (`pio_hook.py`) und der Paketkonfiguration (`library.json`)
- Listing 7.1: Szenario 02 und `v0.2.0`-Ausgabe
- Listing 7.2: Szenario 03 und `v0.2.0`-Ausgabe
- Listing 7.3: Szenario 04 und `v0.2.0`-Ausgabe
- Listing 7.4: Szenario 05 und `v0.2.0`-Ausgabe
- Listing 7.5: Szenario 06 (mehrere Dateien) und `v0.2.0`-Ausgabe
- Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, `v0.2.0`)

---

# Hauptteil

## 1 Einleitung

### 1.1 Ausgangssituation

Ein Programm auf einem gewöhnlichen PC muss nicht wissen, an welcher Leiterbahn welches Bauteil hängt – Betriebssystem und Treiber verbergen diese Details. Bei einem **Mikrocontroller** (*Microcontroller Unit*, MCU) wie dem ESP32-C3 oder ESP32-S3 von Espressif ist das anders. Ein Mikrocontroller ist ein vollständiger kleiner Computer auf einem einzigen Chip, und sein Programm steuert direkt elektrische Anschlüsse. Diese Anschlüsse heißen **GPIOs** (*General-Purpose Input/Output*). Jede GPIO-Nummer bezeichnet einen bestimmten Kontakt des Chips, der auf einem Entwicklungsboard wie dem `esp32-c3-devkitm-1` auf eine Stiftleiste geführt ist.

Äußerlich sehen alle Pins gleich aus. Intern sind sie aber mit unterschiedlichen Baugruppen verbunden:

- **Digitale Ein- und Ausgänge** (`gpio`) schalten zwischen 0 V und 3,3 V, etwa für LEDs, Relais oder Taster.
- **Analog-Digital-Wandler** (`adc`) messen Spannungen von Sensoren und liefern Zahlenwerte. Die ESP32-Chips besitzen zwei Wandler-Gruppen, `ADC1` und `ADC2`.
- **Pulsweitenmodulation** (`pwm`) schaltet einen Ausgang sehr schnell ein und aus, etwa zum Dimmen einer LED.
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
*Abbildung 1.1: Pin-Multiplexing als „Rangierbahnhof“ (ESP32-C3, vereinfacht; Pin-Angaben nach [[7]](#ref-7)).*

Mit großen Sprachmodellen (LLMs) lässt sich Firmware heute in natürlicher Sprache beschreiben, etwa: „Schreibe eine ESP32-C3-Firmware mit Status-LED, Bodenfeuchtesensor, Relais, WLAN und serieller Ausgabe über USB.“ Das Modell liefert in Sekunden strukturierten C++-Code. Untersuchungen zeigen, dass LLMs für typische Embedded-Aufgaben häufig funktionierenden Code erzeugen, aber nicht zuverlässig [[6]](#ref-6). Für die Pin-Belegung ist das besonders heikel: Ein falsch gewählter Pin fällt beim Kompilieren nicht auf, sondern erst auf der realen Hardware. Im ungünstigen Fall startet der Chip nicht mehr; ebenso möglich ist, dass ein Sensor stillschweigend unbrauchbare Werte liefert, nachdem die Schaltung bereits aufgebaut ist. Die Fehlersuche ist dann aufwendig, weil das Symptom keinen direkten Hinweis auf den verursachenden Pin gibt.

An dieser Stelle setzt die vorliegende Arbeit an. Ziel ist eine automatische Prüfinstanz, die fehlerhafte Pin-Belegungen *vor* dem Kompilieren erkennt, den Build in diesem Fall anhält und zugleich eine gültige, minimal-invasive Alternative vorschlägt. Wie weit dieser Anspruch tatsächlich eingelöst wird, untersuchen die Kapitel 7 und 8.

### 1.2 Problemstellung

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

Dass der Compiler diese Fehler nicht findet, hat drei Gründe:

1. **Pins sind nur Zahlen.** Funktionen wie `pinMode(uint8_t pin, uint8_t mode)` akzeptieren jede Zahl von 0 bis 255. Für den Compiler ist `pinMode(12, OUTPUT)` genauso gültig wie `pinMode(4, OUTPUT)`.
2. **Der Compiler kennt die Pin-Belegung des Chips nicht.** Er kennt den Befehlssatz des Prozessors, aber nicht, welche Pins intern belegt sind oder gar nicht existieren.
3. **Konflikte entstehen erst durch Kombination.** `analogRead(5)` ist für sich genommen zulässig. Unzulässig wird es erst, weil an anderer Stelle – vielleicht in einer anderen Datei – `WiFi.begin(...)` aufgerufen wird. Der Compiler übersetzt jede Datei einzeln und prüft solche Wechselwirkungen nicht.

Gesucht ist also ein Werkzeug, das Hardware-Wissen besitzt, das gesamte Projekt betrachtet und vor dem Kompilieren eingreift.

### 1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen

Die technischen Handbücher der ESP32-Chips [[7]](#ref-7), [[8]](#ref-8) unterscheiden zwei Arten der Pin-Verschaltung. Die **GPIO-Matrix** ist ein flexibles digitales Koppelfeld: Digitale Signale wie I2C, SPI, UART oder PWM lassen sich auf nahezu jeden freien Pin legen. Analoge Signale (ADC), der interne Speicher und USB sind dagegen über den **IO_MUX** bzw. direkte Leitungen **fest mit bestimmten Pins verbunden**. Diese Unterscheidung erklärt, warum manche Pins frei austauschbar sind und andere nicht.

Für diese Arbeit werden fünf Fehlerklassen unterschieden. Die Einteilung stammt vom Verfasser; sie deckt die Fehler ab, gegen die das Werkzeug prüft, erhebt aber keinen Anspruch auf Vollständigkeit.

1. **Reservierte und nicht vorhandene Pins.** Beim ESP32-C3 sind GPIO 11–17 mit der Flash-Versorgung (`VDD_SPI`) bzw. dem internen SPI-Flash verbunden [[7]](#ref-7), beim ESP32-S3 GPIO 26–37 mit Flash bzw. PSRAM [[8]](#ref-8). Wer diese Pins umkonfiguriert, stört das Laden von Programmbefehlen. Hinzu kommen Nummern, die es auf dem Chip gar nicht gibt – etwa GPIO 32, das von älteren ESP32-Boards bekannt ist, beim ESP32-C3 aber nicht existiert. Solche Nummern werden hier **Geister-Pins** genannt.
2. **Konflikte durch aktive Peripherie.** Bei aktivem WLAN können Anwendungen den Wandler `ADC2` nicht zuverlässig nutzen [[9]](#ref-9). Betroffen sind beim ESP32-C3 GPIO 5, beim ESP32-S3 GPIO 11–20. Entsprechend belegt die native USB-Schnittstelle die Pins GPIO 18/19 (C3) bzw. 19/20 (S3).
3. **Fehlende Fähigkeit.** Nicht jeder Pin kann alles. GPIO 6 des ESP32-C3 ist beispielsweise nicht mit dem Analog-Wandler verbunden; `analogRead(6)` liefert dort keine sinnvollen Werte.
4. **Doppelbelegung – und die erlaubte Ausnahme.** Zwei unabhängige Verbraucher auf demselben Pin stören sich gegenseitig. Bei Bussen wie I2C oder SPI ist das Teilen bestimmter Leitungen dagegen ausdrücklich vorgesehen: Mehrere I2C-Sensoren hängen gemeinsam an derselben `SDA`- und derselben `SCL`-Leitung. Umgekehrt dürfen `SDA` und `SCL` selbst, zwei getrennte Bus-Controller (`Wire` und `Wire1`) oder zwei SPI-Chip-Select-Leitungen (`CS`) *nicht* denselben Pin belegen. Ein Prüfwerkzeug muss beide Fälle sauber unterscheiden.
5. **Strapping-Pins.** Beim Einschalten liest der Chip einige Pins aus, um zu entscheiden, wie er startet (ESP32-C3: GPIO 2, 8, 9; ESP32-S3: GPIO 0, 3, 45, 46) [[7]](#ref-7), [[8]](#ref-8). Diese Pins dürfen danach benutzt werden, eine äußere Beschaltung kann aber den Start verhindern. Bei automatischen Korrekturen sollten sie daher eher gemieden werden. Anders als die Klassen 1 bis 4 ist Klasse 5 kein harter Fehler, sondern ein Risiko.

| Fehlerklasse | Beispiel (ESP32-C3) | Folge auf der Hardware |
| :--- | :--- | :--- |
| 1 Reservierte/fehlende Pins | `STATUS_LED = 12`, `PIR_SENSOR = 32` | Absturz bzw. wirkungsloser Code |
| 2 Aktive Peripherie | `SOIL_SENSOR = 5` (ADC2) und `WiFi.begin` | Analogmessung schlägt fehl |
| 3 Fehlende Fähigkeit | `analogRead(6)` | keine gültigen Messwerte |
| 4 Doppelbelegung | `BUZZER_PIN = 7` und `SERVO_PIN = 7`; `SDA = 6` und `SCL = 6` | Signale stören sich / Bus blockiert |
| 5 Strapping-Pins | externe Last an GPIO 2, 8 oder 9 | Chip startet ggf. nicht |

*Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung.*

### 1.4 Zielsetzung und Forschungsfragen

Ziel der Arbeit ist ein Werkzeug, das die fünf Fehlerklassen in PlatformIO-Projekten vor dem Kompilieren erkennt, verständlich mit Dateizeilen-Verweis meldet und eine korrigierte Pin-Belegung vorschlägt, die ein Sprachmodell direkt übernehmen kann. Das Hardware-Wissen soll dabei als validierte Datendatei so vom Programmcode getrennt sein, dass sich weitere Mikrocontroller allein durch eine JSON-Datei ergänzen lassen.

Daraus ergeben sich drei Forschungsfragen:

- **FF1 – Extraktion:** Wie lassen sich Pin-Definitionen, direkte Pin-Literale, benötigte Pin-Fähigkeiten, Bus-Leitungsrollen und aktive Peripherie über mehrere C++-Dateien hinweg zuverlässig aus dem Quelltext gewinnen, ohne die Compiler-Werkzeugkette des Zielchips vorauszusetzen?
- **FF2 – Prüfung und Reparatur:** Wie lässt sich chipspezifisches Wissen als validierbare Datenschicht vom Prüfcode trennen und so in ein Optimierungsproblem übersetzen, dass im Konfliktfall eine Ersatzbelegung entsteht, die möglichst wenig ändert, geteilte Bus-Leitungen erhält, Strapping-Pins meidet und knappe Spezialpins schont?
- **FF3 – Integration:** Wie lässt sich die Prüfung so als Python- und PlatformIO-Paket einbinden, dass fehlerhafte Builds gestoppt werden und eine für Sprachmodelle direkt verwertbare Korrekturanweisung entsteht?

**Zum Begriff „Verifikation“.** Im Titel ist von Verifikation die Rede. Gemeint ist eine formale Prüfung des *aus dem Quelltext extrahierten Pin-Modells* gegen ein *Modell der Hardware*. Es wird also nicht bewiesen, dass das gesamte Programm korrekt ist. Ob die Prüfung tatsächlich alle Fehler findet, hängt davon ab, wie vollständig der Parser den Quelltext erfasst und wie genau das Hardware-Profil den Chip beschreibt. Beide Einschränkungen werden in den Kapiteln 7 und 8 untersucht.

### 1.5 Vorgehen und Aufbau der Arbeit

Die Software entstand iterativ in zwei klar abgegrenzten Entwicklungsständen:

- **Version `0.1.0`** realisierte den ersten funktionsfähigen Prototyp mit Tree-Sitter-Parser, Z3-Solver, zwei Chip-Profilen (`esp32-c3`, `esp32-s3`), neun Regressionsszenarien und einem PlatformIO-Hook. Systematische Grenzfallexperimente deckten dabei konkrete Schwachstellen auf (u. a. bei direkten Zahlenliteralen, nicht pin-bezogenen Konstanten, fehlender Bus-Rollen-Trennung und fehlerhafter Ausgabe `GPIO None` bei Überbuchung).
- **Version `0.2.0`** überarbeitete die Architektur gezielt im Hinblick auf Verständlichkeit und Stabilität: Das Hardware-Profil erhielt ein eigenes, schema-validierendes Modul (`board.py`), alle Schnittstellen wurden auf typisierte Datenklassen umgestellt, die in `0.1.0` gefundenen Parser- und Solver-Lücken wurden behoben, die Paketierung für `pip` und PlatformIO vereinheitlicht und die Testsuite auf 42 modulare Tests samt plattformübergreifender CI (`ruff`, `mypy`, Windows/Linux) ausgebaut.

Die Arbeit dokumentiert den finalen Stand **`0.2.0`** und macht im Evaluationskapitel (Abschnitt 7.4) den Fortschritt gegenüber dem ersten Stand `0.1.0` transparent sichtbar. Die Software entstand mit Unterstützung von KI-Assistenten; Abschnitt 8.3 und das Verzeichnis der KI-Hilfsmittel legen dies offen.

Aufbau der Arbeit: Kapitel 2 erklärt die Grundlagen ohne Vorkenntnisse – Sprachmodelle, Syntaxbäume und den Solver Z3. Kapitel 3 ordnet die Arbeit in verwandte Ansätze ein. Kapitel 4 formuliert die Anforderungen, Kapitel 5 begründet die Entwurfsentscheidungen und führt ein durchgängiges Beispiel vor. Kapitel 6 beschreibt die Implementierung der vier Kernmodule. Kapitel 7 evaluiert das System mit 42 automatisierten Tests, Grenzfallexperimenten, Laufzeitmessungen und einem realen PlatformIO-Registry-Test. Kapitel 8 diskutiert Ergebnisse und verbleibende Grenzen, Kapitel 9 beantwortet die Forschungsfragen.

---

## 2 Grundlagen

Dieses Kapitel erklärt die drei Bausteine, auf denen das Werkzeug beruht: Sprachmodelle (2.1–2.2), die Analyse von Quelltext mit Syntaxbäumen (2.3–2.4) sowie die logische Prüfung und Optimierung mit Z3 (2.5–2.6). Abschnitt 2.7 beschreibt die Entwicklungsumgebung PlatformIO.

### 2.1 Große Sprachmodelle

Ein großes Sprachmodell ist ein neuronales Netz – heute meist ein *Transformer* [[20]](#ref-20) –, das mit sehr großen Textmengen trainiert wurde. Es erzeugt Text Stück für Stück: Aus allen bisherigen Textbausteinen (*Tokens*) $t_1, \dots, t_{k-1}$ schätzt es die Wahrscheinlichkeit für den nächsten Baustein,

$$P(t_k \mid t_1, \dots, t_{k-1}),$$

und wählt daraus einen Baustein aus. Man spricht von *Next-Token-Prediction*.

> **Kurz erklärt:** Ein Sprachmodell „rechnet“ nicht nach, ob ein Pin frei ist. Es schreibt das, was in ähnlichen Texten statistisch häufig folgt.

Daraus lassen sich für die Pin-Belegung drei Schwächen ableiten:

1. **Verzerrung durch Trainingsdaten.** Im Internet gibt es sehr viele Beispiele für den älteren ESP32, auf dem GPIO 12 oder GPIO 32 übliche Pins sind. Es ist plausibel, dass solche Muster auch dann vorgeschlagen werden, wenn ein ESP32-C3 gefordert ist. Diese Erklärung ist eine Hypothese; sie wurde in dieser Arbeit nicht empirisch überprüft.
2. **Keine globale Prüfung.** Das Modell schreibt von vorn nach hinten. Wenn es in Zeile 10 `WiFi.begin(...)` erzeugt, gibt es keinen eingebauten Mechanismus, der prüft, ob `SOIL_SENSOR = 5` aus Zeile 5 dadurch ungültig geworden ist.
3. **Unzuverlässige Selbstkorrektur.** Bittet man ein Modell, die eigene Antwort ohne externe Rückmeldung zu prüfen, verbessert sich das Ergebnis nicht zuverlässig; teilweise wird es sogar schlechter [[13]](#ref-13).

### 2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip

Garcez und Lamb beschreiben die Entwicklung der KI in drei Wellen [[11]](#ref-11): Die erste Welle war **symbolisch** – Regeln und Logik, die exakt und nachprüfbar sind, sich aber schwer auf unscharfe Aufgaben übertragen lassen. Die zweite Welle ist **neuronal** – lernende Netze wie Sprachmodelle, die flexibel sind, aber keine Korrektheitsgarantien geben. Die dritte Welle, die **neuro-symbolische KI**, verbindet beide Ansätze.

Kambhampati et al. übertragen diesen Gedanken mit dem **LLM-Modulo-Framework** auf Planungsaufgaben [[15]](#ref-15): Das Sprachmodell erzeugt Kandidatenlösungen, externe Prüfer (*Critics*) bewerten sie und geben Rückmeldung, bis ein Kandidat alle Prüfungen besteht. Harte Prüfer stehen für unverhandelbare Bedingungen, weiche Prüfer für Qualitätswünsche.

Bildlich ist das Sprachmodell der Architekt, der schnell Entwürfe zeichnet, und der Prüfer der Statiker, der nachrechnet. Findet der Statiker einen Fehler, schickt er dem Architekten eine präzise Korrektur, statt den ganzen Entwurf zu verwerfen. Abbildung 2.1 zeigt, wie `mcu-pin-solver` diesen Kreislauf umsetzt.

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
*Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver` (nach dem Prinzip aus [[15]](#ref-15)).*

Wichtig für die Einordnung: Das Werkzeug selbst enthält kein neuronales Netz. Es ist der symbolische Prüfer im Kreislauf; „neuro-symbolisch“ ist also das *Gesamtsystem* aus Sprachmodell und Prüfer. Der Schritt zurück zum Sprachmodell erfolgt in Version `0.2.0` manuell, indem der ausgegebene Prompt kopiert wird.

### 2.3 Quelltextanalyse: vom Text zum Syntaxbaum

Um Pins zu prüfen, muss das Werkzeug zuerst herausfinden, welche Pins im Quelltext stehen. Naheliegend wäre eine Textsuche mit **regulären Ausdrücken** (*Regex*), etwa nach dem Muster `#define NAME ZAHL`. Das stößt auf ein grundsätzliches Problem: Reguläre Ausdrücke beschreiben in der Chomsky-Hierarchie nur die einfachste Sprachklasse (Typ 3, reguläre Sprachen) [[12]](#ref-12). Sie können beliebig tief verschachtelte Klammern nicht korrekt erkennen und haben keinen Begriff davon, ob eine Fundstelle in einem Kommentar, einer Zeichenkette oder echtem Programmcode liegt. Die Syntax von C++ ist deutlich komplexer. Eine reine Textsuche fällt deshalb auf folgende Fälle herein:

1. Kommentare: `// WiFi.begin("Test");` würde fälschlich als WLAN-Start erkannt.
2. Zeichenketten: `Serial.println("Bitte nicht WiFi.begin() aufrufen");` ebenso.
3. Lokale Variablen: `for (int i = 0; ...)` oder `int retries = 12;` sehen ähnlich aus wie `const int SENSOR = 5;`.
4. Formatierung: Leerzeichen wie in `WiFi . begin()` sind in C++ erlaubt.

Ein **Parser** geht stattdessen wie das Frontend eines Compilers vor [[1]](#ref-1): Zuerst zerlegt die *lexikalische Analyse* den Text in Bausteine (*Tokens*) wie `const`, `int`, `LED`, `=`, `12`, `;`. Dann ordnet die *syntaktische Analyse* diese Bausteine nach den Regeln der Sprache zu einem Baum.

Man unterscheidet zwei Baumformen (Abbildung 2.2): Der **konkrete Syntaxbaum** (CST) enthält jedes Zeichen, auch `=` und `;`. Der **abstrakte Syntaxbaum** (AST) lässt reine Satzzeichen weg und zeigt nur die inhaltliche Struktur: Typ, Name, Wert.

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

> **Kurz erklärt:** Im Syntaxbaum ist ein Kommentar ein Knoten vom Typ „Kommentar“ und eine Zeichenkette ein Knoten vom Typ „Zeichenkette“. Wer nur nach Knoten vom Typ „Funktionsaufruf“ sucht, kann von Kommentaren nicht getäuscht werden.

### 2.4 Tree-Sitter

**Tree-Sitter** ist ein Parser-Generator mit fertigen Grammatiken für viele Sprachen, darunter C++ (`tree-sitter-cpp`) [[4]](#ref-4). Für diese Arbeit sind drei Eigenschaften entscheidend:

1. **Fehlertoleranz.** Tree-Sitter erzeugt auch dann einen Baum, wenn Code unvollständig ist oder Header wie `Arduino.h` fehlen. Fehlerhafte Stellen werden als Fehlerknoten markiert, der Rest bleibt nutzbar.
2. **Kein Compiler nötig.** Es reicht ein Python-Paket; die Werkzeugkette des Zielchips muss nicht installiert sein.
3. **Benannte Felder und Zeilenpositionen.** Tree-Sitter liefert technisch einen konkreten Baum, bietet aber benannte Felder wie `name`, `value` oder `function` sowie exakte Zeilennummern (`start_point.row`). Über diese Felder arbeitet man praktisch mit einer abstrakten Sicht.

Eine wichtige Einschränkung gehört ebenfalls dazu: Tree-Sitter führt **keinen Präprozessor** aus und löst **keine Typen** auf. Makros werden nicht expandiert, und alle Zweige einer `#ifdef`-Weiche erscheinen gleichzeitig im Baum. Die Folgen dieser Eigenschaft zeigen die Kapitel 7 und 8.

Abbildung 2.3 zeigt einen Ausschnitt des Baums, den `tree-sitter-cpp` in Version `0.23.4` für ein kurzes Beispiel erzeugt. Feldnamen stehen vor dem Doppelpunkt.

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

Drei Beobachtungen sind für die Implementierung wichtig:

1. Der auskommentierte Aufruf ist ein `comment`-Knoten und wird bei der Suche nach `call_expression` nicht gefunden.
2. `"MyWiFi"` ist ein `string_literal` innerhalb der Argumente, nie die aufgerufene Funktion.
3. Der Wert eines `#define` (`preproc_arg`) enthält den gesamten Rest der Zeile, **einschließlich des Kommentars** (`'12 // Board-LED'`). Der Parser muss diesen Kommentar daher lokal entfernen (Abschnitt 6.3).

### 2.5 SAT, SMT und der Solver Z3

Nachdem die Pins bekannt sind, müssen sie geprüft und gegebenenfalls neu verteilt werden. Dafür nutzt das Werkzeug den Solver **Z3** von Microsoft Research [[5]](#ref-5). Drei Begriffe bauen aufeinander auf [[2]](#ref-2).

**SAT (Erfüllbarkeit).** Ein SAT-Solver entscheidet, ob sich aussagenlogische Variablen so mit „wahr“ oder „falsch“ belegen lassen, dass eine Formel wahr wird. Beispiel: Anna ($A$) oder Ben ($B$) kommt zur Feier ($A \lor B$), aber nicht beide ($\neg(A \land B)$), und Ben sagt ab ($\neg B$). Dann muss Anna kommen – die Formel ist *erfüllbar* (SAT). Fordert man zusätzlich $\neg A$, gibt es keine Lösung mehr (UNSAT).

**SMT (Erfüllbarkeit modulo Theorien).** Pins sind Zahlen, keine Wahrheitswerte. SMT erweitert SAT deshalb um mathematische Theorien. In dieser Arbeit genügt die Theorie der ganzen Zahlen mit linearen Vergleichen ohne Quantoren (im Standard SMT-LIB als Logik `QF_LIA` bezeichnet). Jede Pin-Anforderung wird zu *einer* ganzzahligen Variable $v_i$. Bedingungen lassen sich dann direkt formulieren:

- „Die LED muss auf einem erlaubten Pin liegen“: $v_{\text{LED}} = 0 \lor v_{\text{LED}} = 1 \lor \dots$
- „LED und Relais dürfen nicht denselben Pin haben“: $v_{\text{LED}} \neq v_{\text{Relais}}$

Intern kombiniert Z3 einen SAT-Löser, der Kombinationen durchsucht und aus Sackgassen lernt (*Conflict-Driven Clause Learning*, CDCL), mit einem Löser für die Zahlenbedingungen. Dieses Zusammenspiel heißt DPLL($T$) [[2]](#ref-2). Für das Verständnis dieser Arbeit genügt: Z3 probiert nicht alle Kombinationen einzeln durch, sondern schließt aus jedem gefundenen Widerspruch ganze Bereiche aussichtsloser Belegungen auf einmal aus.

### 2.6 Optimierung mit MaxSMT

Ein gewöhnlicher SMT-Solver liefert *irgendeine* gültige Lösung. Er könnte also auch Pins verschieben, die bereits korrekt waren – für den Nutzer wäre das ärgerlich, weil dann auch die Verdrahtung auf der Platine geändert werden müsste. Gewünscht ist eine Lösung, die **möglichst wenig ändert** und bei notwendigen Verschiebungen hardwarefreundliche Pins bevorzugt.

Dafür bietet Z3 die Optimierungserweiterung $\nu Z$ (Python-Klasse `z3.Optimize`) [[3]](#ref-3). Sie unterscheidet zwei Arten von Bedingungen (Abbildung 2.4):

- **Harte Bedingungen** (`opt.add`) müssen gelten. Sie bilden die physikalischen Regeln ab.
- **Weiche Bedingungen** (`opt.add_soft`) sind Wünsche mit einem Gewicht. Z3 sucht unter allen gültigen Lösungen eine, bei der die Summe der Gewichte erfüllter Wünsche maximal ist (gleichbedeutend: die Summe der Gewichte verletzter Wünsche minimal).

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

Z3 löst solche Probleme standardmäßig mit dem Verfahren *MaxRes* [[16]](#ref-16). Es sucht wiederholt nach Gruppen von Wünschen, die sich gegenseitig ausschließen (sogenannte *unerfüllbare Kerne*), und gibt jeweils den „billigsten“ Wunsch auf. Gewichtetes MaxSMT ist im allgemeinen Fall NP-schwer; für die kleinen Probleme dieser Arbeit (unter 50 Pins, wenige Signale) ist das in der Praxis unproblematisch, wie die Messungen in Abschnitt 7.5 zeigen.

### 2.7 PlatformIO und der Build-Prozess

**PlatformIO** ist eine verbreitete Entwicklungsumgebung für Mikrocontroller [[17]](#ref-17). Ein Projekt wird über die Datei `platformio.ini` konfiguriert; dort stehen unter anderem das Board (z. B. `board = esp32-c3-devkitm-1`), externe Bibliotheken (`lib_deps`) und Zusatzskripte (`extra_scripts`). Ein Zusatzskript mit dem Präfix `pre:` läuft **vor** dem Kompilieren; dasselbe gilt für das in einer Bibliothek über `library.json` eingetragene `extraScript`. PlatformIO basiert auf dem Build-System SCons; ein solches Skript kann den Build mit `env.Exit(1)` abbrechen. Genau diesen Mechanismus nutzt `mcu-pin-solver`, um als „Schranke“ vor dem Compiler zu arbeiten.

> **Zwischenfazit Kapitel 2:** Tree-Sitter liefert die *Struktur* des Quelltextes ohne Compiler, Z3 liefert *Entscheidungen* über Pin-Belegungen mit mathematischer Garantie bezüglich des Modells, und PlatformIO bietet den *Zeitpunkt* (vor dem Kompilieren), an dem beides eingreifen kann.

---

## 3 Verwandte Arbeiten und Stand der Technik

### 3.1 Sprachmodelle in der Embedded- und Automatisierungsentwicklung

Englhardt et al. untersuchten, wie gut GPT-3.5, GPT-4 und PaLM 2 Software für eingebettete Systeme schreiben und Fehler darin finden [[6]](#ref-6). Dafür bauten sie einen Prüfstand, auf dem der erzeugte Code automatisch auf echter Hardware mit Sensoren und Aktoren getestet wurde (*Hardware-in-the-Loop*). Insbesondere GPT-4 erzeugte für viele Aufgaben funktionierenden Code und gab hilfreiche Hinweise zur Fehlersuche, allerdings nicht zuverlässig beim ersten Versuch. Die Autoren empfehlen daher einen Arbeitsablauf, in dem Mensch und Modell zusammenarbeiten. Die vorliegende Arbeit setzt an diesem Befund an, ersetzt den aufwendigen Hardware-Test für einen Teilaspekt – die Pin-Belegung – aber durch eine statische Prüfung vor dem Kompilieren.

Am nächsten verwandt ist **LLM4PLC** von Fakih et al. [[10]](#ref-10). Dort erzeugt ein Sprachmodell Programme für speicherprogrammierbare Steuerungen (SPS). Der Code wird in einer Schleife durch Syntaxprüfung, Compiler und einen formalen Modellprüfer geschickt; deren Fehlermeldungen gehen als Rückmeldung an das Modell zurück, bis alle Prüfungen bestanden sind. Das entspricht dem Grundprinzip des LLM-Modulo-Frameworks [[15]](#ref-15) und dieser Arbeit. Unterschiede bestehen im Anwendungsgebiet (SPS statt Mikrocontroller), im Prüfgegenstand (Programmverhalten statt Pin-Belegung) und darin, dass `mcu-pin-solver` nicht nur Fehler meldet, sondern selbst eine konkrete, optimierte Korrektur berechnet.

### 3.2 Werkzeuge der Embedded-Praxis

- **Statische Analysewerkzeuge für C++** wie `clang-tidy` oder `cppcheck` finden allgemeine Programmierfehler wie Speicherlecks oder Nullzeiger-Zugriffe. Wissen über die Pin-Eigenschaften eines bestimmten Chips besitzen sie nicht.
- **Grafische Konfiguratoren der Hersteller** wie STM32CubeMX [[19]](#ref-19) arbeiten in umgekehrter Richtung: Man wählt Pins in einer Oberfläche, Konflikte werden dort angezeigt, und daraus wird Initialisierungscode erzeugt. Ein Sprachmodell erzeugt aber direkt Code; eine nachträgliche Prüfung von vorhandenem Arduino-Code bieten diese Werkzeuge nicht.
- **Hardware-Beschreibungen im Betriebssystem**, etwa der *Devicetree* im Echtzeitbetriebssystem Zephyr [[21]](#ref-21), legen Pins in eigenen Beschreibungsdateien fest, die beim Build ausgewertet werden. Im Arduino- und PlatformIO-Umfeld, das beim Prototyping verbreitet ist, stehen Pins dagegen direkt im C++-Code.
- **Typsichere Hardware-Abstraktionen in Rust** (auf Basis von `embedded-hal` [[18]](#ref-18)) stellen Pins häufig als eigene Typen dar, die nach dem Ownership-Prinzip nur einmal an einen Treiber übergeben werden können. Eine doppelte Verwendung desselben Pins scheitert so bereits beim Kompilieren. Für den großen Bestand an Arduino-C++-Code steht das nicht zur Verfügung, und eine Ersatzbelegung wird nicht berechnet.

### 3.3 Einordnung und Forschungslücke

Tabelle 3.1 fasst die Einordnung zusammen. Es handelt sich um eine qualitative Einschätzung des Verfassers, nicht um einen systematischen Werkzeugvergleich.

| Ansatz | Prüft vorhandenen Arduino-C++-Code | Kennt Pin-Eigenschaften des Chips | Schlägt konkrete Korrektur vor | Teil eines LLM-Rückkopplungskreises |
| :--- | :---: | :---: | :---: | :---: |
| C++-Linter | ja | nein | nein | nein |
| Hersteller-Konfigurator | nein | ja | nein (zeigt Konflikte) | nein |
| Zephyr Devicetree | nein | ja | nein | nein |
| Rust-HAL | nein | teilweise | nein | nein |
| LLM4PLC [[10]](#ref-10) | nein (SPS-Code) | – | über das LLM | ja |
| `mcu-pin-solver` | ja (Teilmenge, vgl. 8.2) | ja (validiertes JSON-Profil) | ja (Z3 MaxSMT) | ja (Prompt manuell kopiert) |

*Tabelle 3.1: Einordnung verwandter Ansätze (Einschätzung des Verfassers).*

Daraus ergibt sich die Forschungslücke, die diese Arbeit adressiert: Es fehlt ein Werkzeug, das bestehenden Arduino-/PlatformIO-Code ohne Compiler-Werkzeugkette auf Pin-Konflikte prüft, das Hardware-Wissen austauschbar und validiert hält und eine optimierte Korrektur in einer Form zurückgibt, die ein Sprachmodell direkt verarbeiten kann.

---

## 4 Anforderungsanalyse

### 4.1 Akteure und Anwendungsfälle

Das System hat drei Nutzergruppen:

1. **Embedded-Entwicklerinnen und -Entwickler** bauen ein Projekt in PlatformIO oder rufen `mcu-validate` auf der Kommandozeile auf. Sie erwarten, dass Pin-Fehler vor dem Kompilieren mit Dateiname und Zeilennummer verständlich gemeldet werden.
2. **Das Sprachmodell** erzeugt den Code und erhält im Fehlerfall einen kompakten Prompt, nach dem es ausschließlich die betroffenen Pins ändern soll.
3. **Maintainer** ergänzen Unterstützung für weitere Mikrocontroller durch eine neue JSON-Datei (oder übergeben eine eigene `.json`-Datei per CLI) – ohne Python-Code anzufassen.

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

### 4.3 Nicht-funktionale Anforderungen

Die Qualitätsmerkmale orientieren sich am Produktqualitätsmodell der Norm ISO/IEC 25010 [[14]](#ref-14); die zugehörigen Merkmale der Norm sind in Klammern angegeben.

| ID | Merkmal (ISO/IEC 25010) | Abnahmekriterium |
| :--- | :--- | :--- |
| NFA-01 | Erweiterbarkeit (Wartbarkeit – Modifizierbarkeit) | Der Python-Code enthält keine chipspezifischen Pin-Nummern oder Chipnamen; ein neuer Chip erfordert nur eine JSON-Datei. |
| NFA-02 | Zeitverhalten (Leistungseffizienz) | Ein Prüflauf für ein typisches Projekt (bis ca. 20 Dateien und 20 Pins) dauert deutlich unter 1 s. |
| NFA-03 | Portabilität (Übertragbarkeit – Anpassbarkeit) | Lauffähig unter Windows und Linux ohne installierte Compiler-Werkzeugkette des Zielchips. |
| NFA-04 | Korrektheit der Vorschläge (Funktionale Eignung – Korrektheit) | Jeder ausgegebene Z3-Vorschlag besteht eine sofortige erneute Prüfung gegen alle harten Regeln des Hardware-Profils. |
| NFA-05 | Paket-Hygiene (Übertragbarkeit – Installierbarkeit) | Sowohl `pip install .` (inkl. gebündelter Board-JSONs) als auch die Einbindung über die PlatformIO Registry funktionieren eigenständig; Beispielcode wird nicht mitkompiliert; der CLI-Aufruf erzeugt keine Python-Warnungen. |
| NFA-06 | Testbarkeit & Codequalität (Wartbarkeit) | Eine modulare Testsuite deckt alle Kernmodule und Fehlerklassen ab und läuft in der CI zusammen mit statischer Typprüfung (`mypy`) und Linting (`ruff`). |
| NFA-07 | Lesbarkeit & Analysierbarkeit (Wartbarkeit) | Klare, top-down lesbare Gliederung in vier getrennte Kernmodule (`board.py`, `parser.py`, `solver.py`, `cli.py`) mit typisierten Datenklassen und minimalen Laufzeitabhängigkeiten (nur Z3 und Tree-Sitter). |

*Tabelle 4.2: Nicht-funktionale Anforderungen.*

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

Dieses Kapitel begründet die vier wichtigsten Entwurfsentscheidungen und verfolgt anschließend ein vollständiges Beispiel durch das System. Für die Auswahl der Verfahren werden Nutzwertanalysen eingesetzt. Dabei ist eine Einschränkung offen zu benennen: Gewichte und Punkte wurden vom Verfasser festgelegt, und zwar in Kenntnis der späteren Entscheidung. Nutzwertanalysen machen eine Entscheidung nachvollziehbar, beweisen sie aber nicht. Deshalb wird jeweils zusätzlich geprüft, wie stark sich die Gewichte ändern müssten, damit eine andere Option gewinnt (Sensitivitätsanalyse).

### 5.1 Entscheidung 1: Verfahren zur Quelltextanalyse

Zur Wahl standen drei Optionen:

- **A – Reguläre Ausdrücke** direkt auf dem Quelltext.
- **B – `libclang`**, die Programmierschnittstelle des Compilers Clang. Sie liefert einen vollständigen, semantisch aufgelösten Syntaxbaum inklusive Makroexpansion.
- **C – Tree-Sitter** (`tree-sitter-cpp`).

Bewertet wurde auf einer Skala von 1 (ungenügend) bis 5 (sehr gut):

| Kriterium | Gewicht | A Regex | B `libclang` | C Tree-Sitter |
| :--- | :---: | :---: | :---: | :---: |
| K1 Robust gegen Kommentare, Zeichenketten, Schleifen (FA-03) | 25 % | 1 | 5 | 5 |
| K2 Betrieb ohne Werkzeugkette und Header des Zielchips (NFA-03) | 25 % | 5 | 2 | 5 |
| K3 Toleranz gegenüber unvollständigem Code | 15 % | 4 | 2 | 4 |
| K4 Semantische Tiefe (Makros, `#ifdef`, Typen) | 20 % | 1 | 5 | 2 |
| K5 Installations- und Integrationsaufwand | 15 % | 5 | 3 | 5 |
| **Nutzwert** | 100 % | **3,05** | **3,50** | **4,25** |

*Tabelle 5.1: Nutzwertanalyse Quelltextanalyse.*

**Begründung.** Reguläre Ausdrücke scheitern an K1 (Abschnitt 2.3). `libclang` ist semantisch am stärksten: Es würde Makros wie `#define LED (BASE + 2)` ausrechnen und nur den aktiven `#ifdef`-Zweig betrachten. Dafür benötigt es aber die Header des Zielsystems (`Arduino.h`, ESP-IDF) und die passenden Compiler-Optionen; fehlen diese, entstehen Fehlermeldungen und unvollständige Bäume. Tree-Sitter kommt ohne all das aus.

**Sensitivität.** Der Abstand zwischen C und B entsteht vor allem durch K2, K3 und K5. Erhöht man das Gewicht von K4 und verkleinert die übrigen Gewichte anteilig, gewinnt `libclang` erst ab einem Gewicht von etwa 36 % für K4. Die Entscheidung ist also stabil, solange Portabilität wichtiger ist als semantische Tiefe. Der Preis dieser Entscheidung zeigt sich in Kapitel 8: Verbleibende Grenzen wie `#ifdef`-Weichen oder berechnete Makros wären erst mit einem vollständigen Präprozessor lösbar.

### 5.2 Entscheidung 2: Verfahren zur Konfliktlösung

Für die Berechnung einer Ersatzbelegung wurden vier Optionen verglichen:

- **1 – Eigene Heuristik** (z. B. Signale der Reihe nach auf den ersten freien passenden Pin legen).
- **2 – SMT ohne Optimierung** (`z3.Solver`).
- **3 – Gemischt-ganzzahlige lineare Optimierung** (MILP, z. B. mit PuLP).
- **4 – MaxSMT** (`z3.Optimize`).

| Kriterium | Gewicht | 1 Heuristik | 2 SMT | 3 MILP | 4 MaxSMT |
| :--- | :---: | :---: | :---: | :---: | :---: |
| K1 Garantiert optimale Lösung bzgl. der Zielfunktion (FA-08) | 30 % | 1 | 1 | 5 | 5 |
| K2 Natürliche Formulierung von „verschieden“ und „gekoppelt“ (FA-07) | 25 % | 2 | 5 | 2 | 5 |
| K3 Abhängigkeiten und Installation | 15 % | 5 | 4 | 4 | 4 |
| K4 Laufzeit bei bis zu ca. 30 Signalen | 15 % | 5 | 5 | 4 | 4 |
| K5 Nachvollziehbarkeit des Ergebnisses | 15 % | 4 | 2 | 3 | 3 |
| **Nutzwert** | 100 % | **2,90** | **3,20** | **3,65** | **4,40** |

*Tabelle 5.2: Nutzwertanalyse Konfliktlösung.*

**Begründung.** Eine Heuristik ist einfach, findet aber nicht immer die beste Lösung. Ein Gedankenexperiment zeigt das: Liegen bei aktivem WLAN eine LED und ein Analogsensor beide auf GPIO 1 und sind die übrigen ADC1-Pins 0, 3 und 4 schon belegt, dann würde eine Heuristik, die das zuerst deklarierte Signal (die LED) behält, den Sensor auf den einzigen freien ADC1-Pin 2 schieben – einen Strapping-Pin. Ist auch Pin 2 belegt, findet sie gar keine Lösung, obwohl eine existiert: Die LED könnte ausweichen. Ein Optimierer findet diese Lösung zuverlässig (vgl. Abschnitt 6.5, Fall 3).

SMT ohne Optimierung liefert irgendeine gültige Belegung und verschiebt dabei womöglich korrekte Pins. MILP ist für das Problem fachlich ebenso geeignet wie MaxSMT und liefert ebenfalls optimale Lösungen. Der Unterschied liegt in der Formulierung: In MILP müsste man für jede Kombination aus Signal und Pin eine 0/1-Variable anlegen und „verschieden“ über lineare Ungleichungen ausdrücken. In Z3 genügen eine ganzzahlige Variable je Signal und eine Bedingung $v_a \neq v_b$. MaxSMT wurde daher vor allem wegen der kompakten und auch für Einsteiger gut lesbaren Modellierung gewählt.

**Sensitivität.** Der Vorsprung von MaxSMT gegenüber MILP beruht allein auf K2. Wer die Modellierungsfreundlichkeit für unwichtig hält, erhält einen Gleichstand zwischen den beiden Verfahren.

### 5.3 Entscheidung 3: Zweistufiger Ablauf

Unabhängig vom Solver stellt sich die Frage, *wie* Fehler gemeldet werden. Würde man die ursprünglichen Pins als harte Bedingungen an Z3 übergeben, erhielte man im Fehlerfall nur die Antwort „unerfüllbar“ – ohne Begründung. Deshalb arbeitet das System in zwei Stufen:

1. **Stufe 1 – Deterministische Diagnose:** Ein einfacher Python-Durchlauf prüft jedes Signal einzeln gegen das Hardware-Profil und erzeugt für jeden Verstoß eine Klartextmeldung samt Dateizeilen-Verweis. Sind alle Signale gültig, endet die Prüfung hier mit `SAT`, und Z3 wird gar nicht gestartet.
2. **Stufe 2 – MaxSMT-Reparatur:** Nur wenn Stufe 1 Fehler gefunden hat, berechnet Z3 eine Ersatzbelegung.

So erhält der Nutzer alle Fehlerursachen auf einmal (vgl. Szenario 03 mit drei Fehlern), und fehlerfreie Builds bleiben praktisch ohne Zusatzlatenz.

### 5.4 Entscheidung 4: Hardware-Wissen als validierte Daten

Alle Eigenschaften eines Chips – welche Pins es gibt, was sie können, welche reserviert sind und welche Regeln gelten – stehen in einer JSON-Datei, nicht im Programmcode (INV-01). Dadurch entsteht eine klare Arbeitsteilung: Der Python-Code weiß, *wie* geprüft wird; die JSON-Datei weiß, *was* für einen Chip gilt. Ein neuer Mikrocontroller erfordert nur eine neue Datei (eine Prompt-Vorlage dafür enthält Anhang F).

Da solche JSON-Profile in der Praxis auch mit Unterstützung eines Sprachmodells erstellt werden können, validiert Version `0.2.0` jede geladene Datei strikt in `BoardSpec.from_dict()` (Abschnitt 6.2). Typische Schema-Fehler wie eine Zeichenkette `"gpio"` statt einer Liste `["gpio"]`, Zeichenketten `["18"]` statt Ganzzahlen `[18]` in `forbidden_pins` oder Tippfehler bei `when_resource_active` brechen so sofort mit einer präzisen Fehlermeldung ab, statt stillschweigend wirkungslos zu bleiben. Fachliche Fehler gegenüber dem Datenblatt (z. B. ein falsch eingetragener reservierter Pin) kann eine Schema-Prüfung allerdings weiterhin nicht erkennen.

### 5.5 Gesamtarchitektur

Abbildung 5.1 zeigt die modulare Vierschicht-Architektur von Version `0.2.0` vom Start des Builds bis zur Entscheidung.

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

**Schritt 1 – Profil laden und validieren (`board.py`).** Aus `mcu_validator/boards/esp32-c3.json` ergibt sich als typisiertes `BoardSpec`-Objekt unter anderem: GPIO 11–17 sind reserviert, GPIO 5 besitzt nur `adc2`, `ADC1` liegt auf GPIO 0–4, Strapping-Pins sind 2, 8 und 9, aktives `wifi` sperrt `adc2` und aktives `usb_serial` sperrt GPIO 18 und 19.

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

**Schritt 3 – Diagnose (Stufe 1 in `solver.py`).** `STATUS_LED` liegt auf dem reservierten Flash-Pin GPIO 12. `SOIL_SENSOR` fordert `adc` an, also `adc1` oder `adc2`; GPIO 5 bietet nur `adc2`, und genau diese Fähigkeit wird durch die aktive Regel `WIFI_BLOCKS_ADC2` gesperrt. Anders als noch in `v0.1.0` gibt die Fehlermeldung unmittelbar den hinterlegten `reason`-Text dieser Regel aus. `RELAY_PIN` (GPIO 4) ist gültig. Da zwei Fehler vorliegen, folgt Stufe 2.

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

Das Python-Paket `mcu_validator` umfasst insgesamt 1308 Zeilen (mit `pio_hook.py` 1400 Zeilen, einschließlich Docstrings, Typannotationen, Schema-Validierung und Leerzeilen). Gegenüber dem minimalen Prototyp `0.1.0` (379 Zeilen) wurde der Code bewusst in klare, selbstdokumentierende Datenklassen und Einzelaufgaben zerlegt, um Lesbarkeit für Einsteiger und Stabilität im Fehlerfall zu priorisieren. Sämtliche fünf Quellmodule bestehen `ruff` und `mypy` ohne Warnung oder Fehler.

### 6.2 Hardware-Profile und Schema-Validierung (`board.py`)

Gemäß INV-01 liegen sämtliche GPIO-Nummern, Fähigkeiten und Sperrregeln in JSON-Dateien im Paketordner `mcu_validator/boards/`. Die Verortung *innerhalb* des Python-Pakets (in Verbindung mit `package-data` in `pyproject.toml`) stellt sicher, dass die Profile auch nach einem regulären `pip install .` oder aus einem Python-Wheel heraus zuverlässig gefunden werden.

Jedes Profil besteht neben `mcu` und `description` aus fünf Abschnitten (Listing 6.1):

1. **`pins`:** Bildet physisch vorhandene Pin-Nummern (als Zeichenketten) auf `capabilities`, `strapping`, `reserved` und optional `note` ab. Nicht existierende Pins (wie GPIO 22–25 beim ESP32-S3) fehlen als Schlüssel; reservierte Pins (wie GPIO 11–17 beim ESP32-C3) tragen `"reserved": true` und eine leere Liste `"capabilities": []`.
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

Listing 6.2 zeigt die Auflösung und Validierung in `mcu_validator/board.py`. Gegenüber `v0.1.0` wurden drei Schwachstellen beseitigt: (1) `load_board` normalisiert sowohl die Board-Kennung als auch die Dateinamen (`_` $\rightarrow$ `-`) und sortiert absteigend nach Namenslänge, sodass `esp32-c3.json` immer vor einem allgemeineren `esp32.json` greift. (2) Übergibt der Nutzer direkt einen Pfad zu einer `.json`-Datei (z. B. `mcu-validate src ./mein_board.json`), wird diese unmittelbar geladen. (3) `BoardSpec.from_dict()` validiert jeden Schlüssel und Datentyp streng (einschließlich Zurückweisung von Zeichenketten statt Listen bei `capabilities`, Zeichenketten oder Booleans in `forbidden_pins` sowie unbekannten Ressourcen in `when_resource_active`).

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
*Listing 6.2: Laden des Hardware-Profils (`load_board`, `mcu_validator/board.py`, Auszug).*

Tabelle 6.2 stellt die beiden mitgelieferten Hardware-Profile gegenüber. Anders als in `v0.1.0` bilden beide Profile nun auch die Flexibilität der ESP32-GPIO-Matrix ab: Sämtliche nicht reservierten GPIOs unterstützen `i2c`, `spi`, `uart` und `pwm`, und beim ESP32-C3 ist zusätzlich GPIO 11 explizit als reservierte Flash-Spannungsversorgung (`VDD_SPI`) hinterlegt.

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

*Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3 (`v0.2.0`).*

### 6.3 AST-Parser (`parser.py`)

Der Parser in `mcu_validator/parser.py` arbeitet in vier klaren Schritten, die in der Einstiegsfunktion `parse_cpp()` direkt untereinander stehen: Dateiauflösung, AST-Durchlauf, Aufbau der `PinRequest`-Objekte und Erkennung aktiver Peripherie.

**1. Dateiauflösung (`_resolve_source_files`).** Übergibt der Nutzer eine einzelne Datei, wird diese geparst; bei einem Verzeichnis `src/` bindet `_project_search_dirs` automatisch einen vorhandenen Nachbarordner `include/` ein (über `path.resolve()`, sodass auch `.` innerhalb von `src/` funktioniert). Zusätzliche Header-Ordner lassen sich über `include_dirs` (bzw. CLI `--include-dir`) einbinden. Header (`.h`, `.hpp`) werden vor `.c`/`.cpp`/`.ino`-Dateien einsortiert; Build- und Testordner (`.git`, `.pio`, `build`, `test`, `tests`, `.venv`) werden über den *relativen* Pfad ausgeschlossen, sodass auch Testprojekte unterhalb von `tests/scenarios/` korrekt erfasst werden.

**2. Kollisionssichere Schlüsselvergabe (`_record_definition`).** Jeder gefundene Top-Level-Pin wird als typisiertes `_PinDefinition`-Objekt samt Dateipfad und 1-basierter Zeilennummer gespeichert (Listing 6.3). Gleiche Werte desselben Symbols werden dedupliziert; widersprechen sich zwei Definitionen (z. B. aus verschiedenen Dateien oder `#ifdef`-Zweigen), erzeugt `_reserve_unique_key` garantiert eindeutige Schlüssel (`NAME (datei.cpp)`, bei mehrfachen Konflikten `NAME (datei.cpp) #2` usw.). So wird INV-03 auch bei dreifachen `#ifdef`/`#elif`/`#else`-Verzweigungen oder bei Namensgleichheit mit synthetischen `GPIO_12`-Namen niemals verletzt.

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

**3. AST-Durchlauf und zielgerichtete Argumentauswertung (`_scan_files`, `_pin_args_for_call`).** Für jeden Prüflauf wird ein eigener `tree_sitter.Parser(CPP_LANGUAGE)` erzeugt (thread-sicher); `_text()` dekodiert Knoten mit `errors="replace"`, damit Kommentare mit Latin-1-/Windows-1252-Umlauten keinen `UnicodeDecodeError` auslösen. Konstanten werden nur auf oberster Ebene gesucht (`_walk(root, skip_functions=True)`), sodass lokale Variablen in `setup()` oder `loop()` (wie `int blinkCount = 0;`) niemals als Pins gewertet werden. `_parse_uint()` entfernt Zeilen-/Blockkommentare, einfache äußere Klammern (`#define LED (12)`) sowie ganzzahlige Suffixe (`12u`).

Bei Funktionsaufrufen wertet `_pin_args_for_call()` die exakten Argumentpositionen bekannter Arduino-/ESP32-APIs aus (Listing 6.4, Tabelle 6.3). Dadurch werden Nicht-Pin-Argumente wie Baudraten (`Serial.begin(115200)`), 1-Argument-I2C-Adressen (`Wire.begin(0x42)`) oder PWM-Tastgrade (`analogWrite(pin, 128)`) ausgeschlossen. Gleichzeitig ordnet der Parser jedem Bus-Argument eine eindeutige **`bus_group`** zu (z. B. `Wire:sda`, `Wire:scl`, `Wire1:sda`, `SPI:sck`, `SPI:miso`, `SPI:mosi`), während das vierte Argument von `SPI.begin` (Chip-Select `SS`/`CS`) gezielt als exklusives `gpio` ohne `bus_group` eingestuft wird.

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

**4. Fähigkeiten-Menge, Namens-Fallback und direkte Pin-Literale (`_build_pin_requests`).** Für jede Konstante werden *alle* im AST beobachteten Fähigkeiten als Menge (`frozenset[str]`) gesammelt – statt der fehleranfälligen `if/elif`-Kaskade aus `v0.1.0`. Konstanten, die weder in einem bekannten Pin-Aufruf erscheinen noch über `_infer_from_name()` als Pin erkannt werden (z. B. `BAUD_RATE`, `DELAY_MS`, `I2C_ADDR`, `LED_COUNT`), werden übersprungen. `_infer_from_name()` zerlegt Bezeichner in Wörter (sowohl `OLED_SDA_PIN` als auch `oledSdaPin`), ignoriert Nicht-Pin-Endungen (`NON_PIN_SUFFIXES`) und blickt vor einer nachgestellten Silbe `PIN`/`GPIO` auf das eigentliche Funktionswort (`SDA`, `SCL`, `MOSI`, `MISO`, `SCK`, `RX`, `TX`, `CS`).

Direkt eingesetzte Zahlenliterale (`pinMode(12, OUTPUT)`, `analogRead(5)`, `Wire.begin(6, 6)`) werden in `_merge_or_append_literal_uses()` erfasst: Existiert für denselben Pin und dieselbe `bus_group` bereits eine benannte Konstante (etwa `const int STATUS_LED = 6; analogRead(6);`), werden zusätzliche Fähigkeiten auf diesen Pin gemergt, damit fehlende Fähigkeiten nicht verloren gehen. Andernfalls erzeugt der Parser einen eindeutig benannten Eintrag (`GPIO_12`, bei Bus-Konflikten `GPIO_6 (Wire:scl)`).

Gemäß INV-02 arbeitet kein regulärer Ausdruck auf dem ungeparsten C++-Rohtext; alle fünf `re`-Muster in `parser.py` verarbeiten ausschließlich kleine, zuvor aus dem AST isolierte Teilzeichenketten (Tabelle 6.4).

| Muster in `parser.py` | Isolierte AST-Eingabe | Zweck |
| :--- | :--- | :--- |
| `WIRE_CALL_RE`: `^(Wire\d*)\.(?:begin\|setPins)$` | Funktionsname `fn_name` | erkennt `Wire`, `Wire1`, … und extrahiert den Busnamen |
| `SPI_CALL_RE`: `^(SPI\d*)\.begin$` | Funktionsname `fn_name` | erkennt `SPI`, `SPI1`, … und extrahiert den Busnamen |
| `SERIAL_CALL_RE`: `^Serial\d*\.begin$` | Funktionsname `fn_name` | erkennt Hardware-UART-Aufrufe mit `rxPin`/`txPin` |
| `COMMENT_RE`: `//.*\|/\*.*?\*/` | `preproc_arg` eines `#define` | entfernt Zeilen- und Blockkommentare hinter Zahlenwerten |
| `WORD_RE`: `[A-Z]+(?=[A-Z][a-z]\|_|\d\|$)\|[A-Z]?[a-z]+\|\d+` | Bezeichner `name` | zerlegt `SNAKE_CASE` und `camelCase` für `_infer_from_name()` |

*Tabelle 6.4: Lokale reguläre Ausdrücke im Parser (`mcu_validator/parser.py`).*

### 6.4 Regelprüfer und MaxSMT-Solver (`solver.py`)

Die Funktion `validate(project, board)` in `mcu_validator/solver.py` prüft die extrahierten Anforderungen nach einer Vorabprüfung auf eindeutige Namen in zwei Stufen (Abbildung 6.1).

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

In Stufe 1 prüft `_check_capabilities` jede geforderte Fähigkeit $c \in C_i$ einzeln über Mengenoperationen: `matching = board.expand_capability(c) & pin_caps`. Ist `matching` leer, fehlt die Fähigkeit; gilt `matching <= forbidden_caps.keys()`, sind alle passenden Wandlerbanken aktuell gesperrt, und es wird die konkrete `reason`-Begründung der sperrenden Regel ausgegeben.

Findet Stufe 1 mindestens einen Konflikt, baut `_solve_reassignment()` das MaxSMT-Modell auf (Listing 6.5). Jede Anforderung $r_i$ erhält eine über ihren Index erzeugte Z3-Variable `Int(f"pin_{idx}")`. Ist die Kandidatenmenge $P_i$ für ein Signal leer, bricht der Solver sofort mit `None` (`repair_possible=False`) ab – der Notbehelf `var == -1` aus `v0.1.0` entfällt damit vollständig.

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

Mathematisch lässt sich das Modell von `v0.2.0` kompakt in drei Teilen formulieren. Für jede Anforderung $r_i$ ($i \in \{1, \dots, n\}$) mit Fähigkeitsmenge $C_i$ und Bus-Gruppe $b_i$ lautet die zulässige Kandidatenmenge:

$$P_i = \Big\{\, p \in \mathcal{P} \;\Big|\; \neg\text{reserved}(p) \;\land\; p \notin \text{ForbiddenPins} \;\land\; \forall c \in C_i:\; \big(\text{caps}(p) \cap (A(c) \setminus \text{ForbiddenCaps})\big) \neq \emptyset \,\Big\}$$

1. **Domänenbindung (hart):** Existiert ein $i$ mit $P_i = \emptyset$, ist keine Reparatur möglich (`repair_possible=False`). Andernfalls gilt $\bigvee_{p \in P_i} (v_i = p)$.
2. **Paarweise Bus-Leitungskopplung (hart, INV-04):** Zwei Signale dürfen genau dann einen Pin teilen (`_can_share_bus`), wenn sie dieselbe einzelne, teilbare Bus-Fähigkeit *und* dieselbe Bus-Leitungsrolle tragen:
   $$\text{share}(r_i, r_j) \iff C_i = C_j \land |C_i| = 1 \land C_i \subseteq \text{shared\_capabilities} \land b_i = b_j$$
   Für alle Paare $1 \le i < j \le n$ gilt damit:
   $$v_i = v_j \quad \text{falls } \text{share}(r_i, r_j) \land p_i^0 = p_j^0, \qquad \text{sonst } v_i \neq v_j.$$
3. **Dreistufige Zielfunktion (weich, INV-05):** Sei $S_i = P_i \cap S$ die Menge der Strapping-Pins in $P_i$ und $K_i \subseteq P_i$ die Menge der Pins mit knappen, von $r_i$ nicht benötigten Spezialfähigkeiten (`adc`/`usb`). Z3 maximiert:
   $$\max \sum_{i=1}^{n} \Big( 1000 \cdot \mathbb{I}[p_i^0 \in P_i \land v_i = p_i^0] \;+\; 20 \cdot \mathbb{I}[\emptyset \subset S_i \subset P_i \land v_i \notin S_i] \;+\; 5 \cdot \mathbb{I}[\emptyset \subset K_i \subset P_i \land v_i \notin K_i] \Big)$$

Durch die Formulierung als jeweils *eine* gebündelte Klausel (`And([var != p for ...])`) pro Signal und Zielstufe ist die Punkteberechnung unmittelbar nachvollziehbar: Ein gültiger Originalpin bringt 1000 Punkte, Strapping-Freiheit genau 20 Punkte und die Schonung knapper Spezialpins genau 5 Punkte. Selbst ein gültiges Signal auf einem Strapping- und ADC-Pin behält seinen Pin mit deutlichem Vorsprung ($1000 > 20 + 5 = 25$).

### 6.5 Wer darf bleiben? Prioritäten bei gegenseitiger Pin-Blockade

Wenn zwei Signale im Quelltext denselben Pin beanspruchen, entscheidet keine fest einprogrammierte Namensliste, sondern ausschließlich die Zielfunktion (3). Daraus ergeben sich drei typische Fälle:

1. **Fall 1 – Gleichwertige Einzelsignale (Gleichstand).** Liegen `BUZZER_PIN = 7` und `SERVO_PIN = 7` (beide `gpio`) auf demselben Pin, erzielen beide Varianten („Buzzer bleibt, Servo weicht auf freien Nicht-Strapping-/Nicht-ADC-Pin aus“ oder umgekehrt) exakt dieselbe Punktzahl ($1000 + 40 + 10 = 1050$). Die Experimente `c` und `c2` (Abschnitt 7.4) zeigen, dass weiterhin nicht die Deklarationsreihenfolge im C++-Code, sondern die interne Suchheuristik von Z3 den Gleichstand auflöst (in beiden Reihenfolgen behielt `SERVO_PIN` GPIO 7, während `BUZZER_PIN` auf GPIO 20 bzw. GPIO 6 auswich). Für identische Eingaben und eine feste Z3-Version bleibt das Ergebnis reproduzierbar.
2. **Fall 2 – Geteilter Bus gegen einzelnes Störsignal („Bus-Trägheit“).** In Szenario 04 sind `OLED_SDA = 6` und `BME280_SDA = 6` über `bus_group = "Wire:sda"` gekoppelt ($v_{\text{OLED\_SDA}} = v_{\text{BME280\_SDA}}$), ebenso `OLED_SCL` und `BME280_SCL` auf GPIO 7 (`Wire:scl`). Das gekoppelte SDA-Paar bringt zusammen `2000` Haltepunkte ein, die einzelne `STATUS_LED = 6` nur `1000`. Tabelle 6.5 zeigt die Punktewertung auf Basis des `v0.2.0`-Modells: Der Bus bleibt geschlossen auf GPIO 6/7, und die LED weicht auf einen freien, strapping- und ADC-freien Pin aus (GPIO 20).

| Variante in Szenario 04 (`v0.2.0`) | Haltepunkte | Strapping-Meidung | Knappe Pins geschont | Summe | Ergebnis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **A (Z3-Lösung):** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 20 | $4 \times 1000 = 4000$ | $5 \times 20 = 100$ | $5 \times 5 = 25$ | **4125** | **optimal** |
| **B:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 1 (ADC1) | $4000$ | $100$ | $4 \times 5 + 0 = 20$ | 4120 | verworfen |
| **C:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 2 (Strapping + ADC1) | $4000$ | $4 \times 20 = 80$ | $20$ | 4100 | verworfen |
| **D:** `STATUS_LED` bleibt auf 6, SDA-Paar $\rightarrow$ 20 | $3 \times 1000 = 3000$ | $100$ | $25$ | 3125 | verworfen |

*Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal, `v0.2.0`).*

3. **Fall 3 – Spezialist gegen Allrounder (indirekte Priorität durch knappe Pins).** Kollidieren bei aktivem WLAN ein Analogsensor (`SOIL_SENSOR = 1`, braucht `adc1`) und eine LED (`STATUS_LED = 1`, `gpio`) bei bereits belegten ADC1-Pins 0, 3 und 4, bleibt dem Sensor als einziger Ausweichpin der Strapping-Pin 2. Weicht die LED stattdessen auf GPIO 7 aus und bleibt der Sensor auf GPIO 1, spart diese Lösung sowohl den Strapping-Abzug (`+20`) als auch den knappen ADC1-Pin für die LED (`+5`) – ein Vorsprung von **25 Punkten** gegenüber dem umgekehrten Tausch. Die Experimente `f` und `f2` bestätigen dies unabhängig von der Deklarationsreihenfolge.

### 6.6 Bericht, CLI und Reparatur-Prompt (`cli.py`)

Das Modul `mcu_validator/cli.py` nutzt `argparse` und stellt das Kommandozeilenwerkzeug `mcu-validate` (sowie `python -m mcu_validator.cli`) mit klaren Rückgabewerten bereit: `0` bei `SAT`, `1` bei `UNSAT` und `2` bei Eingabe- oder Konfigurationsfehlern (`FileNotFoundError`, `ValueError` bei ungültiger Board-JSON, `OSError`) – ohne unleserliche Python-Stacktraces.

Über optionale Flags lassen sich verfügbare Profile auflisten (`--list-boards`), eigene Board-Ordner angeben (`--boards-dir`), zusätzliche Header-Verzeichnisse einbinden (`--include-dir`, wiederholbar) und die Version anzeigen (`--version`). Der Ausgabekopf zeigt neben Zielpfad und aktiven Modulen stets `Checked Pins : N (...)`. Werden `0` Pins erkannt, gibt das Werkzeug trotz `SAT` eine explizite Warnung aus, damit eine fehlende syntaktische Abdeckung nicht unbemerkt bleibt. Im `UNSAT`-Fall folgen alle Einzelkonflikte mit `datei:zeile`-Angabe sowie entweder die vollständige `Keep`/`Change`-Liste oder – bei `repair_possible=False` – ein klarer Kapazitätshinweis (kein `GPIO None`).

Gemäß INV-06 exportiert `mcu_validator/__init__.py` nur die Bibliotheks-API (`load_board`, `list_boards`, `parse_cpp`, `validate`, Datenklassen und `__version__`), nicht jedoch `.cli`. Ein strenger Testlauf mit `python -W error -m mcu_validator.cli` bestätigt vollständige Warnungsfreiheit.

### 6.7 Integration in PlatformIO und Paketierung (`pio_hook.py`, `library.json`, `pyproject.toml`)

`mcu-pin-solver` wird sowohl als Python-Paket (`pip install .`) als auch über die PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) bereitgestellt. Listing 6.6 zeigt die Kernlogik von `pio_hook.py` sowie das aktualisierte Manifest `library.json`.

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

Gegenüber Version `0.1.0` wurden fünf Details gezielt gehärtet:

1. **Explizites `--include-dir`:** Der Hook übergibt `$PROJECT_INCLUDE_DIR` direkt aus PlatformIO, sodass auch benutzerdefinierte Ordnernamen funktionieren.
2. **Versionsgrenzen & PEP-668-Fehlerhilfe:** Die Erstinstallation fordert kompatible Mindestversionen an und fängt Fehler (z. B. Offline-Betrieb oder geschützte System-Pythons nach PEP 668 unter Linux/macOS) mit einer klaren manuellen Installationsanweisung ab.
3. **Unterscheidung der Exit-Codes:** Konflikte im C++-Code (Exit-Code `1`) und Konfigurations-/Board-Fehler (Exit-Code `2`) erzeugen klar getrennte Meldungen.
4. **Doppelausführung & Pfadermittlung:** `_MCU_VALIDATOR_RAN` verhindert doppelte Prüfläufe in SCons; `_resolve_hook_dir()` prüft zuerst `__file__` und fällt erst danach auf `inspect.currentframe()` zurück.
5. **Paket-Hygiene (`pip` und PlatformIO):** `pyproject.toml` bündelt `boards/*.json` per `package-data`, während `library.json` mit `"srcFilter": ["-<*>"]` verhindert, dass der Demo-Sketch `src/main.cpp` in fremden Projekten mitkompiliert wird.

> **Zwischenfazit Kapitel 6:** Version `0.2.0` teilt die Prüf-Pipeline in vier top-down lesbare, typisierte Module mit Schema-Validierung, präziser Bus-Leitungsmodellierung und gehärteter PlatformIO-/Python-Paketierung.

---

## 7 Evaluation

Dieses Kapitel überprüft Version `0.2.0` empirisch auf vier Säulen: (1) die modulare automatisierte Testsuite (42 Tests inkl. CI-Matrix), (2) gezielte Grenzfallexperimente im direkten Vergleich zwischen `v0.1.0` und `v0.2.0`, (3) getrennte Laufzeitmessungen sowie (4) einen realen End-to-End-Test über die veröffentlichte PlatformIO Registry.

### 7.1 Evaluationsdesign und Messumgebung

Die Testsuite ist nach Modulen gegliedert (`tests/test_board.py`, `test_parser.py`, `test_solver.py`, `test_cli.py`, `test_scenarios.py`) und wird lokal wie in der CI über `python -m unittest discover -s tests -v` (oder `python tests/run_tests.py`) ausgeführt. Alle End-to-End-Szenarien mit Ergebnis `UNSAT` prüfen zusätzlich die **Korrektheit der Z3-Vorschläge (NFA-04)**, indem die vorgeschlagenen Pins auf das `ParsedProject` angewendet und erneut an `validate()` übergeben werden.

Alle Grenzfallexperimente und Laufzeitmessungen wurden auf der in Tabelle 7.1 dokumentierten Umgebung gegen den finalen Stand `v0.2.0` erhoben (Mediane über $N = 10$ Subprozess-Läufe bzw. $M = 30$ In-Process-Läufe).

| Komponente | Spezifikation |
| :--- | :--- |
| Prozessor / Betriebssystem (lokal) | AMD Ryzen 9 3900X 12-Core Processor, Microsoft Windows 10 Pro |
| Python-Version (lokal) | Python `3.14.7` |
| Solver und Parser | `z3-solver` `5.4.1.0`, `tree-sitter` `0.26.1`, `tree-sitter-cpp` `0.23.4` |
| PlatformIO Core (lokal) | PlatformIO Core `6.2.0` (Espressif32 `6.12.0`, Arduino-Framework) |
| CI-Umgebung (GitHub Actions) | `ubuntu-latest` & `windows-latest`, Python `3.10` & `3.12`, plus `ruff` & `mypy` |

*Tabelle 7.1: Messumgebung (`v0.2.0`).*

### 7.2 Automatisierte Testsuite und Regressionsszenarien

Die Ausführung von `python -m unittest discover -s tests -v` bestand alle **42 automatisierten Tests** lokal in ca. 3,4 s sowie in allen fünf Jobs der GitHub-Actions-CI (`lint`, `ubuntu-latest` 3.10/3.12, `windows-latest` 3.10/3.12) ohne Fehler:

- **`test_board.py` (12 Tests):** Konsistenzprüfung aller mitgelieferten Board-JSONs, Präfix-Sortierung, Unterstrich-Normalisierung, direktes Laden von `.json`-Dateien sowie sieben Negativtests für die Schema-Validierung.
- **`test_parser.py` (11 Tests):** Ausblenden von Nicht-Pin-Konstanten und lokalen Variablen, geklammerte Makros `(12)` und `12u`, Latin-1-Kommentare, direkte Pin-Literale inkl. Fähigkeits-Merge auf benannte Pins, 3-Wege-`#ifdef`-Schlüssel, `GPIO_12`-Kollisionsschutz, Namens-Fallback (`OLED_SDA_PIN`, `oledSdaPin`, `SPI_MOSI_PIN`), `Serial1`, dateiübergreifende Neudefinitionen und `--include-dir`.
- **`test_solver.py` (8 Tests):** Ablehnung von `SDA == SCL` (benannt und literal), `Wire` vs. `Wire1`, SPI-`CS`- und `SCK == MOSI`-Konflikten, Bevorzugung gewöhnlicher GPIOs gegenüber knappen ADC-Pins, Überbuchungsfall (`repair_possible=False`), leeres Projekt und Schutz gegen doppelte Signalnamen.
- **`test_cli.py` (7 Tests):** Flags `--list-boards`, `--version`, `--boards-dir`, Warnungsfreiheit unter `python -W error`, Exit-Code `2` ohne Stacktrace bei unbekanntem Board oder defekter JSON sowie 0-Pin-Warnung.
- **`test_scenarios.py` (4 Testmethoden über 9 End-to-End-Konstellationen):** Alle neun Regressionsszenarien (Tabelle 7.2) inklusive automatischer Nachprüfung der Z3-Vorschläge.

| Nr. | Zielpfad | Board | Erwartet & Gemessen | Geprüfter Sachverhalt |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `src/main.cpp` | `esp32-c3` | SAT | Demo-Sketch mit `STATUS_LED = 8` (Strapping), `SOIL_SENSOR = 1`, `RELAY_PIN = 4`, `WiFi.softAP`, `Serial.begin` |
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

Szenario 0 wurde bereits in Abschnitt 5.6 vorgestellt. Die Listings 7.1 bis 7.5 zeigen die tatsächlichen CLI-Ausgaben von Version `0.2.0` für die Szenarien 02 bis 06.

In **Szenario 02** (Listing 7.1) sperrt `Serial.begin(115200)` über `usb_serial` die Pins 18 und 19. `ENABLE_PIN` (GPIO 6) bleibt unverändert; dank der Schonung knapper ADC-Pins landen `STEP_PIN` und `DIR_PIN` auf den freien Standard-GPIOs 21 und 10 (statt wie in `v0.1.0` auf ADC1-Pin 1).

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
*Listing 7.1: CLI-Ausgabe für Szenario 02 (`tests/scenarios/02_usb_serial_conflict.cpp`, Rückgabewert 1).*

In **Szenario 03** (Listing 7.2) meldet Stufe 1 alle drei Fehler samt Dateizeile: Kollision auf GPIO 7, nicht existierender GPIO 32 und fehlendes `adc` auf GPIO 6. `POTI_PIN` wechselt auf `ADC1` (GPIO 0), `PIR_SENSOR` auf den Standard-GPIO 10 und `BUZZER_PIN` auf GPIO 6 (nachdem `POTI_PIN` diesen geräumt hat).

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
*Listing 7.2: CLI-Ausgabe für Szenario 03 (`tests/scenarios/03_duplicate_and_invalid_pin.cpp`, Rückgabewert 1).*

**Szenario 04** (Listing 7.3) bestätigt die Bus-Trägheit aus Abschnitt 6.5: Alle vier gekoppelten I2C-Signale (`Wire:sda` auf GPIO 6, `Wire:scl` auf GPIO 7) bleiben unberührt; allein die störende `STATUS_LED` wechselt auf GPIO 20.

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
*Listing 7.3: CLI-Ausgabe für Szenario 04 (`tests/scenarios/04_shared_i2c_bus.cpp`, Rückgabewert 1).*

**Szenario 05** (Listing 7.4) bestätigt den Schutz vor Fehlalarmen: `WiFi.begin` steht nur in Kommentar und Zeichenkette, weshalb `Active Modules : none` erkannt und `SOIL_SENSOR` (GPIO 5, `ADC2`) als gültig bewertet wird.

```text
=================================================================
 Target         : tests/scenarios/05_ast_ignores_strings_and_comments.cpp (ESP32-C3)
 Active Modules : none
 Checked Pins   : 1 (SOIL_SENSOR=5)
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 7.4: CLI-Ausgabe für Szenario 05 (`tests/scenarios/05_ast_ignores_strings_and_comments.cpp`, Rückgabewert 0).*

**Szenario 06** (Listing 7.5) führt `include/pins.h`, `src/main.cpp` und `src/sensors.cpp` zusammen. Die Diagnose verweist direkt auf `pins.h:4` und `pins.h:5`; anders als in `v0.1.0` weicht `STATUS_LED` nun auf den freien Standard-GPIO 10 aus (statt auf den USB-Pin GPIO 18).

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
*Listing 7.5: CLI-Ausgabe für Szenario 06 (`tests/scenarios/06_multi_file_project/src`, Rückgabewert 1).*

### 7.4 Grenzfallexperimente und Entwicklung von v0.1.0 zu v0.2.0

Tabelle 7.3 dokumentiert alle 13 Grenzfallexperimente auf dem Profil `esp32-c3` und stellt die gemessenen Ergebnisse von Prototyp `v0.1.0` und Version `v0.2.0` unmittelbar gegenüber. Neun in `v0.1.0` aufgedeckte Fehlerklassen wurden in `v0.2.0` vollständig behoben; zwei konzeptionelle Grenzen (`i` bei `gpio_num_t` und `j` bei `#ifdef`-Weichen) bestehen bewusst weiter und werden in Abschnitt 8.2 diskutiert.

| ID | Getesteter Fall | Verhalten in `v0.1.0` | Gemessenes Verhalten in `v0.2.0` | Bewertung (`v0.2.0`) |
| :---: | :--- | :--- | :--- | :--- |
| `a` | Direkte Zahlen (`pinMode(12, OUTPUT); analogRead(5);`) + `WiFi` | `SAT` (**False Negative**) | `UNSAT`: `GPIO_12 -> 10`, `GPIO_5 -> 0` | **behoben** |
| `b` | Lokale Zähler (`blinkCount`, `retries`) & `BAUD_RATE 115200` | `UNSAT` (**False Positive**) | Nur `STATUS_LED = 3` geprüft $\rightarrow$ `SAT` | **behoben** |
| `c`, `c2` | Gleichstand `BUZZER_PIN = 7` / `SERVO_PIN = 7`, beide Reihenfolgen | `BUZZER_PIN` blieb (Z3-Heuristik) | `SERVO_PIN` bleibt in beiden Fällen (`BUZZER -> 20` bzw. `6`) | Gleichstand weiterhin solverabhängig |
| `d` | 6 Analogsensoren `S0..S5` + WLAN (nur 5 `ADC1`-Pins vorhanden) | `GPIO None` für alle 6 Signale | `repair_possible=False`, klare Kapazitätsmeldung (Listing 7.6) | **behoben** |
| `e` | Synthetische Fähigkeit `'can'` ($P_i = \emptyset$, 1 bzw. 2 Signale) | `CAN_TX: -1` bzw. `-1 != -1`-Bruch | Sofort und konsistent `repair_possible=False`, `suggested={}` | **behoben** |
| `f`, `f2` | `SOIL_SENSOR = 1` (`adc`) vs. `STATUS_LED = 1` (`gpio`), beide Reihenfolgen | `SOIL_SENSOR = 1`, `LED -> 7` | In beiden Fällen `SOIL_SENSOR = 1`, `STATUS_LED -> 7` (+25 Pkt.) | Spezialist-Priorität bestätigt |
| `h` | Doppelrolle: `Wire.begin(MY_PIN, MY_SCL)` + `analogRead(MY_PIN)` | Nur `'adc'`; Vorschlag ohne I2C | `capabilities={'adc', 'i2c'}` $\rightarrow$ `MY_PIN -> 0` (kann ADC1 & I2C) | **behoben** |
| `i` | `constexpr int LED_A = 12;`, `static const uint8_t LED_B = 13;`, `const gpio_num_t LED_C = GPIO_NUM_14;` | `LED_A`, `LED_B` erkannt; `LED_C` ignoriert | `LED_A -> 7`, `LED_B -> 6`; `gpio_num_t` weiterhin ignoriert | **verbleibende Grenze** |
| `j` | `#ifdef USE_EXTERNAL_LED` (Pin 2) / `#else` (Pin 12) | Beide Zweige $\rightarrow$ `UNSAT` | Beide Zweige mit eindeutigen Schlüsseln $\rightarrow$ `UNSAT` (kein Absturz auch bei 3 Zweigen) | **verbleibende Grenze** (False Positive) |
| `k` | `Wire.begin(SDA_A, SCL_A)` & `Wire1.begin(SDA_B, SCL_B)` auf 6/7 | `SAT` (**False Negative**) | `UNSAT` (`Wire` $\neq$ `Wire1`), 4 getrennte Pins (`6, 20, 10, 7`) | **behoben** |
| `l` | Zwei `SPI.begin`-Aufrufe mit `MISO_P = 7`, `CS_A = 7`, `CS_B = 7` | `SAT` (**False Negative**) | `UNSAT` (`CS` als `gpio`), alle 5 Signale getrennt (`6, 21, 10, 7, 20`) | **behoben** |
| `m` | `OLED_SDA = 6` und `OLED_SCL = 6` in `Wire.begin(OLED_SDA, OLED_SCL)` | `SAT` (**False Negative**) | `UNSAT` (`Wire:sda` $\neq$ `Wire:scl`), `OLED_SDA=6`, `OLED_SCL -> 10` | **behoben** (neu geprüft) |

*Tabelle 7.3: Ergebnisse der Grenzfallexperimente auf `esp32-c3` (`v0.1.0` im Vergleich zu `v0.2.0`).*

Listing 7.6 dokumentiert die verbesserte Ausgabe im Überbuchungsfall `d` (`pigeonhole.cpp`): Statt der unbrauchbaren Zeilen `Change GPIO ... -> GPIO None` meldet `v0.2.0` klar, dass die Anforderungen die verfügbaren Hardware-Kapazitäten übersteigen.

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

### 7.5 Laufzeitmessung und PlatformIO-End-to-End-Prüfung

Tabelle 7.4 zeigt die gemessenen Medianlaufzeiten für Version `0.2.0`. Als Basislinie dauerte allein der Start des Python-Interpreters samt Import von `z3`, `tree_sitter` und `tree_sitter_cpp` im Median **139 ms**.

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

*Tabelle 7.4: Gemessene Laufzeiten (`v0.2.0`, End-to-End als CLI-Subprozess sowie je Phase im selben Prozess).*

Die Messwerte zeigen trotz umfassender Schema-Validierung, Bus-Rollen-Auswertung und dreistufiger Zielfunktion weiterhin sehr kurze Antwortzeiten:

- **Gesamtlaufzeit deutlich unter 1 s (NFA-02):** Jeder CLI-Lauf liegt zwischen 172 ms (`SAT`) und 211 ms (`UNSAT`). Rund 65–80 % der Zeit entfallen weiterhin auf den Start des Python-Prozesses und das Importieren der Bibliotheken (139 ms).
- **Geringer Mehraufwand der Validierung:** Das Laden und Schema-Prüfen eines Profils benötigt 0,36–0,57 ms, das Parsen von drei Dateien in Szenario 06 lediglich 1,84 ms. Im `SAT`-Fall liegt `validate()` bei 0,01–0,02 ms; im `UNSAT`-Fall löst Z3 das dreistufige MaxSMT-Problem in 10,01–25,97 ms.

**Realer End-to-End-Test über die PlatformIO Registry.** Ergänzend zu den CLI-Benchmarks wurde Version `0.2.0` wie von einem externen Anwender in einem separaten, leeren Projektordner getestet:

1. `pio pkg install` lud `dmatheja/mcu-pin-solver@0.2.0` (20,71 KB) direkt aus der öffentlichen PlatformIO Registry herunter.
2. Ein `pio run` mit fehlerhaftem ESP32-C3-Sketch (`STATUS_LED = 12`, `SOIL_SENSOR = 5`, `WiFi.begin`) stoppte den Build über `pio_hook.py` nach **1,21 s** (`UNSAT`, Exit-Code `1`) *vor* dem Start des C++-Compilers und gab die Diagnose (`main.cpp:3`, `main.cpp:4`) samt Z3-Reparaturvorschlag aus.
3. Nach Übernahme der korrigierten Pin-Nummern lief `pio run` durch den Validator (`SAT`), startete den RISC-V-Compiler und erzeugte `firmware.elf` und `firmware.bin` fehlerfrei in **17,76 s** (Exit-Code `0`).
4. Ebenso bestand ein frischer `git clone` in ein separates Verzeichnis samt `pip install .`, `mcu-validate --list-boards` und allen 42 Tests.

### 7.6 Soll-Ist-Abgleich

Tabelle 7.5 überprüft alle in Kapitel 4 gestellten Anforderungen und Invarianten am finalen Stand `v0.2.0`.

| ID | Anforderung / Invariante | Status | Begründung / Einschränkung |
| :--- | :--- | :---: | :--- |
| FA-01 | Hardware-Profil laden & validieren | erfüllt | `load_board` (längstes Präfix, `_`/`-`, direkter `.json`-Pfad) + strenge Schema-Validierung (`test_board.py`) |
| FA-02 | Mehrere Dateien & `--include-dir` | erfüllt | Liest `include/` + `src/` sowie optionale `--include-dir`-Pfade; schließt `.pio/`, `test/`, `tests/` aus |
| FA-03 | Fehlalarmfreie Extraktion | weitgehend erfüllt | Erfasst Makros (inkl. `(12)`), Deklarationen (`12u`) und direkte Literale; ignoriert Kommentare, Strings, lokale Variablen und Nicht-Pin-Konstanten; offene Grenzen bei `#ifdef` (`j`) und `gpio_num_t` (`i`) |
| FA-04 | Eindeutige Behandlung von Widersprüchen | erfüllt | `_reserve_unique_key` trennt alle abweichenden Definitionen und Literale eindeutig (auch bei 3 `#ifdef`-Zweigen) |
| FA-05 | Fähigkeiten, Bus-Rollen & Module | erfüllt | Mehrfachfähigkeiten als Menge (`h`), positionsgenaue `Wire`/`SPI`/`Serial`-Auswertung inkl. `bus_group` und Namens-Fallback (`OLED_SDA_PIN`) |
| FA-06 | Präzise Diagnose | erfüllt | Meldet alle Fehler einzeln mit `datei:zeile`-Verweis und konkreter Regelbegründung (`reason`) |
| FA-07 | Kollision vs. geteilte Bus-Leitung | erfüllt | Schützt geteilte Bus-Leitungen (`Wire:sda`), lehnt `SDA == SCL` (`m`), `Wire` vs. `Wire1` (`k`), `SCK == MOSI` und doppelte SPI-`CS` (`l`) ab |
| FA-08 | Minimale Reparatur & Kapazitätsmeldung | erfüllt | Dreistufige MaxSMT-Prioritäten (`1000`/`20`/`5`) + klare Meldung bei `repair_possible=False` (`d`, `e`) |
| FA-09 | Transparenter Bericht & Prompt | erfüllt | Zeigt `Checked Pins`, warnt bei 0 Pins und erzeugt kopierbare `Keep`/`Change`-Anweisungen |
| FA-10 | Build-Schranke & CLI | erfüllt | Verifiziert über `pip install .`, `mcu-validate` und realen PlatformIO-Registry-End-to-End-Lauf (`0.2.0`) |
| NFA-01–NFA-07 | Qualitätsanforderungen | erfüllt | 0 chip-spezifische Regeln in Python, E2E $\le 211$ ms, 42 Tests, 5/5 grüne CI-Jobs (`ruff`, `mypy`, Windows & Linux) |
| INV-01–INV-06 | Architektur-Invarianten | erfüllt | Alle sechs Invarianten im Codebestand und durch automatisierte Tests abgesichert |

*Tabelle 7.5: Soll-Ist-Abgleich (`v0.2.0`).*

### 7.7 Gültigkeit der Ergebnisse

Für die wissenschaftliche Einordnung bleiben drei Grenzen der Aussagekraft (*Threats to Validity*) offen zu benennen:

- **Interne Gültigkeit.** Prozess-Startzeiten unter Windows schwanken durch Hintergrundaktivitäten und Dateisystem-Caches. Durch zehn bzw. dreißig Wiederholungen, Auswertung des Medians und Trennung von Subprozess- und In-Process-Messung ist dieser Störeinfluss kontrolliert.
- **Externe Gültigkeit.** Alle 42 Tests, neun Szenarien und dreizehn Grenzfallexperimente wurden im Rahmen dieser Arbeit konstruiert. Es liegt weiterhin **kein** systematischer empirischer Benchmark über eine größere Stichprobe frei von Sprachmodellen erzeugter Embedded-Projekte vor (z. B. Fehlerrate mit vs. ohne `mcu-pin-solver`). Zudem sind bisher nur zwei Espressif-Chips als fertige JSON-Profile enthalten; weitere Architekturen wie RP2040 oder STM32 sind über das offene Schema vorbereitet, aber noch nicht eingepflegt.
- **Konstruktgültigkeit.** Das Ergebnis `SAT` beweist stets nur Korrektheit des *vom Parser erkannten Pin-Modells* relativ zum *hinterlegten JSON-Profil*. Elektrische Randbedingungen oder nicht geparste C++-Konstrukte (Abschnitt 8.2) bleiben außerhalb der formalen Garantie.

---

## 8 Diskussion, Grenzen und Ausblick

### 8.1 Diskussion der Ergebnisse

Die Evaluation zeigt den praktischen Wert einer iterativen, testgetriebenen Entwicklung: Bereits Version `0.1.0` belegte die Grundidee der neuro-symbolischen Trennung, doch erst die gezielten Grenzfallexperimente legten neun konkrete Schwachstellen offen – von übersehenen Zahlenliteralen über fehlende SPI-Chip-Select-Trennung bis zu fehlerhaften `GPIO None`-Prompts und fehlender JSON-Schema-Validierung. Durch die gezielte Überarbeitung auf Version `0.2.0` konnten alle neun Probleme behoben werden, ohne die Verständlichkeit des Codes oder die Ausführungsgeschwindigkeit (weiterhin rund 0,2 s pro CLI-Lauf) zu gefährden.

Der reale Test über die PlatformIO Registry bestätigt darüber hinaus die Alltagstauglichkeit: Ein fehlerhafter Build bricht in 1,21 s ab, lange bevor die mehrsekündige C++-Übersetzung anläuft, und nennt Dateiname, Zeile und eine Z3-geprüfte Ersatzbelegung, die sowohl gültige Pins als auch knappe ADC-Ressourcen schont.

### 8.2 Verbleibende Grenzen des Systems

Auch nach den Verbesserungen in Version `0.2.0` verbleiben sechs klar abgrenzbare Systemgrenzen, die unmittelbar aus den bewussten Entwurfsentscheidungen (Tree-Sitter ohne Präprozessor, generische Board-Profile, manueller Prompt-Kreislauf) folgen (Tabelle 8.1):

1. **Präprozessor-Verzweigungen (`#ifdef` / `#else`).** Tree-Sitter wertet keine bedingte Kompilierung aus und besucht alle Zweige gleichzeitig. Enthält ein inaktiver Zweig einen für ein anderes Board gedachten Pin (Experiment `j`), entsteht weiterhin ein False Positive. Immerhin führt selbst eine mehrfache Neudefinition dank eindeutiger Schlüssel nicht mehr zu einem Solver-Abbruch.
2. **Spezielle C++-Typen und Ausdrücke.** ESP-IDF-Aufzählungstypen (`const gpio_num_t LED = GPIO_NUM_14;`, Experiment `i`), Pin-Arrays (`int pins[] = {...}`), `enum`-Listen und berechnete Makros (`#define LED (BASE + 2)`) werden nicht aufgelöst.
3. **Drittbibliotheks-Konstruktoren und -Methoden.** Wird ein Pin ausschließlich an eine herstellerspezifische Bibliothek übergeben (z. B. `myServo.attach(OUT_1)` oder `OneWire bus(DATA_LINE)`) und enthält der Bezeichner kein Pin-Schlüsselwort (`PIN`, `GPIO`, `SDA`, …), bleibt der Pin unentdeckt; bei Konstruktoren wie `DHT dht(DHT_PIN, DHT22);` greift lediglich der `gpio`-Fallback über den Namen.
4. **USB-Serial-Annahme bei externem UART-Wandler.** In den mitgelieferten ESP32-Profilen aktiviert jeder Aufruf von `Serial.begin(...)` das Modul `usb_serial` und sperrt GPIO 18/19 (C3) bzw. 19/20 (S3). Auf Entwicklungsboards mit externem USB-UART-Wandlerchip (bei denen `Serial` über UART0 läuft und `ARDUINO_USB_CDC_ON_BOOT=0` gesetzt ist) kann diese Regel zu streng sein.
5. **Chip-Abdeckung und Hardware-Vereinfachungen.** Bisher sind nur ESP32-C3 und ESP32-S3 enthalten. Zudem kennt das aktuelle JSON-Schema noch keine Felder für reine Eingangs-Pins (`input_only`, etwa GPIO 34–39 beim klassischen ESP32), PWM-Kanalbudgets oder siliziumspezifische Treiber-Errata (wie das im neueren ESP-IDF-`adc_oneshot`-Treiber standardmäßig deaktivierte `ADC2` auf dem ESP32-C3 [[9]](#ref-9)).
6. **Manueller Rückkopplungskreis und fehlender LLM-Benchmark.** Der Reparatur-Prompt wird noch manuell in den LLM-Chat kopiert, und die tatsächliche Reduktion von Pin-Fehlern über verschiedene reale Sprachmodelle hinweg wurde noch nicht in einer empirischen Studie quantifiziert.

| Nr. | Verbleibende Grenze (`v0.2.0`) | Ort | Auswirkung | Möglicher Ausbau |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `#ifdef` / `#else`-Zweige | `parser.py` | False Positive bei Alternativ-Konfigs (`j`) | Makro-Filter über Build-Flags (`-D...`) aus `platformio.ini` |
| 2 | `gpio_num_t`, Arrays, `enum`, Rechen-Makros | `parser.py` | False Negative (`i`) | Erweiterung der AST-Regeln um `GPIO_NUM_<n>` und `enumerator` |
| 3 | Drittbibliotheks-Aufrufe / Konstruktoren | `parser.py` | False Negative ohne `PIN`-Namensmuster | Konfigurierbare API-Muster oder optionales Profil-Feld |
| 4 | `Serial.begin` bei externem UART-Bridge-Chip | `boards/*.json` / `pio_hook.py` | Ggf. zu strenge Sperre auf USB-Pins | Auswertung von `-DARDUINO_USB_CDC_ON_BOOT` aus PlatformIO |
| 5 | Chip-Katalog & Schema-Details | `boards/*.json` | Nur C3/S3; kein `input_only`/Kanalbudget | Optionale Schema-Felder + Profile für ESP32, C6, RP2040, STM32 |
| 6 | Manueller Prompt & kein LLM-Benchmark | Workflow / Evaluation | Kopierschritt nötig; externe Validität offen | MCP-Tool / `--autofix` + systematische LLM-Vergleichsstudie |

*Tabelle 8.1: Verbleibende Systemgrenzen in Version `0.2.0`.*

### 8.3 Reflexion der KI-gestützten Entstehung

Sowohl die schrittweise Entwicklung von `v0.1.0` und `v0.2.0` als auch Entwürfe dieser Ausarbeitung entstanden unter Mitwirkung großer Sprachmodelle (vgl. Verzeichnis der verwendeten KI-Hilfsmittel). Dabei traten gleich zwei lehrreiche Beobachtungen auf, die das Grundthema dieser Arbeit unmittelbar spiegeln:

1. **Empirische Prüfung gegen plausible Behauptungen:** Ein früherer Textentwurf behauptete, Z3 löse Gleichstände zwischen zwei identischen Pins deterministisch nach ihrer Deklarationsreihenfolge auf. Erst die Experimente `c` und `c2` widerlegten diese Behauptung direkt am Code.
2. **Subtile Fehler erst durch gezielte Tests sichtbar:** Bei der Überarbeitung der Namensheuristik in `v0.2.0` übersah ein vermeintlich korrekter regulärer Ausdruck (`WORD_RE`) Großbuchstaben-Wörter vor Unterstrichen (`OLED_SDA_PIN`), weil der Lookahead nur auf Kleinbuchstaben, Ziffern und Zeilenende prüfte. Erst der neu geschriebene Unit-Test `test_name_inference_recognizes_bus_pins_with_pin_suffix` deckte diesen Fehler sofort auf – ebenso wie die GitHub-Actions-CI-Matrix den Ausfall vorinstallierter Python-3.9-Umgebungen auf `ubuntu-latest` sichtbar machte.

Automatisierte Tests, statische Typprüfung (`mypy`), Linting (`ruff`) und echte End-to-End-Probeläufe erwiesen sich damit als das entscheidende Korrektiv gegenüber plausibel wirkendem, aber im Detail fehlerhaftem KI-Code.

### 8.4 Ausblick

Aus dem erreichten Stand `0.2.0` ergeben sich vier naheliegende nächste Schritte:

1. **Auswertung von Build-Flags aus PlatformIO.** Durch Übergabe aktiver `-D`-Makros aus `platformio.ini` an `cli.py` ließen sich sowohl `#ifdef`-Zweige gezielt filtern als auch native USB-CDC-Boards sauber von Boards mit externem USB-UART-Wandler unterscheiden.
2. **Automatisierter Reparatur-Regelkreis.** Über ein optionales `--json`-Ausgabeformat oder eine Werkzeugschnittstelle (z. B. Model Context Protocol, MCP) könnte ein KI-Coding-Agent `mcu-validate` direkt aufrufen und Konflikte mit begrenzter Iterationszahl automatisch beheben.
3. **Erweiterung des Chip-Katalogs.** Ergänzung geprüfter JSON-Profile für den klassischen ESP32 (inkl. `input_only`), ESP32-C6, Raspberry Pi RP2040 und ausgewählte STM32-Varianten.
4. **Empirische LLM-Evaluation.** Systematische Messung an einer standardisierten Sammlung realer Embedded-Prompts über mehrere aktuelle Sprachmodelle hinweg (Fehlerquote vor vs. nach Einsatz von `mcu-pin-solver`).

---

## 9 Fazit

Die vorliegende Arbeit hat mit `mcu-pin-solver` (Version `0.2.0`) ein datengetriebenes Pre-Build-Werkzeug zur statischen Prüfung und MaxSMT-Reparatur von GPIO-Pin-Belegungen in Embedded-C++-Projekten entworfen, iterativ gehärtet und empirisch evaluiert. Die drei einleitenden Forschungsfragen lassen sich abschließend wie folgt beantworten:

- **Zu FF1 (Extraktion ohne Ziel-Toolchain):** Mit `tree-sitter-cpp` lassen sich Top-Level-Pin-Konstanten, direkte Pin-Literale, Mengen benötigter Fähigkeiten, Bus-Leitungsrollen (`Wire:sda`, `SPI:mosi`, …) sowie aktive Peripherie über verteilte `include/`- und `src/`-Dateien hinweg in unter 2 ms (im selben Prozess) und ohne Ziel-Compiler auslesen. Kommentare, Zeichenketten, lokale Variablen und fachfremde Konstanten erzeugen keine Fehlalarme. Bewusste Grenzen der rein syntaktischen Analyse bleiben `#ifdef`-Alternativen, `gpio_num_t`-Aufzählungen und nicht standardisierte Drittbibliotheks-APIs.
- **Zu FF2 (Validierte Datentrennung und MaxSMT-Reparatur):** Die Auslagerung sämtlicher Chip-Regeln in schema-validierte JSON-Profile (`mcu_validator/boards/*.json`) entkoppelt den Prüfcode vollständig vom Zielchip, wie derselbe Quelltext auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`) belegt. Die zweistufige Prüfung kombiniert präzise Einzeldiagnosen mit Dateizeilen-Verweis in Stufe 1 (0,01–0,02 ms bei `SAT`) mit einer dreistufig gewichteten MaxSMT-Optimierung in `z3.Optimize` in Stufe 2 (10–26 ms bei `UNSAT`), die gültige Originalpins bewahrt (`1000`), Strapping-Pins meidet (`20`), knappe ADC-/USB-Pins schont (`5`), geteilte Bus-Leitungen zusammenhält und unlösbare Überbuchungen klar meldet.
- **Zu FF3 (PlatformIO- und CLI-Integration):** Über `pio_hook.py`, `library.json` (`"srcFilter": ["-<*>"]`) und gebündelte Paketdaten in `pyproject.toml` lässt sich das Werkzeug sowohl über `pip install .` (`mcu-validate`) als auch über die PlatformIO Registry (`dmatheja/mcu-pin-solver@^0.2.0`) ohne Zusatzkonfiguration einsetzen. Im realen End-to-End-Test über die Registry stoppte der Hook ein fehlerhaftes Projekt in 1,21 s vor dem Kompilieren und ließ den korrigierten Build fehlerfrei durchlaufen; alle 42 automatisierten Tests sowie `ruff` und `mypy` bestehen unter Windows und Linux.

Insgesamt belegt das System am konkreten Beispiel, dass das neuro-symbolische LLM-Modulo-Prinzip im Embedded-Prototyping praktisch und mit minimalem Zeitaufwand umsetzbar ist: Das Sprachmodell übernimmt den schnellen Code-Entwurf, während ein gut lesbarer AST-Parser und ein formaler Z3-Solver die Einhaltung physikalischer Hardware-Grenzen erzwingen.

---

## Literaturverzeichnis

- <a id="ref-1"></a>**[1] Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006):** *Compilers: Principles, Techniques, and Tools* (2. Aufl.). Addison-Wesley, Boston.
- <a id="ref-2"></a>**[2] Barrett, C., Sebastiani, R., Seshia, S. A., & Tinelli, C. (2021):** *Satisfiability Modulo Theories.* In: Biere, A., Heule, M., van Maaren, H., & Walsh, T. (Hrsg.): *Handbook of Satisfiability* (2. Aufl.), Frontiers in Artificial Intelligence and Applications, Bd. 336, S. 1267–1329, IOS Press.
- <a id="ref-3"></a>**[3] Bjørner, N., Phan, A.-D., & Fleckenstein, L. (2015):** *$\nu Z$ – An Optimizing SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2015)*, Lecture Notes in Computer Science, Bd. 9035, S. 194–199, Springer. DOI: `10.1007/978-3-662-46681-0_14`.
- <a id="ref-4"></a>**[4] Brunsfeld, M. (2018):** *Tree-sitter – An incremental parsing system for programming tools.* Online-Dokumentation: `https://tree-sitter.github.io/tree-sitter/`.
- <a id="ref-5"></a>**[5] De Moura, L., & Bjørner, N. (2008):** *Z3: An Efficient SMT Solver.* In: *Tools and Algorithms for the Construction and Analysis of Systems (TACAS 2008)*, Lecture Notes in Computer Science, Bd. 4963, S. 337–340, Springer. DOI: `10.1007/978-3-540-78800-3_24`.
- <a id="ref-6"></a>**[6] Englhardt, Z., Li, R., Nissanka, D., Zhang, Z., Narayanswamy, G., Breda, J., Liu, X., Patel, S., & Iyer, V. (2024):** *Exploring and Characterizing Large Language Models for Embedded System Development and Debugging.* In: *Extended Abstracts of the CHI Conference on Human Factors in Computing Systems (CHI EA '24)* (Preprint: `arXiv:2307.03817`).
- <a id="ref-7"></a>**[7] Espressif Systems (2024):** *ESP32-C3 Series Datasheet* & *ESP32-C3 Technical Reference Manual.* Espressif Systems, Shanghai.
- <a id="ref-8"></a>**[8] Espressif Systems (2024):** *ESP32-S3 Series Datasheet* & *ESP32-S3 Technical Reference Manual.* Espressif Systems, Shanghai.
- <a id="ref-9"></a>**[9] Espressif Systems (2024):** *ESP-IDF Programming Guide – Analog to Digital Converter (ADC) Oneshot Mode Driver & Hardware Limitations (ESP32-C3 / ESP32-S3).* Online-Dokumentation: `https://docs.espressif.com/projects/esp-idf/`.
- <a id="ref-10"></a>**[10] Fakih, M., Dharmaji, R., Moghaddas, Y., Quiros Araya, G., Ogundare, O., & Al Faruque, M. A. (2024):** *LLM4PLC: Harnessing Large Language Models for Verifiable Programming of PLCs in Industrial Control Systems.* In: *IEEE/ACM 46th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP 2024)*, S. 192–203.
- <a id="ref-11"></a>**[11] Garcez, A. d'Avila, & Lamb, L. C. (2023):** *Neurosymbolic AI: The 3rd Wave.* Artificial Intelligence Review, 56(11), S. 12387–12406, Springer. DOI: `10.1007/s10462-023-10448-w`.
- <a id="ref-12"></a>**[12] Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006):** *Introduction to Automata Theory, Languages, and Computation* (3. Aufl.). Addison-Wesley, Boston.
- <a id="ref-13"></a>**[13] Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X., & Zhou, D. (2024):** *Large Language Models Cannot Self-Correct Reasoning Yet.* In: *Twelfth International Conference on Learning Representations (ICLR 2024)*.
- <a id="ref-14"></a>**[14] ISO/IEC (2011):** *ISO/IEC 25010:2011 – Systems and software engineering – Systems and software Quality Requirements and Evaluation (SQuaRE) – System and software quality models.* International Organization for Standardization, Genf.
- <a id="ref-15"></a>**[15] Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L., & Murthy, A. (2024):** *LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* In: *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*, PMLR Bd. 235, S. 22895–22907.
- <a id="ref-16"></a>**[16] Narodytska, N., & Bacchus, F. (2014):** *Maximum Satisfiability Using Core-Guided MaxSAT Resolution.* In: *Proceedings of the Twenty-Eighth AAAI Conference on Artificial Intelligence (AAAI 2014)*, S. 2717–2723.
- <a id="ref-17"></a>**[17] PlatformIO (2024):** *PlatformIO Core Documentation – Project Configuration (`platformio.ini`), Library Manifest (`library.json`) and Advanced Scripting.* Online-Dokumentation: `https://docs.platformio.org/`.
- <a id="ref-18"></a>**[18] Rust Embedded Working Group (2024):** *embedded-hal: A Hardware Abstraction Layer (HAL) for embedded systems.* Online-Dokumentation: `https://docs.rs/embedded-hal/`.
- <a id="ref-19"></a>**[19] STMicroelectronics (2024):** *STM32CubeMX: STM32Cube initialization code generator.* Online-Dokumentation: `https://www.st.com/en/development-tools/stm32cubemx.html`.
- <a id="ref-20"></a>**[20] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017):** *Attention Is All You Need.* In: *Advances in Neural Information Processing Systems (NeurIPS 2017)*, Bd. 30.
- <a id="ref-21"></a>**[21] Zephyr Project (2024):** *Zephyr Project Documentation – Devicetree Guide.* Online-Dokumentation: `https://docs.zephyrproject.org/latest/build/dts/index.html`.

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

#### `timing.py` (Laufzeitmessung für Abschnitt 7.5)

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

---

## Verzeichnis der verwendeten KI-Hilfsmittel

| Hilfsmittel | Einsatzbereich | Art der Prüfung und Verantwortung |
| :--- | :--- | :--- |
| LLM-Coding-Assistenten (Gemini / Claude) | Unterstützung beim Entwurf von `v0.1.0`, beim Refactoring auf die typisierte Architektur `v0.2.0` (`board.py`, `parser.py`, `solver.py`, `cli.py`, `pio_hook.py`), bei den Board-JSONs sowie beim Aufbau der modularen Testsuite und CI | Eigenständige fachliche Prüfung und Nachvollzug durch den Verfasser; Abgleich der Hardware-Regeln gegen die Espressif-Datenblätter [[7]](#ref-7), [[8]](#ref-8); Absicherung durch 42 automatisierte Tests, `ruff`, `mypy`, GitHub-Actions-CI und realen PlatformIO-Registry-End-to-End-Test |
| LLM-Textassistenten (Gemini / Claude) | Strukturierungshilfe, sprachliche Glättung und Überarbeitung dieser Ausarbeitung auf Stand `v0.2.0` | Eigenständige fachliche Prüfung aller Aussagen durch den Verfasser; empirische Verifikation sämtlicher Code-Auszüge, CLI-Ausgaben, Grenzfallexperimente und Laufzeitmessungen am realen Repository; Literaturabgleich |

---

## Ehrenwörtliche Erklärung

Ich erkläre ehrenwörtlich, dass ich die vorliegende Studienarbeit mit dem Thema

> *„Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT“*

selbstständig verfasst und keine anderen als die angegebenen Quellen und Hilfsmittel benutzt habe. Alle wörtlich oder sinngemäß aus Quellen entnommenen Stellen sind als solche kenntlich gemacht. Die verwendeten KI-gestützten Hilfsmittel sind im vorstehenden Verzeichnis vollständig offengelegt. Die Arbeit wurde bisher in gleicher oder ähnlicher Form keiner anderen Prüfungsbehörde vorgelegt und noch nicht veröffentlicht. Ich versichere zudem, dass die eingereichte elektronische Fassung mit gegebenenfalls eingereichten gedruckten Exemplaren übereinstimmt.

`[Ort]`, den `[TT.MM.JJJJ]`

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
`David Matheja` *(Unterschrift)*
