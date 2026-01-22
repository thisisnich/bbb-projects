# System Block Diagrams - All Four Modules

This document contains system block diagrams for all four modules in the basketball court monitoring system.

---

## Module 1: Crowd Intelligence Unit
**"Real-time occupancy monitoring with multi-sensor validation"**

```mermaid
graph TB
    subgraph "BBBW1 - Crowd Intelligence Unit"
        BBBW1[BBBW BOARD<br/>BeagleBone Black Wireless<br/>WIFI]
        CAPE1[MIKROE CAPE BOARD<br/>BBBW1]
        
        subgraph "Click Board Slots"
            SLOT1_AN[Slot 1: AN<br/>Analog/GPIO]
            SLOT2_PWM[Slot 2: PWM<br/>PWM/GPIO]
            SLOT3_I2C[Slot 3: I2C<br/>I2C Bus]
            SLOT4_SPI[Slot 4: SPI<br/>SPI Bus]
        end
        
        MIC[MIC Click<br/>Audio Level Detection<br/>Analog/ADC]
        MOTION[Motion Click<br/>PIR Motion Sensor<br/>Digital GPIO]
        OLED1[OLED Click<br/>128x64 Display<br/>I2C]
        PROX[Proximity Click<br/>Proximity Sensor<br/>I2C/SPI]
        WEBCAM[USB Webcam<br/>Video Capture<br/>USB Port]
        
        BBBW1 -->|Stacked| CAPE1
        CAPE1 --> SLOT1_AN
        CAPE1 --> SLOT2_PWM
        CAPE1 --> SLOT3_I2C
        CAPE1 --> SLOT4_SPI
        
        SLOT1_AN -->|Analog Signal<br/>Red Line| MIC
        SLOT2_PWM -->|Digital Signal<br/>Red Line| MOTION
        SLOT3_I2C -->|I2C Signal<br/>Red Line| OLED1
        SLOT4_SPI -->|I2C/SPI Signal<br/>Red Line| PROX
        BBBW1 -->|USB Connection| WEBCAM
    end
    
    AP[ACCESS POINT<br/>WIFI]
    SERVER[PC WEB SERVER<br/>Flask/SocketIO]
    
    BBBW1 -->|WIFI| AP
    AP -->|WIFI| SERVER
    
    style BBBW1 fill:#e1f5ff
    style CAPE1 fill:#fff4e1
    style MIC fill:#ffe1e1
    style MOTION fill:#ffe1e1
    style OLED1 fill:#ffe1e1
    style PROX fill:#ffe1e1
    style WEBCAM fill:#e1ffe1
    style AP fill:#f0e1ff
    style SERVER fill:#e1e1ff
```

**Components:**
- **BBBW BOARD**: BeagleBone Black Wireless (main processing unit)
- **MIKROE CAPE BOARD**: Expansion board providing Click board interfaces
- **Slot 1 (AN)**: MIC Click - Audio level detection for activity monitoring
- **Slot 2 (PWM)**: Motion Click - PIR motion sensor for backup detection
- **Slot 3 (I2C)**: OLED Click - Local status display (128x64)
- **Slot 4 (SPI)**: Proximity Click - Detect people approaching court area
- **USB Webcam**: Video capture for AI-based people counting (connects via USB, not Click slot)

**Communication:**
- All modules connect wirelessly via WIFI to Access Point
- Access Point connects to PC Web Server running Flask/SocketIO
- Data transmitted: People count, crowd level, noise level, motion status, proximity status

---

## Module 2: Environmental Conditions Station
**"Sports-safe weather monitoring with air quality"**

```mermaid
graph TB
    subgraph "BBBW2 - Environmental Conditions Station"
        BBBW2[BBBW BOARD<br/>BeagleBone Black Wireless<br/>WIFI]
        CAPE2[MIKROE CAPE BOARD<br/>BBBW2]
        
        subgraph "Click Board Slots"
            SLOT1_AN2[Slot 1: AN<br/>Analog/GPIO]
            SLOT2_PWM2[Slot 2: PWM<br/>PWM/GPIO]
            SLOT3_I2C2[Slot 3: I2C<br/>I2C Bus]
            SLOT4_SPI2[Slot 4: SPI<br/>SPI Bus]
        end
        
        ENV[Environment Click<br/>Temp, Humidity, Pressure, VOC<br/>I2C]
        UV[UV 3 Click<br/>UV Index Sensor<br/>I2C]
        BAR[Bar Graph 2 Click<br/>LED Bar Display<br/>I2C/SPI]
        OLED2[OLED Click<br/>128x64 Display<br/>I2C]
        
        BBBW2 -->|Stacked| CAPE2
        CAPE2 --> SLOT1_AN2
        CAPE2 --> SLOT2_PWM2
        CAPE2 --> SLOT3_I2C2
        CAPE2 --> SLOT4_SPI2
        
        SLOT1_AN2 -->|I2C Signal<br/>Red Line| ENV
        SLOT2_PWM2 -->|I2C Signal<br/>Red Line| UV
        SLOT3_I2C2 -->|I2C/SPI Signal<br/>Red Line| BAR
        SLOT4_SPI2 -->|I2C Signal<br/>Red Line| OLED2
    end
    
    AP2[ACCESS POINT<br/>WIFI]
    SERVER2[PC WEB SERVER<br/>Flask/SocketIO]
    
    BBBW2 -->|WIFI| AP2
    AP2 -->|WIFI| SERVER2
    
    style BBBW2 fill:#e1f5ff
    style CAPE2 fill:#fff4e1
    style ENV fill:#ffe1e1
    style UV fill:#ffe1e1
    style BAR fill:#ffe1e1
    style OLED2 fill:#ffe1e1
    style AP2 fill:#f0e1ff
    style SERVER2 fill:#e1e1ff
```

