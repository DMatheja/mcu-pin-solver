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
| Matrikelnummer | `[eintragen]` |
| Kurs | `[eintragen]` |
| Dualer Partner | `[eintragen]` |
| Bearbeitungszeitraum | `[TT.MM.JJJJ – TT.MM.JJJJ]` |
| Betreuer/in bzw. Gutachter/in | `[eintragen]` |
| Umfang | 5 ECTS-Leistungspunkte (Workload 150 Stunden) |
| Quellcode | https://github.com/DMatheja/mcu-pin-solver |

---

## Sperrvermerk

*Hinweis für den Verfasser: Das Projekt ist unter MIT-Lizenz öffentlich verfügbar. Ein Sperrvermerk ist daher in der Regel nicht nötig und sollte vor der Abgabe gestrichen werden, sofern der Duale Partner ihn nicht ausdrücklich verlangt.*

---

## Kurzfassung

Große Sprachmodelle (*Large Language Models*, LLMs) erzeugen in Sekunden lauffähig wirkenden C++-Code für Mikrocontroller. Bei der Wahl der Anschluss-Pins (GPIOs) unterlaufen ihnen jedoch Fehler, die kein Compiler bemerkt: Pins, an denen intern der Programmspeicher hängt, Analogmessungen auf Wandlern, die durch das WLAN blockiert sind, oder Doppelbelegungen. Der Grund ist, dass Pin-Nummern im Arduino-Ökosystem gewöhnliche Ganzzahlen sind und der Compiler die Hardware nicht kennt.

Diese Arbeit entwickelt und evaluiert `mcu-pin-solver`, eine Bibliothek, die solche Fehler vor dem Kompilieren findet. Ein Parser auf Basis von Tree-Sitter liest den Quelltext als Syntaxbaum und extrahiert Pin-Definitionen sowie aktive Peripherie (z. B. WLAN). Diese werden mit einer austauschbaren JSON-Beschreibung des Chips abgeglichen. Bei Konflikten berechnet der Theorembeweiser Z3 als gewichtetes Optimierungsproblem (MaxSMT) eine Ersatzbelegung, die möglichst viele gültige Pins unverändert lässt. Das Ergebnis wird als Reparaturanweisung für das Sprachmodell ausgegeben; in PlatformIO stoppt ein Pre-Build-Hook fehlerhafte Builds.

Alle neun Regressionsszenarien werden korrekt bewertet, ein Prüflauf dauert im Median unter 0,2 s. Zwölf zusätzliche Grenzfalltests zeigen aber auch systematische Lücken, etwa bei direkt eingesetzten Zahlen, lokalen Zählervariablen, `#ifdef`-Zweigen und SPI-Chip-Select-Leitungen. Eine Evaluation mit echtem LLM-generiertem Code steht noch aus.

## Abstract

Large Language Models generate plausible embedded C++ code within seconds, yet they frequently assign microcontroller pins incorrectly – e.g. pins wired to internal flash memory, analog inputs blocked by an active Wi-Fi radio, or duplicate assignments. Compilers cannot detect these faults because pin numbers are plain integers.

This thesis presents and evaluates `mcu-pin-solver`, a pre-build checker for PlatformIO. A Tree-Sitter-based parser extracts pin definitions and active peripherals from the source code's syntax tree and checks them against a declarative JSON description of the target chip. If conflicts occur, the Z3 theorem prover solves a weighted MaxSMT problem to compute a repair that keeps as many valid pins as possible; the result is emitted as a repair prompt for the LLM, and a pre-build hook stops the faulty build.

