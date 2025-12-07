# Assignment Documentation Spec
## EGE205 Connect System Design Project - Documentation Requirements

### Purpose
Create comprehensive documentation for Module 5 (Display Client) and Cloud Server Dashboard to fulfill assignment requirements.

---

## Part 1: Assignment Criteria and Constraints

**Questions:**
1. What specific criteria were agreed upon in your team discussion?
   - [ ] Real-time display requirements?
   - [ ] Hardware constraints (BeagleBone, Click boards)?
   - [ ] Communication protocol requirements?
   - [ ] Performance requirements?
   - [ ] User experience requirements?

2. What constraints were identified?
   - [ ] Hardware limitations?
   - [ ] Network requirements?
   - [ ] Power consumption?
   - [ ] Cost constraints?
   - [ ] Time constraints?

**If you don't have specific criteria/constraints from team discussion, I can infer them from the code and system architecture.**

---

## Part 2: Block Diagram

**Questions:**
1. What level of detail is needed?
   - [ ] High-level system overview (all 5 modules)?
   - [ ] Module 5 specific (hardware components)?
   - [ ] Both Module 5 and Dashboard separately?
   - [ ] Communication flow between components?

2. Should I create the diagram using:
   - [ ] Text-based ASCII art (in markdown)?
   - [ ] Mermaid diagrams (renders in markdown)?
   - [ ] Instructions for external tools (SmartDraw, LucidChart)?
   - [ ] Multiple formats?

**Current understanding from code:**
- Module 5: OLED, 8x8 LED Matrix, Analogue Keypad, Potentiometer → BeagleBone → Cloud Server
- Dashboard: Web interface → Flask Server → SocketIO → Modules

---

## Part 3: Schematic / Circuit Diagram

**Questions:**
1. What level of detail is needed?
   - [ ] Full circuit diagram with all connections?
   - [ ] Simplified block-level connections?
   - [ ] Pin assignments only?
   - [ ] Click board slot assignments?

2. Should I include:
   - [ ] BeagleBone Black pin connections?
   - [ ] Click board slot assignments (Slot 1-4)?
   - [ ] I2C, SPI, ADC connections?
   - [ ] Power connections?

**From code, I can see:**
- Slot 1 (I2C): OLED Click (0x3C)
- Slot 2 (ADC): Potentiometer (P9_37)
- Slot 3 (SPI): 8x8 LED Matrix (CS=P9_17, SCK=P9_22, MISO=P9_29, MOSI=P9_18)
- Slot 4 (ADC): Analog Key Click (P9_39)

3. Format preference:
   - [ ] Text-based ASCII diagram?
   - [ ] Mermaid circuit diagram?
   - [ ] Instructions for external tools (Fritzing, KiCad)?
   - [ ] Table format with pin mappings?

---

## Part 4: Flow Chart

**Questions:**
1. Which flow charts are needed?
   - [ ] Module 5 main program flow?
   - [ ] Dashboard server flow?
   - [ ] Button handling flow?
   - [ ] Data update flow?
   - [ ] Connection/registration flow?
   - [ ] All of the above?

2. Format preference:
   - [ ] Mermaid flowchart (renders in markdown)?
   - [ ] Text-based ASCII flowchart?
   - [ ] Instructions for external tools (Draw.io, LucidChart)?
   - [ ] Multiple detailed flowcharts?

**Key flows I can document:**
- Module 5: Initialization → Connection → Button Loop → Display Update → Scroll Loop
- Dashboard: Server Start → SocketIO Events → Data Processing → Broadcast

---

## Part 5: Program Code

**Questions:**
1. What format is preferred?
   - [ ] Full code listing in markdown?
   - [ ] Code with line numbers?
   - [ ] Key functions only with explanations?
   - [ ] Code organized by sections?

2. Should I include:
   - [ ] Code comments explaining logic?
   - [ ] Function descriptions?
   - [ ] Key algorithms explained?
   - [ ] Both Module 5 and Dashboard code?

**Files to include:**
- `Assignment/module5/Module5_Display_Client.py` (1890 lines)
- `Assignment/CloudServer_WebDashboard.py` (568 lines)

---

## Additional Questions

1. **Output Format:**
   - [ ] Single markdown file?
   - [ ] Separate files for each part?
   - [ ] Word document format (I can provide markdown that converts well)?
   - [ ] PDF-ready format?

2. **Documentation Style:**
   - [ ] Academic/formal?
   - [ ] Technical/reference?
   - [ ] Student assignment format?

3. **Diagrams:**
   - Should I create actual diagram files, or provide instructions/templates for external tools?
   - Do you have access to diagramming tools, or should I use text-based formats?

4. **Scope:**
   - [ ] Module 5 only?
   - [ ] Dashboard only?
   - [ ] Both (separate sections)?
   - [ ] Integration between them?

---

## My Recommendations (if you want me to proceed)

Based on the code analysis, I can create:

1. **Part 1:** Inferred criteria/constraints from code and system architecture
2. **Part 2:** Mermaid block diagrams (renders in GitHub/markdown viewers)
3. **Part 3:** Pin mapping tables + ASCII circuit diagrams + instructions for external tools
4. **Part 4:** Mermaid flowcharts for key program flows
5. **Part 5:** Full code listings with section headers and key explanations

**Format:** Single comprehensive markdown file with all parts, plus separate diagram files if needed.

---

## Next Steps

Please answer the questions above, or type **"GO!"** if you want me to proceed with my recommendations and create the documentation based on what I can infer from the code.