**Components:**
- **BBBW BOARD**: BeagleBone Black Wireless (main processing unit)
- **MIKROE CAPE BOARD**: Expansion board providing Click board interfaces
- **Slot 1 (AN)**: Environment Click - Temperature, humidity, pressure, VOC (4-in-1 sensor)
- **Slot 2 (PWM)**: UV 3 Click - UV index sensor for sunburn risk assessment
- **Slot 3 (I2C)**: Bar Graph 2 Click - Visual comfort indicator (LED bars)
- **Slot 4 (SPI)**: OLED Click - Local display showing environmental readings (128x64)

**Communication:**
- Connects wirelessly via WIFI to Access Point
- Data transmitted: Temperature, humidity, pressure, UV index, VOC levels, comfort score

---

## Module 3: Interactive Feedback Kiosk
**"Community voice with intuitive gesture control"**

```mermaid
graph TB
    subgraph "BBBW3 - Interactive Feedback Kiosk"
        BBBW3[BBBW BOARD<br/>BeagleBone Black Wireless<br/>WIFI]
        CAPE3[MIKROE CAPE BOARD<br/>BBBW3]
        
        subgraph "Click Board Slots"
            SLOT1_AN3[Slot 1: AN<br/>Analog/GPIO]
            SLOT2_PWM3[Slot 2: PWM<br/>PWM/GPIO]
            SLOT3_I2C3[Slot 3: I2C<br/>I2C Bus]
            SLOT4_SPI3[Slot 4: SPI<br/>SPI Bus]
        end
        
        GESTURE[IR Gesture Click<br/>Gesture Sensor<br/>I2C]
        LEDMAT[LED Matrix Click<br/>8x8 LED Matrix<br/>SPI]
        OLED3[OLED Click<br/>128x64 Display<br/>I2C]
        BUZZ1[Buzz 2 Click<br/>Buzzer<br/>GPIO/PWM]
        
        BBBW3 -->|Stacked| CAPE3
        CAPE3 --> SLOT1_AN3
        CAPE3 --> SLOT2_PWM3
        CAPE3 --> SLOT3_I2C3
        CAPE3 --> SLOT4_SPI3
        
        SLOT1_AN3 -->|I2C Signal<br/>Red Line| GESTURE
        SLOT2_PWM3 -->|SPI Signal<br/>Red Line| LEDMAT
        SLOT3_I2C3 -->|I2C Signal<br/>Red Line| OLED3
        SLOT4_SPI3 -->|GPIO/PWM Signal<br/>Red Line| BUZZ1
    end
    
    AP3[ACCESS POINT<br/>WIFI]
    SERVER3[PC WEB SERVER<br/>Flask/SocketIO]
    
    BBBW3 -->|WIFI| AP3
    AP3 -->|WIFI| SERVER3
    
    style BBBW3 fill:#e1f5ff
    style CAPE3 fill:#fff4e1
    style GESTURE fill:#ffe1e1
    style LEDMAT fill:#ffe1e1
    style OLED3 fill:#ffe1e1
    style BUZZ1 fill:#ffe1e1
    style AP3 fill:#f0e1ff
    style SERVER3 fill:#e1e1ff
```

**Components:**
- **BBBW BOARD**: BeagleBone Black Wireless (main processing unit)
- **MIKROE CAPE BOARD**: Expansion board providing Click board interfaces
- **Slot 1 (AN)**: IR Gesture Click - Touchless gesture interaction (swipe, select, push)
- **Slot 2 (PWM)**: LED Matrix Click - 8x8 LED matrix for visual status/confirmation
- **Slot 3 (I2C)**: OLED Click - Display prompts and feedback (128x64)
- **Slot 4 (SPI)**: Buzz 2 Click - Audio feedback for interactions

**Communication:**
- Connects wirelessly via WIFI to Access Point
- Data transmitted: User ratings, maintenance reports, gesture interactions, feedback timestamps

---

## Module 4: Security & Maintenance Alert Dashboard
**"Real-time monitoring for residents, security, and maintenance staff"**