All nine regression scenarios are classified correctly, with a median check time below 0.2 s. Twelve additional edge-case experiments, however, reveal systematic gaps (literal pin numbers, local counter variables, `#ifdef` branches, SPI chip-select lines). An evaluation on real LLM-generated code remains future work.

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
  - [2.3 Quelltextanalyse vom Text zum Syntaxbaum](#23-quelltextanalyse-vom-text-zum-syntaxbaum)
  - [2.4 Tree-Sitter](#24-tree-sitter)
  - [2.5 SAT, SMT und der Solver Z3](#25-sat-smt-und-der-solver-z3)
  - [2.6 Optimierung mit MaxSMT](#26-optimierung-mit-maxsmt)
  - [2.7 PlatformIO und der Build-Prozess](#27-platformio-und-der-build-prozess)
- [3 Verwandte Arbeiten und Stand der Technik](#3-verwandte-arbeiten-und-stand-der-technik)
- [4 Anforderungsanalyse](#4-anforderungsanalyse)
- [5 Konzeption und Entwurfsentscheidungen](#5-konzeption-und-entwurfsentscheidungen)
  - [5.1 Entscheidung 1: Verfahren zur Quelltextanalyse](#51-entscheidung-1-verfahren-zur-quelltextanalyse)
  - [5.2 Entscheidung 2: Verfahren zur Konfliktlösung](#52-entscheidung-2-verfahren-zur-konfliktlösung)
  - [5.3 Entscheidung 3: Zweistufiger Ablauf](#53-entscheidung-3-zweistufiger-ablauf)
  - [5.4 Entscheidung 4: Hardware-Wissen als Daten](#54-entscheidung-4-hardware-wissen-als-daten)
  - [5.5 Gesamtarchitektur](#55-gesamtarchitektur)
  - [5.6 Durchgängiges Beispiel](#56-durchgängiges-beispiel)
- [6 Implementierung](#6-implementierung)
  - [6.1 Repository und Softwareumgebung](#61-repository-und-softwareumgebung)
  - [6.2 Hardware-Profile](#62-hardware-profile)
  - [6.3 Parser](#63-parser)
  - [6.4 Solver](#64-solver)
  - [6.5 Wer darf bleiben? Prioritäten bei gegenseitiger Pin-Blockade](#65-wer-darf-bleiben-prioritäten-bei-gegenseitiger-pin-blockade)
  - [6.6 Bericht und Reparatur-Prompt](#66-bericht-und-reparatur-prompt)
  - [6.7 Integration in PlatformIO](#67-integration-in-platformio)
- [7 Evaluation](#7-evaluation)
  - [7.1 Evaluationsdesign und Messumgebung](#71-evaluationsdesign-und-messumgebung)
  - [7.2 Regressionsszenarien](#72-regressionsszenarien)
  - [7.3 Ausgewählte Szenarien im Detail](#73-ausgewählte-szenarien-im-detail)
  - [7.4 Grenzfallexperimente](#74-grenzfallexperimente)
  - [7.5 Laufzeitmessung](#75-laufzeitmessung)
  - [7.6 Soll-Ist-Abgleich](#76-soll-ist-abgleich)
  - [7.7 Gültigkeit der Ergebnisse](#77-gültigkeit-der-ergebnisse)
- [8 Diskussion, Grenzen und Ausblick](#8-diskussion-grenzen-und-ausblick)
  - [8.1 Diskussion der Ergebnisse](#81-diskussion-der-ergebnisse)
  - [8.2 Grenzen des Systems](#82-grenzen-des-systems)
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
| MCU | *Microcontroller Unit*, Mikrocontroller |
| MILP | *Mixed-Integer Linear Programming*, gemischt-ganzzahlige lineare Optimierung |
| PSRAM | *Pseudo-Static RAM*, zusätzlicher Arbeitsspeicher |
| PWM | *Pulse-Width Modulation*, Pulsweitenmodulation |
| SAT | *Satisfiability*, Erfüllbarkeit; auch Ergebnis „erfüllbar“ |
| SMT | *Satisfiability Modulo Theories*, Erfüllbarkeit über mathematischen Theorien |
| SPI | *Serial Peripheral Interface*, schneller serieller Bus |
| UART | *Universal Asynchronous Receiver Transmitter*, serielle Schnittstelle |
| UNSAT | *Unsatisfiable*, Ergebnis „nicht erfüllbar“ |
| USB-CDC | *USB Communications Device Class*, serielle Konsole über USB |

## Symbolverzeichnis

| Symbol | Bedeutung |
| :--- | :--- |
| $\mathcal{P}$ | Menge aller im Hardware-Profil eingetragenen GPIO-Nummern eines Chips |
| $r_i$ | $i$-te aus dem Quelltext extrahierte Pin-Anforderung, $i = 1, \dots, n$ |
| $p_i^0$ | im Quelltext notierte (ursprüngliche) Pin-Nummer von $r_i$ |
| $c_i$ | von $r_i$ benötigte Fähigkeit, z. B. `gpio`, `adc`, `i2c` |
| $v_i$ | ganzzahlige Entscheidungsvariable in Z3: neuer Pin für $r_i$ |
| $P_i$ | Menge der für $r_i$ zulässigen Pins (Kandidatenmenge) |
| $S$ | Menge der Strapping-Pins des Chips |
| $\mathbb{I}[\cdot]$ | Indikatorfunktion: 1, wenn die Bedingung gilt, sonst 0 |

## Abbildungsverzeichnis

- Abbildung 1.1: Pin-Multiplexing als „Rangierbahnhof“ (ESP32-C3, vereinfacht)
- Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver`
- Abbildung 2.2: Konkreter und abstrakter Syntaxbaum (schematisch)
- Abbildung 2.3: Von Tree-Sitter erzeugter Syntaxbaum eines Beispielprogramms
- Abbildung 2.4: Harte und weiche Bedingungen in MaxSMT
- Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess
- Abbildung 6.1: Zweistufiger Ablauf in `validate_with_z3`

## Tabellenverzeichnis

- Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung
- Tabelle 3.1: Einordnung verwandter Ansätze
- Tabelle 4.1: Funktionale Anforderungen
- Tabelle 4.2: Nicht-funktionale Anforderungen
- Tabelle 4.3: Architektur-Invarianten
- Tabelle 5.1: Nutzwertanalyse Quelltextanalyse
- Tabelle 5.2: Nutzwertanalyse Konfliktlösung
- Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0
- Tabelle 6.1: Dateien des Repositories
- Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3
- Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten
- Tabelle 6.4: Lokale reguläre Ausdrücke im Parser
- Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal)
- Tabelle 7.1: Messumgebung
- Tabelle 7.2: Ergebnisse der Regressionsszenarien
- Tabelle 7.3: Ergebnisse der Grenzfallexperimente
- Tabelle 7.4: Laufzeiten
- Tabelle 7.5: Soll-Ist-Abgleich
- Tabelle 8.1: Zusammenfassung der Systemgrenzen

## Listingverzeichnis

- Listing 1.1: Kompilierbares, aber auf dem ESP32-C3 fehlerhaftes Programm
- Listing 5.1: Szenario 0 (`00_flash_and_wifi_conflict.cpp`)
- Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3
- Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3
- Listing 6.1: Auszug aus `boards/esp32-c3.json`
- Listing 6.2: Laden des Hardware-Profils (`load_board_data`)
- Listing 6.3: Kollisionsschutz über Dateigrenzen (`_record_pin`)
- Listing 6.4: Extraktion von Pin-Deklarationen im Parser (Auszug)
- Listing 6.5: Aufbau des MaxSMT-Modells im Solver (Auszug)
- Listing 6.6: Kern des PlatformIO-Hooks (Auszug)
- Listing 7.1: Szenario 02 und Ausgabe
- Listing 7.2: Szenario 03 und Ausgabe
- Listing 7.3: Szenario 04 und Ausgabe
- Listing 7.4: Szenario 05 und Ausgabe
- Listing 7.5: Szenario 06 (mehrere Dateien) und Ausgabe
- Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall d)

---

# Hauptteil

*Hinweis: Der Seitenumfang von 40 bis 70 Seiten nach Abschnitt 3.4.3 der DHBW-Richtlinie bezieht sich auf die Kapitel 1 bis 9. Vorspann, Verzeichnisse und Anhänge zählen nicht dazu. Vollständige Quelltexte stehen deshalb im Anhang; der Hauptteil zeigt nur die für das Verständnis nötigen Auszüge.*

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
  I2C-/SPI-Controller     ───┘                        └──► GPIO 6, 7  (I2C, SPI)
  Interner SPI-Flash  ────────────── fest verdrahtet ────► GPIO 12–17  (nicht nutzbar)
  USB-Schnittstelle   ────────────── fest verdrahtet ────► GPIO 18, 19 (bei USB belegt)
```
*Abbildung 1.1: Pin-Multiplexing als „Rangierbahnhof“ (ESP32-C3, vereinfacht; Pin-Angaben nach [[7]](#ref-7)).*

Mit großen Sprachmodellen (LLMs) lässt sich Firmware heute in natürlicher Sprache beschreiben, etwa: „Schreibe eine ESP32-C3-Firmware mit Status-LED, Bodenfeuchtesensor, Relais, WLAN und serieller Ausgabe über USB.“ Das Modell liefert in Sekunden strukturierten C++-Code. Studien zeigen, dass LLMs dabei für typische Embedded-Aufgaben bemerkenswert oft funktionierenden Code erzeugen, aber eben nicht zuverlässig [[6]](#ref-6). Für die Pin-Belegung ist das besonders heikel: Ein falscher Pin fällt beim Kompilieren nicht auf, sondern erst auf der echten Platine – im schlechtesten Fall als Absturz beim Start.

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
2. **Der Compiler kennt den Chip nicht.** Er kennt den Befehlssatz des Prozessors, aber nicht, welche Pins intern belegt sind oder gar nicht existieren.
3. **Konflikte entstehen erst durch Kombination.** `analogRead(5)` ist für sich genommen zulässig. Unzulässig wird es erst, weil an anderer Stelle – vielleicht in einer anderen Datei – `WiFi.begin(...)` aufgerufen wird. Der Compiler übersetzt jede Datei einzeln und prüft solche Wechselwirkungen nicht.

Gesucht ist also ein Werkzeug, das Hardware-Wissen besitzt, das gesamte Projekt betrachtet und vor dem Kompilieren eingreift.

### 1.3 Fünf Fehlerklassen und ihre elektronischen Ursachen

In den technischen Handbüchern der ESP32-Chips [[7]](#ref-7), [[8]](#ref-8) wird zwischen zwei Arten der Pin-Verschaltung unterschieden. Die **GPIO-Matrix** ist ein flexibles digitales Koppelfeld: Digitale Signale wie I2C, SPI, UART oder PWM lassen sich auf fast jeden freien Pin legen. Analoge Signale (ADC), der interne Speicher und USB sind dagegen über den **IO_MUX** bzw. direkte Leitungen **fest mit bestimmten Pins verbunden**. Diese Unterscheidung erklärt, warum manche Pins frei austauschbar sind und andere nicht.

Für diese Arbeit werden fünf Fehlerklassen unterschieden. Die Einteilung stammt vom Verfasser; sie deckt die Fehler ab, gegen die das Werkzeug prüft, erhebt aber keinen Anspruch auf Vollständigkeit.

1. **Reservierte und nicht vorhandene Pins.** Beim ESP32-C3 sind GPIO 12–17 mit dem internen SPI-Flash verbunden [[7]](#ref-7), beim ESP32-S3 GPIO 26–37 mit Flash bzw. PSRAM [[8]](#ref-8). Wer dort schreibt, stört das Laden von Programmbefehlen. Hinzu kommen Nummern, die es auf dem Chip gar nicht gibt – etwa GPIO 32, das von älteren ESP32-Boards bekannt ist, beim ESP32-C3 aber nicht existiert. Solche Nummern werden hier **Geister-Pins** genannt.
2. **Konflikte durch aktive Peripherie.** Der WLAN-Treiber benutzt den Wandler `ADC2` selbst; Anwendungen können `ADC2` deshalb nur nutzen, solange WLAN nicht läuft [[9]](#ref-9). Betroffen sind beim ESP32-C3 GPIO 5, beim ESP32-S3 GPIO 11–20. Entsprechend belegt die native USB-Schnittstelle die Pins GPIO 18/19 (C3) bzw. 19/20 (S3).
3. **Fehlende Fähigkeit.** Nicht jeder Pin kann alles. GPIO 6 des ESP32-C3 beherrscht etwa I2C und SPI, hat aber keine Verbindung zum Analog-Wandler. `analogRead(6)` liefert dort keine sinnvollen Werte.
4. **Doppelbelegung – und die erlaubte Ausnahme.** Zwei unabhängige Verbraucher auf demselben Pin stören sich gegenseitig. Bei Bussen wie I2C ist das Teilen dagegen ausdrücklich vorgesehen: Mehrere Sensoren hängen an denselben Leitungen SDA und SCL. Ein Prüfwerkzeug muss beide Fälle unterscheiden.
5. **Strapping-Pins.** Beim Einschalten liest der Chip einige Pins aus, um zu entscheiden, wie er startet (ESP32-C3: GPIO 2, 8, 9; ESP32-S3: GPIO 0, 3, 45, 46) [[7]](#ref-7), [[8]](#ref-8). Diese Pins dürfen danach benutzt werden, eine äußere Beschaltung kann aber den Start verhindern. Bei automatischen Korrekturen sollten sie daher eher gemieden werden.

| Fehlerklasse | Beispiel (ESP32-C3) | Folge auf der Hardware |
| :--- | :--- | :--- |
| 1 Reservierte/fehlende Pins | `STATUS_LED = 12`, `PIR_SENSOR = 32` | Absturz bzw. wirkungsloser Code |
| 2 Aktive Peripherie | `SOIL_SENSOR = 5` (ADC2) und `WiFi.begin` | Analogmessung schlägt fehl |
| 3 Fehlende Fähigkeit | `analogRead(6)` | keine gültigen Messwerte |
| 4 Doppelbelegung | `BUZZER_PIN = 7` und `SERVO_PIN = 7` | Signale stören sich |
| 5 Strapping-Pins | externe Last an GPIO 2, 8 oder 9 | Chip startet ggf. nicht |

*Tabelle 1.1: Fünf Fehlerklassen bei der Pin-Belegung.*

### 1.4 Zielsetzung und Forschungsfragen

Ziel der Arbeit ist ein Werkzeug, das die fünf Fehlerklassen in PlatformIO-Projekten vor dem Kompilieren erkennt, verständlich meldet und eine korrigierte Pin-Belegung vorschlägt, die das Sprachmodell übernehmen kann.

Daraus ergeben sich drei Forschungsfragen:

- **FF1 – Extraktion:** Wie lassen sich Pin-Definitionen, benötigte Pin-Fähigkeiten und aktive Peripherie über mehrere C++-Dateien hinweg zuverlässig aus dem Quelltext gewinnen, ohne die Compiler-Werkzeugkette des Zielchips vorauszusetzen?
- **FF2 – Prüfung und Reparatur:** Wie lässt sich chipspezifisches Wissen vom Prüfcode trennen und so in ein Optimierungsproblem übersetzen, dass im Konfliktfall eine Ersatzbelegung entsteht, die möglichst wenig ändert, geteilte Busse erhält und Strapping-Pins meidet?
- **FF3 – Integration:** Wie lässt sich die Prüfung so in PlatformIO einbinden, dass fehlerhafte Builds gestoppt werden und eine für Sprachmodelle direkt verwertbare Korrekturanweisung entsteht?

**Zum Begriff „Verifikation“.** Im Titel ist von Verifikation die Rede. Gemeint ist damit eine formale Prüfung des *aus dem Quelltext extrahierten Pin-Modells* gegen ein *Modell der Hardware*. Es wird also nicht bewiesen, dass das gesamte Programm korrekt ist. Ob die Prüfung tatsächlich alle Fehler findet, hängt davon ab, wie vollständig der Parser den Quelltext erfasst und wie genau das Hardware-Profil den Chip beschreibt. Beide Einschränkungen werden in Kapitel 7 und 8 untersucht.

### 1.5 Vorgehen und Aufbau der Arbeit

Die Software entstand iterativ: Ein erster Prototyp für eine Einzeldatei und den ESP32-C3 wurde schrittweise um mehrere Dateien, ein zweites Chip-Profil, geteilte Busse und die PlatformIO-Integration erweitert. Jede Erweiterung wurde durch ein Testszenario abgesichert. Die Software wurde dabei mit Unterstützung von KI-Assistenten entwickelt; Abschnitt 8.3 und das Verzeichnis der KI-Hilfsmittel legen dies offen.

Die Arbeit ist wie folgt aufgebaut: Kapitel 2 erklärt die Grundlagen ohne Vorkenntnisse – Sprachmodelle, Syntaxbäume und den Solver Z3. Kapitel 3 ordnet die Arbeit in verwandte Ansätze ein. Kapitel 4 formuliert die Anforderungen, Kapitel 5 begründet die Entwurfsentscheidungen und führt ein durchgängiges Beispiel vor. Kapitel 6 beschreibt die Implementierung. Kapitel 7 evaluiert das System mit Regressionstests, eigenen Grenzfallexperimenten und Laufzeitmessungen. Kapitel 8 diskutiert Ergebnisse und Grenzen, Kapitel 9 beantwortet die Forschungsfragen.

---

## 2 Grundlagen

Dieses Kapitel erklärt die drei Bausteine, auf denen das Werkzeug beruht: Sprachmodelle (2.1–2.2), die Analyse von Quelltext mit Syntaxbäumen (2.3–2.4) und die logische Prüfung und Optimierung mit Z3 (2.5–2.6). Abschnitt 2.7 beschreibt PlatformIO.

### 2.1 Große Sprachmodelle

Ein großes Sprachmodell ist ein neuronales Netz – heute meist ein *Transformer* [[17]](#ref-17) –, das mit sehr großen Textmengen trainiert wurde. Es erzeugt Text Stück für Stück: Aus allen bisherigen Textbausteinen (*Tokens*) $t_1, \dots, t_{k-1}$ schätzt es die Wahrscheinlichkeit für den nächsten Baustein,

$$P(t_k \mid t_1, \dots, t_{k-1}),$$

und wählt einen passenden aus. Man spricht von *Next-Token-Prediction*.

> **Kurz erklärt:** Ein Sprachmodell „rechnet“ nicht nach, ob ein Pin frei ist. Es schreibt das, was in ähnlichen Texten statistisch häufig folgt.

Daraus folgen für die Pin-Belegung drei Schwächen:

1. **Verzerrung durch Trainingsdaten.** Im Internet gibt es sehr viele Beispiele für den älteren ESP32, auf dem GPIO 12 oder GPIO 32 übliche Pins sind. Solche Muster sind statistisch „naheliegend“, auch wenn ein ESP32-C3 gefordert ist.
2. **Keine globale Prüfung.** Das Modell schreibt von oben nach unten. Wenn es in Zeile 10 `WiFi.begin(...)` schreibt, prüft nichts nach, ob `SOIL_SENSOR = 5` aus Zeile 5 dadurch ungültig geworden ist.
3. **Unzuverlässige Selbstkorrektur.** Bittet man ein Modell, die eigene Antwort zu prüfen, verbessert sich das Ergebnis ohne externes Feedback nicht zuverlässig; teilweise wird es sogar schlechter [[13]](#ref-13).

### 2.2 Neuro-symbolische KI und das LLM-Modulo-Prinzip

Garcez und Lamb beschreiben die Entwicklung der KI in drei Wellen [[11]](#ref-11): Die erste Welle war **symbolisch** – Regeln und Logik, die exakt und nachprüfbar sind, aber keine unscharfen Aufgaben lösen. Die zweite Welle ist **neuronal** – lernende Netze wie Sprachmodelle, die flexibel und kreativ sind, aber keine Garantien geben. Die dritte Welle, die **neuro-symbolische KI**, verbindet beide.

Kambhampati et al. übertragen diesen Gedanken mit dem **LLM-Modulo-Framework** auf Planungsaufgaben [[14]](#ref-14): Das Sprachmodell erzeugt Kandidatenlösungen, externe Prüfer (*Critics*) bewerten sie und geben Rückmeldung, bis ein Kandidat alle Prüfungen besteht. Harte Prüfer stehen für unverhandelbare Bedingungen, weiche Prüfer für Qualitätswünsche.

Bildlich ist das Sprachmodell der Architekt, der schnell Entwürfe zeichnet, und der Prüfer der Statiker, der nachrechnet. Findet der Statiker einen Fehler, schickt er dem Architekten eine präzise Korrektur – er reißt nicht den ganzen Entwurf ab. Abbildung 2.1 zeigt, wie `mcu-pin-solver` diesen Kreislauf umsetzt.

```text
  ┌────────────────────────────────────────────────────────────┐
  │ 1. Generieren (LLM): Nutzerwunsch → C++-Code               │
  └──────────────────────────────┬─────────────────────────────┘
                                 ▼
  ┌────────────────────────────────────────────────────────────┐
  │ 2. Extrahieren (Tree-Sitter): Pins, Fähigkeiten, Module    │
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
*Abbildung 2.1: Der LLM-Modulo-Kreislauf in `mcu-pin-solver` (nach dem Prinzip aus [[14]](#ref-14)).*

Wichtig für die Einordnung: Das Werkzeug selbst enthält kein neuronales Netz. Es ist der symbolische Prüfer im Kreislauf; der Schritt zurück zum Sprachmodell erfolgt in Version 0.1.0 manuell, indem der Prompt kopiert wird.

### 2.3 Quelltextanalyse vom Text zum Syntaxbaum

Um Pins zu prüfen, muss das Werkzeug zuerst herausfinden, welche Pins im Quelltext stehen. Naheliegend wäre eine Textsuche mit **regulären Ausdrücken** (*Regex*), etwa nach dem Muster `#define NAME ZAHL`. Das scheitert aus einem grundsätzlichen Grund: Reguläre Ausdrücke beschreiben in der Chomsky-Hierarchie nur die einfachsten Sprachen (Typ 3) [[12]](#ref-12). Sie können sich nicht „merken“, ob sie sich gerade in einem Kommentar, einer Zeichenkette oder einer verschachtelten Klammer befinden. Programmiersprachen wie C++ sind deutlich komplexer. Eine Textsuche fällt deshalb auf folgende Fälle herein:

1. Kommentare: `// WiFi.begin("Test");` würde fälschlich als WLAN-Start erkannt.
2. Zeichenketten: `Serial.println("Bitte nicht WiFi.begin() aufrufen");` ebenso.
3. Schleifenvariablen: `for (int i = 0; ...)` sieht ähnlich aus wie `const int SENSOR = 0;`.
4. Formatierung: Leerzeichen wie in `WiFi . begin()` sind in C++ erlaubt.

Ein **Parser** geht stattdessen wie ein Compiler vor [[1]](#ref-1): Zuerst zerlegt die *lexikalische Analyse* den Text in Bausteine (*Tokens*) wie `const`, `int`, `LED`, `=`, `12`, `;`. Dann ordnet die *syntaktische Analyse* diese Bausteine nach den Regeln der Sprache zu einem Baum.

Man unterscheidet zwei Baumformen (Abbildung 2.2): Der **konkrete Syntaxbaum** (CST) enthält jedes Zeichen, auch `=` und `;`. Der **abstrakte Syntaxbaum** (AST) lässt reine Satzzeichen weg und zeigt nur die Bedeutung: Typ, Name, Wert.

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
3. **Benannte Felder.** Tree-Sitter liefert technisch einen konkreten Baum, bietet aber benannte Felder wie `name`, `value` oder `function` an. Über diese Felder arbeitet man praktisch mit einer abstrakten Sicht.

Abbildung 2.3 zeigt einen Ausschnitt des Baums, den `tree-sitter-cpp` in der verwendeten Version 0.23.4 für ein kurzes Beispiel erzeugt. Feldnamen stehen vor dem Doppelpunkt.

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
3. Der Wert eines `#define` (`preproc_arg`) enthält den gesamten Rest der Zeile, **einschließlich des Kommentars** (`'12 // Board-LED'`). Der Parser muss diesen Kommentar daher selbst entfernen (Abschnitt 6.3).

### 2.5 SAT, SMT und der Solver Z3

Nachdem die Pins bekannt sind, müssen sie geprüft und gegebenenfalls neu verteilt werden. Dafür nutzt das Werkzeug den Solver **Z3** von Microsoft Research [[5]](#ref-5). Drei Begriffe bauen aufeinander auf [[2]](#ref-2).

**SAT (Erfüllbarkeit).** Ein SAT-Solver löst Rätsel mit Aussagen, die wahr oder falsch sind. Beispiel: Anna ($A$) oder Ben ($B$) kommt zur Feier ($A \lor B$), aber nicht beide ($\neg(A \land B)$), und Ben sagt ab ($\neg B$). Dann muss Anna kommen – das Rätsel ist *erfüllbar* (SAT). Fordert man zusätzlich $\neg A$, gibt es keine Lösung mehr (UNSAT).

**SMT (Erfüllbarkeit modulo Theorien).** Pins sind Zahlen, keine Wahrheitswerte. SMT erweitert SAT deshalb um mathematische Theorien. In dieser Arbeit genügt die Theorie der ganzen Zahlen mit linearen Vergleichen (in Z3 als `QF_LIA` bezeichnet). Jede Pin-Anforderung wird zu *einer* ganzzahligen Variable $v_i$. Bedingungen lassen sich dann direkt formulieren:

- „Die LED muss auf einem erlaubten Pin liegen“: $v_{\text{LED}} = 0 \lor v_{\text{LED}} = 1 \lor \dots$
- „LED und Relais dürfen nicht denselben Pin haben“: $v_{\text{LED}} \neq v_{\text{Relais}}$

Intern kombiniert Z3 einen SAT-Löser, der Kombinationen durchsucht und aus Sackgassen lernt (*Conflict-Driven Clause Learning*, CDCL), mit einem Löser für die Zahlenbedingungen. Dieses Zusammenspiel heißt DPLL($T$) [[2]](#ref-2). Für das Verständnis dieser Arbeit genügt: Z3 probiert nicht alle Kombinationen durch, sondern schließt ganze Bereiche aussichtsloser Belegungen auf einmal aus.

### 2.6 Optimierung mit MaxSMT

Ein gewöhnlicher SMT-Solver liefert *irgendeine* gültige Lösung. Er könnte also auch Pins verschieben, die bereits korrekt waren – für den Nutzer wäre das ärgerlich, weil die Verdrahtung auf der Platine dann ebenfalls geändert werden müsste. Gewünscht ist eine Lösung, die **möglichst wenig ändert**.

Dafür bietet Z3 die Erweiterung $\nu Z$ (`z3.Optimize`) [[3]](#ref-3). Sie unterscheidet zwei Arten von Bedingungen (Abbildung 2.4):

- **Harte Bedingungen** (`opt.add`) müssen erfüllt sein. Sie bilden die physikalischen Regeln ab.
- **Weiche Bedingungen** (`opt.add_soft`) sind Wünsche mit einem Gewicht. Z3 sucht unter allen gültigen Lösungen eine, bei der die Summe der Gewichte erfüllter Wünsche maximal ist.

```text
  HARTE BEDINGUNGEN (müssen gelten)
  • jeder Pin existiert, ist nicht reserviert und hat die nötige Fähigkeit
  • keine Sperre durch aktive Peripherie (z. B. ADC2 bei WLAN)
  • verschiedene Signale auf verschiedenen Pins –
    außer Signale desselben geteilten Busses, die zusammenbleiben
                              │
                              ▼  unter allen gültigen Lösungen:
  WEICHE BEDINGUNGEN (Punkte sammeln)
  • +100 Punkte je Signal, das seinen ursprünglichen Pin behält
  •  +10 Punkte je Strapping-Pin, den ein Signal nicht belegt
```
*Abbildung 2.4: Harte und weiche Bedingungen in MaxSMT.*

Gelöst wird dieses Problem in Z3 standardmäßig mit dem Verfahren *MaxRes* [[15]](#ref-15). Es sucht wiederholt nach Gruppen von Wünschen, die sich gegenseitig ausschließen, und gibt jeweils den „billigsten“ Wunsch auf. Gewichtetes MaxSMT ist im allgemeinen Fall NP-schwer; für die kleinen Probleme dieser Arbeit (unter 50 Pins, wenige Signale) ist das in der Praxis unproblematisch, wie die Messungen in Abschnitt 7.5 zeigen.

### 2.7 PlatformIO und der Build-Prozess

**PlatformIO** ist eine verbreitete Entwicklungsumgebung für Mikrocontroller [[16]](#ref-16). Ein Projekt wird über die Datei `platformio.ini` konfiguriert; dort stehen unter anderem das Board (z. B. `board = esp32-c3-devkitm-1`), externe Bibliotheken (`lib_deps`) und Zusatzskripte (`extra_scripts`). Ein Zusatzskript mit dem Präfix `pre:` läuft **vor** dem Kompilieren. PlatformIO basiert auf dem Build-System SCons; ein solches Skript kann den Build mit `env.Exit(1)` abbrechen. Genau diesen Mechanismus nutzt `mcu-pin-solver`, um als „Schranke“ vor dem Compiler zu arbeiten.

---

## 3 Verwandte Arbeiten und Stand der Technik

### 3.1 Sprachmodelle in der Embedded- und Automatisierungsentwicklung

Englhardt et al. untersuchten, wie gut GPT-3.5, GPT-4 und PaLM 2 Software für eingebettete Systeme schreiben und Fehler darin finden [[6]](#ref-6). Sie bauten dafür einen Prüfstand, auf dem der erzeugte Code automatisch auf echter Hardware mit Sensoren und Aktoren getestet wurde (*Hardware-in-the-Loop*). Ergebnis: Insbesondere GPT-4 erzeugte für viele Aufgaben funktionierenden Code und gab hilfreiche Hinweise zur Fehlersuche, aber nicht zuverlässig beim ersten Versuch. Die Autoren empfehlen daher einen Arbeitsablauf, in dem Mensch und Modell zusammenarbeiten. Die vorliegende Arbeit setzt an diesem Befund an, ersetzt den teuren Hardware-Test für einen Teilaspekt – die Pin-Belegung – aber durch eine statische Prüfung vor dem Kompilieren.

Am nächsten verwandt ist **LLM4PLC** von Fakih et al. [[10]](#ref-10). Dort erzeugt ein Sprachmodell Programme für speicherprogrammierbare Steuerungen (SPS). Der Code wird in einer Schleife durch Syntaxprüfung, Compiler und einen formalen Modellprüfer geschickt; deren Fehlermeldungen gehen als Rückmeldung an das Modell zurück, bis alle Prüfungen bestanden sind. Das ist dasselbe Grundprinzip wie das LLM-Modulo-Framework [[14]](#ref-14) und wie in dieser Arbeit. Unterschiede bestehen im Anwendungsgebiet (SPS statt Mikrocontroller), im Prüfgegenstand (Programmverhalten statt Pin-Belegung) und darin, dass `mcu-pin-solver` nicht nur Fehler meldet, sondern eine konkrete optimierte Korrektur berechnet.

### 3.2 Werkzeuge der Embedded-Praxis

- **Statische Analysewerkzeuge für C++** wie `clang-tidy` oder `cppcheck` finden Programmierfehler wie Speicherlecks oder Nullzeiger. Hardware-Wissen über Pins besitzen sie nicht.
- **Grafische Konfiguratoren der Hersteller** wie STM32CubeMX arbeiten in umgekehrter Richtung: Man wählt Pins in einer Oberfläche, Konflikte werden dort angezeigt, und daraus wird Code erzeugt. Ein Sprachmodell erzeugt aber direkt Code; eine nachträgliche Prüfung von vorhandenem Arduino-Code bieten diese Werkzeuge nicht.
- **Hardware-Beschreibungen im Betriebssystem**, etwa der DeviceTree im Echtzeitbetriebssystem Zephyr, legen Pins in eigenen Dateien fest. Im Arduino- und PlatformIO-Umfeld, das beim Prototyping verbreitet ist, stehen Pins dagegen direkt im C++-Code.
- **Typsichere Hardware-Bibliotheken in Rust** (z. B. `embedded-hal`) stellen jeden Pin als Objekt dar, das nur einmal an einen Treiber übergeben werden kann. Eine doppelte Verwendung desselben Pins scheitert so bereits beim Kompilieren. Für den großen Bestand an Arduino-C++-Code steht das nicht zur Verfügung, und eine Ersatzbelegung wird nicht berechnet.

### 3.3 Einordnung und Forschungslücke

Tabelle 3.1 fasst die Einordnung zusammen. Es handelt sich um eine qualitative Einschätzung des Verfassers, nicht um einen systematischen Werkzeugvergleich.

| Ansatz | Prüft vorhandenen Arduino-C++-Code | Kennt Pin-Eigenschaften des Chips | Schlägt konkrete Korrektur vor | Teil eines LLM-Rückkopplungskreises |
| :--- | :---: | :---: | :---: | :---: |
| C++-Linter | ja | nein | nein | nein |
| Hersteller-Konfigurator | nein | ja | nein (zeigt Konflikte) | nein |
| Zephyr DeviceTree | nein | ja | nein | nein |
| Rust-HAL | nein | teilweise | nein | nein |
| LLM4PLC [[10]](#ref-10) | nein (SPS-Code) | – | über das LLM | ja |
| `mcu-pin-solver` | ja (Teilmenge, vgl. 8.2) | ja (JSON-Profil) | ja (Z3) | ja (Prompt manuell kopiert) |

*Tabelle 3.1: Einordnung verwandter Ansätze (Einschätzung des Verfassers).*

Die Lücke, die diese Arbeit adressiert, ist damit: ein Werkzeug, das bestehenden Arduino-/PlatformIO-Code ohne Compiler-Werkzeugkette auf Pin-Konflikte prüft, das Hardware-Wissen austauschbar hält und eine optimierte Korrektur in einer Form zurückgibt, die ein Sprachmodell direkt verarbeiten kann.

---

## 4 Anforderungsanalyse

### 4.1 Akteure und Anwendungsfälle

Das System hat drei Nutzergruppen:

1. **Embedded-Entwicklerin bzw. -Entwickler.** Baut ein Projekt in PlatformIO oder ruft das Werkzeug auf der Kommandozeile auf. Erwartet, dass Pin-Fehler vor dem Kompilieren gemeldet werden, und zwar verständlich.
2. **Sprachmodell.** Erzeugt den Code und erhält im Fehlerfall einen Prompt, nach dem es nur die betroffenen Pins ändern soll.
3. **Maintainer.** Ergänzt Unterstützung für weitere Chips, indem eine JSON-Datei angelegt wird – ohne Python-Code zu ändern.

### 4.2 Funktionale Anforderungen

| ID | Anforderung | Beschreibung |
| :--- | :--- | :--- |
| FA-01 | Hardware-Profil laden | Aus einer Board-Kennung (z. B. `esp32-c3-devkitm-1`) wird das passende Profil `boards/<chip>.json` gefunden. |
| FA-02 | Mehrere Dateien | Bei Angabe von `src/` werden alle `.h`, `.hpp`, `.c`, `.cpp`, `.ino` in `src/` und im Nachbarordner `include/` gelesen; `tests/` und `.pio/` werden ausgelassen. |
| FA-03 | Fehlalarmfreie Extraktion | Pin-Konstanten aus `#define` und `int`-/`uint8_t`-Deklarationen werden über den Syntaxbaum gelesen; Kommentare, Zeichenketten und `for`-Schleifenvariablen werden nicht als Pins oder Aufrufe gewertet. |
| FA-04 | Widersprüchliche Definitionen | Gleiche Definitionen in mehreren Dateien werden zusammengefasst, widersprüchliche bleiben getrennt sichtbar. |
| FA-05 | Fähigkeiten und Module | Aus Funktionsaufrufen werden die benötigten Fähigkeiten (`gpio`, `adc`, `pwm`, `i2c`, `spi`, `uart`) und aktive Module (`wifi`, `usb_serial`) abgeleitet. |
| FA-06 | Diagnose | Jeder Verstoß (Pin fehlt, Doppelbelegung, reserviert, Fähigkeit fehlt, Sperre durch Modul) wird einzeln im Klartext gemeldet. |
| FA-07 | Kollision vs. Bus | Unabhängige Signale auf einem Pin sind ein Fehler; Signale desselben teilbaren Busses dürfen einen Pin teilen und bleiben bei einer Verschiebung zusammen. |
| FA-08 | Minimale Reparatur | Bei Konflikten wird eine gültige Belegung berechnet, die möglichst viele gültige Originalpins behält und Strapping-Pins meidet. |
| FA-09 | Reparatur-Prompt | Ausgegeben wird ein kopierbarer Text mit allen Fehlern und für jedes Signal einer Anweisung „Keep“ oder „Change“. |
| FA-10 | Build-Schranke und CLI | Als PlatformIO-Bibliothek stoppt das Werkzeug fehlerhafte Builds vor dem Kompilieren; es ist zusätzlich eigenständig per Kommandozeile nutzbar. |

*Tabelle 4.1: Funktionale Anforderungen.*

### 4.3 Nicht-funktionale Anforderungen

Die Qualitätsmerkmale orientieren sich an der Norm ISO/IEC 25010.

| ID | Merkmal | Abnahmekriterium |
| :--- | :--- | :--- |
| NFA-01 | Erweiterbarkeit | Der Python-Code enthält keine chipspezifischen Pin-Nummern oder Chipnamen; ein neuer Chip erfordert nur eine JSON-Datei. |
| NFA-02 | Zeitverhalten | Ein Prüflauf für ein typisches Projekt (bis ca. 20 Dateien und 20 Pins) dauert deutlich unter 1 s. |
| NFA-03 | Portabilität | Lauffähig unter Windows und Linux ohne installierte Compiler-Werkzeugkette des Zielchips. |
| NFA-04 | Korrektheit der Vorschläge | Jeder ausgegebene Vorschlag erfüllt alle harten Regeln des Hardware-Profils. |
| NFA-05 | Paket-Hygiene | Als Bibliothek eingebunden, wird kein Beispielcode der Bibliothek mitkompiliert; der CLI-Aufruf erzeugt keine Python-Warnungen. |
| NFA-06 | Testbarkeit | Eine automatisierte Testsuite deckt alle Fehlerklassen ab und läuft bei jeder Änderung in der CI. |
| NFA-07 | Analysierbarkeit | Die Kernlogik bleibt unter 400 Zeilen Python und ist in klar getrennte Module gegliedert. |

*Tabelle 4.2: Nicht-funktionale Anforderungen.*

### 4.4 Architektur-Invarianten und Systemgrenzen

Damit spätere Änderungen – durch Menschen oder KI-Assistenten – die Architektur nicht schleichend aufweichen, legt die Datei `AGENTS.md` im Repository sechs verbindliche Regeln fest (Tabelle 4.3).

| ID | Invariante | Regel |
| :--- | :--- | :--- |
| INV-01 | Keine Chip-Logik in Python | GPIO-Nummern, reservierte Bereiche, Strapping-Pins, Auslöser und Konfliktregeln stehen nur in `boards/*.json`. |
| INV-02 | Syntaxbaum zuerst | C++-Strukturen werden nur über Tree-Sitter gewonnen; reguläre Ausdrücke dienen nur zum Bereinigen kurzer, bereits aus dem Baum herausgelöster Zeichenketten. |
| INV-03 | Kollisionssichere Zusammenführung | Widersprüchliche Definitionen desselben Namens werden unter `NAME (datei)` gespeichert, nicht überschrieben. |
| INV-04 | Paarweise Bus-Kopplung | Signale werden paarweise verglichen (gleich bei geteiltem Bus, sonst verschieden); ein pauschales „alle verschieden“ ist verboten. |
| INV-05 | Gewichtsrangfolge | Pin behalten (Gewicht 100) wiegt stets schwerer als Strapping meiden (Gewicht 10); harte Regeln werden nie abgeschwächt. |
| INV-06 | Paket-Hygiene | `srcFilter` und `export` in `library.json`; kein Import von `.cli` in `__init__.py`. |

*Tabelle 4.3: Architektur-Invarianten.*

**Im Umfang enthalten** sind die statische Analyse von Pin-Deklarationen und Peripherieaufrufen, die Prüfung gegen JSON-Profile, die Berechnung einer Ersatzbelegung und die Einbindung in PlatformIO. **Nicht enthalten** sind elektrische Simulation (z. B. Strombelastbarkeit), die Auswertung von Werten, die erst zur Laufzeit entstehen, und das automatische Ändern von Quelltext.

---

## 5 Konzeption und Entwurfsentscheidungen

Dieses Kapitel begründet die vier wichtigsten Entwurfsentscheidungen und führt dann ein vollständiges Beispiel durch das System. Für die Auswahl der Verfahren werden Nutzwertanalysen verwendet. Dabei ist eine Einschränkung offen zu benennen: Gewichte und Punkte wurden vom Verfasser festgelegt, und zwar in Kenntnis der späteren Entscheidung. Nutzwertanalysen machen eine Entscheidung nachvollziehbar, sie beweisen sie nicht. Deshalb wird jeweils auch geprüft, wie stark sich die Gewichte ändern müssten, damit eine andere Option gewinnt (Sensitivität).

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

**Begründung.** Reguläre Ausdrücke scheitern an K1 (Abschnitt 2.3). `libclang` ist semantisch am stärksten: Es würde Makros wie `#define LED (BASE + 2)` ausrechnen und nur den aktiven `#ifdef`-Zweig betrachten. Dafür benötigt es aber die Header des Zielsystems (`Arduino.h`, ESP-IDF) und die richtigen Compiler-Optionen, sonst entstehen Fehler und unvollständige Bäume. Tree-Sitter kommt ohne all das aus.

**Sensitivität.** Der Abstand zwischen C und B entsteht vor allem durch K2, K3 und K5. Erhöht man das Gewicht von K4 und verkleinert die übrigen anteilig, gewinnt `libclang` erst ab einem Gewicht von etwa 36 % für K4. Die Entscheidung ist also stabil, solange Portabilität wichtiger ist als semantische Tiefe. Der Preis dieser Entscheidung zeigt sich in Kapitel 8: Mehrere der dort beschriebenen Grenzen (Makro-Ausdrücke, `#ifdef`) wären mit `libclang` lösbar.

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

**Begründung.** Eine Heuristik ist einfach, findet aber nicht immer die beste Lösung. Ein Gedankenexperiment zeigt das: Liegen bei aktivem WLAN eine LED und ein Analogsensor beide auf GPIO 1 und sind die übrigen ADC1-Pins 0, 3 und 4 schon belegt, dann würde eine Heuristik, die das zuerst deklarierte Signal (die LED) behält, den Sensor auf den einzigen freien ADC1-Pin 2 schieben – einen Strapping-Pin. Ist auch Pin 2 belegt, findet sie gar keine Lösung, obwohl eine existiert: Die LED könnte ausweichen. Ein Optimierer findet diese Lösung (vgl. Abschnitt 6.5, Fall 3).

SMT ohne Optimierung liefert irgendeine gültige Belegung und verschiebt dabei womöglich korrekte Pins. MILP ist für das Problem fachlich genauso geeignet wie MaxSMT und liefert ebenfalls optimale Lösungen. Der Unterschied liegt in der Formulierung: In MILP müsste man für jede Kombination aus Signal und Pin eine 0/1-Variable anlegen und „verschieden“ über lineare Ungleichungen ausdrücken. In Z3 genügt eine ganzzahlige Variable je Signal und eine Bedingung $v_a \neq v_b$. MaxSMT wurde daher vor allem wegen der kompakteren, lesbareren Modellierung gewählt.

**Sensitivität.** Der Vorsprung von MaxSMT gegenüber MILP beruht allein auf K2. Wer die Modellierungsfreundlichkeit für unwichtig hält, erhält einen Gleichstand zwischen den beiden Verfahren.

### 5.3 Entscheidung 3: Zweistufiger Ablauf

Unabhängig vom Solver stellt sich die Frage, *wie* Fehler gemeldet werden. Würde man die ursprünglichen Pins als harte Bedingungen an Z3 übergeben, erhielte man im Fehlerfall nur die Antwort „unerfüllbar“ – ohne Begründung. Deshalb arbeitet das System in zwei Stufen:

1. **Stufe 1 – Diagnose:** Ein einfacher Python-Durchlauf prüft jedes Signal einzeln gegen das Hardware-Profil und erzeugt für jeden Verstoß eine Klartextmeldung. Sind alle Signale gültig, endet die Prüfung hier mit SAT, und Z3 wird gar nicht gestartet.
2. **Stufe 2 – Reparatur:** Nur wenn Stufe 1 Fehler gefunden hat, berechnet Z3 eine Ersatzbelegung.

So bekommt der Nutzer alle Fehlerursachen auf einmal (vgl. Szenario 03 mit drei Fehlern), und fehlerfreie Builds werden nicht verlangsamt.

### 5.4 Entscheidung 4: Hardware-Wissen als Daten

Alle Eigenschaften eines Chips – welche Pins es gibt, was sie können, welche reserviert sind und welche Regeln gelten – stehen in einer JSON-Datei, nicht im Programmcode (INV-01). Dadurch entsteht eine klare Arbeitsteilung: Der Python-Code weiß, *wie* geprüft wird; die JSON-Datei weiß, *was* für einen Chip gilt. Ein neuer Chip erfordert nur eine neue Datei. Der Nachteil: Die Qualität der Prüfung hängt vollständig von der Qualität dieser Datei ab. Ein falscher Eintrag führt zu falschen Ergebnissen, ohne dass der Code das bemerken kann (vgl. Abschnitt 8.2 zu ADC2 auf dem ESP32-C3).

### 5.5 Gesamtarchitektur

Abbildung 5.1 zeigt den Ablauf vom Start des Builds bis zur Entscheidung.

```text
  platformio.ini + Projektdateien (include/, src/)
          │   "pio run" startet das Pre-Build-Skript vor dem Compiler
          ▼
  pio_hook.py
    ├─ läuft nur einmal pro Build (Merker _MCU_VALIDATOR_RAN)
    ├─ wählt Python-Interpreter, installiert fehlende Pakete
    └─ ruft auf: python -m mcu_validator.cli <src-Ordner> <board>
          ▼
  mcu_validator/cli.py
    ├─ load_board_data(board)        → boards/<chip>.json
    ├─ parse_cpp_file(pfad, profil)  → Anforderungen, aktive Module
    └─ validate_with_z3(...)         → Stufe 1 Diagnose, ggf. Stufe 2 Z3
          │
          ├── SAT   (Rückgabewert 0) → Compiler startet
          └── UNSAT (Rückgabewert 1) → env.Exit(1), Reparatur-Prompt
```
*Abbildung 5.1: Gesamtarchitektur und Datenfluss im Build-Prozess.*

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

**Schritt 1 – Profil laden.** Aus `boards/esp32-c3.json` ergibt sich unter anderem: GPIO 12–17 sind reserviert, GPIO 5 hat nur `adc2`, ADC1 liegt auf GPIO 0–4, Strapping-Pins sind 2, 8 und 9, aktives WLAN sperrt `adc2`, aktive USB-Konsole sperrt GPIO 18 und 19.

**Schritt 2 – Quelltext analysieren.** Der Parser findet `STATUS_LED = 12` (der Zeilenkommentar im `#define` wird entfernt), `SOIL_SENSOR = 5` und `RELAY_PIN = 4`. Die Zeile `int reading = analogRead(SOIL_SENSOR);` wird nicht als Pin gezählt, weil rechts kein Zahlenwert, sondern ein Funktionsaufruf steht. Weil `SOIL_SENSOR` in `analogRead` vorkommt, braucht es die Fähigkeit `adc`. `WiFi.begin` und `Serial.begin` aktivieren die Module `wifi` und `usb_serial`. Ergebnis:

```python
requests = [
    {"name": "STATUS_LED",  "pin": 12, "cap": "gpio"},
    {"name": "SOIL_SENSOR", "pin": 5,  "cap": "adc"},
    {"name": "RELAY_PIN",   "pin": 4,  "cap": "gpio"},
]
active_resources = ["wifi", "usb_serial"]
```

**Schritt 3 – Diagnose (Stufe 1).** `STATUS_LED` liegt auf einem reservierten Pin. `SOIL_SENSOR` braucht `adc`, also `adc1` oder `adc2`; GPIO 5 bietet nur `adc2`, und das ist durch WLAN gesperrt. `RELAY_PIN` ist gültig. Es gibt zwei Fehler, also folgt Stufe 2.

**Schritt 4 – Reparatur (Stufe 2).** Für jedes Signal wird die Menge der zulässigen Pins bestimmt. Weil die USB-Konsole aktiv ist, fallen GPIO 18 und 19 weg:

$$P_{\text{LED}} = P_{\text{RELAY}} = \{0, 1, \dots, 10, 20, 21\}, \qquad P_{\text{SOIL}} = \{0, 1, 2, 3, 4\}$$

Hart gefordert ist zudem, dass alle drei Signale verschiedene Pins haben. Als Wünsche gibt es 100 Punkte für jedes Signal auf seinem Originalpin (für LED und Sensor unerreichbar, für das Relais erreichbar) sowie 10 Punkte für jeden Strapping-Pin der Kandidatenmenge, den ein Signal nicht belegt. LED und Relais können so höchstens 30 Strapping-Punkte erreichen (Pins 2, 8, 9), der Sensor höchstens 10 (nur Pin 2 liegt in seiner Menge).

| Belegung (LED, Sensor, Relais) | Relais behalten | Strapping-Punkte | Summe | Bewertung |
| :--- | :---: | :---: | :---: | :--- |
| (12, 5, 4) – Original | – | – | ungültig | verletzt harte Regeln |
| (21, 1, 0) | 0 | 30 + 10 + 30 | 70 | Relais unnötig verschoben |
| (21, 2, 4) | 100 | 30 + 0 + 30 | 160 | Sensor auf Strapping-Pin 2 |
| (21, 1, 4) – Ausgabe von Z3 | 100 | 30 + 10 + 30 | 170 | optimal |

*Tabelle 5.3: Punktebewertung ausgewählter Belegungen in Szenario 0.*

Es gibt mehrere gleichwertige Lösungen mit 170 Punkten, etwa (10, 0, 4) oder (20, 3, 4). Welche davon Z3 ausgibt, legt das Modell nicht fest; das Ergebnis ist aber für dieselbe Eingabe und dieselbe Z3-Version reproduzierbar (Abschnitt 6.5).

**Schritt 5 – Ausgabe.** Listing 5.2 zeigt die tatsächliche Ausgabe. Dieselbe Datei ist auf einem ESP32-S3 fehlerfrei (Listing 5.3), denn dort ist GPIO 12 ein normaler Pin und GPIO 5 gehört zu ADC1. Allein der Austausch des Hardware-Profils ändert also das Ergebnis – genau die Trennung aus Entscheidung 4.

```text
=================================================================
 Checked File   : tests/scenarios/00_flash_and_wifi_conflict.cpp (ESP32-C3)
 Active Modules : ['wifi', 'usb_serial']
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 12): Reserved pin! (Internal SPI flash (SPIIO4))
  - SOIL_SENSOR (GPIO 5): Conflicts with active ['wifi', 'usb_serial'] (ADC2 conflicts with Wi-Fi).

Please regenerate the code using this exact Z3-verified pin assignment:
  - STATUS_LED: Change GPIO 12 -> GPIO 21
  - SOIL_SENSOR: Change GPIO 5 -> GPIO 1
  - RELAY_PIN: Keep GPIO 4 (unchanged)

-----------------------------------------------------
```
*Listing 5.2: CLI-Ausgabe für Szenario 0 auf ESP32-C3 (Rückgabewert 1).*

```text
=================================================================
 Checked File   : tests/scenarios/00_flash_and_wifi_conflict.cpp (ESP32-S3)
 Active Modules : ['wifi', 'usb_serial']
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 5.3: CLI-Ausgabe für Szenario 0 auf ESP32-S3 (Rückgabewert 0).*

Ein Detail der Ausgabe ist ungenau: Die Meldung für `SOIL_SENSOR` nennt alle aktiven Module (`['wifi', 'usb_serial']`), obwohl nur `wifi` den Konflikt verursacht. Das liegt daran, dass der Solver die Liste der aktiven Module unverändert in die Meldung schreibt (Abschnitt 6.4).

---


## 6 Implementierung

Dieses Kapitel beschreibt die Umsetzung von `mcu-pin-solver` in Version 0.1.0 anhand der realen Projektdateien. Zur besseren Lesbarkeit zeigt der Hauptteil nur Auszüge; die vollständigen Quelltexte und Hardware-Profile finden sich in den Anhängen A bis E.

### 6.1 Repository und Softwareumgebung

Das System gliedert sich in vier Schichten: die Integration (`pio_hook.py`, `library.json`, `pyproject.toml`), die Orchestrierung und Ausgabe (`cli.py`, `__init__.py`), den Verifikationskern (`parser.py`, `solver.py`) und die deklarativen Hardware-Daten (`boards/*.json`). Tabelle 6.1 gibt eine Übersicht aller Projektdateien.

| Datei / Ordner | Umfang | Aufgabe |
| :--- | :--- | :--- |
| `boards/esp32-c3.json` | 49 Zeilen JSON | Hardware-Profil für den ESP32-C3 (Anhang A) |
| `boards/esp32-s3.json` | 73 Zeilen JSON | Hardware-Profil für den ESP32-S3 (Anhang B) |
| `mcu_validator/parser.py` | 167 Zeilen Python | Dateiauflösung, Tree-Sitter-Analyse, Modul-Auslöser (Anhang C) |
| `mcu_validator/solver.py` | 117 Zeilen Python | Profil-Loader, Stufe-1-Prüfung, Z3-MaxSMT-Optimierung (Anhang D) |
| `mcu_validator/cli.py` | 49 Zeilen Python | Berichtsformatierung, CLI-Einstiegspunkt, Rückgabewert (Anhang E) |
| `mcu_validator/__init__.py` | 4 Zeilen Python | Paket-Exports ohne Vorab-Import von `.cli` (Anhang E) |
| `pio_hook.py` | 42 Zeilen Python | PlatformIO-Pre-Build-Hook inkl. Paketprüfung (Anhang E) |
| `library.json` | 33 Zeilen JSON | PlatformIO-Manifest mit `extraScript`, `srcFilter` und `export` (Anhang E) |
| `pyproject.toml` | 17 Zeilen TOML | Python-Paketmetadaten (`requires-python >= 3.9`) und Skript `mcu-validate` |
| `src/main.cpp` und `platformio.ini` | 56 + 11 Zeilen | Demo-Projekt für lokale `pio run`-Tests |
| `tests/run_tests.py` und `tests/scenarios/` | 55 Zeilen + 7 Fälle | Regressionstestsuite für neun Prüfkonstellationen |
| `.github/workflows/ci.yml` | 18 Zeilen YAML | CI-Workflow (`ubuntu-latest`, Python `3.12`) |
| `README.md` und `AGENTS.md` | 85 + 95 Zeilen | Installationsanleitung, Prompt-Vorlage und Architektur-Invarianten |

*Tabelle 6.1: Dateien des Repositories.*

Die vier Module des Python-Pakets `mcu_validator` umfassen zusammen 337 Zeilen; selbst unter Einrechnung von `pio_hook.py` ergibt sich ein Gesamtumfang von 379 Zeilen Python-Code (inklusive Leerzeilen und Kommentare). Die Vorgabe NFA-07 (unter 400 Zeilen Kernlogik) ist damit eingehalten.

### 6.2 Hardware-Profile

Gemäß INV-01 liegen sämtliche GPIO-Nummern, Fähigkeiten und Sperrregeln in JSON-Dateien im Ordner `boards/`. Jedes Profil besteht aus fünf Sektionen (Listing 6.1):

1. **`pins`:** Bildet ausschließlich physisch herausgeführte Pin-Nummern (als Strings) auf ihre Eigenschaften ab (`capabilities`, `strapping`, `reserved` und optional `note`). Nicht existierende Pins (wie GPIO 11 auf dem ESP32-C3 oder GPIO 22–25 auf dem ESP32-S3) fehlen als Schlüssel. Reservierte Pins tragen `"reserved": true` und eine leere Fähigkeitsliste.
2. **`capability_aliases`:** Löst allgemeine Fähigkeiten aus dem C++-Code (`"adc"`) auf chipspezifische Bänke (`["adc1", "adc2"]`) auf.
3. **`shared_capabilities`:** Nennt Bus-Fähigkeiten (`["i2c", "spi"]`), bei denen mehrere Signale denselben Pin teilen dürfen.
4. **`resource_triggers`:** Ordnet Peripherienamen (`"wifi"`, `"usb_serial"`) den auslösenden C++-Aufrufen zu (`["WiFi.begin", "WiFi.softAP"]`, `["Serial.begin"]`).
5. **`conflict_rules`:** Formuliert kontextabhängige Verbote mit `when_resource_active` in Kombination mit `forbidden_capability` oder `forbidden_pins`.

```json
{
  "mcu": "ESP32-C3",
  "description": "Espressif ESP32-C3 (RISC-V, Single-Core, Wi-Fi/BLE)",
  "pins": {
    "2":  { "capabilities": ["gpio", "adc1", "pwm"], "strapping": true,  "reserved": false, "note": "Strapping Pin (Boot Mode)" },
    "5":  { "capabilities": ["gpio", "adc2", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "6":  { "capabilities": ["gpio", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "12": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIIO4)" },
    "18": { "capabilities": ["gpio", "usb"], "strapping": false, "reserved": false, "note": "USB D-" },
    "20": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 RX" },
    "21": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 TX" }
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
*Listing 6.1: Auszug aus `boards/esp32-c3.json` (vollständig in Anhang A).*

Listing 6.2 zeigt, wie `load_board_data` aus einem PlatformIO-Board-Namen (z. B. `esp32-c3-devkitm-1`) das passende Profil auswählt. Der Name wird in Kleinbuchstaben mit Bindestrich normalisiert und per Teilstring-Suche mit den alphabetisch sortierten Dateistämmen in `boards/` abgeglichen. *(Hinweis zur Skalierung: Kommen künftig Profile mit verschachtelten Präfixen wie `esp32.json` neben `esp32-c3.json` hinzu, muss nach absteigender Namenslänge sortiert werden, damit nicht das kürzere Präfix zuerst greift.)*

```python
BOARDS_DIR = Path(__file__).resolve().parent.parent / "boards"

def load_board_data(board_id="esp32-c3"):
    board_id_lower = board_id.lower().replace("_", "-")
    for json_file in sorted(BOARDS_DIR.glob("*.json")):
        if json_file.stem.lower() in board_id_lower:
            return json.loads(json_file.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"No hardware definition found for board '{board_id}' in {BOARDS_DIR}")
```
*Listing 6.2: Laden des Hardware-Profils (`load_board_data`, `mcu_validator/solver.py`, Z. 5–13).*

Wie stark sich bereits zwei verwandte Chips der ESP32-Familie unterscheiden, fasst Tabelle 6.2 zusammen.

| Merkmal | `boards/esp32-c3.json` | `boards/esp32-s3.json` |
| :--- | :--- | :--- |
| Architektur | RISC-V Single-Core | Xtensa LX7 Dual-Core |
| Eingetragene GPIOs | `0–10`, `12–21` (21 Einträge; `11` fehlt) | `0–21`, `26–48` (45 Einträge; `22–25` fehlen) |
| Reservierter Flash / PSRAM | `12–17` (`Internal SPI flash`) | `26–37` (`Internal SPI` / `Octal-SPI flash / PSRAM`) |
| Strapping-Pins | `2, 8, 9` | `0, 3, 45, 46` |
| `ADC1` (mit WLAN nutzbar) | `0–4` | `1–10` |
| `ADC2` (bei WLAN gesperrt) | `5` | `11–20` |
| Native USB-Pins | `18` (D-), `19` (D+) | `19` (D-), `20` (D+) |
| UART0 | `20` (RX), `21` (TX) | `43` (TX), `44` (RX) |

*Tabelle 6.2: Vergleich der Hardware-Profile ESP32-C3 und ESP32-S3.*

### 6.3 Parser

Der Parser in `mcu_validator/parser.py` arbeitet in drei Schritten: Dateiauflösung, Syntaxbaum-Durchlauf und Klassifikation.

**1. Dateiauflösung (`_resolve_source_files`) und Kollisionsschutz (`_record_pin`).** Übergibt der Nutzer oder der PlatformIO-Hook eine einzelne Datei, wird direkt diese geparst. Wird dagegen ein Verzeichnis `src/` übergeben, bindet `_resolve_source_files` automatisch ein vorhandenes Geschwisterverzeichnis `include/` ein und sucht rekursiv alle Dateien mit den Endungen `.h`, `.hpp`, `.c`, `.cpp` und `.ino`. Zwei Details verhindern dabei subtile Fehler:
- Header-Dateien (`.h`, `.hpp`) werden vor den übrigen Quelldateien sortiert, sodass zentrale Definitionen aus `include/` zuerst gelesen werden.
- Unterordner namens `tests` oder `.pio` werden auf Basis des *relativen* Pfades ab dem Suchordner ausgeblendet (`p.relative_to(d).parts`). Eine Prüfung gegen den vollständigen Pfad `p.parts` würde fehlgehen, wenn der zu prüfende Projektordner selbst unterhalb eines Ordners `tests/` liegt – wie beim Testszenario `tests/scenarios/06_multi_file_project/src`.

Werden Konstanten über mehrere Dateien hinweg definiert, sorgt `_record_pin` (Listing 6.3) für die Invariante INV-03: Identische Werte desselben Bezeichners werden dedupliziert; widersprechen sich zwei Dateien (z. B. `STATUS_LED = 8` in `pins.h` und `#define STATUS_LED 12` in `motor.cpp`), bleibt der zweite Eintrag datei-qualifiziert erhalten und löst im Solver einen Konflikt aus.

```python
def _record_pin(pins_in_code, name, pin_val, file_path):
    """Store pin definition, preserving conflicting cross-file redefinitions under distinct keys."""
    if name not in pins_in_code or pins_in_code[name] == pin_val:
        pins_in_code[name] = pin_val
    else:
        pins_in_code[f"{name} ({file_path.name})"] = pin_val
```
*Listing 6.3: Kollisionsschutz über Dateigrenzen (`_record_pin`, `mcu_validator/parser.py`, Z. 67–72).*

**2. AST-Durchlauf.** Für jede Datei erzeugt `tree-sitter-cpp` einen Syntaxbaum (`AST_PARSER.parse(file_path.read_bytes())`), über den der rekursive Generator `_walk_ast` läuft. Ausgewertet werden drei Knotentypen (Listing 6.4):
- `preproc_def` (`#define NAME ZAHL`): Da Tree-Sitter einen eventuellen Zeilenkommentar in `preproc_arg` belässt (Abschnitt 2.4), wird dieser lokal entfernt, bevor `.isdigit()` eine reine nicht-negative Ganzzahl prüft.
- `declaration` außerhalb von `for_statement` (`int` oder `uint8_t`): Die Prüfung auf `node.parent.type != "for_statement"` schließt `for (int i = 0; ...)` aus. Auch `const int` und `constexpr int` werden erfasst, weil Qualifizierer im Baum als eigene `type_qualifier`-Geschwisterknoten stehen und `child_by_field_name("type")` weiterhin `"int"` bzw. `"uint8_t"` liefert (Abschnitt 7.4, Experiment `i`). Die rechte Seite eines `init_declarator` muss sowohl ein `identifier`-Ziel als auch ein direktes `number_literal` mit Ziffern aufweisen.
- `call_expression`: Der Funktionsausdruck wird um Whitespace bereinigt (`fn_name`), und aus dem Argumentteilbaum (`arguments`) werden alle `identifier`-Knoten gesammelt.

```python
for node in _walk_ast(tree.root_node):
    # 1. Preprocessor macro definitions: #define PIN_NAME 12
    if node.type == "preproc_def":
        name_node = node.child_by_field_name("name")
        val_node = node.child_by_field_name("value")
        if name_node and val_node:
            val_str = re.sub(r"//.*|/\*.*?\*/", "", _node_text(val_node), flags=re.DOTALL).strip()
            if val_str.isdigit():
                _record_pin(pins_in_code, _node_text(name_node).strip(), int(val_str), file_path)

    # 2. Pin variable declarations: const int / uint8_t / constexpr PIN_NAME = 12;
    elif node.type == "declaration" and node.parent and node.parent.type != "for_statement":
        type_node = node.child_by_field_name("type")
        if _node_text(type_node).strip() in ("int", "uint8_t"):
            for child in node.children:
                if child.type == "init_declarator":
                    decl_node = child.child_by_field_name("declarator")
                    val_node = child.child_by_field_name("value")
                    if decl_node and val_node and decl_node.type == "identifier" and val_node.type == "number_literal":
                        val_str = _node_text(val_node).strip()
                        if val_str.isdigit():
                            _record_pin(pins_in_code, _node_text(decl_node).strip(), int(val_str), file_path)

    # 3. Function & method calls: e.g. analogRead(PIN), Wire.begin(SDA, SCL), WiFi.begin(...)
    elif node.type == "call_expression":
        fn_node = node.child_by_field_name("function")
        args_node = node.child_by_field_name("arguments")
        if fn_node and args_node:
            fn_name = re.sub(r"\s+", "", _node_text(fn_node))
            arg_ids = [
                _node_text(child).strip()
                for child in _walk_ast(args_node)
                if child.type == "identifier"
            ]
            call_expressions.append((fn_name, arg_ids))
```
*Listing 6.4: Extraktion von Pin-Deklarationen und Aufrufen im Parser (`mcu_validator/parser.py`, Z. 86–120).*

**3. Fähigkeitenklassifikation und Auslöser.** Im Anschluss ordnet `parse_cpp_file` jedes gefundene Pin-Symbol einer einzigen Fähigkeit zu (Tabelle 6.3). Schließlich werden die `resource_triggers` des Hardware-Profils über einen exakten oder punktbegrenzten Endungsvergleich (`fn == pat or fn.endswith("." + pat)`) gegen alle aufgerufenen Funktionen geprüft. So aktiviert `board.WiFi.begin()` das Modul `wifi`, ein unbeteiligtes `myWiFi.begin()` hingegen nicht.

| Funktionsmuster im AST | Abgeleitete Fähigkeit | Bedeutung |
| :--- | :---: | :--- |
| Standard (z. B. `pinMode`, `digitalWrite`) | `gpio` | allgemeiner digitaler Ein-/Ausgang |
| `analogRead` | `adc` | analoge Messung (per Alias auf `adc1`/`adc2` aufgelöst) |
| `analogWrite`, `ledcAttach`, `ledcAttachPin` | `pwm` | Pulsweitenmodulation (Arduino oder ESP32-LEDC) |
| `Wire*.begin`, `Wire*.setPins` *(oder `SDA`/`SCL`-Name bei aktivem `Wire`)* | `i2c` | teilbarer Zweidrahtbus |
| `SPI*.begin` | `spi` | teilbarer SPI-Bus |
| `Serial1.begin`, `Serial2.begin` *(nur mit Ziffer)* | `uart` | Hardware-UART (abgegrenzt gegen USB-CDC `Serial.begin`) |

*Tabelle 6.3: Zuordnung von Funktionsaufrufen zu Fähigkeiten.*

Gemäß Invariante INV-02 durchsucht `parser.py` niemals den Rohtext mit regulären Ausdrücken. Alle vier im Modul eingesetzten `re`-Aufrufe arbeiten ausschließlich auf bereits vom Syntaxbaum isolierten Teilstrings (Tabelle 6.4).

| Zeile | Aufruf in `parser.py` | AST-isolierte Eingabe | Zweck |
| :---: | :--- | :--- | :--- |
| 92 | `re.sub(r"//.*\|/\*.*?\*/", "", ..., flags=re.DOTALL)` | `preproc_arg` eines `#define` | entfernt Zeilen- und Blockkommentare hinter dem Zahlenwert |
| 114 | `re.sub(r"\s+", "", _node_text(fn_node))` | Funktionsausdruck einer `call_expression` | normiert erlaubte Leerzeichen (z. B. `WiFi . begin`) |
| 132–137 | `^Wire\d*\.(?:begin\|setPins)$`, `^SPI\d*\.begin$`, `^Serial\d+\.begin$` | normierter Funktionsname `fn_name` | erkennt nummerierte Busse (`Wire1`, `SPI2`, `Serial1`); `\d+` trennt `Serial1` von `Serial` |
| 147 | `re.search(r"(?:^\|_)(?:SDA\|SCL)(?:_\|$)", name, re.IGNORECASE)` | Pin-Bezeichner bei aktivem `Wire` | erkennt I2C-Pins (`OLED_SDA`), falls `Wire.begin()` ohne Argumente aufgerufen wird |

*Tabelle 6.4: Lokale reguläre Ausdrücke im Parser.*

### 6.4 Solver

Die Funktion `validate_with_z3` in `mcu_validator/solver.py` prüft die extrahierten Anforderungen zweistufig gegen das JSON-Profil (Abbildung 6.1).

```text
  Eingabe: (requests, active_resources, board_data)
                        │
                        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Stufe 1: Deterministische Diagnose (ohne Z3)                        │
  │ Für jedes Signal r_i auf seinem Originalpin p_i^0:                  │
  │  1. Existiert Pin p im Profil?                                      │
  │  2. Doppelbelegung mit bisherigem Signal (Ausnahme: gleicher Bus    │
  │     und in shared_capabilities)?                                    │
  │  3. Ist Pin als reserved: true markiert?                            │
  │  4. Besitzt Pin mindestens eine passende Fähigkeit (über Aliase)?   │
  │  5. Sperrt eine aktive Regel den Pin oder alle passenden Fähigkeiten│
  │     (matching_caps.issubset(forbidden_caps))?                       │
  └─────────────────────┬─────────────────────────────┬─────────────────┘
          conflicts==[] ▼                             ▼ conflicts != []
  ┌───────────────────────────┐     ┌───────────────────────────────────┐
  │ Rückgabe: (True, [], ...) │     │ Stufe 2: Z3 Optimize (MaxSMT)     │
  │ (Z3 wird nicht gestartet) │     │ berechnet minimale Ersatzbelegung │
  └───────────────────────────┘     └─────────────────┬─────────────────┘
                                                      ▼
                                    Rückgabe: (False, conflicts, suggested)
```
*Abbildung 6.1: Zweistufiger Ablauf in `validate_with_z3`.*

Zwei Details in Stufe 1 erklären beobachtete Eigenheiten des Systems:
- Bei einer Sperre durch `conflict_rules` (Zeile 62) prüft der Solver `matching_caps.issubset(forbidden_caps)`: Besitzt ein Pin für dieselbe Anforderung mehrere passende Teilfähigkeiten und nur eine davon ist gesperrt, gilt der Pin weiterhin als nutzbar; erst wenn *alle* passenden Teilfähigkeiten (oder der Pin als Nummer in `forbidden_pins`) gesperrt sind, wird ein Konflikt gemeldet.
- In der Fehlermeldung der Zeile 64 gibt der Solver pauschal `Conflicts with active {active_resources}` aus, also die Liste aller aktiven Module statt nur des auslösenden Moduls. Bei aktivem `wifi` und `usb_serial` nennt die ADC2-Meldung daher beide Namen (vgl. Abschnitt 5.6, Listing 5.2).

Werden in Stufe 1 ein oder mehrere Konflikte gefunden, baut Stufe 2 das MaxSMT-Optimierungsmodell auf (Listing 6.5).

```python
    opt = Optimize()
    z3_vars = {}
    for req in requests:
        var = Int(req["name"])
        z3_vars[req["name"]] = var
        target_caps = set(aliases.get(req["cap"], [req["cap"]])) - forbidden_caps

        allowed_pins = [
            p for p, info in pins_db.items()
            if not info.get("reserved")
            and p not in forbidden_pins
            and target_caps.intersection(info["capabilities"])
        ]

        if allowed_pins:
            opt.add(Or([var == p for p in allowed_pins]))
        else:
            opt.add(var == -1)

        # Soft Constraint 1 (weight 100): Keep valid original pins unchanged whenever possible
        opt.add_soft(var == req["pin"], weight=100)

        # Soft Constraint 2 (weight 10): Avoid boot/strapping pins during reassignment
        for p in allowed_pins:
            if pins_db[p].get("strapping"):
                opt.add_soft(var != p, weight=10)

    # Couple shared bus lines together and keep all other signal pairs on distinct pins
    for i, req_a in enumerate(requests):
        for req_b in requests[i + 1:]:
            var_a = z3_vars[req_a["name"]]
            var_b = z3_vars[req_b["name"]]
            if (
                req_a["cap"] == req_b["cap"]
                and req_a["cap"] in shared_caps
                and req_a["pin"] == req_b["pin"]
            ):
                opt.add(var_a == var_b)
            else:
                opt.add(var_a != var_b)
```
*Listing 6.5: Aufbau des MaxSMT-Modells im Solver (`mcu_validator/solver.py`, Z. 71–110).*

Mathematisch lässt sich das Modell mit den Größen aus dem Symbolverzeichnis in drei Teile fassen. Mit der über `capability_aliases` aufgelösten Fähigkeitsmenge $A(c_i)$ bildet der Solver zunächst für jede Anforderung $r_i$ ($i \in \{1, \dots, n\}$) die Kandidatenmenge:

$$P_i = \Big\{\, p \in \mathcal{P} \;\Big|\; \neg\text{reserved}(p) \;\land\; p \notin \text{ForbiddenPins} \;\land\; \big(\text{caps}(p) \cap (A(c_i) \setminus \text{ForbiddenCaps})\big) \neq \emptyset \,\Big\}$$

1. **Domänenbindung (hart):** Ist $P_i \neq \emptyset$, gilt $\bigvee_{p \in P_i} (v_i = p)$; andernfalls setzt das Programm als Notbehelf $v_i = -1$ (die damit verbundene Störanfälligkeit bei zwei unlösbaren Signalen zeigt Abschnitt 7.4, Experiment `e`).
2. **Paarweise Kopplung (hart, INV-04):** Für alle Paare $1 \le i < j \le n$ gilt:
   $$v_i = v_j \quad \text{falls } c_i = c_j \land c_i \in \text{shared\_capabilities} \land p_i^0 = p_j^0, \qquad \text{sonst } v_i \neq v_j.$$
   Ein globales `z3.Distinct(...)` wäre falsch, weil es geteilte I2C- oder SPI-Leitungen trennen würde; erst diese paarweise Fallunterscheidung hält zusammengehörige Bus-Signale auf demselben Pin.
3. **Zielfunktion (weich, INV-05):** Z3 maximiert die gewichtete Summe:
   $$\max \sum_{i=1}^{n} \left( 100 \cdot \mathbb{I}[v_i = p_i^0] + \sum_{p \in P_i \cap S} 10 \cdot \mathbb{I}[v_i \neq p] \right)$$
   Für ein gültig platziertes Signal auf einem Strapping-Pin liefert das Beibehalten $100$ Punkte minus den Verlust einer $10$-Punkte-Bedingung, also $+90$ Punkte Nettovorteil gegenüber einer Verschiebung. Damit bleibt ein bestehender gültiger Pin *immer* stehen, auch wenn er ein Strapping-Pin ist (etwa `STATUS_LED = 8` in `src/main.cpp`). Muss ein Signal hingegen ohnehin neu vergeben werden ($p_i^0 \notin P_i$ oder durch eine Doppelbelegung verdrängt), vermeidet es Strapping-Pins, um die $10$ Punkte pro Strapping-Pin nicht zu verlieren.

### 6.5 Wer darf bleiben? Prioritäten bei gegenseitiger Pin-Blockade

Eine nahe liegende Frage an die Logik lautet: *Wenn sich zwei Signale im Quelltext gegenseitig auf demselben Pin blockieren – welches Signal darf bleiben, und welches muss weichen?*

Im Programm ist nirgends eine feste Prioritätsliste nach Namen oder Signaltypen hinterlegt. In Stufe 1 meldet die Schleife lediglich das später angetroffene Signal als Konfliktauslöser. Über die eigentliche Reparatur entscheidet in Stufe 2 allein die globale Punktezahl aus Zielfunktion (3). Daraus ergeben sich drei klar unterscheidbare Fälle:

1. **Fall 1 – Gleichwertige Einzelsignale (Gleichstand / Tie-Breaking).** Liegen etwa `BUZZER_PIN = 7` und `SERVO_PIN = 7` (beide `gpio`) auf demselben Pin, so stehen beiden dieselben 15 freien GPIOs zur Verfügung (darunter die drei Strapping-Pins `{2, 8, 9}`). Egal ob der Buzzer auf Pin 7 bleibt (+100 + 30) und der Servo auf einen Nicht-Strapping-Pin wie GPIO 10 ausweicht (+30) oder umgekehrt: Beide Lösungen erzielen exakt **160 Punkte**. Was dann passiert, wurde in Abschnitt 7.4 experimentell überprüft (Experimente `c` und `c2`): Anders als man intuitiv erwarten würde, entscheidet **nicht** die Deklarationsreihenfolge im C++-Code. Selbst wenn `SERVO_PIN` vor `BUZZER_PIN` deklariert wird, behält Z3 in beiden Fällen `BUZZER_PIN` auf GPIO 7 und verschiebt `SERVO_PIN` (einmal auf GPIO 10, im umgekehrten Test auf GPIO 20). Den Gleichstand löst also die interne Klausel- und Variablenordnung von `z3.Optimize` (MaxRes) auf. Für identische Eingaben und eine feste Z3-Version bleibt die Ausgabe aber deterministisch (fünf aufeinanderfolgende Läufe von Szenario 03 lieferten fünfmal denselben Hashwert).
2. **Fall 2 – Geteilter Bus gegen einzelnes Störsignal („Bus-Trägheit“).** In Szenario 04 sind `OLED_SDA = 6` und `BME280_SDA = 6` über `v_OLED_SDA == v_BME280_SDA` gekoppelt, während `STATUS_LED = 6` ein einzelnes `gpio`-Signal ist. Beide Bus-Geräte bringen jeweils 100 Haltepunkte ein, zusammen also **200 Punkte** gegenüber nur **100 Punkten** der LED. Da auf dem ESP32-C3 für I2C nur die Pins `{6, 7, 8, 9}` infrage kommen (davon `{8, 9}` Strapping-Pins, also maximal $+20$ Strapping-Punkte je I2C-Signal) und für `STATUS_LED` `{2, 8, 9}` als Strapping-Pins in `allowed_pins` liegen (maximal $+30$ Punkte), zeigt Tabelle 6.5 die Gesamtpunkte: Die Kopplung schützt den Bus rechnerisch.

| Variante in Szenario 04 | Haltepunkte | Strapping-Vermeidung | Gesamtsumme | Ergebnis |
| :--- | :---: | :---: | :---: | :--- |
| **A (Z3-Lösung):** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 10 | $4 \times 100 = 400$ | $4 \times 20 + 30 = 110$ | **510 Punkte** | optimal |
| **B:** Bus bleibt auf 6/7, `STATUS_LED` $\rightarrow$ 2 (Strapping) | $4 \times 100 = 400$ | $4 \times 20 + 20 = 100$ | **500 Punkte** | verworfen |
| **C:** `STATUS_LED` bleibt auf 6, SDA-Paar $\rightarrow$ 8 (Strapping) | $3 \times 100 = 300$ | $2 \times 10 + 2 \times 20 + 30 = 90$ | **390 Punkte** | verworfen |

*Tabelle 6.5: Punktebewertung in Szenario 04 (Bus gegen Einzelsignal).*

3. **Fall 3 – Spezialist gegen Allrounder (indirekte Priorität durch knappe Pins).** Kollidieren bei aktivem WLAN ein analoger Sensor (`SOIL_SENSOR = 1`, braucht `adc1` aus `{0, 1, 2, 3, 4}`) und eine LED (`STATUS_LED = 1`, `gpio`), haben zunächst beide je 100 Haltepunkte. Sind jedoch die übrigen Nicht-Strapping-ADC1-Pins `0, 3, 4` bereits durch andere Sensoren belegt, bleibt für den Spezialisten als einziger Ausweichpin nur Strapping-Pin 2. Wiche der Sensor auf Pin 2 aus und bliebe die LED auf Pin 1, verlöre das Modell 10 Strapping-Punkte; weicht hingegen die LED auf einen freien Nicht-Strapping-Pin (z. B. GPIO 7) aus und der Sensor bleibt auf GPIO 1, gewinnt diese Variante **10 Punkte** mehr. Wäre auch Pin 2 bereits belegt, erzwängen die harten Regeln den Verbleib des Spezialisten sogar absolut. Experiment `f` und `f2` in Abschnitt 7.4 bestätigen diese Herleitung unabhängig von der Deklarationsreihenfolge im Code.

### 6.6 Bericht und Reparatur-Prompt

Das Modul `mcu_validator/cli.py` (49 Zeilen, Anhang E) lädt über `validate_file` das Hardware-Profil, ruft Parser und Solver auf, formatiert den Bericht mit `format_report` und beendet den Prozess bei SAT mit Rückgabewert 0 bzw. bei UNSAT mit Rückgabewert 1.

Im `UNSAT`-Fall erzeugt `format_report` den Abschnitt `--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---`. Neben der Liste aller Einzelkonflikte enthält er für **jedes** erkannte Signal entweder `Keep GPIO <p> (unchanged)` oder `Change GPIO <alt> -> GPIO <neu>`. Die expliziten `Keep`-Zeilen sind bewusst gesetzt: Gibt man einem Sprachmodell nur eine abstrakte Fehlerliste, ändert es erfahrungsgemäß oft auch unbeteiligte Konstanten ab.

Die Paketdatei `mcu_validator/__init__.py` exportiert ausschließlich `parse_cpp_file`, `load_board_data` und `validate_with_z3` – nicht aber `.cli` (INV-06). Würde `__init__.py` das Submodul `.cli` bereits importieren, befände sich `mcu_validator.cli` beim Aufruf `python -m mcu_validator.cli` bereits in `sys.modules`, bevor Pythons `runpy`-Lader es als Hauptskript ausführt, was eine `RuntimeWarning` auslöst.

### 6.7 Integration in PlatformIO

Um `mcu-pin-solver` mit minimalem Aufwand in beliebige PlatformIO-Projekte einzubinden, wird das Werkzeug nicht über manuell kopierte Skripte, sondern als PlatformIO-Bibliothek verteilt (`dmatheja/mcu-pin-solver` in Version `0.1.0`). Listing 6.6 zeigt den wesentlichen Teil des Pre-Build-Hooks `pio_hook.py` und die Build-Steuerung in `library.json`.

```python
# --- Auszug aus pio_hook.py (Z. 9–42) ---
if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True

    hook_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))

    python_cmd = shutil.which("py") or sys.executable

    check_deps = subprocess.run(
        [python_cmd, "-c", "import z3, tree_sitter, tree_sitter_cpp"],
        capture_output=True,
    )
    if check_deps.returncode != 0:
        print("\n>>> [MCU-Validator] Installing dependencies (first-time setup)...")
        subprocess.run(
            [python_cmd, "-m", "pip", "install", "z3-solver", "tree-sitter", "tree-sitter-cpp"],
            check=True,
        )

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = str(hook_dir) + os.pathsep + run_env.get("PYTHONPATH", "")
    result = subprocess.run(
        [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id],
        env=run_env,
    )
    if result.returncode != 0:
        print("\n>>> BUILD STOPPED: Please fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)
```
```json
  // --- Auszug aus library.json (Z. 19–33) ---
  "export": {
    "include": [
      "boards/*.json",
      "mcu_validator/*.py",
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

Vier Details lösen typische Schwierigkeiten im Build-Alltag:
1. **`_MCU_VALIDATOR_RAN`:** Da das zugrunde liegende SCons-Skript in einem Build-Lauf mehrfach ausgewertet werden kann, verhindert dieses Flag auf `env` eine doppelte Prüfung.
2. **Interpreter-Wahl und Erstinstallation:** PlatformIO nutzt intern eine eigene Python-Umgebung (`penv`). `shutil.which("py") or sys.executable` greift unter Windows auf den regulären Python-Launcher zurück und installiert die drei Abhängigkeiten (`z3-solver`, `tree-sitter`, `tree-sitter-cpp`) beim ersten Start automatisch nach.
3. **`"srcFilter": ["-<*>"]`:** Die Bibliothek enthält unter `src/main.cpp` ein eigenes ESP32-C3-Demoprojekt. Ohne diesen Filter würde PlatformIO bei Fremdprojekten (etwa für einen STM32) versuchen, dieses Demoprojekt als Bibliotheksquelltext mitzukompilieren.
4. **`"export": { "include": [...] }`:** Begrenzt Registry-Pakete auf die zur Laufzeit nötigen Dateien und schließt Test- und Demo-Ordner aus.

---

## 7 Evaluation

Dieses Kapitel überprüft das fertige System empirisch. Anders als ein reiner Regressionstest der eigenen Testsuite umfasst die Evaluation drei Säulen: (1) die automatisierte Testsuite des Repositories, (2) zwölf eigene Grenzfallexperimente zur gezielten Suche nach Schwachstellen sowie (3) getrennte Laufzeitmessungen.

### 7.1 Evaluationsdesign und Messumgebung

Die Regressionstests (`tests/run_tests.py`) starten für jeden der neun Fälle den CLI-Einstiegspunkt `python -m mcu_validator.cli` in einem eigenen Subprozess und prüfen den Rückgabewert (0 für SAT, 1 für UNSAT). Ergänzend führt das eigens erstellte Versuchsskript `experiments.py` (Anhang G) zwölf gezielte Grenzfallsketche plus zwei synthetische Tests über die Python-Schnittstelle aus, um zu ermitteln, in welchen Fällen False Positives, False Negatives oder unerwartete Solver-Entscheidungen auftreten. Das Skript `timing.py` (Anhang G) misst schließlich sowohl die gesamte Wanduhr-Laufzeit eines CLI-Subprozesses (Median über $N = 10$ Läufe) als auch die reinen Ausführungszeiten der drei Phasen Laden, Parsen und Lösen im selben Prozess (Median über $M = 30$ Läufe). Alle Messungen erfolgten unter der in Tabelle 7.1 dokumentierten Umgebung.

| Komponente | Spezifikation |
| :--- | :--- |
| Prozessor | AMD Ryzen 9 3900X 12-Core Processor |
| Betriebssystem (lokal) | Microsoft Windows 10 Pro |
| Python-Version (lokal) | Python `3.14.7` |
| Solver und Parser | `z3-solver` `5.4.1.0` (Z3 `5.4.1`), `tree-sitter` `0.26.1`, `tree-sitter-cpp` `0.23.4` |
| CI-Umgebung | GitHub Actions (`ubuntu-latest`), Python `3.12` (`.github/workflows/ci.yml`) |
| PlatformIO CLI (`pio`) | auf der lokalen Messmaschine nicht im Suchpfad installiert |

*Tabelle 7.1: Messumgebung.*

### 7.2 Regressionsszenarien

Die Ausführung von `python tests/run_tests.py` bestand alle neun definierten Szenarien ohne Fehler (`9/9 tests passed!`, Rückgabewert 0). Tabelle 7.2 listet alle Fälle im Überblick.

| Nr. | Zielpfad | Board | Erwartet & Gemessen | Geprüfter Sachverhalt |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `src/main.cpp` | `esp32-c3` | SAT | Demo-Sketch mit `STATUS_LED = 8` (Strapping), `SOIL_SENSOR = 1`, `WiFi.softAP`, `Serial.begin`, `unsigned long counter = 0` |
| 2 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1 und 2: Flash-Pin 12 und `ADC2` (Pin 5) bei aktivem WLAN |
| 3 | `tests/scenarios/00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | Identischer Code auf ESP32-S3 gültig (Pin 12 normal, Pin 5 in `ADC1`) |
| 4 | `tests/scenarios/01_valid_sketch.cpp` | `esp32-c3` | SAT | Positivkontrolle: fehlerfreier Sketch mit WLAN und USB-Serial |
| 5 | `tests/scenarios/02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 2: `Serial.begin` sperrt USB-Pins 18 und 19 |
| 6 | `tests/scenarios/03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | Fehlerklassen 1, 3, 4: Doppelbelegung (7), Geister-Pin (32), fehlendes ADC (6) |
| 7 | `tests/scenarios/04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | Fehlerklasse 4: I2C-Bus auf 6/7 bleibt erhalten, LED auf 6 weicht aus |
| 8 | `tests/scenarios/05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | AST ignoriert `WiFi.begin(...)` in Kommentar und Zeichenkette |
| 9 | `tests/scenarios/06_multi_file_project/src` | `esp32-c3` | UNSAT | Mehrere Dateien: `include/pins.h` + `src/main.cpp` + `src/sensors.cpp` |

*Tabelle 7.2: Ergebnisse der Regressionsszenarien.*

### 7.3 Ausgewählte Szenarien im Detail

Szenario 0 wurde bereits in Abschnitt 5.6 behandelt. Die Listings 7.1 bis 7.5 dokumentieren den vollständigen Quelltext und die tatsächliche CLI-Ausgabe der Szenarien 02 bis 06.

In **Szenario 02** (Listing 7.1) aktiviert `Serial.begin(115200)` das Modul `usb_serial`, wodurch GPIO 18 und 19 für den Schrittmotor gesperrt sind. `ENABLE_PIN` auf GPIO 6 bleibt unverändert, während `STEP_PIN` und `DIR_PIN` auf GPIO 21 und 1 verlegt werden.

```cpp
#include <Arduino.h>

// SCENARIO 2: USB-Serial blocks GPIO 18 and 19 on ESP32-C3 (expected: UNSAT)
#define STEP_PIN 18          // Error: GPIO 18 is USB D- (conflicts with Serial.begin)
#define DIR_PIN 19           // Error: GPIO 19 is USB D+ (conflicts with Serial.begin)
const int ENABLE_PIN = 6;    // Valid free GPIO (should be preserved by Z3)

void setup() {
    Serial.begin(115200);    // Activates 'usb_serial' -> blocks GPIO 18 & 19

    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(ENABLE_PIN, OUTPUT);
}

void loop() {
    digitalWrite(STEP_PIN, HIGH);
}
```
```text
=================================================================
 Checked File   : tests/scenarios/02_usb_serial_conflict.cpp (ESP32-C3)
 Active Modules : ['usb_serial']
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STEP_PIN (GPIO 18): Conflicts with active ['usb_serial'] (USB D-).
  - DIR_PIN (GPIO 19): Conflicts with active ['usb_serial'] (USB D+).

Please regenerate the code using this exact Z3-verified pin assignment:
  - STEP_PIN: Change GPIO 18 -> GPIO 21
  - DIR_PIN: Change GPIO 19 -> GPIO 1
  - ENABLE_PIN: Keep GPIO 6 (unchanged)

-----------------------------------------------------
```
*Listing 7.1: Szenario 02 (`tests/scenarios/02_usb_serial_conflict.cpp`) und Ausgabe (Rückgabewert 1).*

**Szenario 03** (Listing 7.2) prüft drei verschiedene Fehler in einem Programm: Doppelbelegung auf GPIO 7, nicht existierendes GPIO 32 und fehlendes `adc` auf GPIO 6. Da kein WLAN aktiv ist, ist GPIO 5 (`adc2`) als digitaler Ausgang erlaubt und nimmt `SERVO_PIN` auf, während `POTI_PIN` auf `ADC1` (GPIO 0) gelegt wird.

```cpp
#include <Arduino.h>

// SCENARIO 3: Duplicate pin, nonexistent pin, and missing ADC capability (expected: UNSAT)
#define BUZZER_PIN 7         // Valid pin, but collides with SERVO_PIN
#define SERVO_PIN 7          // Error 1: Duplicate assignment on GPIO 7
const int PIR_SENSOR = 32;   // Error 2: GPIO 32 does not exist on ESP32-C3
const int POTI_PIN = 6;      // Error 3: GPIO 6 has no ADC capability

void setup() {
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(SERVO_PIN, OUTPUT);
    pinMode(PIR_SENSOR, INPUT);
}

void loop() {
    int pot = analogRead(POTI_PIN);
    digitalWrite(BUZZER_PIN, HIGH);
}
```
```text
=================================================================
 Checked File   : tests/scenarios/03_duplicate_and_invalid_pin.cpp (ESP32-C3)
 Active Modules : []
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - SERVO_PIN (GPIO 7): Duplicate assignment with BUZZER_PIN.
  - PIR_SENSOR (GPIO 32): Pin does not exist on ESP32-C3.
  - POTI_PIN (GPIO 6): Does not support capability 'adc'.

Please regenerate the code using this exact Z3-verified pin assignment:
  - BUZZER_PIN: Keep GPIO 7 (unchanged)
  - SERVO_PIN: Change GPIO 7 -> GPIO 5
  - PIR_SENSOR: Change GPIO 32 -> GPIO 1
  - POTI_PIN: Change GPIO 6 -> GPIO 0

-----------------------------------------------------
```
*Listing 7.2: Szenario 03 (`tests/scenarios/03_duplicate_and_invalid_pin.cpp`) und Ausgabe (Rückgabewert 1).*

**Szenario 04** (Listing 7.3) belegt den in Abschnitt 6.5 hergeleiteten Effekt der Bus-Trägheit: `OLED_SDA` und `BME280_SDA` teilen sich GPIO 6, `OLED_SCL` und `BME280_SCL` teilen sich GPIO 7. Alle vier Bus-Pins bleiben unverändert, einzig `STATUS_LED` wird auf GPIO 10 verlegt. *(Zu beachten ist, dass `BME280_SDA` und `BME280_SCL` im Beispiel nicht explizit an `Wire.begin` übergeben werden; der Parser stuft sie über den `SDA`/`SCL`-Fallback als `i2c` ein, da `Wire` im Programm verwendet wird.)*

```cpp
#include <Arduino.h>
#include <Wire.h>

// SCENARIO 4: Shared I2C bus (OLED + BME280 on GPIO 6/7 is valid), but STATUS_LED collides on GPIO 6
#define OLED_SDA 6           // Valid: I2C SDA shared with BME280_SDA
#define OLED_SCL 7           // Valid: I2C SCL shared with BME280_SCL
#define BME280_SDA 6         // Valid: Shared I2C bus line on GPIO 6
#define BME280_SCL 7         // Valid: Shared I2C bus line on GPIO 7
#define STATUS_LED 6         // Error: Standard GPIO cannot share GPIO 6 with I2C SDA!

void setup() {
    Wire.begin(OLED_SDA, OLED_SCL);
    pinMode(STATUS_LED, OUTPUT);
}

void loop() {
    digitalWrite(STATUS_LED, HIGH);
}
```
```text
=================================================================
 Checked File   : tests/scenarios/04_shared_i2c_bus.cpp (ESP32-C3)
 Active Modules : []
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 6): Duplicate assignment with OLED_SDA.

Please regenerate the code using this exact Z3-verified pin assignment:
  - OLED_SDA: Keep GPIO 6 (unchanged)
  - OLED_SCL: Keep GPIO 7 (unchanged)
  - BME280_SDA: Keep GPIO 6 (unchanged)
  - BME280_SCL: Keep GPIO 7 (unchanged)
  - STATUS_LED: Change GPIO 6 -> GPIO 10

-----------------------------------------------------
```
*Listing 7.3: Szenario 04 (`tests/scenarios/04_shared_i2c_bus.cpp`) und Ausgabe (Rückgabewert 1).*

**Szenario 05** (Listing 7.4) bestätigt den Schutz vor Fehlalarmen durch Kommentare und Zeichenketten: Obwohl `WiFi.begin` zweimal im Quelltext steht, erkennt der AST keine aktiven Module (`[]`) und lässt GPIO 5 (`adc2`) zu.

```cpp
#include <Arduino.h>

// SCENARIO 5: AST parser test - WiFi.begin only appears in comments and strings!
// A naive regex/substring parser would falsely detect 'wifi' as active and reject GPIO 5 (ADC2).
// Because WiFi is NOT actually called in the AST, GPIO 5 (ADC2) is completely valid here (SAT).
// WiFi.begin("FakeCommentWiFi", "12345678");

const int SOIL_SENSOR = 5;   // Valid ADC2 pin when Wi-Fi is not active

void setup() {
    Serial.println("Note: Do not call WiFi.begin() when reading ADC2 on GPIO 5");
}

void loop() {
    int reading = analogRead(SOIL_SENSOR);
}
```
```text
=================================================================
 Checked File   : tests/scenarios/05_ast_ignores_strings_and_comments.cpp (ESP32-C3)
 Active Modules : []
=================================================================
 RESULT: SAT (All pins valid! No hardware conflicts detected.)
```
*Listing 7.4: Szenario 05 (`tests/scenarios/05_ast_ignores_strings_and_comments.cpp`) und Ausgabe (Rückgabewert 0).*

**Szenario 06** (Listing 7.5) prüft ein verteiltes Projekt: Die Pin-Definitionen stehen in `include/pins.h`, der WLAN-Aufruf in `src/main.cpp` und `analogRead(SOIL_SENSOR)` in `src/sensors.cpp`. Der Parser führt alle drei Dateien zusammen. Da `Serial.begin` in diesem Projekt fehlt, darf `STATUS_LED` auf GPIO 18 ausweichen.

```cpp
// --- include/pins.h ---
#pragma once
#define STATUS_LED 12        // Conflicts with ESP32-C3 internal SPI flash
const int SOIL_SENSOR = 5;   // ADC2 pin: conflicts when another .cpp calls WiFi.begin

// --- src/main.cpp ---
#include <Arduino.h>
#include <WiFi.h>
#include "pins.h"
int readSoilMoisture();
void setup() {
    pinMode(STATUS_LED, OUTPUT);
    WiFi.begin("MySSID", "MyPassword");
}
void loop() {
    digitalWrite(STATUS_LED, HIGH);
    readSoilMoisture();
    delay(1000);
}

// --- src/sensors.cpp ---
#include <Arduino.h>
#include "pins.h"
int readSoilMoisture() {
    return analogRead(SOIL_SENSOR);
}
```
```text
=================================================================
 Checked File   : tests/scenarios/06_multi_file_project/src (ESP32-C3)
 Active Modules : ['wifi']
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - STATUS_LED (GPIO 12): Reserved pin! (Internal SPI flash (SPIIO4))
  - SOIL_SENSOR (GPIO 5): Conflicts with active ['wifi'] (ADC2 conflicts with Wi-Fi).

Please regenerate the code using this exact Z3-verified pin assignment:
  - STATUS_LED: Change GPIO 12 -> GPIO 18
  - SOIL_SENSOR: Change GPIO 5 -> GPIO 0

-----------------------------------------------------
```
*Listing 7.5: Szenario 06 (`tests/scenarios/06_multi_file_project`) und Ausgabe (Rückgabewert 1).*

### 7.4 Grenzfallexperimente

Während die Regressionssuite den angedachten Gut- und Fehlerfall prüft, untersucht `experiments.py` gezielt Konstrukte, bei denen das System an Grenzen stoßen könnte. Tabelle 7.3 fasst die Ergebnisse aller 13 Testfälle (12 C++-Beispiele plus die zweite Variante des Leere-Domänen-Tests `e`) auf dem Profil `esp32-c3` zusammen.

| ID | Getesteter Fall | Beobachtetes Ergebnis | Einordnung |
| :--- | :--- | :--- | :--- |
| `a` | Direkte Zahlen (`pinMode(12, OUTPUT); analogRead(5);`) bei aktivem `WiFi` | `requests = []`, `SAT` | **False Negative** (beide Fehler übersehen) |
| `b` | Lokale Zähler in `loop()` (`int blinkCount = 0; uint8_t retries = 12;`) | `blinkCount` (Pin 0) und `retries` (Pin 12) extrahiert $\rightarrow$ `UNSAT` | **False Positive** |
| `c`, `c2` | Gleichstand `BUZZER_PIN = 7` / `SERVO_PIN = 7` in beiden Deklarationsreihenfolgen | In **beiden** Fällen bleibt `BUZZER_PIN` auf `7` (`SERVO_PIN -> 20` bzw. `10`) | Widerlegt reine Reihenfolge-Annahme |
| `d` | 6 Analogsensoren `S0..S5` mit WLAN (nur 5 `ADC1`-Pins vorhanden) | `UNSAT`, `suggested = {}` (`GPIO None` für alle 6 Sensoren) | Schubfachprinzip nicht erklärt |
| `e` | Synthetische Fähigkeit `'can'` ohne passende Pins ($P_i = \emptyset$) + `LED = 12` | Bei 1 unlösbarem Signal: `CAN_TX: -1, LED: 10`; bei 2 unlösbaren: `suggested = {}` | `-1 != -1`-Fehler ab zwei unlösbaren Signalen |
| `f`, `f2` | `SOIL_SENSOR = 1` (`adc`) vs. `STATUS_LED = 1` (`gpio`) bei belegten `0, 3, 4`, beide Reihenfolgen | In **beiden** Fällen bleibt `SOIL_SENSOR` auf `1`, `STATUS_LED -> 7` | Bestätigt Spezialist-Priorität (Fall 3) |
| `h` | Doppelrolle: `Wire.begin(MY_PIN, MY_SCL)` und `analogRead(MY_PIN)` auf GPIO 6 | Nur `'adc'` zugewiesen; Vorschlag `MY_PIN -> 5` (Pin 5 kann kein I2C!) | **Fehlerhafter Vorschlag** durch `if/elif`-Schatten |
| `i` | `constexpr int LED_A = 12;`, `static const uint8_t LED_B = 13;`, `const gpio_num_t LED_C = GPIO_NUM_14;` | `LED_A` und `LED_B` erkannt (`UNSAT`), `LED_C` ignoriert | Teilweise Lücke bei ESP-IDF-Typen (`gpio_num_t`) |
| `j` | `#ifdef USE_EXTERNAL_LED` (Pin 2) / `#else` (Pin 12) | Beide Zweige gelesen; `STATUS_LED (datei) = 12` $\rightarrow$ `UNSAT` | **False Positive** bei Alternativ-Konfigurationen |
| `k` | `Wire.begin(SDA_A, SCL_A)` und `Wire1.begin(SDA_B, SCL_B)` beide auf GPIO 6/7 | Alle 4 Pins als `'i2c'` eingestuft $\rightarrow$ `SAT` | **False Negative** bei zwei getrennten I2C-Controllern |
| `l` | Zwei `SPI.begin`-Aufrufe mit `MISO_P = 7`, `CS_A = 7`, `CS_B = 7` | Alle Argumente als teilbar `'spi'` eingestuft $\rightarrow$ `SAT` | **False Negative** bei SPI-Chip-Select (`CS`) |

*Tabelle 7.3: Ergebnisse der Grenzfallexperimente auf `esp32-c3`.*

Listing 7.6 zeigt zur Verdeutlichung die tatsächliche CLI-Ausgabe im Überbuchungsfall `d` (`pigeonhole.cpp`): Weil sechs paarweise verschiedene Signale nicht auf fünf `ADC1`-Pins passen, liefert `opt.check()` in Z3 `unsat`, `suggested` bleibt leer `{}`, und `format_report` gibt für jedes Signal `GPIO None` aus – für das Sprachmodell keine brauchbare Reparaturanweisung.

```text
=================================================================
 Checked File   : C:\Users\D\.gemini\antigravity\brain\cb7b3c15-e350-49bb-8c87-0df89cb1d937\scratch\pigeonhole.cpp (ESP32-C3)
 Active Modules : ['wifi']
=================================================================
 RESULT: UNSAT (Hardware conflicts detected!)

--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---

Your C++ code for the ESP32-C3 contains the following hardware errors:
  - S5 (GPIO 5): Conflicts with active ['wifi'] (ADC2 conflicts with Wi-Fi).

Please regenerate the code using this exact Z3-verified pin assignment:
  - S0: Change GPIO 0 -> GPIO None
  - S1: Change GPIO 1 -> GPIO None
  - S2: Change GPIO 3 -> GPIO None
  - S3: Change GPIO 4 -> GPIO None
  - S4: Change GPIO 2 -> GPIO None
  - S5: Change GPIO 5 -> GPIO None

-----------------------------------------------------
```
*Listing 7.6: Ausgabe bei überbuchten ADC-Pins (Grenzfall `d`, `pigeonhole.cpp`, Rückgabewert 1).*

### 7.5 Laufzeitmessung

Tabelle 7.4 dokumentiert die gemessenen Medianlaufzeiten aus `timing.py`. Zum Vergleich wurde zunächst als Basislinie allein der Start des Python-Interpreters samt Import der drei Pakete (`python -c "import z3, tree_sitter, tree_sitter_cpp"`) zehnmal gemessen; der Median lag bei **138 ms**.

| Szenario | Board | Ergebnis | E2E Median ($N=10$) | Laden ($M=30$) | Parsen ($M=30$) | Lösen ($M=30$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `src/main.cpp` | `esp32-c3` | SAT | 149 ms | 0,23 ms | 0,89 ms | 0,01 ms |
| `00_flash_and_wifi_conflict.cpp` | `esp32-c3` | UNSAT | 170 ms | 0,31 ms | 0,42 ms | 14,06 ms |
| `00_flash_and_wifi_conflict.cpp` | `esp32-s3` | SAT | 152 ms | 0,25 ms | 0,38 ms | 0,02 ms |
| `01_valid_sketch.cpp` | `esp32-c3` | SAT | 148 ms | 0,22 ms | 0,38 ms | 0,01 ms |
| `02_usb_serial_conflict.cpp` | `esp32-c3` | UNSAT | 171 ms | 0,36 ms | 0,39 ms | 17,69 ms |
| `03_duplicate_and_invalid_pin.cpp` | `esp32-c3` | UNSAT | 178 ms | 0,35 ms | 0,40 ms | 22,36 ms |
| `04_shared_i2c_bus.cpp` | `esp32-c3` | UNSAT | 168 ms | 0,32 ms | 0,33 ms | 15,06 ms |
| `05_ast_ignores_strings_and_comments.cpp` | `esp32-c3` | SAT | 146 ms | 0,22 ms | 0,24 ms | 0,01 ms |
| `06_multi_file_project/src` | `esp32-c3` | UNSAT | 164 ms | 0,28 ms | 1,54 ms | 8,86 ms |

*Tabelle 7.4: Gemessene Laufzeiten (End-to-End als Subprozess sowie je Verifikationsphase im selben Prozess).*

Die Messwerte bestätigen zwei Entwurfsannahmen deutlich:
- **Geringer Zusatzaufwand im Build:** Jeder Aufruf bleibt unter 0,18 s und damit weit unter dem Zielwert aus NFA-02 (`< 1,0 s`). Rund 80 bis 90 % der End-to-End-Zeit (138 ms von 146–178 ms) entfallen auf den Start des Python-Prozesses und das Laden der nativen Bibliotheken.
- **Wirksamkeit der Zweistufigkeit:** Bei allen `SAT`-Szenarien benötigt die eigentliche Prüfung (`Lösen`) 0,01–0,02 ms, weil Z3 gar nicht gestartet wird. Bei den `UNSAT`-Szenarien liegt die Z3-Optimierung bei 8,86–22,36 ms; das Parsen bleibt selbst über die drei Dateien von Szenario 06 bei 1,54 ms.

### 7.6 Soll-Ist-Abgleich

Tabelle 7.5 prüft alle in Kapitel 4 gestellten Anforderungen und Invarianten anhand der tatsächlichen Befunde.

| ID | Anforderung / Invariante | Status | Begründung / Einschränkung |
| :--- | :--- | :---: | :--- |
| FA-01 | Hardware-Profil laden | erfüllt | `load_board_data` löst `esp32-c3` und `esp32-s3` korrekt auf (Szenarien 2 und 3) |
| FA-02 | Mehrere Dateien | erfüllt | `_resolve_source_files` liest `include/` + `src/` (Szenario 9) |
| FA-03 | Fehlalarmfreie Extraktion | teilweise erfüllt | Schließt Kommentare, Strings und `for`-Köpfe aus (Szenario 8), erfasst aber lokale `int`-Zähler und beide `#ifdef`-Zweige (`b`, `j`) und übersieht direkte Zahlen (`a`) sowie `gpio_num_t` (`i`) |
| FA-04 | Widersprüchliche Definitionen | erfüllt | `_record_pin` trennt abweichende Werte über Dateinamen-Zusatz (belegt in `j`) |
| FA-05 | Fähigkeiten und Module | teilweise erfüllt | `gpio`, `adc`, `i2c` und `wifi`/`usb_serial` greifen; bei Doppelrolle verdeckt erste Fähigkeit die zweite (`h`); `pwm`/`spi`/`uart` sind implementiert, aber nicht durch Regressionstests abgedeckt |
| FA-06 | Diagnose | erfüllt | Meldet bis zu drei Fehler gleichzeitig im Klartext (Szenario 6), mit der Unschärfe, dass `active_resources` als Gesamtliste ausgegeben wird |
| FA-07 | Kollision vs. Bus | teilweise erfüllt | Schützt geteiltes I2C (Szenario 7), trennt aber weder `CS`/`SS` von `SPI`-Datenleitungen (`l`) noch `Wire` von `Wire1` (`k`) |
| FA-08 | Minimale Reparatur | teilweise erfüllt | Optimal für gültige Probleminstanzen (Szenarien 2, 5, 6, 7, 9); bei Überbuchung (`d`) oder zwei unlösbaren Signalen (`e`) entsteht jedoch `GPIO None` |
| FA-09 | Reparatur-Prompt | erfüllt | Gibt Diagnose sowie vollständige `Keep`/`Change`-Liste aus |
| FA-10 | Build-Schranke und CLI | CLI erfüllt / Hook nicht lokal getestet | CLI und `library.json` geprüft; `pio` war auf der Messmaschine nicht installiert (Build-Schranke nur per Code-Inspektion in `pio_hook.py` und früheren Projektläufen belegt) |
| NFA-01–NFA-07 | Qualitätsanforderungen | erfüllt | 0 chip-spezifische Einträge im Python-Code, E2E < 0,18 s, 337/379 Zeilen Python, `runpy`-frei, CI mit Python `3.12` vorhanden |
| INV-01–INV-06 | Architektur-Invarianten | erfüllt | Alle sechs Invarianten im aktuellen Codebestand eingehalten |

*Tabelle 7.5: Soll-Ist-Abgleich.*

### 7.7 Gültigkeit der Ergebnisse

Für die wissenschaftliche Bewertung sind die Grenzen der Aussagekraft (*Threats to Validity*) offen zu benennen:

- **Interne Gültigkeit.** Prozess-Startzeiten unter Windows schwanken durch Hintergrundprozesse und Festplatten-Cache. Durch zehn bzw. dreißig Wiederholungen, Auswertung des Medians sowie die Trennung in End-to-End- und In-Process-Zeiten ist dieser Einfluss kontrolliert.
- **Externe Gültigkeit.** Alle neun Regressionsszenarien und zwölf Grenzfalltests wurden vom Verfasser erstellt. Es liegt bislang **kein** empirischer Vergleich über eine größere Stichprobe frei von Sprachmodellen erzeugter Embedded-Projekte (z. B. mit Messung der Erfolgsquote mit vs. ohne `mcu-pin-solver`) vor. Außerdem sind bisher nur zwei Espressif-Chips modelliert; weitere Architekturen wie RP2040 oder STM32 sind nur konzeptionell vorbereitet.
- **Konstruktgültigkeit.** Das Ergebnis `SAT` beweist nur, dass die vom Parser extrahierten Signale gegen das hinterlegte JSON-Profil zulässig sind – nicht, dass der C++-Code im Übrigen frei von Pin-Fehlern oder elektrischen Problemen ist.

---
## 8 Diskussion, Grenzen und Ausblick

### 8.1 Diskussion der Ergebnisse

Die Evaluation bestätigt die Tragfähigkeit der gewählten neuro-symbolischen Arbeitsteilung: Ohne installierten Cross-Compiler und ohne eigene Konfigurationsdateien im Nutzerprojekt findet `mcu-pin-solver` die fünf definierten Fehlerklassen projektweit über Header und Quelldateien hinweg. Mit einer End-to-End-Laufzeit zwischen 146 ms und 178 ms (davon unter 2 ms im `SAT`-Fall und rund 9 bis 23 ms bei Z3-Optimierung) bleibt der Eingriff im Build-Alltag praktisch unbemerkt. Ebenso belegt der Vergleich von Szenario 0 auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`), dass sich die Prüfregeln sauber von der Programmlogik trennen lassen.

Gleichzeitig zeigen die Grenzfallexperimente den Preis der Entwurfsentscheidungen aus Kapitel 5. Weil bewusst auf `tree-sitter-cpp` ohne Präprozessor und ohne Typauflösung eines Compilers gesetzt wurde, bleiben Konstrukte außerhalb des schmalen syntaktischen Suchmusters unberücksichtigt oder werden fehlinterpretiert. Diese Lücken sind keine zufälligen Programmierfehler, sondern unmittelbare Folgen des Kompromisses zwischen Portabilität (`NFA-03`), Kompaktheit (`NFA-07`) und semantischer Tiefe.

### 8.2 Grenzen des Systems

Auf Basis von Code-Inspektion und den Experimenten aus Abschnitt 7.4 lassen sich acht konkrete Systemgrenzen benennen (Tabelle 8.1):

1. **Direkte Zahlenliterale (*Magic Numbers*).** Da der Parser in `call_expression` nur `identifier`-Knoten sammelt, bleiben Aufrufe wie `pinMode(12, OUTPUT);` oder `analogRead(5);` ohne Konstante völlig unbemerkt (`a_magic_numbers`, False Negative).
2. **Lokale `int`-Zähler und unberücksichtigte Deklarationstypen.** Eine gewöhnliche Zählervariable wie `int blinkCount = 0;` oder `uint8_t retries = 12;` außerhalb eines `for`-Kopfes erfüllt alle AST-Bedingungen und wird als Pin gewertet (`b_local_counter`, False Positive; in `src/main.cpp` blieb `counter` lediglich dank `unsigned long` außen vor). Umgekehrt werden `gpio_num_t`, Pin-Arrays (`int pins[] = {...}`), `enum`-Definitionen sowie berechnete Makros wie `#define LED (BASE + 2)` nicht aufgelöst (`i_constexpr_and_gpio_num_t`).
3. **Präprozessor-Verzweigungen (`#ifdef` / `#else`).** Tree-Sitter führt keinen Präprozessor aus und besucht alle Zweige im Baum. Alternative Pin-Belegungen für verschiedene Board-Varianten innerhalb einer `#ifdef`-Weiche erscheinen daher gleichzeitig als widersprüchliche Pin-Definitionen (`j_ifdef_both_branches`, False Positive).
4. **Pin-Übergabe in Klassenkonstruktoren.** Treiberobjekte wie `DHT dht(DHT_PIN, DHT22);` oder `Adafruit_SSD1306 display(..., OLED_RESET);` übergeben Pins bereits bei der Deklaration. Weil der Parser keine Konstruktor-Fähigkeiten zuordnet, werden solche Signale pauschal nur als `gpio` geprüft.
5. **Rollen-Überdeckung durch die `if/elif`-Kaskade.** Die Zuordnung in `parser.py` vergibt für jedes Pin-Symbol genau eine Fähigkeit in fester Priorität (`adc` vor `pwm` vor `i2c` vor `spi` vor `uart` vor `gpio`). Wird ein Symbol fälschlich doppelt verwendet – etwa in `Wire.begin(MY_PIN, MY_SCL)` und `analogRead(MY_PIN)` –, verdeckt `adc` die I2C-Rolle, und Z3 kann einen ungeeigneten Ersatz-Pin ohne I2C vorschlagen (`h_role_shadowing`).
6. **SPI-Chip-Select (`CS`/`SS`) und getrennte Bus-Controller (`Wire` vs. `Wire1`).** Alle Argumente von `SPI*.begin(...)` erhalten dieselbe teilbare Fähigkeit `spi`. Während sich Takt (`SCK`) und Daten (`MISO`, `MOSI`) teilen lassen, muss eine Chip-Select-Leitung je Gerät exklusiv bleiben (`l_spi_two_cs_same_pin`). Ebenso unterscheidet der Solver bei `i2c`-Signalen nicht, zu welchem Bus-Controller sie gehören, sodass zwei getrennte I2C-Instanzen (`Wire` und `Wire1`) fälschlich auf denselben Pins akzeptiert werden (`k_wire_vs_wire1_same_pin`).
7. **Schubfachprinzip und der `-1 != -1`-Randfall in `solver.py`.** Übersteigt die Zahl der Signale die verfügbaren Pins einer Spezialkategorie (z. B. sechs Analogsensoren bei aktivem WLAN auf fünf `ADC1`-Pins, `d_pigeonhole_6_adc_wifi`), liefert Z3 berechtigterweise `unsat` und `suggested = {}` (`GPIO None` für alle Signale), ohne auf die ausgeschöpfte Hardware-Kapazität hinzuweisen. Ähnliches geschieht schon bei *zwei* unmöglichen Signalen mit leerer Kandidatenmenge ($P_A = P_B = \emptyset$): Weil Zeile 88 beide fest auf `-1` setzt, die Paar-Schleife aber weiterhin `var_a != var_b` verlangt (`e_empty_domain`), kippt das gesamte Modell in `unsat`, und selbst reparierbare übrige Pins verlieren ihren Vorschlag.
8. **Abdeckung und Vereinfachung in den JSON-Profilen.** Bisher liegen nur Profile für **ESP32-C3** und **ESP32-S3** vor. Außerdem fehlen Schema-Felder für reine Eingangs-Pins (`input_only`, z. B. GPIO 34–39 beim klassischen ESP32), Kanalbudgets (maximale Anzahl gleichzeitiger PWM-Kanäle) und elektrische Beschaltungsvorgaben an Strapping-Pins. Zudem vereinfacht jedes Profil die Hardware-Realität: Wie ein Blick in die aktuelle ESP-IDF-Dokumentation zeigt [[9]](#ref-9), ist `ADC2` auf dem ESP32-C3 im neueren `adc_oneshot`-Treiber aufgrund von Hardware-Instabilitäten sogar unabhängig von WLAN standardmäßig deaktiviert und erfordert zur Nutzung das explizite Kconfig-Flag `CONFIG_ADC_ONESHOT_FORCE_USE_ADC2_ON_C3`. Ein JSON-Profil, das `ADC2` nur bei aktivem WLAN sperrt, bildet diese Treiber- bzw. Silizium-Einschränkung noch nicht ab.

| Nr. | Grenze | Ort im System | Beleg (Abschnitt 7.4) | Auswirkung | Möglicher Lösungsansatz |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Direkte Zahlen (*Magic Numbers*) | `parser.py` | Experiment `a` | False Negative | `number_literal`-Argumente mit Zeilenposition erfassen |
| 2 | Lokale Zähler & fehlende Typen | `parser.py` | Experiment `b`, `i` | False Positive bzw. Negative | Variablen innerhalb von Funktionen nur bei Nutzung in Pin-Aufrufen zählen; `gpio_num_t` ergänzen |
| 3 | `#ifdef` / `#else`-Zweige | `parser.py` | Experiment `j` | False Positive | Aktive Makro-Zweige filtern oder getrennt prüfen |
| 4 | Klassenkonstruktoren | `parser.py` | Code-Inspektion | Nur `gpio`-Prüfung | Bekannte Konstruktor-Muster in Fähigkeitszuordnung aufnehmen |
| 5 | Rollen-Überdeckung (`if/elif`) | `parser.py` | Experiment `h` | Falscher Ersatzvorschlag | Fähigkeiten pro Symbol als Menge statt Einzelwert führen |
| 6 | SPI-`CS` und `Wire` vs. `Wire1` | `parser.py` / `solver.py` | Experiment `k`, `l` | False Negative | Viertes `SPI.begin`-Argument exklusiv markieren; Bus-Instanz mitführen |
| 7 | Überbuchung & `-1 != -1` | `solver.py` / `cli.py` | Experiment `d`, `e` | `GPIO None` im Prompt | Unmögliche Signale ($P_i = \emptyset$) vom Paar-Distinct ausnehmen; Vorab-Kapazitätsprüfung |
| 8 | Schema & Chip-Abdeckung | `boards/*.json` | ESP-IDF-Doku [[9]](#ref-9) | Nur C3/S3; fehlende `input_only`/Errata | Schema rückwärtskompatibel um `.get(...)`-Felder erweitern |

*Tabelle 8.1: Zusammenfassung der Systemgrenzen.*

### 8.3 Reflexion der KI-gestützten Entstehung

Sowohl Teile des Software-Prototyps als auch frühere Textentwürfe dieser Ausarbeitung entstanden unter Mitwirkung großer Sprachmodelle (vgl. Verzeichnis der verwendeten KI-Hilfsmittel). Rückblickend trat dabei genau jenes Muster zutage, das die Arbeit selbst untersucht: Sprachmodelle formulieren überzeugend klingende Behauptungen, die bei genauer technischer Nachprüfung nicht immer stimmen.

Ein konkretes Beispiel aus der Arbeit an diesem Dokument belegt das: Ein früherer Textentwurf behauptete, Z3 löse Gleichstände zwischen zwei identischen Pins deterministisch nach ihrer Deklarationsreihenfolge im C++-Quelltext auf. Erst das eigens geschriebene Experiment (`c` und `c2` in Abschnitt 7.4) widerlegte diese Annahme: Selbst bei umgekehrter Deklarationsreihenfolge im Code blieb `BUZZER_PIN` in beiden Fällen auf GPIO 7 stehen. Ohne den experimentellen Gegenbeweis und das zeilenweise Nachlesen des realen Codes hätte diese Fehlbehauptung in der Arbeit gestanden. Schriftliche Invarianten wie `AGENTS.md`, automatisierte Tests und eigene Nachmessungen erwiesen sich damit nicht nur für die Software, sondern auch für den Entstehungsprozess der Dokumentation als unverzichtbar.

### 8.4 Ausblick

Aus den gewonnenen Befunden ergeben sich vier nächste Ausbaustufen:

1. **Behebung der gefundenen Parser- und Solver-Lücken.** Die in Tabelle 8.1 benannten Korrekturen lassen sich schrittweise und abwärtskompatibel umsetzen – allen voran das Ignorieren unbenutzter lokaler Zählervariablen (um False Positives zu vermeiden), die Trennung der SPI-Chip-Select-Leitung, die Entschärfung des `-1 != -1`-Fehlers sowie eine verständliche Kapazitätswarnung beim Schubfachprinzip.
2. **Automatisierter Reparatur-Regelkreis.** Über eine optionale Flagge (etwa `--autofix`) oder eine MCP-Werkzeugschnittstelle könnte der Build-Hook das Sprachmodell bei `UNSAT` direkt ansteuern und geänderte Konstanten mit begrenzter Wiederholungszahl (z. B. maximal drei Durchläufen gegen Endlosschleifen) selbst einpflegen.
3. **Erweiterung des Chip-Katalogs und JSON-Schemas.** Ergänzung verifizierter Profile für den klassischen ESP32, ESP32-C6, RP2040 und ausgewählte STM32-Varianten inklusive optionaler Felder wie `input_only` und Kanalbudgets.
4. **Empirische Evaluation an realem LLM-Code.** Systematischer Vergleich über mehrere gängige Sprachmodelle anhand eines standardisierten Satzes von Embedded-Aufgaben mit Messung der Kompilier- und Hardware-Korrektheitsrate vor und nach Einsatz von `mcu-pin-solver`.

---

## 9 Fazit

Die vorliegende Arbeit hat ein datengetriebenes Pre-Build-Werkzeug zur Prüfung und Reparatur von GPIO-Pin-Belegungen in Embedded-C++-Code entworfen, implementiert und experimentell untersucht. Die drei einleitenden Forschungsfragen lassen sich abschließend wie folgt beantworten:

- **Zu FF1 (Extraktion ohne Ziel-Toolchain):** Mit `tree-sitter-cpp` lassen sich `#define`-Makros, Konstanten, Funktionsaufrufe und Peripherie-Auslöser über verteilte `include/`- und `src/`-Dateien hinweg schnell (unter 2 ms für das Beispielprojekt) und ohne installierte Compiler-Header auslesen. Kommentare, Zeichenketten und `for`-Schleifenvariablen erzeugen dabei keine Fehlalarme. Die Entscheidung gegen ein vollständiges Compiler-Frontend bringt jedoch klare Grenzen mit sich: Direkte Zahlenliterale, lokale Zählervariablen außerhalb von Schleifen und `#ifdef`-Alternativen werden in Version 0.1.0 nicht korrekt aufgelöst.
- **Zu FF2 (Trennung von Wissen und MaxSMT-Reparatur):** Die Auslagerung sämtlicher Pin-Daten und Konfliktregeln in JSON-Profile (`boards/*.json`) entkoppelt die Prüflogik vollständig vom Zielchip, wie derselbe Quelltext auf ESP32-C3 (`UNSAT`) und ESP32-S3 (`SAT`) zeigt. Das zweistufige Verfahren in `z3.Optimize` liefert im Fehlerfall vollständige Einzeldiagnosen in Stufe 1 und berechnet in Stufe 2 unter paarweiser Bus-Kopplung (`v_a == v_b`) und gewichteten Zielen (`100` für Originalpins gegen `10` für Strapping-Meidung) nachweisbar optimale Ersatzbelegungen im Bereich von wenigen Millisekunden.
- **Zu FF3 (PlatformIO-Integration):** Über den SCons-Pre-Build-Hook `pio_hook.py` und die Isolation in `library.json` (`"srcFilter": ["-<*>"]`) lässt sich die Prüfung vor den C++-Compiler schalten, stoppt fehlerhafte Builds via `env.Exit(1)` und erzeugt einen Reparatur-Prompt mit expliziten `Keep`- und `Change`-Anweisungen. Die lokale PlatformIO-CLI-Ausführung konnte auf dem Testsystem zwar nicht unmittelbar nachgeholt werden, die CLI-Pipeline ist jedoch durch neun automatisierte Testszenarien abgesichert.

Insgesamt zeigt die Arbeit am konkreten System, dass das neuro-symbolische LLM-Modulo-Prinzip für statische Hardware-Regeln im Embedded-Prototyping praktisch nutzbar ist: Das Sprachmodell übernimmt den schnellen Code-Entwurf, während ein kleiner deterministischer Syntaxbaum-Parser und ein formaler Solver die Einhaltung physikalischer Pin-Grenzen erzwingen.

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
- <a id="ref-14"></a>**[14] Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L., & Murthy, A. (2024):** *LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* In: *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*, PMLR Bd. 235, S. 22895–22907.
- <a id="ref-15"></a>**[15] Narodytska, N., & Bacchus, F. (2014):** *Maximum Satisfiability Using Core-Guided MaxSAT Resolution.* In: *Proceedings of the Twenty-Eighth AAAI Conference on Artificial Intelligence (AAAI 2014)*, S. 2717–2723.
- <a id="ref-16"></a>**[16] PlatformIO (2024):** *PlatformIO Core Documentation – Project Configuration (`platformio.ini`), Library Manifest (`library.json`) and Advanced Scripting.* Online-Dokumentation: `https://docs.platformio.org/`.
- <a id="ref-17"></a>**[17] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017):** *Attention Is All You Need.* In: *Advances in Neural Information Processing Systems (NeurIPS 2017)*, Bd. 30.

---

## Anhang

### Anhang A: Hardware-Profil `boards/esp32-c3.json`

```json
{
  "mcu": "ESP32-C3",
  "description": "Espressif ESP32-C3 (RISC-V, Single-Core, Wi-Fi/BLE)",
  "pins": {
    "0":  { "capabilities": ["gpio", "adc1", "pwm"], "strapping": false, "reserved": false },
    "1":  { "capabilities": ["gpio", "adc1", "pwm"], "strapping": false, "reserved": false },
    "2":  { "capabilities": ["gpio", "adc1", "pwm"], "strapping": true,  "reserved": false, "note": "Strapping Pin (Boot Mode)" },
    "3":  { "capabilities": ["gpio", "adc1", "pwm"], "strapping": false, "reserved": false },
    "4":  { "capabilities": ["gpio", "adc1", "pwm", "jtag"], "strapping": false, "reserved": false },
    "5":  { "capabilities": ["gpio", "adc2", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "6":  { "capabilities": ["gpio", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "7":  { "capabilities": ["gpio", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "8":  { "capabilities": ["gpio", "pwm", "i2c"], "strapping": true,  "reserved": false, "note": "Strapping Pin (ROM Log / Boot)" },
    "9":  { "capabilities": ["gpio", "pwm", "i2c"], "strapping": true,  "reserved": false, "note": "Strapping Pin (BOOT Button)" },
    "10": { "capabilities": ["gpio", "pwm", "spi"], "strapping": false, "reserved": false },
    "12": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIIO4)" },
    "13": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIIO5)" },
    "14": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPICS0)" },
    "15": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPICLK)" },
    "16": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPID)" },
    "17": { "capabilities": [], "strapping": false, "reserved": true, "note": "Internal SPI flash (SPIQ)" },
    "18": { "capabilities": ["gpio", "usb"], "strapping": false, "reserved": false, "note": "USB D-" },
    "19": { "capabilities": ["gpio", "usb"], "strapping": false, "reserved": false, "note": "USB D+" },
    "20": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 RX" },
    "21": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 TX" }
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

### Anhang B: Hardware-Profil `boards/esp32-s3.json`

```json
{
  "mcu": "ESP32-S3",
  "description": "Espressif ESP32-S3 (Dual-Core Xtensa LX7, Wi-Fi/BLE)",
  "pins": {
    "0":  { "capabilities": ["gpio", "pwm", "i2c"], "strapping": true,  "reserved": false, "note": "Strapping Pin (Boot Mode)" },
    "1":  { "capabilities": ["gpio", "adc1", "pwm", "i2c"], "strapping": false, "reserved": false },
    "2":  { "capabilities": ["gpio", "adc1", "pwm", "i2c"], "strapping": false, "reserved": false },
    "3":  { "capabilities": ["gpio", "adc1", "pwm", "i2c"], "strapping": true,  "reserved": false, "note": "Strapping Pin (JTAG Signal Source)" },
    "4":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "5":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "6":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "7":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "8":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "9":  { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "10": { "capabilities": ["gpio", "adc1", "pwm", "i2c", "spi"], "strapping": false, "reserved": false },
    "11": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "12": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "13": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "14": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "15": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "16": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "17": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "18": { "capabilities": ["gpio", "adc2", "pwm", "i2c", "spi"], "strapping": false, "reserved": false, "note": "ADC2 conflicts with Wi-Fi" },
    "19": { "capabilities": ["gpio", "adc2", "usb"], "strapping": false, "reserved": false, "note": "USB D- & ADC2" },
    "20": { "capabilities": ["gpio", "adc2", "usb"], "strapping": false, "reserved": false, "note": "USB D+ & ADC2" },
    "21": { "capabilities": ["gpio", "pwm", "i2c"], "strapping": false, "reserved": false },
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
    "38": { "capabilities": ["gpio", "pwm", "spi"], "strapping": false, "reserved": false },
    "39": { "capabilities": ["gpio", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "MTCK/MTDO/MTDI/MTMS (JTAG)" },
    "40": { "capabilities": ["gpio", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "MTCK/MTDO/MTDI/MTMS (JTAG)" },
    "41": { "capabilities": ["gpio", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "MTCK/MTDO/MTDI/MTMS (JTAG)" },
    "42": { "capabilities": ["gpio", "pwm", "jtag"], "strapping": false, "reserved": false, "note": "MTCK/MTDO/MTDI/MTMS (JTAG)" },
    "43": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 TX" },
    "44": { "capabilities": ["gpio", "uart"], "strapping": false, "reserved": false, "note": "UART0 RX" },
    "45": { "capabilities": ["gpio", "pwm"], "strapping": true,  "reserved": false, "note": "Strapping Pin (VDD_SPI Voltage)" },
    "46": { "capabilities": ["gpio", "pwm"], "strapping": true,  "reserved": false, "note": "Strapping Pin (ROM Log / Boot)" },
    "47": { "capabilities": ["gpio", "pwm"], "strapping": false, "reserved": false },
    "48": { "capabilities": ["gpio", "pwm"], "strapping": false, "reserved": false }
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

### Anhang C: Quelltext `mcu_validator/parser.py`

```python
import re
from pathlib import Path
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

CPP_LANGUAGE = Language(tscpp.language())
AST_PARSER = Parser(CPP_LANGUAGE)

CPP_EXTENSIONS = (".h", ".hpp", ".c", ".cpp", ".ino")

DEFAULT_TRIGGERS = {
    "wifi": ["WiFi.begin", "WiFi.softAP"],
    "usb_serial": ["Serial.begin"],
}

def _node_text(node):
    return node.text.decode("utf-8") if node else ""

def _walk_ast(node):
    yield node
    for child in node.children:
        yield from _walk_ast(child)

def _resolve_source_files(target):
    """Resolve a single file, directory (src/ + sibling include/), or sequence into sorted C/C++ files."""
    if isinstance(target, (list, tuple, set)):
        resolved, seen = [], set()
        for item in target:
            for p in _resolve_source_files(item):
                key = p.resolve()
                if key not in seen:
                    seen.add(key)
                    resolved.append(p)
        return resolved

    path = Path(target)
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []

    if path.name == "src" and (path.parent / "include").is_dir():
        search_dirs = [path.parent / "include", path]
    elif (path / "include").is_dir() or (path / "src").is_dir():
        search_dirs = [d for d in (path / "include", path / "src") if d.is_dir()]
    else:
        search_dirs = [path]

    found, seen = [], set()
    for d in search_dirs:
        for p in d.rglob("*"):
            rel_parts = p.relative_to(d).parts
            if (
                p.is_file()
                and p.suffix.lower() in CPP_EXTENSIONS
                and "tests" not in rel_parts
                and ".pio" not in rel_parts
            ):
                key = p.resolve()
                if key not in seen:
                    seen.add(key)
                    found.append(p)

    header_exts = {".h", ".hpp"}
    return sorted(found, key=lambda p: (0 if p.suffix.lower() in header_exts else 1, str(p)))

def _record_pin(pins_in_code, name, pin_val, file_path):
    """Store pin definition, preserving conflicting cross-file redefinitions under distinct keys."""
    if name not in pins_in_code or pins_in_code[name] == pin_val:
        pins_in_code[name] = pin_val
    else:
        pins_in_code[f"{name} ({file_path.name})"] = pin_val

# Extracts pin assignments, capabilities, and active peripherals using a C/C++ Abstract Syntax Tree (AST)
def parse_cpp_file(cpp_path, board_data=None):
    files = _resolve_source_files(cpp_path)
    if not files and not isinstance(cpp_path, (list, tuple, set)) and not Path(cpp_path).exists():
        raise FileNotFoundError(f"Source path not found: {cpp_path}")

    pins_in_code = {}
    call_expressions = []

    for file_path in files:
        tree = AST_PARSER.parse(file_path.read_bytes())

        for node in _walk_ast(tree.root_node):
            # 1. Preprocessor macro definitions: #define PIN_NAME 12
            if node.type == "preproc_def":
                name_node = node.child_by_field_name("name")
                val_node = node.child_by_field_name("value")
                if name_node and val_node:
                    val_str = re.sub(r"//.*|/\*.*?\*/", "", _node_text(val_node), flags=re.DOTALL).strip()
                    if val_str.isdigit():
                        _record_pin(pins_in_code, _node_text(name_node).strip(), int(val_str), file_path)

            # 2. Pin variable declarations: const int / uint8_t / constexpr PIN_NAME = 12;
            elif node.type == "declaration" and node.parent and node.parent.type != "for_statement":
                type_node = node.child_by_field_name("type")
                if _node_text(type_node).strip() in ("int", "uint8_t"):
                    for child in node.children:
                        if child.type == "init_declarator":
                            decl_node = child.child_by_field_name("declarator")
                            val_node = child.child_by_field_name("value")
                            if decl_node and val_node and decl_node.type == "identifier" and val_node.type == "number_literal":
                                val_str = _node_text(val_node).strip()
                                if val_str.isdigit():
                                    _record_pin(pins_in_code, _node_text(decl_node).strip(), int(val_str), file_path)

            # 3. Function & method calls: e.g. analogRead(PIN), Wire.begin(SDA, SCL), WiFi.begin(...)
            elif node.type == "call_expression":
                fn_node = node.child_by_field_name("function")
                args_node = node.child_by_field_name("arguments")
                if fn_node and args_node:
                    fn_name = re.sub(r"\s+", "", _node_text(fn_node))
                    arg_ids = [
                        _node_text(child).strip()
                        for child in _walk_ast(args_node)
                        if child.type == "identifier"
                    ]
                    call_expressions.append((fn_name, arg_ids))

    # Classify pin capabilities from AST call expressions
    adc_pins, pwm_pins, i2c_pins, spi_pins, uart_pins = set(), set(), set(), set(), set()
    called_functions = set()

    for fn_name, arg_ids in call_expressions:
        called_functions.add(fn_name)
        if fn_name == "analogRead":
            adc_pins.update(arg_ids)
        elif fn_name in ("analogWrite", "ledcAttach", "ledcAttachPin"):
            pwm_pins.update(arg_ids)
        elif re.match(r"^Wire\d*\.(?:begin|setPins)$", fn_name):
            i2c_pins.update(arg_ids)
        elif re.match(r"^SPI\d*\.begin$", fn_name):
            spi_pins.update(arg_ids)
        elif re.match(r"^Serial\d+\.begin$", fn_name):
            uart_pins.update(arg_ids)

    wire_used = any(fn.startswith("Wire") for fn in called_functions)

    requests = []
    for name, pin_number in pins_in_code.items():
        if name in adc_pins:
            cap = "adc"
        elif name in pwm_pins:
            cap = "pwm"
        elif name in i2c_pins or (wire_used and re.search(r"(?:^|_)(?:SDA|SCL)(?:_|$)", name, re.IGNORECASE)):
            cap = "i2c"
        elif name in spi_pins:
            cap = "spi"
        elif name in uart_pins:
            cap = "uart"
        else:
            cap = "gpio"
        requests.append({"name": name, "pin": pin_number, "cap": cap})

    # Match active peripheral triggers against actual AST function calls
    triggers = (board_data or {}).get("resource_triggers", DEFAULT_TRIGGERS)
    active_resources = [
        resource for resource, patterns in triggers.items()
        if any(
            any(fn == pat or fn.endswith("." + pat) for fn in called_functions)
            for pat in patterns
        )
    ]

    return requests, active_resources
```

### Anhang D: Quelltext `mcu_validator/solver.py`

```python
import json
from pathlib import Path
from z3 import Int, Or, Optimize, sat

BOARDS_DIR = Path(__file__).resolve().parent.parent / "boards"

# Loads the matching JSON hardware definition for a board name (e.g. 'esp32-s3-devkitc-1' -> 'esp32-s3.json')
def load_board_data(board_id="esp32-c3"):
    board_id_lower = board_id.lower().replace("_", "-")
    for json_file in sorted(BOARDS_DIR.glob("*.json")):
        if json_file.stem.lower() in board_id_lower:
            return json.loads(json_file.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"No hardware definition found for board '{board_id}' in {BOARDS_DIR}")

# Validates pin requests against the board JSON and computes a minimal-invasive repair via Z3 MaxSMT
def validate_with_z3(requests, active_resources, board_data):
    pins_db = {int(k): v for k, v in board_data["pins"].items()}
    aliases = board_data.get("capability_aliases", {})
    shared_caps = set(board_data.get("shared_capabilities", []))
    rules = board_data.get("conflict_rules", [])

    # 1. Evaluate active conflict rules
    forbidden_caps = set()
    forbidden_pins = set()
    for rule in rules:
        if rule["when_resource_active"] in active_resources:
            if "forbidden_capability" in rule:
                forbidden_caps.add(rule["forbidden_capability"])
            if "forbidden_pins" in rule:
                forbidden_pins.update(rule["forbidden_pins"])

    # 2. Check current pin assignments for conflicts
    conflicts = []
    seen_pins = {}
    for req in requests:
        p = req["pin"]
        info = pins_db.get(p)
        if not info:
            conflicts.append(f"{req['name']} (GPIO {p}): Pin does not exist on {board_data['mcu']}.")
            continue

        # Allow shared pins only if all signals on that pin share the same bus capability (e.g. i2c, spi)
        if p in seen_pins:
            incompatible = [
                prev for prev in seen_pins[p]
                if not (req["cap"] == prev["cap"] and req["cap"] in shared_caps)
            ]
            if incompatible:
                conflicts.append(
                    f"{req['name']} (GPIO {p}): Duplicate assignment with {incompatible[0]['name']}."
                )
        seen_pins.setdefault(p, []).append(req)

        if info.get("reserved"):
            conflicts.append(f"{req['name']} (GPIO {p}): Reserved pin! ({info.get('note', 'Reserved')})")
            continue

        target_caps = set(aliases.get(req["cap"], [req["cap"]]))
        matching_caps = target_caps.intersection(info["capabilities"])
        if not matching_caps:
            conflicts.append(f"{req['name']} (GPIO {p}): Does not support capability '{req['cap']}'.")
        elif matching_caps.issubset(forbidden_caps) or p in forbidden_pins:
            conflicts.append(
                f"{req['name']} (GPIO {p}): Conflicts with active {active_resources} ({info.get('note', 'Blocked')})."
            )

    if not conflicts:
        return True, [], {r["name"]: r["pin"] for r in requests}

    # 3. Z3 Optimize (MaxSMT): Compute a minimal-invasive pin reassignment
    opt = Optimize()
    z3_vars = {}
    for req in requests:
        var = Int(req["name"])
        z3_vars[req["name"]] = var
        target_caps = set(aliases.get(req["cap"], [req["cap"]])) - forbidden_caps

        allowed_pins = [
            p for p, info in pins_db.items()
            if not info.get("reserved")
            and p not in forbidden_pins
            and target_caps.intersection(info["capabilities"])
        ]

        if allowed_pins:
            opt.add(Or([var == p for p in allowed_pins]))
        else:
            opt.add(var == -1)

        # Soft Constraint 1 (weight 100): Keep valid original pins unchanged whenever possible
        opt.add_soft(var == req["pin"], weight=100)

        # Soft Constraint 2 (weight 10): Avoid boot/strapping pins during reassignment
        for p in allowed_pins:
            if pins_db[p].get("strapping"):
                opt.add_soft(var != p, weight=10)

    # Couple shared bus lines together and keep all other signal pairs on distinct pins
    for i, req_a in enumerate(requests):
        for req_b in requests[i + 1:]:
            var_a = z3_vars[req_a["name"]]
            var_b = z3_vars[req_b["name"]]
            if (
                req_a["cap"] == req_b["cap"]
                and req_a["cap"] in shared_caps
                and req_a["pin"] == req_b["pin"]
            ):
                opt.add(var_a == var_b)
            else:
                opt.add(var_a != var_b)

    suggested = {}
    if opt.check() == sat:
        model = opt.model()
        suggested = {name: model[var].as_long() for name, var in z3_vars.items()}

    return False, conflicts, suggested
```

### Anhang E: Quelltexte `cli.py`, `__init__.py`, `pio_hook.py` und `library.json`

#### `mcu_validator/cli.py`

```python
import sys
from .parser import parse_cpp_file
from .solver import load_board_data, validate_with_z3

# Formats the validation result and generates the LLM repair prompt
def format_report(cpp_path, board_data, active_resources, requests, is_valid, conflicts, suggested):
    lines = [
        "=" * 65,
        f" Checked File   : {cpp_path} ({board_data['mcu']})",
        f" Active Modules : {active_resources}",
        "=" * 65,
    ]
    if is_valid:
        lines.append(" RESULT: SAT (All pins valid! No hardware conflicts detected.)")
    else:
        lines.extend([
            " RESULT: UNSAT (Hardware conflicts detected!)\n",
            "--- COPY THIS PROMPT BACK TO YOUR AI (LLM-MODULO) ---\n",
            f"Your C++ code for the {board_data['mcu']} contains the following hardware errors:",
        ])
        for conflict in conflicts:
            lines.append(f"  - {conflict}")
        lines.append("\nPlease regenerate the code using this exact Z3-verified pin assignment:")
        for req in requests:
            name, old_p = req["name"], req["pin"]
            new_p = suggested.get(name)
            if old_p == new_p:
                lines.append(f"  - {name}: Keep GPIO {old_p} (unchanged)")
            else:
                lines.append(f"  - {name}: Change GPIO {old_p} -> GPIO {new_p}")
        lines.append("\n-----------------------------------------------------")
    return "\n".join(lines)

def validate_file(cpp_path, board_id="esp32-c3"):
    board_data = load_board_data(board_id)
    requests, active_res = parse_cpp_file(cpp_path, board_data)
    is_valid, conflicts, suggested = validate_with_z3(requests, active_res, board_data)
    report = format_report(cpp_path, board_data, active_res, requests, is_valid, conflicts, suggested)
    return is_valid, report

def main():
    cpp_file = sys.argv[1] if len(sys.argv) > 1 else "src/main.cpp"
    board_id = sys.argv[2] if len(sys.argv) > 2 else "esp32-c3"
    is_valid, report = validate_file(cpp_file, board_id)
    print(report)
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
```

#### `mcu_validator/__init__.py`

```python
from .parser import parse_cpp_file
from .solver import load_board_data, validate_with_z3

__all__ = ["parse_cpp_file", "load_board_data", "validate_with_z3"]
```

#### `pio_hook.py`

```python
Import("env")
import inspect
import os
import shutil
import subprocess
import sys
from pathlib import Path

if not env.get("_MCU_VALIDATOR_RAN"):
    env["_MCU_VALIDATOR_RAN"] = True

    hook_dir = Path(inspect.getfile(inspect.currentframe())).resolve().parent
    board_id = env.GetProjectOption("board", "esp32-c3")
    src_dir = Path(env.subst("$PROJECT_SRC_DIR"))

    python_cmd = shutil.which("py") or sys.executable

    check_deps = subprocess.run(
        [python_cmd, "-c", "import z3, tree_sitter, tree_sitter_cpp"],
        capture_output=True,
    )
    if check_deps.returncode != 0:
        print("\n>>> [MCU-Validator] Installing dependencies (first-time setup)...")
        subprocess.run(
            [python_cmd, "-m", "pip", "install", "z3-solver", "tree-sitter", "tree-sitter-cpp"],
            check=True,
        )

    run_env = os.environ.copy()
    run_env["PYTHONPATH"] = str(hook_dir) + os.pathsep + run_env.get("PYTHONPATH", "")

    print(f"\n>>> [MCU-Validator] Checking hardware constraints for board '{board_id}'...")

    result = subprocess.run(
        [python_cmd, "-m", "mcu_validator.cli", str(src_dir), board_id],
        env=run_env,
    )
    if result.returncode != 0:
        print("\n>>> BUILD STOPPED: Please fix the hardware pin conflicts in your C++ code first!\n")
        env.Exit(1)

    print("\n>>> [MCU-Validator] Hardware validation passed (SAT). Starting compiler...\n")
```

#### `library.json`

```json
{
  "name": "mcu-pin-solver",
  "version": "0.1.0",
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
      "boards/*.json",
      "mcu_validator/*.py",
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

Vorlage aus `README.md` (Zeilen 68–85) zur Erstellung weiterer Profile unter `boards/<chip>.json` (ein Abgleich gegen das jeweilige Hersteller-Datenblatt bleibt erforderlich):

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

### Anhang G: Versuchsskripte zur Evaluation (`experiments.py` und `timing.py`)

#### `experiments.py` (Tree-Sitter-Dump für Abbildung 2.3 sowie Grenzfalltests in Abschnitt 7.4)

```python
"""Verification experiments for the thesis revision (run from repo root).

E1: Tree-Sitter structure of the Abb. 3.3 snippet (incl. preproc_arg content)
E2: Edge cases / limits claimed in chapter 7 (in-process via the public API)
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from mcu_validator import parse_cpp_file, load_board_data, validate_with_z3  # noqa: E402
from mcu_validator.parser import AST_PARSER  # noqa: E402

SNIPPET = b"""// WiFi.begin()
#define STATUS_LED 12 // Board-LED
const int SOIL_SENSOR = 5;
void setup() {
    WiFi.begin("MyWiFi");
    analogRead(SOIL_SENSOR);
}
"""


def dump(node, depth=0, field=None):
    txt = node.text.decode() if node.child_count == 0 or node.type in ("preproc_arg", "comment", "string_literal") else ""
    label = f"{field}: " if field else ""
    print("  " * depth + f"{label}{node.type}" + (f"  -> {txt!r}" if txt else ""))
    for i, child in enumerate(node.children):
        dump(child, depth + 1, node.field_name_for_child(i))


print("=" * 70, "\nE1: tree-sitter-cpp tree of Abb. 3.3 snippet\n" + "=" * 70)
dump(AST_PARSER.parse(SNIPPET).root_node)

CASES = {
    "a_magic_numbers": """#include <WiFi.h>
void setup() { Serial.begin(115200); WiFi.begin("x","y"); pinMode(12, OUTPUT); }
void loop() { int raw = analogRead(5); }
""",
    "b_local_counter": """#define STATUS_LED 3
void setup() { pinMode(STATUS_LED, OUTPUT); }
void loop() { int blinkCount = 0; uint8_t retries = 12; digitalWrite(STATUS_LED, HIGH); }
""",
    "c_tiebreak_swapped": """#define SERVO_PIN 7
#define BUZZER_PIN 7
void setup() { pinMode(SERVO_PIN, OUTPUT); pinMode(BUZZER_PIN, OUTPUT); }
""",
    "c2_tiebreak_original": """#define BUZZER_PIN 7
#define SERVO_PIN 7
void setup() { pinMode(BUZZER_PIN, OUTPUT); pinMode(SERVO_PIN, OUTPUT); }
""",
    "d_pigeonhole_6_adc_wifi": """#include <WiFi.h>
const int S0 = 0; const int S1 = 1; const int S2 = 3; const int S3 = 4; const int S4 = 2; const int S5 = 5;
void setup() { WiFi.begin("x","y"); }
void loop() { analogRead(S0); analogRead(S1); analogRead(S2); analogRead(S3); analogRead(S4); analogRead(S5); }
""",
    "f_specialist_vs_allrounder": """#include <WiFi.h>
const int A_0 = 0; const int A_3 = 3; const int A_4 = 4;
const int SOIL_SENSOR = 1;
const int STATUS_LED = 1;
void setup() { WiFi.begin("x","y"); pinMode(STATUS_LED, OUTPUT); }
void loop() { analogRead(A_0); analogRead(A_3); analogRead(A_4); analogRead(SOIL_SENSOR); }
""",
    "f2_specialist_declared_second": """#include <WiFi.h>
const int A_0 = 0; const int A_3 = 3; const int A_4 = 4;
const int STATUS_LED = 1;
const int SOIL_SENSOR = 1;
void setup() { WiFi.begin("x","y"); pinMode(STATUS_LED, OUTPUT); }
void loop() { analogRead(A_0); analogRead(A_3); analogRead(A_4); analogRead(SOIL_SENSOR); }
""",
    "h_role_shadowing": """#include <Wire.h>
const int MY_PIN = 6; const int MY_SCL = 7;
void setup() { Wire.begin(MY_PIN, MY_SCL); }
void loop() { analogRead(MY_PIN); }
""",
    "i_constexpr_and_gpio_num_t": """constexpr int LED_A = 12;
static const uint8_t LED_B = 13;
const gpio_num_t LED_C = GPIO_NUM_14;
void setup() { pinMode(LED_A, OUTPUT); }
""",
    "j_ifdef_both_branches": """#ifdef USE_EXTERNAL_LED
#define STATUS_LED 2
#else
#define STATUS_LED 12
#endif
void setup() { pinMode(STATUS_LED, OUTPUT); }
""",
    "k_wire_vs_wire1_same_pin": """#include <Wire.h>
const int SDA_A = 6; const int SCL_A = 7; const int SDA_B = 6; const int SCL_B = 7;
void setup() { Wire.begin(SDA_A, SCL_A); Wire1.begin(SDA_B, SCL_B); }
""",
    "l_spi_two_cs_same_pin": """#include <SPI.h>
const int SCK_P = 6; const int MISO_P = 7; const int MOSI_P = 10; const int CS_A = 7; const int CS_B = 7;
void setup() { SPI.begin(SCK_P, MISO_P, MOSI_P, CS_A); SPI.begin(SCK_P, MISO_P, MOSI_P, CS_B); }
""",
}

board = load_board_data("esp32-c3")
tmp = Path(tempfile.mkdtemp())
for name, code in CASES.items():
    f = tmp / f"{name}.cpp"
    f.write_text(code, encoding="utf-8")
    reqs, res = parse_cpp_file(f, board)
    ok, conflicts, sugg = validate_with_z3(reqs, res, board)
    print("=" * 70, f"\nE2 {name}\n" + "=" * 70)
    print(" requests :", reqs)
    print(" resources:", res)
    print(" SAT      :", ok)
    for c in conflicts:
        print("  conflict:", c)
    print(" suggested:", sugg)

# E2e: request with a capability that no pin offers (synthetic, via public API)
print("=" * 70, "\nE2 e_empty_domain (synthetic capability 'can')\n" + "=" * 70)
for reqs in (
    [{"name": "CAN_TX", "pin": 4, "cap": "can"}, {"name": "LED", "pin": 12, "cap": "gpio"}],
    [{"name": "CAN_TX", "pin": 4, "cap": "can"}, {"name": "CAN_RX", "pin": 5, "cap": "can"}, {"name": "LED", "pin": 12, "cap": "gpio"}],
):
    ok, conflicts, sugg = validate_with_z3(reqs, [], board)
    print(" requests :", [r["name"] for r in reqs], "| SAT:", ok, "| suggested:", sugg)
```

#### `timing.py` (Laufzeitmessung für Abschnitt 7.5)

```python
"""Runtime measurement for the thesis (run from repo root).

T1: end-to-end wall time per CLI subprocess (as PlatformIO / run_tests.py call it), N runs each
T2: in-process phase times (load_board_data, parse_cpp_file, validate_with_z3), M runs each
"""
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from mcu_validator import parse_cpp_file, load_board_data, validate_with_z3  # noqa: E402

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

ms = lambda xs: statistics.median(xs) * 1000  # noqa: E731

# Interpreter start + imports only (baseline)
base = []
for _ in range(N):
    t = time.perf_counter()
    subprocess.run([sys.executable, "-c", "import z3, tree_sitter, tree_sitter_cpp"], capture_output=True)
    base.append(time.perf_counter() - t)
print(f"Baseline (python start + import z3/tree_sitter): median {ms(base):.0f} ms")

print(f"\n{'case':58} {'board':9} {'res':5} {'E2E med':>8} {'load':>7} {'parse':>7} {'solve':>8}")
for target, board_id in CASES:
    e2e = []
    rc = None
    for _ in range(N):
        t = time.perf_counter()
        rc = subprocess.run([sys.executable, "-m", "mcu_validator.cli", target, board_id], capture_output=True).returncode
        e2e.append(time.perf_counter() - t)
    tl, tp, ts = [], [], []
    for _ in range(M):
        t0 = time.perf_counter(); board = load_board_data(board_id)
        t1 = time.perf_counter(); reqs, res = parse_cpp_file(target, board)
        t2 = time.perf_counter(); validate_with_z3(reqs, res, board)
        t3 = time.perf_counter()
        tl.append(t1 - t0); tp.append(t2 - t1); ts.append(t3 - t2)
    print(f"{target:58} {board_id:9} {'SAT' if rc == 0 else 'UNSAT':5} {ms(e2e):6.0f}ms {ms(tl):5.2f}ms {ms(tp):5.2f}ms {ms(ts):6.2f}ms")
```

---

## Verzeichnis der verwendeten KI-Hilfsmittel

| Hilfsmittel | Einsatzbereich | Art der Prüfung und Verantwortung |
| :--- | :--- | :--- |
| LLM-Coding-Assistenten (Gemini / Claude) | Unterstützung beim Entwurf des Python-Prototyps (`mcu_validator`, `pio_hook.py`, Testszenarien) sowie bei der Formulierung der Board-JSONs | Vollständiges Code-Review durch den Verfasser; Abgleich der Hardware-Regeln gegen die Espressif-Datenblätter [[7]](#ref-7), [[8]](#ref-8); Absicherung durch neun automatisierte Testszenarien |
| LLM-Textassistenten (Gemini / Claude) | Strukturierungshilfe, sprachliche Glättung und Erstellung von Entwurfsfassungen dieser Ausarbeitung | Eigenständige fachliche Prüfung aller Aussagen durch den Verfasser; Überprüfung aller Verhaltensbehauptungen und Messwerte mittels `experiments.py` und `timing.py`; Literaturabgleich |

---

## Ehrenwörtliche Erklärung

Ich erkläre ehrenwörtlich, dass ich die vorliegende Studienarbeit mit dem Thema

> *„Neuro-Symbolische Hardware-Verifikation von LLM-generiertem Embedded-C++-Code mittels AST-Analyse und Z3 MaxSMT“*

selbstständig verfasst und keine anderen als die angegebenen Quellen und Hilfsmittel benutzt habe. Alle wörtlich oder sinngemäß aus Quellen entnommenen Stellen sind als solche kenntlich gemacht. Die verwendeten KI-gestützten Hilfsmittel sind im vorstehenden Verzeichnis vollständig offengelegt. Die Arbeit wurde bisher in gleicher oder ähnlicher Form keiner anderen Prüfungsbehörde vorgelegt und noch nicht veröffentlicht. Ich versichere zudem, dass die eingereichte elektronische Fassung mit gegebenenfalls eingereichten gedruckten Exemplaren übereinstimmt.

`[Ort]`, den `[TT.MM.JJJJ]`

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
`David Matheja` *(Unterschrift)*
