# J.A.R.V.I.S. // Complete Laptop Voice Monitor & Controller

A complete voice-operated AI system for your Windows PC powered by **`agent-desktop`**, **PyAudio**, and **Windows Accessibility & App Launchers**.

---

### Key Upgrades

1. **Strict Wake Word (`"Jarvis"`)**:
   - JARVIS now triggers **only when you start your sentence with "Jarvis"** (e.g., *"Jarvis, open..."*).
   - Casual background conversations or room noise are automatically ignored.

2. **WhatsApp Contact & Chat Automation**:
   - Understands any contact name:
     - *"Jarvis, open WhatsApp chat of Rahul"*
     - *"Jarvis, open chat with Mom on WhatsApp"*
     - *"Jarvis, message Priya on WhatsApp saying I will be there soon"*
   - Automatically focuses WhatsApp, searches the contact, opens their conversation, and types/sends your message.

3. **Universal Laptop Access (220+ Installed Apps)**:
   - Queries Windows `Get-StartApps` dynamically.
   - Any app installed on your laptop can be launched:
     - *"Jarvis, open Android Studio"*
     - *"Jarvis, open Excel"*
     - *"Jarvis, open Spotify"*
     - *"Jarvis, open Chrome"*
     - *"Jarvis, open Calculator"*
     - *"Jarvis, open VS Code"*

4. **GitHub & Web Automation**:
   - *"Jarvis, open my GitHub"* (opens `https://github.com/Somil450`)
   - *"Jarvis, open repo agent-desktop"* (opens your repo)
   - *"Jarvis, open ChatGPT"*
   - *"Jarvis, search [query] on Chrome"*
   - *"Jarvis, play [music] on YouTube"*

5. **Local Folders & System Controls**:
   - *"Jarvis, open downloads"*
   - *"Jarvis, open documents"*
   - *"Jarvis, minimize all windows"*
   - *"Jarvis, take a screenshot"*
   - *"Jarvis, volume up"* / *"volume down"* / *"mute"*
   - *"Jarvis, lock workstation"*
   - *"Jarvis, status report"*

---

### How to Run

1. Open PowerShell or double-click `run_jarvis.bat`.
2. Start speaking:
   > *"Jarvis, open WhatsApp chat of [Name]"*  
   > *"Jarvis, open my GitHub"*  
   > *"Jarvis, open ChatGPT"*