```mermaid
graph TB
    subgraph "BBBW4 - Security & Maintenance Alert Dashboard"
        BBBW4[BBBW BOARD<br/>BeagleBone Black Wireless<br/>WIFI]
        CAPE4[MIKROE CAPE BOARD<br/>BBBW4]
        
        subgraph "Click Board Slots"
            SLOT1_AN4[Slot 1: AN<br/>Analog/GPIO]
            SLOT2_PWM4[Slot 2: PWM<br/>PWM/GPIO]
            SLOT3_I2C4[Slot 3: I2C<br/>I2C Bus]
            SLOT4_SPI4[Slot 4: SPI<br/>SPI Bus]
        end
        
        SEG7[7-Segment 8x8 Click<br/>8-Digit Display<br/>SPI]
        LEDMAT2[LED Matrix Click<br/>8x8 LED Matrix<br/>SPI]
        OLED4[OLED Click<br/>128x64 Display<br/>I2C]
        BUZZ2[Buzz 2 Click<br/>Buzzer<br/>GPIO/PWM]
        
        BBBW4 -->|Stacked| CAPE4
        CAPE4 --> SLOT1_AN4
        CAPE4 --> SLOT2_PWM4
        CAPE4 --> SLOT3_I2C4
        CAPE4 --> SLOT4_SPI4
        
        SLOT1_AN4 -->|SPI Signal<br/>Red Line| SEG7
        SLOT2_PWM4 -->|SPI Signal<br/>Red Line| LEDMAT2
        SLOT3_I2C4 -->|I2C Signal<br/>Red Line| OLED4
        SLOT4_SPI4 -->|GPIO/PWM Signal<br/>Red Line| BUZZ2
    end
    
    AP4[ACCESS POINT<br/>WIFI]
    SERVER4[PC WEB SERVER<br/>Flask/SocketIO]
    
    BBBW4 -->|WIFI| AP4
    AP4 -->|WIFI| SERVER4
    
    style BBBW4 fill:#e1f5ff
    style CAPE4 fill:#fff4e1
    style SEG7 fill:#ffe1e1
    style LEDMAT2 fill:#ffe1e1
    style OLED4 fill:#ffe1e1
    style BUZZ2 fill:#ffe1e1
    style AP4 fill:#f0e1ff
    style SERVER4 fill:#e1e1ff
```

**Components:**
- **BBBW BOARD**: BeagleBone Black Wireless (main processing unit)
- **MIKROE CAPE BOARD**: Expansion board providing Click board interfaces
- **Slot 1 (AN)**: 7-Segment 8x8 Click - Shows current active alerts count
- **Slot 2 (PWM)**: LED Matrix Click - Visual status indicators (at-a-glance health)
- **Slot 3 (I2C)**: OLED Click - Main alert display (128x64)
- **Slot 4 (SPI)**: Buzz 2 Click - Audio alerts for urgent issues

**Communication:**
- Connects wirelessly via WIFI to Access Point
- Receives data from: Module 1 (crowd alerts), Module 2 (environment warnings), Module 3 (feedback/ratings)
- Displays: Unusual activity alerts, maintenance issues, noise complaints, facility status

---

## System Overview - All Modules Connected

```mermaid
graph TB
    subgraph "Client Systems"
        M1[BBBW1<br/>Crowd Intelligence]
        M2[BBBW2<br/>Environmental Station]
        M3[BBBW3<br/>Feedback Kiosk]
        M4[BBBW4<br/>Security Dashboard]
    end
    
    AP[ACCESS POINT<br/>WIFI Hub]
    SERVER[PC WEB SERVER<br/>Flask/SocketIO<br/>Port 5000]
    
    M1 -->|WIFI| AP
    M2 -->|WIFI| AP
    M3 -->|WIFI| AP
    M4 -->|WIFI| AP
    
    AP -->|WIFI| SERVER
    
    style M1 fill:#e1f5ff
    style M2 fill:#e1f5ff
    style M3 fill:#e1f5ff
    style M4 fill:#e1f5ff
    style AP fill:#f0e1ff
    style SERVER fill:#e1e1ff
```

**Network Architecture:**
- All four BBBW modules connect wirelessly to a central Access Point
- Access Point routes data to PC Web Server running Flask/SocketIO
- Server aggregates data from all modules and provides web dashboard
- Real-time bidirectional communication via WebSocket (SocketIO)

---

## Connection Details

### Signal Types (as shown in diagrams):
- **Red Lines**: Power and ground connections
- **Black Lines with Labels**: Data/signal connections
  - **DIGITAL SIGNAL**: GPIO, digital I/O
  - **ANALOG SIGNAL**: ADC, analog input
  - **I2C Signal**: I2C bus communication
  - **SPI Signal**: SPI bus communication

### MikroE Cape Board Connection Points:
- **P8/GPIO**: General purpose I/O pins
- **P9/GPIO**: General purpose I/O pins  
- **PWM/GPIO**: PWM and GPIO functionality
- **DIGITAL**: Digital signal lines
- **ANALOG**: Analog signal lines

### Click Board Slot Functions:
- **Slot 1 (AN)**: Analog/GPIO - ADC access, analog inputs
- **Slot 2 (PWM)**: PWM/GPIO - PWM outputs, digital I/O
- **Slot 3 (I2C)**: I2C bus - Multiple I2C devices can share
- **Slot 4 (SPI)**: SPI bus - SPI devices with different CS pins

---

**Last Updated:** 2025-01-27  
**Version:** 1.0
